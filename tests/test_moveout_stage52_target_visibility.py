"""Stage 5.2 deterministic target visibility schema and callback tests.

These tests prove only contract validation, binding, storage, and comparator
behavior. They do not establish visual-model accuracy or hosted quorum behavior.
"""

import hashlib
import io
import json
import re

from PIL import Image
import pytest


URL = ("https://raw.githubusercontent.com/Chinny070/moveout/"
       "0fb633b74dac5f968984d84b5d12a0765cb65a9d/benchmarks/a.png")


def address(value):
    return "0x" + value.hex() if isinstance(value, bytes) else str(value)


def png_bytes():
    stream = io.BytesIO()
    Image.new("RGB", (24, 24), (220, 220, 220)).save(stream, format="PNG")
    return stream.getvalue()


def mock_image(vm, body):
    vm.mock_web(re.escape(URL), {
        "method": "GET", "response": {
            "status": 200,
            "headers": {"content-type": b"image/png"},
            "body": body,
        },
    })


def target_result(**updates):
    result = {
        "surface_visibility": "VISIBLE",
        "target_location": "LOCATED",
        "target_visibility": "ADEQUATE",
        "foreground_obstruction": "ABSENT",
        "frame_coverage": "IN_FRAME",
        "target_clarity": "ADEQUATE",
        "feature_presence": "ABSENT",
    }
    result.update(updates)
    return result


@pytest.fixture
def target_world(direct_deploy, direct_vm, direct_alice, direct_bob, direct_charlie):
    contract = direct_deploy("contracts/moveout_protocol_v1.py")
    direct_vm.sender = direct_alice
    property_id = contract.create_property("Stage 5.2 House", "s52-property")
    unit_id = contract.create_unit(property_id, "Unit 1", "s52-unit")
    tenancy_id = contract.create_tenancy(
        property_id, unit_id, address(direct_bob), "test tenancy", "s52-tenancy"
    )
    with direct_vm.prank(direct_bob):
        contract.activate_tenancy(tenancy_id)
    room_id = contract.create_room(unit_id, "Bedroom", "s52-room")
    area_id = contract.create_area_item(room_id, "WALL", "North Wall", "", "s52-area")
    inspection_id = contract.create_inspection(tenancy_id, "MOVE_IN", "s52-inspection")
    contract.include_area_in_inspection(inspection_id, area_id, "s52-include")
    body = png_bytes()
    digest = hashlib.sha256(body).hexdigest()
    evidence_id = contract.submit_evidence(
        inspection_id, area_id, "", "PHOTO", URL, digest, "", "s52-evidence"
    )
    contract.freeze_evidence(evidence_id)
    target_id = contract.create_target_nomination(
        inspection_id, area_id, "north-wall-mark", "Mark beside the bedroom window",
        evidence_id, "", "[1000,1000,8000,8000]", "", "s52-target",
    )
    contract.freeze_inspection(inspection_id)
    mock_image(direct_vm, body)
    verification_id = contract.verify_evidence_provenance(
        tenancy_id, evidence_id, "s52-verify"
    )
    assert direct_vm.run_validator() is True
    return {
        "contract": contract, "vm": direct_vm, "manager": direct_alice,
        "tenant": direct_bob, "outsider": direct_charlie,
        "property": property_id, "unit": unit_id, "tenancy": tenancy_id,
        "inspection": inspection_id, "room": room_id, "area": area_id,
        "evidence": evidence_id, "target": target_id, "digest": digest,
        "body": body, "verification": verification_id,
    }


def observe(world, answer=None):
    world["vm"].clear_mocks()
    mock_image(world["vm"], world["body"])
    world["vm"].mock_llm(
        r"Assess only the nominated target",
        json.dumps(answer if answer is not None else target_result()),
    )
    return world["contract"].observe_nominated_target(
        world["tenancy"], world["target"], world["evidence"], "s52-observe"
    )


