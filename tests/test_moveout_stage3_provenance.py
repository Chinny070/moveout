"""Direct Mode coverage for frozen-image byte provenance verification."""

import hashlib
import io
import json
import re

from PIL import Image
import pytest


CONTRACT_PATH = "contracts/moveout_protocol_v1.py"
SOURCE = "https://assets.example.test/moveout/evidence.png"


def address(value):
    return "0x" + value.hex() if isinstance(value, bytes) else str(value)


def image_bytes(fmt="PNG", color=(210, 40, 30)):
    stream = io.BytesIO()
    Image.new("RGB", (8, 6), color).save(stream, format=fmt)
    return stream.getvalue()


def mock_image(vm, url, body, mime="image/png", status=200):
    vm.clear_mocks()
    vm.mock_web(re.escape(url), {
        "method": "GET",
        "response": {
            "status": status,
            "headers": {"content-type": mime.encode("ascii")},
            "body": body,
        },
    })


@pytest.fixture
def world(direct_deploy, direct_vm, direct_alice, direct_bob, direct_charlie):
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_alice
    prop = contract.create_property("Stage 3 Proof Property", "s3-property")
    unit = contract.create_unit(prop, "Unit A", "s3-unit")
    tenancy = contract.create_tenancy(prop, unit, address(direct_bob), "", "s3-tenancy")
    with direct_vm.prank(direct_bob):
        contract.activate_tenancy(tenancy)
    inspection = contract.create_inspection(tenancy, "MOVE_IN", "s3-inspection")
    room = contract.create_room(unit, "Bedroom", "s3-room")
    area = contract.create_area_item(room, "WALL", "North Wall", "", "s3-area")
    contract.include_area_in_inspection(inspection, area, "s3-include")
    return {"c": contract, "vm": direct_vm, "alice": direct_alice,
            "bob": direct_bob, "charlie": direct_charlie, "property": prop,
            "unit": unit, "tenancy": tenancy, "inspection": inspection,
            "room": room, "area": area}


def add_evidence(world, *, body=None, url=SOURCE, kind="PHOTO", expected=None,
                 freeze=True, request="evidence"):
    body = body if body is not None else image_bytes()
    expected = expected if expected is not None else hashlib.sha256(body).hexdigest()
    c = world["c"]
    evidence_id = c.submit_evidence(
        world["inspection"], world["area"], "", kind, url, expected, "",
        "s3-" + request,
    )
    if freeze:
        c.freeze_evidence(evidence_id)
        c.freeze_inspection(world["inspection"])
    return evidence_id, body


def verify(world, evidence_id, request="verify"):
    return world["c"].verify_evidence_provenance(
        world["tenancy"], evidence_id, "s3-" + request
    )


def test_nonexistent_evidence_rejected(world):
    with world["vm"].expect_revert("MO_ERR_NOT_FOUND"):
        verify(world, "EVID-999")


def test_unfrozen_evidence_rejected(world):
    evidence_id, _ = add_evidence(world, freeze=False, request="unfrozen")
    with world["vm"].expect_revert("MO_ERR_STATE"):
        verify(world, evidence_id, "unfrozen-call")


@pytest.mark.parametrize("source", ["http://assets.example.test/a.png", "https:///a.png",
                                     "https://user@assets.example.test/a.png",
                                     "https://assets.example.test/a.png#frag"])
def test_malformed_or_nonpublic_source_rejected(world, source):
    evidence_id, _ = add_evidence(world, url=source, request="bad-source" + str(len(source)))
    with world["vm"].expect_revert("MO_ERR_SOURCE"):
        verify(world, evidence_id, "bad-source-call" + str(len(source)))


def test_malformed_digest_rejected_before_retrieval(world):
    evidence_id, _ = add_evidence(world, request="tampered-digest")
    evidence = json.loads(world["c"].evidence_records[evidence_id])
    evidence["expected_sha256"] = "not-a-digest"
    world["c"].evidence_records[evidence_id] = json.dumps(evidence)
    with world["vm"].expect_revert("MO_ERR_SHA256"):
        verify(world, evidence_id, "malformed-digest-call")


@pytest.mark.parametrize("fmt,mime", [("PNG", "image/png"), ("JPEG", "image/jpeg")])
def test_matching_supported_image_is_verified(world, fmt, mime):
    body = image_bytes(fmt)
    evidence_id, _ = add_evidence(world, body=body, request="valid-" + fmt.lower())
    mock_image(world["vm"], SOURCE, body, mime)
    verification_id = verify(world, evidence_id, "valid-" + fmt.lower() + "-verify")
    result = json.loads(world["c"].get_evidence_verification(verification_id))
    assert result["outcome"] == "VERIFIED"
    assert result["retrieved_sha256"] == hashlib.sha256(body).hexdigest()
    assert result["expected_sha256"] == result["retrieved_sha256"]
    assert result["content_type"] == mime


