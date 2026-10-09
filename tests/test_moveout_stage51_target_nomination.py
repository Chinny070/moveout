"""Direct Mode tests for Stage 5.1 target nomination/storage only."""

import hashlib
import io
import json
import re

import pytest
from PIL import Image


CONTRACT_PATH = "contracts/moveout_protocol_v1.py"
SHA = "a" * 64


def address(value):
    if isinstance(value, bytes):
        return "0x" + value.hex()
    return str(value)


@pytest.fixture
def nomination_world(direct_deploy, direct_vm, direct_alice, direct_bob, direct_charlie):
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_alice
    property_id = contract.create_property("Nomination House", "n-prop")
    unit_id = contract.create_unit(property_id, "Unit 1", "n-unit")
    tenancy_id = contract.create_tenancy(
        property_id, unit_id, address(direct_bob), "test tenancy", "n-tenancy"
    )
    with direct_vm.prank(direct_bob):
        contract.activate_tenancy(tenancy_id)
    room_id = contract.create_room(unit_id, "Bedroom", "n-room")
    area_id = contract.create_area_item(room_id, "WALL", "North Wall", "", "n-area")
    inspection_id = contract.create_inspection(tenancy_id, "MOVE_IN", "n-inspection")
    with direct_vm.prank(direct_bob):
        contract.include_area_in_inspection(inspection_id, area_id, "n-area-include")
    return {
        "contract": contract, "vm": direct_vm, "manager": direct_alice,
        "tenant": direct_bob, "outsider": direct_charlie,
        "property": property_id, "unit": unit_id, "tenancy": tenancy_id,
        "room": room_id, "area": area_id, "inspection": inspection_id,
    }


def nominate(world, *, inspection=None, area=None, identifier="north-wall",
             description="North wall near the bedroom window", evidence="",
             slot="", box="", supersedes="", request="target-request"):
    return world["contract"].create_target_nomination(
        inspection or world["inspection"], area or world["area"], identifier,
        description, evidence, slot, box, supersedes, request,
    )


def make_frozen_photo(world, inspection=None, area=None, request="photo"):
    c = world["contract"]
    inspection = inspection or world["inspection"]
    area = area or world["area"]
    evidence_id = c.submit_evidence(
        inspection, area, "", "PHOTO", "https://evidence.example/photo.png",
        SHA, "", request,
    )
    c.freeze_evidence(evidence_id)
    return evidence_id


def png_bytes():
    stream = io.BytesIO()
    Image.new("RGB", (2, 2), (30, 100, 180)).save(stream, format="PNG")
    return stream.getvalue()


def test_authorized_tenant_can_create_target_nomination(nomination_world):
    w = nomination_world
    with w["vm"].prank(w["tenant"]):
        target_id = nominate(w)
    record = json.loads(w["contract"].get_target_nomination(target_id))
    assert record["target_id"] == target_id
    assert record["target_identifier"] == "north-wall"
    assert record["target_description"] == "North wall near the bedroom window"
    assert record["inspection_id"] == w["inspection"]
    assert record["area_item_id"] == w["area"]
    assert record["creator"].lower() == address(w["tenant"]).lower()
    assert record["creator_side"] == "TENANT"
    assert record["schema_version"] == 1
    assert record["lifecycle_status"] == "NOMINATED"