def envelope(world, observations=None):
    observations = observations or target_result()
    target = json.loads(world["contract"].get_target_nomination(world["target"]))
    status, reasons, conflicts = world["contract"]._target_candidate_summary(
        world["target"], target["target_version"], target["target_nomination_digest"],
        world["evidence"], observations,
    )
    return {
        "stage": "OBSERVATION", "schema_valid": True,
        "observation_schema_version": 2,
        "target_nomination_schema_version": target["schema_version"],
        "target_id": world["target"], "target_version": target["target_version"],
        "target_nomination_digest": target["target_nomination_digest"],
        "inspection_id": world["inspection"], "area_item_id": world["area"],
        "property_id": world["property"], "unit_id": world["unit"],
        "tenancy_id": world["tenancy"],
        "evidence_id": world["evidence"], "digest": world["digest"],
        "verification_id": world["verification"],
        "source_ref_sha256": hashlib.sha256(URL.encode()).hexdigest(),
        "assessment_status": status, "insufficiency_reasons": reasons,
        "conflict_observation_ids": conflicts,
        "observations": observations,
    }


def test_fully_visible_nominated_target_is_recorded_with_v2_binding(target_world):
    observation_id = observe(target_world)
    assert target_world["vm"].run_validator() is True
    record = json.loads(target_world["contract"].get_visual_observation_record(observation_id))
    assert record["kind"] == "TARGET_AWARE_SINGLE_V2"
    assert record["status"] == "OBSERVED"
    assert record["observation_schema_version"] == 2
    assert record["target_id"] == target_world["target"]
    assert record["target_nomination_digest"]
    assert record["observations"]["feature_presence"] == "ABSENT"


@pytest.mark.parametrize("candidate,reason", [
    (target_result(surface_visibility="PARTIAL", target_visibility="INADEQUATE",
                   feature_presence="UNCERTAIN"), "TARGET_VISIBILITY_INADEQUATE"),
    (target_result(foreground_obstruction="PRESENT", target_visibility="INADEQUATE",
                   feature_presence="UNCERTAIN"), "FOREGROUND_OBSTRUCTION_PRESENT"),
    (target_result(frame_coverage="PARTLY_OUTSIDE", target_visibility="INADEQUATE",
                   feature_presence="UNCERTAIN"), "TARGET_PARTLY_OUTSIDE_FRAME"),
    (target_result(foreground_obstruction="PRESENT", frame_coverage="PARTLY_OUTSIDE",
                   target_visibility="INADEQUATE", feature_presence="UNCERTAIN"),
     "FOREGROUND_OBSTRUCTION_PRESENT"),
    (target_result(target_visibility="UNCERTAIN", target_clarity="UNCERTAIN",
                   feature_presence="UNCERTAIN"), "TARGET_VISIBILITY_UNCERTAIN"),
    (target_result(target_location="NOT_LOCATABLE", target_visibility="INADEQUATE",
                   feature_presence="UNCERTAIN"), "TARGET_NOT_LOCATABLE"),
    (target_result(frame_coverage="OUTSIDE", target_visibility="INADEQUATE",
                   feature_presence="UNCERTAIN"), "TARGET_OUTSIDE_FRAME"),
    (target_result(target_clarity="INADEQUATE", target_visibility="INADEQUATE",
                   feature_presence="UNCERTAIN"), "TARGET_CLARITY_INADEQUATE"),
    (target_result(target_location="UNCERTAIN", target_visibility="UNCERTAIN",
                   feature_presence="UNCERTAIN"), "TARGET_LOCATION_UNCERTAIN"),
    (target_result(surface_visibility="UNCERTAIN", target_location="UNCERTAIN",
                   target_visibility="UNCERTAIN", foreground_obstruction="UNCERTAIN",
                   frame_coverage="UNCERTAIN", target_clarity="UNCERTAIN",
                   feature_presence="UNCERTAIN"), "SURFACE_VISIBILITY_UNCERTAIN"),
])
def test_valid_visibility_limit_is_explicitly_insufficient(target_world, candidate, reason):
    observation_id = observe(target_world, candidate)
    assert target_world["vm"].run_validator() is True
    record = json.loads(target_world["contract"].get_visual_observation_record(observation_id))
    assert record["status"] == "INCONCLUSIVE"
    assert record["assessment_status"] == "INSUFFICIENT"
    assert reason in record["insufficiency_reasons"]
    assert record["observations"]["feature_presence"] != "ABSENT"


def test_unrelated_furniture_outside_target_does_not_force_obstruction(target_world):
    normalized, valid = target_world["contract"]._normalize_target_observation(target_result())
    assert valid is True
    assert normalized["foreground_obstruction"] == "ABSENT"