def test_digest_mismatch_is_not_verified(world):
    body = image_bytes()
    evidence_id, _ = add_evidence(world, body=body, expected="0" * 64,
                                  request="wrong-digest")
    mock_image(world["vm"], SOURCE, body)
    verification_id = verify(world, evidence_id, "wrong-digest-verify")
    result = json.loads(world["c"].get_evidence_verification(verification_id))
    assert result["outcome"] == "DIGEST_MISMATCH"
    assert result["retrieved_sha256"] != result["expected_sha256"]


def test_html_is_invalid_even_when_http_succeeds_and_name_looks_like_png(world):
    body = b"<!doctype html><html><body>not an image</body></html>"
    evidence_id, _ = add_evidence(world, url=SOURCE, request="html-response")
    mock_image(world["vm"], SOURCE, body, "text/html")
    verification_id = verify(world, evidence_id, "html-verify")
    result = json.loads(world["c"].get_evidence_verification(verification_id))
    assert result["outcome"] == "INVALID_CONTENT"
    assert result["failure_code"] == "NON_IMAGE_CONTENT"
    assert result["retrieved_sha256"] == ""


def test_unsupported_image_mime_fails_closed(world):
    evidence_id, _ = add_evidence(world, request="webp")
    mock_image(world["vm"], SOURCE, b"RIFF0000WEBP", "image/webp")
    verification_id = verify(world, evidence_id, "webp-verify")
    result = json.loads(world["c"].get_evidence_verification(verification_id))
    assert result["outcome"] == "UNSUPPORTED"
    assert result["failure_code"] == "UNSUPPORTED_IMAGE_MEDIA_TYPE"


def test_format_signature_must_match_mime_and_source_extension_is_ignored(world):
    evidence_id, _ = add_evidence(world, url=SOURCE + "?name=looks-like.png",
                                  request="signature-mismatch")
    mock_image(world["vm"], SOURCE + "?name=looks-like.png", b"not png bytes", "image/png")
    verification_id = verify(world, evidence_id, "signature-mismatch-verify")
    result = json.loads(world["c"].get_evidence_verification(verification_id))
    assert result["outcome"] == "INVALID_CONTENT"
    assert result["failure_code"] == "PNG_SIGNATURE_OR_STRUCTURE"


def test_oversized_body_rejected_before_hashing(world):
    c = world["c"]
    body = b"x" * (int(c.MAX_VERIFICATION_BODY_BYTES) + 1)
    result = c._classify_verification_response(
        200, {"content-type": b"image/png"}, body, "0" * 64, "1" * 64,
    )
    assert result["outcome"] == "UNSUPPORTED"
    assert result["failure_code"] == "BODY_TOO_LARGE"
    assert result["retrieved_sha256"] == ""


def test_non_success_status_is_unavailable(world):
    evidence_id, _ = add_evidence(world, request="not-found")
    mock_image(world["vm"], SOURCE, b"Not Found", "text/plain", 404)
    verification_id = verify(world, evidence_id, "not-found-verify")
    result = json.loads(world["c"].get_evidence_verification(verification_id))
    assert result["outcome"] == "UNAVAILABLE"
    assert result["failure_code"] == "HTTP_STATUS"
    assert result["http_status"] == 404


def test_fetch_exception_is_recorded_as_unavailable(world):
    evidence_id, _ = add_evidence(world, request="fetch-error")
    # No web mock is registered: Direct Mode raises a mock lookup error.
    verification_id = verify(world, evidence_id, "fetch-error-verify")
    result = json.loads(world["c"].get_evidence_verification(verification_id))
    assert result["outcome"] == "UNAVAILABLE"
    assert result["failure_code"] == "FETCH_ERROR"


def test_unsupported_evidence_record_type_rejected(world):
    evidence_id, _ = add_evidence(world, kind="DOCUMENT", request="document-type")
    with world["vm"].expect_revert("MO_ERR_UNSUPPORTED_EVIDENCE_TYPE"):
        verify(world, evidence_id, "document-type-call")