def test_unauthorized_actor_cannot_nominate(nomination_world):
    w = nomination_world
    with w["vm"].prank(w["outsider"]):
        with w["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
            nominate(w)


def test_invalid_inspection_and_area_references_are_rejected(nomination_world):
    w = nomination_world
    with w["vm"].prank(w["tenant"]):
        with w["vm"].expect_revert("MO_ERR_NOT_FOUND"):
            nominate(w, inspection="INSP-999", request="bad-inspection")
        with w["vm"].expect_revert("MO_ERR_NOT_FOUND"):
            nominate(w, area="AREA-999", request="bad-area")


def test_duplicate_identity_requires_explicit_new_version(nomination_world):
    w = nomination_world
    with w["vm"].prank(w["tenant"]):
        original = nominate(w, request="identity-first")
        with w["vm"].expect_revert("MO_ERR_DUPLICATE"):
            nominate(w, request="identity-duplicate")
        revised = nominate(w, description="North wall beside window", supersedes=original,
                           request="identity-revision")
    old = json.loads(w["contract"].get_target_nomination(original))
    new = json.loads(w["contract"].get_target_nomination(revised))
    assert new["target_version"] == old["target_version"] + 1
    assert old["lifecycle_status"] == "SUPERSEDED"
    assert new["is_latest_version"] is True
    assert old["target_nomination_digest"] != new["target_nomination_digest"]


def test_user_cannot_choose_or_reuse_contract_target_id(nomination_world):
    w = nomination_world
    with w["vm"].prank(w["tenant"]):
        target_id = nominate(w)
        assert target_id.startswith("TARG-")
        with w["vm"].expect_revert("MO_ERR_SCHEMA"):
            nominate(w, identifier=target_id, request="target-id-injection")


def test_same_identifier_in_another_inspection_gets_new_global_target_id(nomination_world):
    w = nomination_world
    with w["vm"].prank(w["tenant"]):
        first = nominate(w, request="same-key-a")
        second_inspection = w["contract"].create_inspection(
            w["tenancy"], "PERIODIC", "second-inspection"
        )
        second = nominate(w, inspection=second_inspection, request="same-key-b")
    assert first != second
    assert json.loads(w["contract"].get_target_nomination(first))["inspection_id"] != \
        json.loads(w["contract"].get_target_nomination(second))["inspection_id"]


def test_canonical_digest_is_deterministic_independent_of_mapping_order(nomination_world):
    c = nomination_world["contract"]
    first = {"digest_domain": "MOVEOUT_TARGET_NOMINATION_V1", "schema_version": 1,
             "target_id": "TARG-1", "region_box": {"x_min": 1, "y_min": 2}}
    second = {"region_box": {"y_min": 2, "x_min": 1}, "target_id": "TARG-1",
              "schema_version": 1, "digest_domain": "MOVEOUT_TARGET_NOMINATION_V1"}
    assert c._json(first) == c._json(second)
    # The production digest uses an explicit field whitelist and canonical JSON.
    record = {
        "digest_domain": "MOVEOUT_TARGET_NOMINATION_V1", "schema_version": 1,
        "target_id": "TARG-1", "target_version": 1, "target_identifier": "north-wall",
        "target_description": "North wall", "inspection_id": "INSP-1",
        "property_id": "PROP-1", "unit_id": "UNIT-1", "tenancy_id": "TEN-1",
        "room_id": "ROOM-1", "area_item_id": "AREA-1", "reference_evidence_id": "",
        "reference_digest": "", "reference_digest_status": "NONE",
        "reference_verification_id": "", "reference_capture_slot_id": "",
        "region_box": None, "creator": "0x1", "creator_side": "TENANT",
        "created_at": "100", "supersedes_target_id": "",
    }
    reversed_record = dict(reversed(list(record.items())))
    assert c._target_nomination_digest(record) == c._target_nomination_digest(reversed_record)
    assert len(c._target_nomination_digest(record)) == 64


def test_box_nomination_binds_frozen_evidence_and_marks_unverified_digest(nomination_world):
    w = nomination_world
    evidence_id = make_frozen_photo(w)
    with w["vm"].prank(w["tenant"]):
        target_id = nominate(w, evidence=evidence_id,
                             box='[100,200,900,1200]', request="box-target")
    record = json.loads(w["contract"].get_target_nomination(target_id))
    assert record["reference_evidence_id"] == evidence_id
    assert record["reference_digest"] == SHA
    assert record["reference_digest_status"] == "CALLER_ASSERTED_EXPECTED_SHA256"
    assert record["region_box"] == {
        "x_min": 100, "y_min": 200, "x_max": 900, "y_max": 1200,
    }
    assert len(record["target_nomination_digest"]) == 64


def test_verified_reference_digest_is_distinguished_from_caller_assertion(nomination_world):
    w = nomination_world
    c = w["contract"]
    body = png_bytes()
    source = "https://assets.example.test/reference.png"
    evidence_id = c.submit_evidence(
        w["inspection"], w["area"], "", "PHOTO", source,
        hashlib.sha256(body).hexdigest(), "", "verified-reference-photo",
    )
    c.freeze_evidence(evidence_id)
    with w["vm"].prank(w["tenant"]):
        target_id = nominate(w, evidence=evidence_id, box="[0,0,10000,10000]",
                             request="verified-reference-target")
    c.freeze_inspection(w["inspection"])
    w["vm"].mock_web(re.escape(source), {
        "method": "GET", "response": {
            "status": 200,
            "headers": {"content-type": b"image/png"},
            "body": body,
        },
    })
    verification_id = c.verify_evidence_provenance(
        w["tenancy"], evidence_id, "verified-reference-check"
    )
    record = json.loads(c.get_target_nomination(target_id))
    assert record["reference_digest_status"] == "CALLER_ASSERTED_EXPECTED_SHA256"
    assert record["reference_verification_id"] == ""
    assert record["reference_provenance"]["status"] == "VERIFIED_RETRIEVED_SHA256"
    assert record["reference_provenance"]["verification_id"] == verification_id
    assert record["reference_digest"] == hashlib.sha256(body).hexdigest()


def test_digest_mismatch_remains_visible_and_never_becomes_verified(nomination_world):
    w = nomination_world
    c = w["contract"]
    body = png_bytes()
    source = "https://assets.example.test/mismatch.png"
    evidence_id = c.submit_evidence(
        w["inspection"], w["area"], "", "PHOTO", source,
        "0" * 64, "", "mismatch-reference-photo",
    )
    c.freeze_evidence(evidence_id)
    with w["vm"].prank(w["tenant"]):
        target_id = nominate(w, evidence=evidence_id, box="[0,0,10000,10000]",
                             request="mismatch-reference-target")
    c.freeze_inspection(w["inspection"])
    w["vm"].mock_web(re.escape(source), {
        "method": "GET", "response": {
            "status": 200,
            "headers": {"content-type": b"image/png"},
            "body": body,
        },
    })
    verification_id = c.verify_evidence_provenance(
        w["tenancy"], evidence_id, "mismatch-reference-check"
    )
    record = json.loads(c.get_target_nomination(target_id))
    assert record["reference_digest_status"] == "CALLER_ASSERTED_EXPECTED_SHA256"
    assert record["reference_digest"] == "0" * 64
    assert record["reference_provenance"]["verification_id"] == verification_id
    assert record["reference_provenance"]["status"] == "DIGEST_MISMATCH"


def test_capture_slot_reference_is_bound_to_same_inspection_area(nomination_world):
    w = nomination_world
    c = w["contract"]
    with w["vm"].prank(w["tenant"]):
        slot_id = c.create_capture_slot(
            w["inspection"], w["area"], "OVERVIEW", "North wall", "", "", "",
            "target-ref-slot",
        )
    evidence_id = c.submit_evidence_for_slot(
        w["inspection"], w["area"], slot_id, "", "PHOTO",
        "https://evidence.example/slot.png", SHA, "", "UNKNOWN", "UNKNOWN", "",
        "slot-reference-photo",
    )
    c.freeze_evidence(evidence_id)
    with w["vm"].prank(w["tenant"]):
        target_id = nominate(w, evidence=evidence_id, request="target-slot-binding")
    record = json.loads(c.get_target_nomination(target_id))
    assert record["reference_capture_slot_id"] == slot_id


def test_region_box_requires_evidence_and_exact_schema(nomination_world):
    w = nomination_world
    with w["vm"].prank(w["tenant"]):
        with w["vm"].expect_revert("MO_ERR_SCHEMA"):
            nominate(w, box='[0,0,10,10]',
                     request="box-without-evidence")
        with w["vm"].expect_revert("MO_ERR_SCHEMA"):
            nominate(w, evidence="", box="not-json", request="malformed-box")
        with w["vm"].expect_revert("MO_ERR_SCHEMA"):
            nominate(w, box=None, request="non-string-box")
        with w["vm"].expect_revert("MO_ERR_SCHEMA"):
            nominate(w, evidence="", box='[0,0,1,1,2]',
                     request="extra-box-field")


@pytest.mark.parametrize("box", [
    '[0,0,0,1]',
    '[0,2,1,1]',
    '[-1,0,1,1]',
    '[0,0,10001,1]',
    '[0.5,0,1,1]',
    '[true,0,1,1]',
])
def test_invalid_box_coordinates_rejected(nomination_world, box):
    w = nomination_world
    evidence_id = make_frozen_photo(w, request="box-photo-" + str(len(box)))
    with w["vm"].prank(w["tenant"]):
        with w["vm"].expect_revert():
            nominate(w, evidence=evidence_id, box=box, request="invalid-box-" + str(len(box)))


def test_evidence_reference_must_be_frozen_and_bound_to_same_inspection_area(nomination_world):
    w = nomination_world
    c = w["contract"]
    pending = c.submit_evidence(w["inspection"], w["area"], "", "PHOTO",
                                "https://evidence.example/pending.png", SHA, "", "pending-photo")
    with w["vm"].prank(w["tenant"]):
        with w["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
            nominate(w, evidence=pending, box='[0,0,1,1]',
                     request="pending-evidence-target")

        with w["vm"].prank(w["manager"]):
            other_room = c.create_room(w["unit"], "Hall", "other-room")
            other_area = c.create_area_item(
                other_room, "WALL", "Hall Wall", "", "other-area"
            )
        other_inspection = c.create_inspection(w["tenancy"], "PERIODIC", "other-inspection")
        other_evidence = make_frozen_photo(w, other_inspection, other_area, "other-photo")
        with w["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
            nominate(w, evidence=other_evidence,
                     box='[0,0,1,1]',
                     request="cross-inspection-evidence")


def test_creator_can_add_multiple_targets_in_one_area(nomination_world):
    w = nomination_world
    with w["vm"].prank(w["tenant"]):
        first = nominate(w, identifier="window-frame", request="window-target")
        second = nominate(w, identifier="wall-outlet", request="outlet-target")
    assert first != second
    page = json.loads(w["contract"].list_area_target_nominations(
        w["inspection"], w["area"], 0, 10
    ))
    assert [item["target_id"] for item in page["items"]] == [first, second]


def test_target_membership_freezes_with_inspection(nomination_world):
    w = nomination_world
    c = w["contract"]
    with w["vm"].prank(w["tenant"]):
        target_id = nominate(w, request="freeze-target")
    make_frozen_photo(w, request="freeze-evidence")
    before = c.get_target_nomination(target_id)
    c.freeze_inspection(w["inspection"])
    inspection = json.loads(c.get_inspection(w["inspection"]))
    assert inspection["contents_committed"]["target_nomination_ids"] == [target_id]
    after = json.loads(c.get_target_nomination(target_id))
    assert after["lifecycle_status"] == "FROZEN"
    assert after["target_nomination_digest"] == json.loads(before)["target_nomination_digest"]
    assert after["creator"] == json.loads(before)["creator"]


def test_frozen_inspection_rejects_new_target_and_has_no_mutation_or_delete_api(nomination_world):
    w = nomination_world
    c = w["contract"]
    with w["vm"].prank(w["tenant"]):
        target_id = nominate(w, request="frozen-target")
    make_frozen_photo(w, request="frozen-evidence")
    c.freeze_inspection(w["inspection"])
    before_inspection = c.get_inspection(w["inspection"])
    before_target = c.get_target_nomination(target_id)
    with w["vm"].prank(w["tenant"]):
        with w["vm"].expect_revert("MO_ERR_FROZEN_INSPECTION"):
            nominate(w, identifier="late-target", request="late-target")
    assert c.get_inspection(w["inspection"]) == before_inspection
    assert c.get_target_nomination(target_id) == before_target
    assert not hasattr(c, "delete_target_nomination")
    assert not hasattr(c, "update_target_nomination")


def test_legacy_inspection_without_target_fields_still_reads_and_freezes(nomination_world):
    w = nomination_world
    c = w["contract"]
    inspection = json.loads(c.get_inspection(w["inspection"]))
    inspection.pop("target_nomination_ids", None)
    c.inspections[w["inspection"]] = c._json(inspection)
    make_frozen_photo(w, request="legacy-freeze-evidence")
    assert json.loads(c.list_target_nominations(w["inspection"], 0, 10))["items"] == []
    c.freeze_inspection(w["inspection"])
    frozen = json.loads(c.get_inspection(w["inspection"]))
    assert frozen["contents_committed"]["target_nomination_ids"] == []


def test_area_membership_and_evidence_digest_are_unchanged_by_nomination(nomination_world):
    w = nomination_world
    c = w["contract"]
    evidence_id = make_frozen_photo(w)
    evidence_before = c.get_evidence(evidence_id)
    inspection_before = json.loads(c.get_inspection(w["inspection"]))
    with w["vm"].prank(w["tenant"]):
        nominate(w, request="nonmutating-target")
    evidence_after = c.get_evidence(evidence_id)
    inspection_after = json.loads(c.get_inspection(w["inspection"]))
    assert evidence_after == evidence_before
    assert json.loads(evidence_after)["expected_sha256"] == SHA
    assert inspection_after["evidence_ids"] == inspection_before["evidence_ids"]
    assert inspection_after["target_nomination_ids"] != []


def test_area_and_inspection_lists_are_stable_bounded_and_paged(nomination_world):
    w = nomination_world
    with w["vm"].prank(w["tenant"]):
        first = nominate(w, identifier="north-wall", request="page-one")
        second = nominate(w, identifier="south-wall", request="page-two")
    c = w["contract"]
    first_page = json.loads(c.list_target_nominations(w["inspection"], 0, 1))
    second_page = json.loads(c.list_target_nominations(w["inspection"], 1, 1))
    assert first_page["items"][0]["target_id"] == first
    assert first_page["has_more"] is True
    assert second_page["items"][0]["target_id"] == second
    assert second_page["has_more"] is False
    with w["vm"].expect_revert("MO_ERR_BOUNDS"):
        c.list_target_nominations(w["inspection"], 0, 51)


def test_nomination_request_retry_is_idempotent_and_payload_reuse_rejected(nomination_world):
    w = nomination_world
    with w["vm"].prank(w["tenant"]):
        first = nominate(w, request="target-idempotency")
        assert nominate(w, request="target-idempotency") == first
        with w["vm"].expect_revert("MO_ERR_DUPLICATE"):
            nominate(w, description="Different nomination", request="target-idempotency")


def test_bad_identifier_malformed_fields_and_revision_context_rejected(nomination_world):
    w = nomination_world
    with w["vm"].prank(w["tenant"]):
        with w["vm"].expect_revert("MO_ERR_SCHEMA"):
            nominate(w, identifier="North Wall", request="uppercase-key")
        with w["vm"].expect_revert("MO_ERR_BOUNDS"):
            nominate(w, identifier="", request="empty-key")
        with w["vm"].expect_revert("MO_ERR_NOT_FOUND"):
            nominate(w, supersedes="TARG-999", request="missing-supersedes")


def test_reference_capture_slot_must_match_bound_photo(nomination_world):
    w = nomination_world
    c = w["contract"]
    evidence_id = make_frozen_photo(w)
    with w["vm"].prank(w["tenant"]):
        slot_id = c.create_capture_slot(
            w["inspection"], w["area"], "DETAIL", "Detail", "", "", "", "n-slot"
        )
        with w["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
            nominate(w, evidence=evidence_id, slot=slot_id, request="mismatched-slot")


def test_cross_inspection_supersession_is_rejected(nomination_world):
    w = nomination_world
    with w["vm"].prank(w["tenant"]):
        first = nominate(w, request="version-a")
        second_inspection = w["contract"].create_inspection(
            w["tenancy"], "PERIODIC", "version-other-inspection"
        )
        with w["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
            nominate(w, inspection=second_inspection, supersedes=first,
                     request="version-cross-inspection")