@pytest.mark.parametrize("bad", [
    target_result(foreground_obstruction="PRESENT", feature_presence="ABSENT"),
    target_result(frame_coverage="OUTSIDE", feature_presence="ABSENT"),
    target_result(target_clarity="UNCERTAIN", feature_presence="ABSENT"),
    target_result(target_location="UNCERTAIN", feature_presence="ABSENT"),
    target_result(target_location="NOT_LOCATABLE", feature_presence="PRESENT",
                  target_visibility="INADEQUATE"),
    target_result(target_location="LOCATED", target_visibility="ADEQUATE",
                  foreground_obstruction="PRESENT"),
    target_result(surface_visibility="NOT_ESTABLISHED", target_location="LOCATED"),
])
def test_inconsistent_or_unsafe_absence_candidate_fails_closed(target_world, bad):
    normalized, valid = target_world["contract"]._normalize_target_observation(bad)
    assert valid is False
    assert normalized == {}


@pytest.mark.parametrize("bad", [
    {**target_result(), "foreground_obstruction": "MAYBE"},
    {key: value for key, value in target_result().items() if key != "frame_coverage"},
    {**target_result(), "invented_field": "x"},
    None,
    "not json",
])
def test_malformed_ai_output_is_not_normalized_to_a_negative(target_world, bad):
    normalized, valid = target_world["contract"]._normalize_target_observation(bad)
    assert valid is False
    assert normalized == {}


def test_malformed_ai_output_reverts_without_persisting_a_visual_observation(target_world):
    world = target_world
    world["vm"].clear_mocks()
    mock_image(world["vm"], world["body"])
    world["vm"].mock_llm(r"Assess only the nominated target", json.dumps({
        "surface_visibility": "VISIBLE", "target_location": "LOCATED",
        "target_visibility": "ADEQUATE", "foreground_obstruction": "ABSENT",
        "frame_coverage": "IN_FRAME", "target_clarity": "ADEQUATE",
        # Missing feature_presence is not defaulted to ABSENT or UNCERTAIN.
    }))
    before = len(world["contract"].visual_observations)
    with world["vm"].expect_revert("MO_ERR_INCONCLUSIVE"):
        world["contract"].observe_nominated_target(
            world["tenancy"], world["target"], world["evidence"], "s52-malformed"
        )
    assert len(world["contract"].visual_observations) == before


def test_wrong_target_evidence_pair_is_rejected_before_interpretation(target_world):
    with target_world["vm"].expect_revert("target_reference_image_required"):
        target_world["contract"]._prepare_target_visual_assessment(
            target_world["target"], "EVIDENCE-WRONG"
        )


def test_wrong_target_id_is_rejected(target_world):
    with target_world["vm"].expect_revert("MO_ERR_NOT_FOUND"):
        target_world["contract"].observe_nominated_target(
            target_world["tenancy"], "TARG-999", target_world["evidence"],
            "s52-wrong-target",
        )


def test_nomination_digest_tampering_is_rejected(target_world):
    stored = json.loads(target_world["contract"].target_nominations[target_world["target"]])
    stored["target_description"] = "a different target"
    target_world["contract"].target_nominations[target_world["target"]] = json.dumps(stored)
    with target_world["vm"].expect_revert("target_nomination_digest_mismatch"):
        target_world["contract"]._prepare_target_visual_assessment(
            target_world["target"], target_world["evidence"]
        )


def test_evidence_digest_mismatch_cannot_be_used(target_world):
    evidence = json.loads(target_world["contract"].get_evidence(target_world["evidence"]))
    evidence["expected_sha256"] = "0" * 64
    target_world["contract"].evidence_records[target_world["evidence"]] = json.dumps(evidence)
    with target_world["vm"].expect_revert("latest_verification_not_verified"):
        target_world["contract"]._prepare_target_visual_assessment(
            target_world["target"], target_world["evidence"]
        )


def test_target_nomination_must_be_frozen_and_in_frozen_snapshot(target_world):
    inspection = json.loads(target_world["contract"].get_inspection(target_world["inspection"]))
    inspection["contents_committed"]["target_nomination_ids"] = []
    target_world["contract"].inspections[target_world["inspection"]] = json.dumps(inspection)
    with target_world["vm"].expect_revert("frozen_latest_target_nomination_required"):
        target_world["contract"]._prepare_target_visual_assessment(
            target_world["target"], target_world["evidence"]
        )