def test_wrong_tenancy_and_unauthorized_actor_rejected(world):
    evidence_id, _ = add_evidence(world, request="scope")
    c = world["c"]
    second_unit = c.create_unit(world["property"], "Unit B", "s3-second-unit")
    other_tenancy = c.create_tenancy(
        world["property"], second_unit, address(world["charlie"]), "", "s3-other-tenancy"
    )
    with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
        c.verify_evidence_provenance(other_tenancy, evidence_id, "s3-wrong-tenancy")
    world["vm"].sender = world["charlie"]
    with world["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
        c.verify_evidence_provenance(world["tenancy"], evidence_id, "s3-unauthorized")


def test_tenant_participant_can_verify_frozen_evidence(world):
    evidence_id, body = add_evidence(world, request="tenant")
    mock_image(world["vm"], SOURCE, body)
    with world["vm"].prank(world["bob"]):
        verification_id = verify(world, evidence_id, "tenant-verify")
    assert json.loads(world["c"].get_evidence_verification(verification_id))["outcome"] == "VERIFIED"


def test_verification_does_not_mutate_evidence_or_create_visual_findings(world):
    evidence_id, body = add_evidence(world, request="immutable")
    before = world["c"].get_evidence(evidence_id)
    mock_image(world["vm"], SOURCE, body)
    verify(world, evidence_id, "immutable-verify")
    assert world["c"].get_evidence(evidence_id) == before
    assert json.loads(world["c"].list_visual_observations(world["inspection"], 0, 50))["items"] == []
    assert json.loads(world["c"].list_established_conditions(world["inspection"], 0, 50))["items"] == []


def test_participant_capture_metadata_cannot_force_verified(world):
    body = image_bytes()
    c = world["c"]
    slot_id = c.create_capture_slot(
        world["inspection"], world["area"], "OVERVIEW", "Wall overview",
        "Include the entire wall", "", "", "s3-metadata-slot",
    )
    evidence_id = c.submit_evidence_for_slot(
        world["inspection"], world["area"], slot_id, "", "PHOTO", SOURCE,
        "0" * 64, "", "NONE", "NORMAL", "Participant asserts this is verified",
        "s3-metadata-evidence",
    )
    c.freeze_evidence(evidence_id)
    c.freeze_inspection(world["inspection"])
    mock_image(world["vm"], SOURCE, body)

    verification_id = verify(world, evidence_id, "metadata-cannot-force")
    result = json.loads(c.get_evidence_verification(verification_id))
    evidence = json.loads(c.get_evidence(evidence_id))

    assert evidence["participant_capture_metadata"]["note_ref"] == (
        "Participant asserts this is verified"
    )
    assert result["outcome"] == "DIGEST_MISMATCH"
    assert result["outcome"] != "VERIFIED"


def test_reverification_appends_and_preserves_prior_record(world):
    first_body = image_bytes("PNG", (10, 80, 130))
    second_body = image_bytes("PNG", (80, 10, 130))
    evidence_id, _ = add_evidence(world, body=first_body, request="append-only")
    mock_image(world["vm"], SOURCE, first_body)
    first_id = verify(world, evidence_id, "first-verify")
    mock_image(world["vm"], SOURCE, second_body)
    second_id = verify(world, evidence_id, "second-verify")
    first = json.loads(world["c"].get_evidence_verification(first_id))
    second = json.loads(world["c"].get_evidence_verification(second_id))
    summary = json.loads(world["c"].get_evidence_verification_status(evidence_id))
    assert first["outcome"] == "VERIFIED"
    assert second["outcome"] == "DIGEST_MISMATCH"
    assert second["previous_verification_id"] == first_id
    assert summary["historically_verified"] is True
    assert summary["latest_differs_from_first"] is True


def test_same_request_id_replays_without_a_new_verification(world):
    evidence_id, body = add_evidence(world, request="idempotent")
    mock_image(world["vm"], SOURCE, body)
    first_id = verify(world, evidence_id, "same-request")
    second_id = verify(world, evidence_id, "same-request")
    assert first_id == second_id
    assert json.loads(world["c"].get_evidence_verification_status(evidence_id))["verification_count"] == 1


def test_validator_independently_fetches_and_rejects_changed_bytes(world):
    first_body = image_bytes("PNG", (12, 34, 56))
    changed_body = image_bytes("PNG", (56, 34, 12))
    evidence_id, _ = add_evidence(world, body=first_body, request="validator-independent")
    mock_image(world["vm"], SOURCE, first_body)
    verify(world, evidence_id, "validator-independent-call")
    assert world["vm"].run_validator() is True
    mock_image(world["vm"], SOURCE, changed_body)
    assert world["vm"].run_validator() is False


def test_validator_independently_accepts_same_frozen_bytes(world):
    body = image_bytes()
    evidence_id, _ = add_evidence(world, body=body, request="validator-same")
    mock_image(world["vm"], SOURCE, body)
    verify(world, evidence_id, "validator-same-call")
    assert world["vm"].run_validator() is True


def test_verification_history_read_is_bounded_and_paginated(world):
    body = image_bytes()
    evidence_id, _ = add_evidence(world, body=body, request="pagination")
    mock_image(world["vm"], SOURCE, body)
    verify(world, evidence_id, "pagination-first")
    verify(world, evidence_id, "pagination-second")
    first_page = json.loads(world["c"].list_evidence_verifications(evidence_id, 0, 1))
    second_page = json.loads(world["c"].list_evidence_verifications(evidence_id, 1, 1))
    assert len(first_page["items"]) == 1
    assert len(second_page["items"]) == 1
    assert first_page["items"][0]["verification_id"] != second_page["items"][0]["verification_id"]


def test_response_with_missing_content_type_fails_closed(world):
    body = image_bytes()
    result = world["c"]._classify_verification_response(
        200, {}, body, hashlib.sha256(body).hexdigest(), "1" * 64,
    )
    assert result["outcome"] == "INVALID_CONTENT"
    assert result["failure_code"] == "NON_IMAGE_CONTENT"
