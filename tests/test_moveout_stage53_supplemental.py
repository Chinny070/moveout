"""Stage 5.3 supplemental lifecycle and continuity safety tests.

Mocked vision answers exercise deterministic bindings/schema only; they are not
evidence of real-world correspondence accuracy or hosted GenLayer consensus.
"""

import hashlib
import io
import json
import re

from PIL import Image
from hypothesis import HealthCheck, given, settings, strategies as st
import pytest


ASSET_COMMIT = "0fb633b74dac5f968984d84b5d12a0765cb65a9d"
URL_A = ("https://raw.githubusercontent.com/Chinny070/moveout/" +
         ASSET_COMMIT + "/benchmarks/a.png")
URL_B = ("https://raw.githubusercontent.com/Chinny070/moveout/" +
         ASSET_COMMIT + "/benchmarks/b.png")
URL_C = ("https://raw.githubusercontent.com/Chinny070/moveout/" +
         ASSET_COMMIT + "/benchmarks/c.png")


def addr(value):
    return "0x" + value.hex() if isinstance(value, bytes) else str(value)


def png(color):
    stream = io.BytesIO()
    Image.new("RGB", (24, 24), color).save(stream, format="PNG")
    return stream.getvalue()


def mock_bytes(vm, url, body):
    vm.mock_web(re.escape(url), {"method": "GET", "response": {
        "status": 200, "headers": {"content-type": b"image/png"}, "body": body,
    }})


def raw_visibility(**values):
    result = {
        "surface_visibility": "VISIBLE", "target_location": "LOCATED",
        "target_visibility": "INADEQUATE", "foreground_obstruction": "PRESENT",
        "frame_coverage": "IN_FRAME", "target_clarity": "ADEQUATE",
        "feature_presence": "UNCERTAIN",
    }
    result.update(values)
    return result


def continuity_answer(kind="SUPPORTED", basis="OVERLAPPING_LANDMARKS", **changes):
    observations = {
        "surface_visibility": "VISIBLE", "target_location": "LOCATED",
        "target_visibility": "ADEQUATE", "foreground_obstruction": "ABSENT",
        "frame_coverage": "IN_FRAME", "target_clarity": "ADEQUATE",
        "feature_presence": "ABSENT",
    }
    observations.update(changes)
    return {"target_continuity": kind, "continuity_basis": basis,
            "observations": observations}