def test_insufficient_target_locator_is_rejected(target_world):
    stored = json.loads(target_world["contract"].target_nominations[target_world["target"]])
    stored["target_description"] = ""
    stored["region_box"] = None
    stored["target_nomination_digest"] = target_world["contract"]._target_nomination_digest(stored)
    target_world["contract"].target_nominations[target_world["target"]] = json.dumps(stored)
    with target_world["vm"].expect_revert("target_locator_required"):
        target_world["contract"]._prepare_target_visual_assessment(
            target_world["target"], target_world["evidence"]
        )


@pytest.mark.parametrize("field,value", [
    ("observation_schema_version", 1),
    ("target_nomination_schema_version", 9),
    ("target_id", "TARG-OTHER"),
    ("target_version", 9),
    ("target_nomination_digest", "f" * 64),
    ("inspection_id", "INSP-OTHER"),
    ("area_item_id", "AREA-OTHER"),
    ("property_id", "PROP-OTHER"),
    ("unit_id", "UNIT-OTHER"),
    ("tenancy_id", "TENANCY-OTHER"),
    ("evidence_id", "EVID-OTHER"),
    ("digest", "e" * 64),
    ("verification_id", "EVER-OTHER"),
    ("source_ref_sha256", "d" * 64),
    ("assessment_status", "INSUFFICIENT"),
    ("insufficiency_reasons", ["TARGET_OUTSIDE_FRAME"]),
    ("conflict_observation_ids", ["OBS-OTHER"]),
])
def test_equivalence_requires_exact_provenance_target_and_summary(target_world, field, value):
    leader = envelope(target_world)
    validator = envelope(target_world)
    validator[field] = value
    assert target_world["contract"]._target_observation_equivalent(leader, validator) is False


@pytest.mark.parametrize("field,updates", [
    ("surface_visibility", {"surface_visibility": "PARTIAL"}),
    ("target_location", {"target_location": "UNCERTAIN", "target_visibility": "UNCERTAIN",
                          "feature_presence": "UNCERTAIN"}),
    ("target_visibility", {"target_visibility": "INADEQUATE", "feature_presence": "UNCERTAIN"}),
    ("foreground_obstruction", {"foreground_obstruction": "PRESENT",
                                 "target_visibility": "INADEQUATE", "feature_presence": "UNCERTAIN"}),
    ("frame_coverage", {"frame_coverage": "PARTLY_OUTSIDE", "target_visibility": "INADEQUATE",
                        "feature_presence": "UNCERTAIN"}),
    ("target_clarity", {"target_clarity": "UNCERTAIN", "target_visibility": "UNCERTAIN",
                        "feature_presence": "UNCERTAIN"}),
    ("feature_presence", {"feature_presence": "PRESENT"}),
])
def test_equivalence_requires_exact_agreement_on_each_safety_field(target_world, field, updates):
    leader = envelope(target_world)
    validator = envelope(target_world, target_result(**updates))
    assert leader["observations"][field] != validator["observations"][field]
    assert target_world["contract"]._target_observation_equivalent(leader, validator) is False


def test_matching_uncertain_candidates_are_equivalent_but_remain_insufficient(target_world):
    uncertain = target_result(target_location="UNCERTAIN", target_visibility="UNCERTAIN",
                              foreground_obstruction="UNCERTAIN", frame_coverage="UNCERTAIN",
                              target_clarity="UNCERTAIN", feature_presence="UNCERTAIN")
    candidate = envelope(target_world, uncertain)
    assert target_world["contract"]._target_observation_equivalent(candidate, candidate) is True
    assert candidate["assessment_status"] == "INSUFFICIENT"


def test_conflicting_prior_target_observation_remains_inconclusive(target_world):
    prior = {
        "observation_id": "OBS-PRIOR-TARGET", "kind": "TARGET_AWARE_SINGLE_V2",
        "target_id": target_world["target"], "target_version": 1,
        "target_nomination_digest": json.loads(target_world["contract"].get_target_nomination(
            target_world["target"]
        ))["target_nomination_digest"],
        "status": "OBSERVED", "insufficiency_reasons": [],
        "observations": target_result(feature_presence="PRESENT"),
    }
    target_world["contract"].visual_observations[prior["observation_id"]] = json.dumps(prior)
    target_world["contract"].observation_ids_by_evidence[target_world["evidence"]] = json.dumps(
        [prior["observation_id"]]
    )
    candidate = envelope(target_world, target_result(feature_presence="ABSENT"))
    assert candidate["assessment_status"] == "INSUFFICIENT"
    assert candidate["conflict_observation_ids"] == [prior["observation_id"]]
    assert "CONFLICTING_PRIOR_TARGET_OBSERVATION" in candidate["insufficiency_reasons"]
    assert target_world["contract"]._target_observation_equivalent(candidate, candidate) is True


def test_equivalence_rejects_invalid_or_missing_candidate(target_world):
    candidate = envelope(target_world)
    missing = dict(candidate)
    del missing["target_nomination_digest"]
    invalid = dict(candidate)
    invalid["observations"] = target_result(frame_coverage="OUTSIDE")
    assert target_world["contract"]._target_observation_equivalent(candidate, missing) is False
    assert target_world["contract"]._target_observation_equivalent(candidate, invalid) is False
    assert target_world["contract"]._target_observation_equivalent(
        {**candidate, "stage": "INCONCLUSIVE"}, candidate
    ) is False


def test_unauthorized_observation_submission_is_rejected(target_world):
    target_world["vm"].sender = target_world["outsider"]
    with target_world["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
        target_world["contract"].observe_nominated_target(
            target_world["tenancy"], target_world["target"], target_world["evidence"],
            "s52-outsider",
        )


def test_target_observation_does_not_mutate_frozen_evidence_or_create_finding(target_world):
    evidence_before = target_world["contract"].get_evidence(target_world["evidence"])
    inspection_before = target_world["contract"].get_inspection(target_world["inspection"])
    observation_id = observe(target_world, target_result(feature_presence="PRESENT"))
    assert target_world["vm"].run_validator() is True
    record = json.loads(target_world["contract"].get_visual_observation_record(observation_id))
    assert record["status"] == "OBSERVED"
    assert target_world["contract"].get_evidence(target_world["evidence"]) == evidence_before
    assert target_world["contract"].get_inspection(target_world["inspection"]) == inspection_before
    assert json.loads(target_world["contract"].list_established_conditions(
        target_world["inspection"], 0, 50
    ))["items"] == []


def test_legacy_observations_remain_readable_and_unchanged(target_world):
    legacy = {
        "observation_id": "OBS-LEGACY", "kind": "SINGLE_IMAGE", "status": "OBSERVED",
        "observations": {"area_visibility": "VISIBLE", "crack_present": "NO"},
    }
    target_world["contract"].visual_observations["OBS-LEGACY"] = json.dumps(legacy)
    assert json.loads(target_world["contract"].get_visual_observation_record("OBS-LEGACY")) == legacy


def test_target_observation_append_does_not_overwrite_legacy_or_prior_records(target_world):
    prior = {"observation_id": "OBS-PRIOR", "kind": "SINGLE_IMAGE",
             "status": "OBSERVED", "observations": {"crack_present": "YES"}}
    target_world["contract"].visual_observations["OBS-PRIOR"] = json.dumps(prior)
    before = target_world["contract"].get_visual_observation_record("OBS-PRIOR")
    observe(target_world)
    assert target_world["vm"].run_validator() is True
    assert target_world["contract"].get_visual_observation_record("OBS-PRIOR") == before


def test_direct_callback_models_only_one_validator_vote_not_majority_or_unanimity(target_world):
    # Direct Mode captures one callback and can verify its Boolean comparator.
    # It cannot simulate the network committee, hidden dissent, or finality.
    observation_id = observe(target_world)
    assert target_world["vm"].run_validator() is True
    assert json.loads(target_world["contract"].get_visual_observation_record(
        observation_id
    ))["target_id"] == target_world["target"]


def test_cross_image_assessment_is_rejected_for_a_reference_anchored_target(target_world):
    evidence = json.loads(target_world["contract"].get_evidence(target_world["evidence"]))
    evidence["evidence_id"] = "EVIDENCE-OTHER"
    evidence["expected_sha256"] = target_world["digest"]
    target_world["contract"].evidence_records["EVIDENCE-OTHER"] = json.dumps(evidence)
    with target_world["vm"].expect_revert("target_reference_image_required"):
        target_world["contract"]._prepare_target_visual_assessment(
            target_world["target"], "EVIDENCE-OTHER"
        )