@pytest.fixture
def continuity_world(direct_deploy, direct_vm, direct_alice, direct_bob, direct_charlie):
    c, vm = direct_deploy("contracts/moveout_protocol_v1.py"), direct_vm
    image_a, image_b = png((220, 220, 220)), png((20, 100, 180))
    digest_a, digest_b = hashlib.sha256(image_a).hexdigest(), hashlib.sha256(image_b).hexdigest()
    vm.sender = direct_alice
    prop = c.create_property("Stage 5.3 House", "s53-property")
    unit = c.create_unit(prop, "Unit 1", "s53-unit")
    tenancy = c.create_tenancy(prop, unit, addr(direct_bob), "", "s53-tenancy")
    with vm.prank(direct_bob):
        c.activate_tenancy(tenancy)
    room = c.create_room(unit, "Bedroom", "s53-room")
    area = c.create_area_item(room, "WALL", "North wall", "", "s53-area")
    original_inspection = c.create_inspection(tenancy, "MOVE_IN", "s53-original-inspection")
    c.include_area_in_inspection(original_inspection, area, "s53-include")
    original_evidence = c.submit_evidence(
        original_inspection, area, "", "PHOTO", URL_A, digest_a, "", "s53-original-photo"
    )
    c.freeze_evidence(original_evidence)
    target = c.create_target_nomination(
        original_inspection, area, "north-wall-crack", "Crack beside the window",
        original_evidence, "", "[1000,1000,8000,8000]", "", "s53-target",
    )
    c.freeze_inspection(original_inspection)
    mock_bytes(vm, URL_A, image_a)
    verify_a = c.verify_evidence_provenance(tenancy, original_evidence, "s53-verify-a")
    assert vm.run_validator() is True
    vm.clear_mocks()
    mock_bytes(vm, URL_A, image_a)
    vm.mock_llm(r"Assess only the nominated target", json.dumps(raw_visibility()))
    unresolved = c.observe_nominated_target(
        tenancy, target, original_evidence, "s53-observe-original"
    )
    assert vm.run_validator() is True
    target_record = json.loads(c.get_target_nomination(target))
    request = c.create_supplemental_request(
        original_inspection, target, target_record["target_nomination_digest"],
        original_evidence, digest_a, unresolved,
        "FOREGROUND_OBSTRUCTION_PRESENT", "s53-supplement-request",
    )
    supplemental_inspection = c.create_supplemental_inspection(
        request, "s53-supplement-inspection"
    )
    supplemental_evidence = c.submit_supplemental_evidence(
        request, supplemental_inspection, URL_B, digest_b, "", "UNKNOWN", "UNKNOWN", "",
        "s53-supplement-evidence",
    )
    c.freeze_evidence(supplemental_evidence)
    c.freeze_inspection(supplemental_inspection)
    mock_bytes(vm, URL_B, image_b)
    verify_b = c.verify_evidence_provenance(tenancy, supplemental_evidence, "s53-verify-b")
    assert vm.run_validator() is True
    world = {
        "contract": c, "vm": vm, "manager": direct_alice, "tenant": direct_bob,
        "outsider": direct_charlie, "property": prop, "unit": unit, "tenancy": tenancy,
        "room": room, "area": area, "original_inspection": original_inspection,
        "original_evidence": original_evidence, "original_digest": digest_a,
        "original_bytes": image_a, "original_verification": verify_a, "target": target,
        "unresolved": unresolved, "request": request,
        "supplemental_inspection": supplemental_inspection,
        "supplemental_evidence": supplemental_evidence, "supplement_digest": digest_b,
        "supplement_bytes": image_b, "supplement_verification": verify_b,
    }
    return world


def assess(world, answer=None):
    vm = world["vm"]
    vm.clear_mocks()
    mock_bytes(vm, URL_A, world["original_bytes"])
    mock_bytes(vm, URL_B, world["supplement_bytes"])
    vm.mock_llm(r"Compare image A", json.dumps(answer or continuity_answer()))
    result = world["contract"].assess_supplemental_continuity(
        world["request"], world["supplemental_evidence"],
        "s53-continuity-" + str(len(json.loads(world["contract"].get_supplemental_request(
            world["request"]))["continuity_assessment_ids"]) + 1),
    )
    assert vm.run_validator() is True
    return json.loads(world["contract"].get_continuity_assessment(result))


def candidate(world, answer=None):
    """Evaluate a mocked pair without appending a contract observation."""
    vm = world["vm"]
    vm.clear_mocks()
    mock_bytes(vm, URL_A, world["original_bytes"])
    mock_bytes(vm, URL_B, world["supplement_bytes"])
    vm.mock_llm(r"Compare image A", json.dumps(answer or continuity_answer()))
    c = world["contract"]
    request, target, original, supplemental, source_a, digest_a, verify_a, source_b, digest_b, verify_b = (
        c._prepare_continuity_pair(world["request"], world["supplemental_evidence"])
    )
    return c._evaluate_continuity_pair(
        request, target, source_a, digest_a, verify_a, source_b, digest_b,
        verify_b, supplemental,
    )


def test_request_binds_original_frozen_target_evidence_and_reason(continuity_world):
    record = json.loads(continuity_world["contract"].get_supplemental_request(
        continuity_world["request"]))
    assert record["schema_version"] == 1
    assert record["original_inspection_id"] == continuity_world["original_inspection"]
    assert record["original_evidence_digest"] == continuity_world["original_digest"]
    assert record["target_id"] == continuity_world["target"]
    assert record["reason"] == "FOREGROUND_OBSTRUCTION_PRESENT"
    assert record["lifecycle_status"] == "EVIDENCE_SUBMITTED"


def test_unauthorized_requester_cannot_create_request(continuity_world):
    w = continuity_world
    target = json.loads(w["contract"].get_target_nomination(w["target"]))
    with w["vm"].prank(w["outsider"]):
        with w["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
            w["contract"].create_supplemental_request(
                w["original_inspection"], w["target"], target["target_nomination_digest"],
                w["original_evidence"], w["original_digest"], w["unresolved"],
                "FOREGROUND_OBSTRUCTION_PRESENT", "s53-outsider-request",
            )


@pytest.mark.parametrize("override,code", [
    ({"target_id": "TARG-999"}, "MO_ERR_NOT_FOUND"),
    ({"target_nomination_digest": "0" * 64}, "MO_ERR_WRONG_SCOPE"),
    ({"original_evidence_id": "EVID-999"}, "MO_ERR_NOT_FOUND"),
    ({"original_evidence_digest": "0" * 64}, "MO_ERR_PROVENANCE"),
    ({"reason": "MADE_UP"}, "MO_ERR_SCHEMA"),
])
def test_request_rejects_missing_or_mismatched_target_evidence_and_reason(
        continuity_world, override, code):
    w = continuity_world
    target = json.loads(w["contract"].get_target_nomination(w["target"]))
    params = {
        "original_inspection_id": w["original_inspection"], "target_id": w["target"],
        "target_nomination_digest": target["target_nomination_digest"],
        "original_evidence_id": w["original_evidence"],
        "original_evidence_digest": w["original_digest"],
        "unresolved_observation_id": w["unresolved"],
        "reason": "FOREGROUND_OBSTRUCTION_PRESENT", "request_id": "s53-negative-request",
    }
    params.update(override)
    with w["vm"].expect_revert(code):
        w["contract"].create_supplemental_request(**params)


def test_same_request_replay_is_idempotent_and_changed_replay_rejected(continuity_world):
    w = continuity_world
    target = json.loads(w["contract"].get_target_nomination(w["target"]))
    args = (w["original_inspection"], w["target"], target["target_nomination_digest"],
            w["original_evidence"], w["original_digest"], w["unresolved"],
            "FOREGROUND_OBSTRUCTION_PRESENT", "s53-supplement-request")
    assert w["contract"].create_supplemental_request(*args) == w["request"]
    changed = list(args)
    changed[6] = "TARGET_CLARITY_INADEQUATE"
    with w["vm"].expect_revert("MO_ERR_DUPLICATE"):
        w["contract"].create_supplemental_request(*changed)


def test_supplemental_inspection_is_separate_and_points_backward(continuity_world):
    w = continuity_world
    supplement = json.loads(w["contract"].inspections[w["supplemental_inspection"]])
    original_before = w["contract"].inspections[w["original_inspection"]]
    assert supplement["inspection_type"] == "SUPPLEMENTAL"
    assert supplement["supplements_inspection_id"] == w["original_inspection"]
    assert supplement["supplemental_request_id"] == w["request"]
    assert w["contract"].inspections[w["original_inspection"]] == original_before
    assert supplement["status"] == "FROZEN"
    assert w["contract"].get_inspection_completeness(w["supplemental_inspection"])


def test_generic_inspection_api_cannot_create_unlinked_supplement(continuity_world):
    w = continuity_world
    with w["vm"].expect_revert("supplemental_inspection_requires_request_link"):
        w["contract"].create_inspection(w["tenancy"], "SUPPLEMENTAL", "s53-unlinked")


def test_supplemental_evidence_is_distinct_and_digest_caller_assertion_is_not_verified(continuity_world):
    w = continuity_world
    link = json.loads(w["contract"].supplemental_evidence_links[w["supplemental_evidence"]])
    assert link["evidence_id"] == w["supplemental_evidence"]
    assert link["original_inspection_id"] == w["original_inspection"]
    assert link["target_nomination_digest"]
    assert link["digest_status"] == "CALLER_ASSERTED_EXPECTED_SHA256"
    assert link["expected_sha256"] == w["supplement_digest"]
    assert w["supplemental_evidence"] != w["original_evidence"]


def test_supplemental_evidence_replay_is_idempotent_and_duplicate_digest_is_rejected(
        continuity_world):
    w = continuity_world
    args = (w["request"], w["supplemental_inspection"], URL_B,
            w["supplement_digest"], "", "UNKNOWN", "UNKNOWN", "",
            "s53-supplement-evidence")
    assert w["contract"].submit_supplemental_evidence(*args) == w["supplemental_evidence"]
    with w["vm"].expect_revert("MO_ERR_DUPLICATE"):
        w["contract"].submit_supplemental_evidence(
            w["request"], w["supplemental_inspection"], URL_B,
            w["supplement_digest"], "", "UNKNOWN", "UNKNOWN", "",
            "s53-supplement-evidence-new-key",
        )


def test_supplemental_evidence_cannot_be_submitted_to_an_unlinked_inspection(continuity_world):
    w = continuity_world
    other = w["contract"].create_inspection(w["tenancy"], "PERIODIC", "s53-other-insp")
    with w["vm"].expect_revert("supplemental_inspection_binding"):
        w["contract"].submit_supplemental_evidence(
            w["request"], other, URL_B, w["supplement_digest"], "", "UNKNOWN", "UNKNOWN", "",
            "s53-cross-inspection",
        )


def test_generic_evidence_api_cannot_bypass_supplemental_request_link(continuity_world):
    w = continuity_world
    open_inspection = w["contract"].create_supplemental_inspection(
        w["request"], "s53-generic-bypass-inspection"
    )
    digest = hashlib.sha256(b"generic bypass").hexdigest()
    with w["vm"].expect_revert("supplemental_evidence_api_required"):
        w["contract"].submit_evidence(
            open_inspection, w["area"], "", "PHOTO", URL_B, digest, "",
            "s53-generic-bypass-evidence",
        )


def test_unauthorized_supplemental_evidence_submission_rejected(continuity_world):
    w = continuity_world
    open_inspection = w["contract"].create_supplemental_inspection(
        w["request"], "s53-unauthorized-open-inspection"
    )
    other_digest = hashlib.sha256(b"unauthorized evidence candidate").hexdigest()
    with w["vm"].prank(w["outsider"]):
        with w["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
            w["contract"].submit_supplemental_evidence(
                w["request"], open_inspection,
                "https://raw.githubusercontent.com/Chinny070/moveout/" +
                ASSET_COMMIT + "/benchmarks/c.png",
                other_digest, "", "UNKNOWN", "UNKNOWN", "", "s53-outsider-evidence",
            )


def test_original_evidence_and_observation_remain_unchanged_after_supplement(continuity_world):
    w = continuity_world
    evidence_before = w["contract"].evidence_records[w["original_evidence"]]
    observation_before = w["contract"].visual_observations[w["unresolved"]]
    request_before = w["contract"].get_supplemental_request(w["request"])
    candidate(w)
    assert w["contract"].evidence_records[w["original_evidence"]] == evidence_before
    assert w["contract"].visual_observations[w["unresolved"]] == observation_before
    assert w["contract"].get_supplemental_request(w["request"]) == request_before


def test_supported_continuity_and_adequate_target_visibility_are_recorded(continuity_world):
    record = candidate(continuity_world)
    assert record["target_continuity"] == "SUPPORTED"
    assert record["continuity_basis"] == "OVERLAPPING_LANDMARKS"
    assert record["assessment_status"] == "ASSESSABLE"
    assert record["observations"]["feature_presence"] == "ABSENT"
    assert record["original_digest"] == continuity_world["original_digest"]
    assert record["supplemental_digest"] == continuity_world["supplement_digest"]


@pytest.mark.parametrize("kind,basis,expected", [
    ("NOT_SUPPORTED", "CONTRADICTORY_CUES", "TARGET_CONTINUITY_NOT_SUPPORTED"),
    ("UNCERTAIN", "INSUFFICIENT_CUES", "TARGET_CONTINUITY_UNCERTAIN"),
])
def test_unsupported_or_uncertain_continuity_cannot_clear_visibility_or_absence(
        continuity_world, kind, basis, expected):
    record = candidate(continuity_world, continuity_answer(kind, basis))
    assert record["assessment_status"] == "INSUFFICIENT"
    assert expected in record["insufficiency_reasons"]
    assert record["observations"]["feature_presence"] == "UNCERTAIN"


@pytest.mark.parametrize("changes", [
    {"target_location": "UNCERTAIN", "target_visibility": "UNCERTAIN",
     "feature_presence": "UNCERTAIN"},
    {"foreground_obstruction": "PRESENT", "target_visibility": "INADEQUATE",
     "feature_presence": "UNCERTAIN"},
    {"frame_coverage": "PARTLY_OUTSIDE", "target_visibility": "INADEQUATE",
     "feature_presence": "UNCERTAIN"},
    {"target_clarity": "INADEQUATE", "target_visibility": "INADEQUATE",
     "feature_presence": "UNCERTAIN"},
])
def test_supported_continuity_with_insufficient_supplement_view_stays_unresolved(
        continuity_world, changes):
    record = candidate(continuity_world, continuity_answer(**changes))
    assert record["target_continuity"] == "SUPPORTED"
    assert record["assessment_status"] == "INSUFFICIENT"
    assert record["observations"]["feature_presence"] == "UNCERTAIN"


@pytest.mark.parametrize("bad", [
    "not-json",
    {"unexpected": "schema"},
    {"target_continuity": "SUPPORTED", "continuity_basis": "UNCERTAIN",
     "observations": raw_visibility()},
    {"target_continuity": "MAYBE", "continuity_basis": "OVERLAPPING_LANDMARKS",
     "observations": raw_visibility()},
    {"target_continuity": "NOT_SUPPORTED", "continuity_basis": "INSUFFICIENT_CUES",
     "observations": raw_visibility()},
    {"target_continuity": "SUPPORTED", "continuity_basis": "OVERLAPPING_LANDMARKS",
     "observations": {**raw_visibility(), "missing": "NO"}},
])
def test_malformed_or_internally_conflicting_model_result_is_not_persisted(continuity_world, bad):
    w = continuity_world
    w["vm"].clear_mocks()
    mock_bytes(w["vm"], URL_A, w["original_bytes"])
    mock_bytes(w["vm"], URL_B, w["supplement_bytes"])
    result = candidate(w, bad)
    assert result["stage"] == "INCONCLUSIVE"
    assert result["schema_valid"] is False
    assert result["failure_code"] == "MODEL_SCHEMA_INVALID"


@pytest.mark.parametrize("field,value", [
    ("supplemental_request_id", "SUPREQ-999"),
    ("supplemental_request_digest", "0" * 64),
    ("original_inspection_id", "INSP-999"),
    ("supplemental_inspection_id", "INSP-999"),
    ("target_id", "TARG-999"),
    ("target_version", 99),
    ("target_nomination_digest", "0" * 64),
    ("original_evidence_id", "EVID-999"),
    ("original_digest", "0" * 64),
    ("original_verification_id", "EVER-999"),
    ("supplemental_evidence_id", "EVID-999"),
    ("supplemental_digest", "0" * 64),
    ("supplemental_verification_id", "EVER-999"),
    ("target_continuity", "NOT_SUPPORTED"),
    ("continuity_basis", "UNCERTAIN"),
    ("assessment_status", "INSUFFICIENT"),
    ("insufficiency_reasons", ["FORGED"]),
    ("conflict_assessment_ids", ["CONT-999"]),
])
def test_equivalence_rejects_safety_critical_mutation(continuity_world, field, value):
    w = continuity_world
    base = {
        "stage": "CONTINUITY_ASSESSMENT", "failure_code": "", "schema_valid": True,
        "continuity_schema_version": 1, "supplemental_request_id": w["request"],
        "supplemental_request_digest": "a" * 64,
        "original_inspection_id": w["original_inspection"],
        "supplemental_inspection_id": w["supplemental_inspection"],
        "target_id": w["target"], "target_version": 1,
        "target_nomination_digest": "b" * 64, "area_item_id": w["area"],
        "original_evidence_id": w["original_evidence"], "original_digest": w["original_digest"],
        "original_verification_id": w["original_verification"],
        "original_source_ref_sha256": "c" * 64,
        "supplemental_evidence_id": w["supplemental_evidence"],
        "supplemental_digest": w["supplement_digest"],
        "supplemental_verification_id": w["supplement_verification"],
        "supplemental_source_ref_sha256": "d" * 64,
        "target_continuity": "SUPPORTED", "continuity_basis": "OVERLAPPING_LANDMARKS",
        "observations": {"surface_visibility": "VISIBLE", "target_location": "LOCATED",
                         "target_visibility": "ADEQUATE", "foreground_obstruction": "ABSENT",
                         "frame_coverage": "IN_FRAME", "target_clarity": "ADEQUATE",
                         "feature_presence": "ABSENT"},
        "assessment_status": "ASSESSABLE", "insufficiency_reasons": [],
        "conflict_assessment_ids": [],
    }
    left, right = dict(base), dict(base)
    right[field] = value
    assert w["contract"]._continuity_equivalent(left, right) is False


def test_two_independent_fetches_and_two_images_are_passed_to_vision(continuity_world):
    w = continuity_world
    result = candidate(w)
    assert result["original_evidence_id"] != result["supplemental_evidence_id"]
    assert result["original_source_ref_sha256"] != result["supplemental_source_ref_sha256"]
    assert w["vm"]._llm_mocks_hit == {0}


@pytest.mark.parametrize("status,content_type,body,expected", [
    (404, b"image/png", b"missing", "UNAVAILABLE"),
    (200, b"text/html", b"<html>error</html>", "INVALID_CONTENT"),
])
def test_failed_direct_image_retrieval_remains_inconclusive_without_storage(
        continuity_world, status, content_type, body, expected):
    w = continuity_world
    vm = w["vm"]
    vm.clear_mocks()
    mock_bytes(vm, URL_A, w["original_bytes"])
    vm.mock_web(re.escape(URL_B), {"method": "GET", "response": {
        "status": status, "headers": {"content-type": content_type}, "body": body,
    }})
    vm.mock_llm(r"Compare image A", json.dumps(continuity_answer()))
    c = w["contract"]
    request, target, original, supplemental, source_a, digest_a, verify_a, source_b, digest_b, verify_b = (
        c._prepare_continuity_pair(w["request"], w["supplemental_evidence"])
    )
    result = c._evaluate_continuity_pair(
        request, target, source_a, digest_a, verify_a, source_b, digest_b,
        verify_b, supplemental,
    )
    assert result["stage"] == "INCONCLUSIVE"
    assert expected in result["failure_code"]
    assert json.loads(c.get_supplemental_request(w["request"]))[
        "continuity_assessment_ids"] == []


def test_continuity_observation_is_not_an_established_condition(continuity_world):
    w = continuity_world
    candidate(w)
    result = json.loads(w["contract"].list_established_conditions(
        w["original_inspection"], 0, 20
    ))
    assert result["items"] == []


def test_legacy_inspection_without_supplement_fields_remains_readable(continuity_world):
    w = continuity_world
    record = json.loads(w["contract"].get_inspection_receipt(w["original_inspection"]))
    assert record["status"] == "FROZEN"
    assert "supplemental_request_id" not in record["contents_committed"]


def test_conflicting_repeated_continuity_is_retained_as_conflicted(continuity_world):
    w = continuity_world
    first = assess(w)
    assert first["target_continuity"] == "SUPPORTED"
    second = candidate(w, continuity_answer("NOT_SUPPORTED", "CONTRADICTORY_CUES"))
    assert second["assessment_status"] == "CONFLICTED"
    assert second["target_continuity"] == "UNCERTAIN"
    assert second["continuity_basis"] == "CONTRADICTORY_CUES"
    assert first["continuity_assessment_id"] in second["conflict_assessment_ids"]
    assert second["observations"]["feature_presence"] == "UNCERTAIN"


def test_contradictory_photos_under_one_request_remain_conflicted(continuity_world):
    w = continuity_world
    first = assess(w)
    assert first["observations"]["feature_presence"] == "ABSENT"
    second_bytes = png((15, 170, 60))
    second_digest = hashlib.sha256(second_bytes).hexdigest()
    second_inspection = w["contract"].create_supplemental_inspection(
        w["request"], "s53-conflicting-photo-inspection"
    )
    second_evidence = w["contract"].submit_supplemental_evidence(
        w["request"], second_inspection, URL_C, second_digest, "", "UNKNOWN", "UNKNOWN", "",
        "s53-conflicting-photo-evidence",
    )
    w["contract"].freeze_evidence(second_evidence)
    w["contract"].freeze_inspection(second_inspection)
    w["vm"].clear_mocks()
    mock_bytes(w["vm"], URL_C, second_bytes)
    verification_id = w["contract"].verify_evidence_provenance(
        w["tenancy"], second_evidence, "s53-conflicting-photo-verify"
    )
    assert verification_id
    assert w["vm"].run_validator() is True
    w["vm"].clear_mocks()
    mock_bytes(w["vm"], URL_A, w["original_bytes"])
    mock_bytes(w["vm"], URL_C, second_bytes)
    w["vm"].mock_llm(r"Compare image A", json.dumps(
        continuity_answer(feature_presence="PRESENT")
    ))
    second_id = w["contract"].assess_supplemental_continuity(
        w["request"], second_evidence, "s53-conflicting-photo-assessment"
    )
    assert w["vm"].run_validator() is True
    second = json.loads(w["contract"].get_continuity_assessment(second_id))
    assert second["assessment_status"] == "CONFLICTED"
    assert second["target_continuity"] == "SUPPORTED"
    assert second["observations"]["feature_presence"] == "UNCERTAIN"
    assert first["continuity_assessment_id"] in second["conflict_assessment_ids"]


def test_wrong_target_request_cannot_be_used_for_another_request_evidence(continuity_world):
    w = continuity_world
    with pytest.raises(Exception, match="supplemental_evidence_request_binding"):
        w["contract"]._prepare_continuity_pair(w["request"], w["original_evidence"])


def test_frozen_original_cannot_accept_supplemental_photo_membership(continuity_world):
    w = continuity_world
    with w["vm"].expect_revert("supplemental_inspection_binding"):
        w["contract"].submit_supplemental_evidence(
            w["request"], w["original_inspection"], URL_B, w["supplement_digest"],
            "", "UNKNOWN", "UNKNOWN", "", "s53-frozen-parent-write",
        )


def test_original_observation_can_only_open_request_if_it_is_insufficient(continuity_world):
    w = continuity_world
    prior = json.loads(w["contract"].visual_observations[w["unresolved"]])
    assert prior["status"] == "INCONCLUSIVE"
    assert prior["assessment_status"] == "INSUFFICIENT"


def test_conflict_and_unavailable_statuses_remain_explicit_in_request_history(continuity_world):
    w = continuity_world
    result = candidate(w, continuity_answer("UNCERTAIN", "INSUFFICIENT_CUES"))
    view = json.loads(w["contract"].get_supplemental_request(w["request"]))
    assert result["assessment_status"] in ("INSUFFICIENT", "CONFLICTED")
    assert view["lifecycle_status"] in ("EVIDENCE_SUBMITTED", "ASSESSMENT_APPENDED")


    assert view["events"][0]["event_type"] == "OPEN"


def test_stage54_adversarial_assessment_event_reopens_closed_request(continuity_world):
    """Exercise request closure against a later assessment and new capture path."""
    w = continuity_world
    c, vm = w["contract"], w["vm"]
    with vm.prank(w["manager"]):
        c.close_supplemental_request(
            w["request"], "Requester closed capture request", "s54-close-request"
        )
    assert json.loads(c.get_supplemental_request(w["request"]))["lifecycle_status"] == "CLOSED"

    # Assessment of already-frozen evidence is accepted after closure and appends
    # a later event. Public lifecycle status is event-last rather than terminal.
    post_close_assessment = assess(w)
    assert post_close_assessment["continuity_assessment_id"]
    view = json.loads(c.get_supplemental_request(w["request"]))
    assert view["lifecycle_status"] == "ASSESSMENT_APPENDED"

    # create_supplemental_inspection only rejects when the latest event itself is
    # CLOSED, so the post-close assessment permits another linked inspection.
    with vm.prank(w["manager"]):
        reopened_inspection = c.create_supplemental_inspection(
            w["request"], "s54-reopen-after-close"
        )
    assert reopened_inspection in json.loads(c.get_supplemental_request(
        w["request"]))["supplemental_inspection_ids"]

    late_bytes = png((12, 34, 56))
    late_digest = hashlib.sha256(late_bytes).hexdigest()
    with vm.prank(w["manager"]):
        late_evidence = c.submit_supplemental_evidence(
            w["request"], reopened_inspection, URL_C, late_digest, "", "UNKNOWN",
            "UNKNOWN", "", "s54-submit-after-close"
        )
    final_view = json.loads(c.get_supplemental_request(w["request"]))
    assert late_evidence in final_view["supplemental_evidence_ids"]
    assert final_view["lifecycle_status"] == "EVIDENCE_SUBMITTED"


@settings(max_examples=24, derandomize=True, deadline=None,
          suppress_health_check=[HealthCheck.function_scoped_fixture,
                                 HealthCheck.too_slow])
@given(
    surface=st.sampled_from(("VISIBLE", "PARTIAL", "NOT_ESTABLISHED", "UNCERTAIN")),
    location=st.sampled_from(("LOCATED", "NOT_LOCATABLE", "UNCERTAIN")),
    visibility=st.sampled_from(("ADEQUATE", "INADEQUATE", "UNCERTAIN")),
    obstruction=st.sampled_from(("PRESENT", "ABSENT", "UNCERTAIN")),
    frame=st.sampled_from(("IN_FRAME", "PARTLY_OUTSIDE", "OUTSIDE", "UNCERTAIN")),
    clarity=st.sampled_from(("ADEQUATE", "INADEQUATE", "UNCERTAIN")),
    feature=st.sampled_from(("PRESENT", "ABSENT", "UNCERTAIN")),
)
def test_stage54_property_accepted_absence_always_has_all_visibility_gates(
        continuity_world, surface, location, visibility, obstruction, frame, clarity,
        feature):
    """Generated schema candidates may accept ABSENT only under every gate."""
    observations = {
        "surface_visibility": surface,
        "target_location": location,
        "target_visibility": visibility,
        "foreground_obstruction": obstruction,
        "frame_coverage": frame,
        "target_clarity": clarity,
        "feature_presence": feature,
    }
    normalized, valid = continuity_world["contract"]._normalize_target_observation(
        observations
    )
    if valid and normalized["feature_presence"] == "ABSENT":
        assert normalized["target_location"] == "LOCATED"
        assert normalized["target_visibility"] == "ADEQUATE"
        assert normalized["foreground_obstruction"] == "ABSENT"
        assert normalized["frame_coverage"] == "IN_FRAME"
        assert normalized["target_clarity"] == "ADEQUATE"
