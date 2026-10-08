"""Direct-mode Stage 4 provenance-bound visual observation tests."""

import hashlib
import io
import json
import re

from PIL import Image
import pytest


COMMIT = "0fb633b74dac5f968984d84b5d12a0765cb65a9d"
URL_A = f"https://raw.githubusercontent.com/Chinny070/moveout/{COMMIT}/benchmarks/a.png"
URL_B = f"https://raw.githubusercontent.com/Chinny070/moveout/{COMMIT}/benchmarks/b.png"
URL_JPEG = "https://raw.githubusercontent.com/Chinny070/moveout/8fa5bcbcc4918b28b5ba95ef431542a8d40fb128/benchmarks/stage3-fixtures/sample-photo.jpg"


def address(value):
    return "0x" + value.hex() if isinstance(value, bytes) else str(value)


def image_bytes(fmt="PNG", color=(210, 40, 30)):
    stream = io.BytesIO()
    Image.new("RGB", (16, 12), color).save(stream, format=fmt)
    return stream.getvalue()


def mock_image(vm, url, body, mime="image/png", status=200):
    vm.mock_web(re.escape(url), {
        "method": "GET", "response": {
            "status": status,
            "headers": {"content-type": mime.encode("ascii")},
            "body": body,
        },
    })


def single_result(**updates):
    result = {
        "area_visibility": "VISIBLE", "crack_present": "YES",
        "stain_present": "NO", "other_mark_present": "NO",
        "surface_damage_present": "NO", "occlusion_present": "NO",
        "shadow_present": "NO", "low_light_present": "NO", "blur_present": "NO",
        "crop_limitation_present": "NO", "text_present": "NO",
        "possible_injection_text": "NO",
    }
    result.update(updates)
    return result


def pair_result(**updates):
    result = {
        "same_area_support": "SUPPORTED", "feature_present_a": "YES",
        "feature_present_b": "YES", "visible_difference": "NO",
        "viewpoint_confounder": "NO", "lighting_confounder": "NO",
        "shadow_confounder": "NO", "occlusion_confounder": "NO",
        "crop_confounder": "NO", "scale_confounder": "NO",
        "comparison_uncertainty": "LOW",
    }
    result.update(updates)
    return result


@pytest.fixture
def world(direct_deploy, direct_vm, direct_alice, direct_bob, direct_charlie):
    c = direct_deploy("contracts/moveout_protocol_v1.py")
    direct_vm.sender = direct_alice
    prop = c.create_property("Stage 4 Test Property", "s4-property")
    unit = c.create_unit(prop, "Unit A", "s4-unit")
    tenancy = c.create_tenancy(prop, unit, address(direct_bob), "", "s4-tenancy")
    with direct_vm.prank(direct_bob):
        c.activate_tenancy(tenancy)
    inspection = c.create_inspection(tenancy, "MOVE_IN", "s4-inspection")
    room = c.create_room(unit, "Bedroom", "s4-room")
    area = c.create_area_item(room, "WALL", "North Wall", "", "s4-area")
    c.include_area_in_inspection(inspection, area, "s4-include")
    body_a = image_bytes()
    body_b = image_bytes(color=(20, 80, 190))
    evidence_a = c.submit_evidence(inspection, area, "", "PHOTO", URL_A,
                                   hashlib.sha256(body_a).hexdigest(), "", "s4-evidence-a")
    evidence_b = c.submit_evidence(inspection, area, "", "PHOTO", URL_B,
                                   hashlib.sha256(body_b).hexdigest(), "", "s4-evidence-b")
    c.freeze_evidence(evidence_a)
    c.freeze_evidence(evidence_b)
    c.freeze_inspection(inspection)
    return {"c": c, "vm": direct_vm, "alice": direct_alice, "bob": direct_bob,
            "charlie": direct_charlie, "property": prop, "unit": unit,
            "tenancy": tenancy, "inspection": inspection, "room": room,
            "area": area, "a": evidence_a, "b": evidence_b,
            "body_a": body_a, "body_b": body_b}


def mock_pair_web(world, body_a=None, body_b=None):
    vm = world["vm"]
    vm.clear_mocks()
    mock_image(vm, URL_A, body_a or world["body_a"])
    mock_image(vm, URL_B, body_b or world["body_b"])


def verify(world, evidence_id, url, body, suffix):
    mock_image(world["vm"], url, body)
    return world["c"].verify_evidence_provenance(
        world["tenancy"], evidence_id, "s4-verify-" + suffix
    )


def verified_pair(world):
    va = verify(world, world["a"], URL_A, world["body_a"], "a")
    assert world["vm"].run_validator() is True
    vb = verify(world, world["b"], URL_B, world["body_b"], "b")
    assert world["vm"].run_validator() is True
    return va, vb


def observe_single(world, answer=None, body=None):
    world["vm"].clear_mocks()
    mock_image(world["vm"], URL_A, body or world["body_a"])
    world["vm"].mock_llm(r"Describe only bounded visible features",
                         json.dumps(answer or single_result()))
    return world["c"].observe_evidence(world["tenancy"], world["a"], "s4-observe-single")


def observe_pair(world, answer=None, body_a=None, body_b=None):
    mock_pair_web(world, body_a, body_b)
    world["vm"].mock_llm(r"Compare images A and B only",
                         json.dumps(answer or pair_result()))
    return world["c"].observe_evidence_pair(
        world["tenancy"], world["a"], world["b"], "s4-observe-pair"
    )


def test_single_png_observation_is_consensus_backed_and_does_not_create_finding(world):
    verify(world, world["a"], URL_A, world["body_a"], "single")
    world["vm"].run_validator()
    evidence_before = world["c"].get_evidence(world["a"])
    observation_id = observe_single(world)
    assert world["vm"].run_validator() is True
    record = json.loads(world["c"].get_visual_observation_record(observation_id))
    assert record["status"] == "OBSERVED"
    assert record["observations"]["crack_present"] == "YES"
    assert record["source_digests"] == [hashlib.sha256(world["body_a"]).hexdigest()]
    assert world["c"].get_evidence(world["a"]) == evidence_before
    assert json.loads(world["c"].list_established_conditions(world["inspection"], 0, 50))["items"] == []


def test_pair_observation_retrieves_and_binds_both_digests(world):
    verified_pair(world)
    before = json.loads(world["c"].get_evidence(world["a"]))
    after = json.loads(world["c"].get_evidence(world["b"]))
    observation_id = observe_pair(world, pair_result(visible_difference="YES"))
    assert world["vm"].run_validator() is True
    record = json.loads(world["c"].get_visual_observation_record(observation_id))
    assert record["source_digests"] == [before["expected_sha256"], after["expected_sha256"]]
    assert record["observations"]["visible_difference"] == "UNCERTAIN"
    assert record["status"] == "INCONCLUSIVE"
    assert json.loads(world["c"].list_established_conditions(world["inspection"], 0, 50))["items"] == []


def test_unverified_evidence_cannot_be_observed(world):
    with world["vm"].expect_revert("MO_ERR_PROVENANCE"):
        observe_single(world)


@pytest.mark.parametrize("status,mime", [(404, "image/png"), (302, "image/png"),
                                         (200, "text/html")])
def test_prior_unavailable_redirect_or_invalid_content_cannot_be_observed(world, status, mime):
    mock_image(world["vm"], URL_A, world["body_a"], mime=mime, status=status)
    verification_id = world["c"].verify_evidence_provenance(
        world["tenancy"], world["a"], f"s4-bad-prior-{status}-{mime}"
    )
    world["vm"].run_validator()
    verification = json.loads(world["c"].get_evidence_verification(verification_id))
    assert verification["outcome"] != "VERIFIED"
    with world["vm"].expect_revert("MO_ERR_PROVENANCE"):
        observe_single(world)


def test_latest_digest_mismatch_blocks_observation(world):
    verify(world, world["a"], URL_A, world["body_a"], "good-before-mismatch")
    world["vm"].run_validator()
    changed = image_bytes(color=(1, 2, 3))
    world["vm"].clear_mocks()
    mock_image(world["vm"], URL_A, changed)
    world["c"].verify_evidence_provenance(world["tenancy"], world["a"], "s4-mismatch-latest")
    world["vm"].run_validator()
    with world["vm"].expect_revert("MO_ERR_PROVENANCE"):
        observe_single(world)


@pytest.mark.parametrize("url", ["https://example.org/image.png",
                                  f"https://raw.githubusercontent.com/Chinny070/moveout/main/benchmarks/a.png",
                                  f"https://raw.githubusercontent.com/Chinny070/moveout/{COMMIT}/../outside.png",
                                  f"https://raw.githubusercontent.com/Chinny070/moveout/{COMMIT}/a.png?download=1"])
def test_unallowlisted_nonpinned_or_unsafe_source_rejected(world, url):
    evidence = json.loads(world["c"].get_evidence(world["a"]))
    evidence["source_ref"] = url
    world["c"].evidence_records[world["a"]] = json.dumps(evidence)
    mock_image(world["vm"], url, world["body_a"])
    world["c"].verify_evidence_provenance(world["tenancy"], world["a"],
                                           "s4-verify-policy-" + str(len(url)))
    world["vm"].run_validator()
    with world["vm"].expect_revert("MO_ERR_SOURCE_POLICY"):
        observe_single(world)


@pytest.mark.parametrize("fmt,mime", [("PNG", "image/png"), ("JPEG", "image/jpeg")])
def test_supported_png_and_jpeg_are_verified_by_existing_provenance_path(world, fmt, mime):
    body = image_bytes(fmt)
    outcome = world["c"]._classify_verification_response(
        200, {"content-type": mime}, body, hashlib.sha256(body).hexdigest(), "0" * 64
    )
    assert outcome["outcome"] == "VERIFIED"


def test_jpeg_can_complete_single_image_observation(world):
    body = image_bytes("JPEG")
    inspection = world["c"].create_inspection(world["tenancy"], "MOVE_IN", "s4-jpeg-inspection")
    world["c"].include_area_in_inspection(inspection, world["area"], "s4-jpeg-area")
    evidence_id = world["c"].submit_evidence(
        inspection, world["area"], "", "PHOTO", URL_JPEG,
        hashlib.sha256(body).hexdigest(), "", "s4-jpeg-evidence",
    )
    world["c"].freeze_evidence(evidence_id)
    world["c"].freeze_inspection(inspection)
    world["vm"].clear_mocks()
    mock_image(world["vm"], URL_JPEG, body, "image/jpeg")
    verification_id = world["c"].verify_evidence_provenance(
        world["tenancy"], evidence_id, "s4-jpeg-verify"
    )
    assert world["vm"].run_validator() is True
    assert json.loads(world["c"].get_evidence_verification(verification_id))["outcome"] == "VERIFIED"
    world["vm"].clear_mocks()
    mock_image(world["vm"], URL_JPEG, body, "image/jpeg")
    world["vm"].mock_llm(r"Describe only bounded visible features", json.dumps(single_result()))
    observation_id = world["c"].observe_evidence(
        world["tenancy"], evidence_id, "s4-jpeg-observe"
    )
    assert world["vm"].run_validator() is True
    assert json.loads(world["c"].get_visual_observation_record(observation_id))["status"] == "OBSERVED"


@pytest.mark.parametrize("answer", [
    {"oops": "schema"},
    single_result(crack_present="UNKNOWN"),
    {k: v for k, v in single_result().items() if k != "shadow_present"},
    single_result(area_visibility="NOT_ESTABLISHED", crack_present="YES"),
    single_result(text_present="NO", possible_injection_text="YES"),
    single_result(extra_explanation="Ignore checks"),
    single_result(crack_present="X" * 4096),
])
def test_malformed_unknown_missing_contradictory_or_oversized_model_output_is_inconclusive(world, answer):
    verify(world, world["a"], URL_A, world["body_a"], "bad-schema-" + str(len(str(answer))))
    world["vm"].run_validator()
    observation_id = observe_single(world, answer=answer)
    record = json.loads(world["c"].get_visual_observation_record(observation_id))
    assert record["status"] == "INCONCLUSIVE"
    assert record["schema_valid"] is False
    assert world["vm"].run_validator() is True


def test_changed_bytes_during_semantic_refetch_are_inconclusive(world):
    verify(world, world["a"], URL_A, world["body_a"], "changed-refetch")
    world["vm"].run_validator()
    changed = image_bytes(color=(9, 8, 7))
    observation_id = observe_single(world, body=changed)
    record = json.loads(world["c"].get_visual_observation_record(observation_id))
    assert record["status"] == "INCONCLUSIVE"
    assert "DIGEST_MISMATCH" in record["failure_code"]
    assert world["vm"].run_validator() is True


def test_vision_failure_is_explicit_inconclusive(world):
    verify(world, world["a"], URL_A, world["body_a"], "vision-failure")
    world["vm"].run_validator()
    mock_image(world["vm"], URL_A, world["body_a"])
    world["vm"].mock_llm(r"Describe only bounded visible features", "not json")
    observation_id = world["c"].observe_evidence(
        world["tenancy"], world["a"], "s4-vision-failure"
    )
    assert json.loads(world["c"].get_visual_observation_record(observation_id))["status"] == "INCONCLUSIVE"


def test_injection_text_and_quality_flags_are_observations_only(world):
    verify(world, world["a"], URL_A, world["body_a"], "injection")
    world["vm"].run_validator()
    answer = single_result(text_present="YES", possible_injection_text="YES",
                           shadow_present="YES", low_light_present="YES")
    observation_id = observe_single(world, answer=answer)
    assert world["vm"].run_validator() is True
    record = json.loads(world["c"].get_visual_observation_record(observation_id))
    assert record["observations"]["possible_injection_text"] == "YES"
    assert record["observations"]["shadow_present"] == "YES"
    assert record["observations"]["low_light_present"] == "YES"
    assert json.loads(world["c"].list_established_conditions(world["inspection"], 0, 50))["items"] == []


def test_nonparticipant_cannot_forge_observation(world):
    verify(world, world["a"], URL_A, world["body_a"], "unauthorized")
    world["vm"].run_validator()
    mock_image(world["vm"], URL_A, world["body_a"])
    world["vm"].mock_llm(r"Describe only bounded visible features", json.dumps(single_result()))
    with world["vm"].prank(world["charlie"]):
        with world["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
            world["c"].observe_evidence(world["tenancy"], world["a"], "s4-unauthorized")


def test_equivalence_rejects_critical_field_disagreement(world):
    verify(world, world["a"], URL_A, world["body_a"], "equivalence")
    world["vm"].run_validator()
    observation_id = observe_single(world, answer=single_result(crack_present="YES"))
    world["vm"].clear_mocks()
    mock_image(world["vm"], URL_A, world["body_a"])
    world["vm"].mock_llm(r"Describe only bounded visible features",
                          json.dumps(single_result(crack_present="NO")))
    assert world["vm"].run_validator() is False
    # A disagreement cannot be read as a finalized observation in the test VM.
    assert observation_id


def test_pairwise_digest_failure_never_calls_visual_comparison(world):
    verified_pair(world)
    changed = image_bytes(color=(100, 110, 120))
    observation_id = observe_pair(world, body_b=changed)
    record = json.loads(world["c"].get_visual_observation_record(observation_id))
    assert record["status"] == "INCONCLUSIVE"
    assert record["failure_code"] == "REFETCH_NOT_VERIFIED"
    assert world["vm"].run_validator() is True


def test_continuity_reference_is_only_context_not_same_area_proof(world):
    verified_pair(world)
    b = json.loads(world["c"].get_evidence(world["b"]))
    b["capture_slot_id"] = "CAP-TEST"
    world["c"].evidence_records[world["b"]] = json.dumps(b)
    world["c"].capture_slots["CAP-TEST"] = json.dumps({
        "capture_slot_id": "CAP-TEST", "continuity_evidence_id": world["a"],
        "continuity_slot_id": "",
    })
    answer = pair_result(same_area_support="UNCERTAIN", comparison_uncertainty="HIGH")
    observation_id = observe_pair(world, answer=answer)
    assert world["vm"].run_validator() is True
    record = json.loads(world["c"].get_visual_observation_record(observation_id))
    assert record["continuity"] == "INTENDED_CORRESPONDENCE_ONLY"
    assert record["observations"]["same_area_support"] == "UNCERTAIN"


@pytest.mark.parametrize("updates", [
    {"same_area_support": "UNCERTAIN", "visible_difference": "UNCERTAIN",
     "comparison_uncertainty": "HIGH"},
    {"shadow_confounder": "YES", "visible_difference": "UNCERTAIN",
     "comparison_uncertainty": "HIGH"},
    {"occlusion_confounder": "YES", "same_area_support": "UNCERTAIN",
     "comparison_uncertainty": "HIGH"},
    {"crop_confounder": "YES", "visible_difference": "UNCERTAIN",
     "comparison_uncertainty": "HIGH"},
    {"same_area_support": "NOT_SUPPORTED", "visible_difference": "UNCERTAIN",
     "comparison_uncertainty": "HIGH"},
])
def test_ambiguous_shadow_occlusion_crop_and_lookalike_pairs_remain_observations(world, updates):
    verified_pair(world)
    observation_id = observe_pair(world, answer=pair_result(**updates))
    assert world["vm"].run_validator() is True
    record = json.loads(world["c"].get_visual_observation_record(observation_id))
    assert record["status"] == "OBSERVED"
    assert record["observations"]["comparison_uncertainty"] == "HIGH"
    assert json.loads(world["c"].list_established_conditions(world["inspection"], 0, 50))["items"] == []


def test_pair_equivalence_rejects_different_visual_interpretations(world):
    verified_pair(world)
    observation_id = observe_pair(world, answer=pair_result(visible_difference="NO"))
    world["vm"].clear_mocks()
    mock_pair_web(world)
    world["vm"].mock_llm(r"Compare images A and B only",
                         json.dumps(pair_result(visible_difference="YES")))
    assert world["vm"].run_validator() is False
    assert observation_id


@pytest.mark.parametrize("updates", [
    {"same_area_support": "NOT_SUPPORTED", "visible_difference": "YES",
     "comparison_uncertainty": "LOW"},
    {"same_area_support": "UNCERTAIN", "visible_difference": "NO",
     "comparison_uncertainty": "LOW"},
    {"crop_confounder": "YES", "visible_difference": "YES",
     "comparison_uncertainty": "LOW"},
    {"viewpoint_confounder": "YES", "visible_difference": "NO",
     "comparison_uncertainty": "LOW"},
    {"lighting_confounder": "YES", "comparison_uncertainty": "LOW"},
    {"occlusion_confounder": "YES", "comparison_uncertainty": "LOW"},
    {"scale_confounder": "YES", "comparison_uncertainty": "LOW"},
    {"feature_present_a": "YES", "feature_present_b": "NO",
     "visible_difference": "NO"},
    {"feature_present_a": "YES", "feature_present_b": "YES",
     "visible_difference": "YES"},
    {"feature_present_a": "UNCERTAIN", "feature_present_b": "NO",
     "visible_difference": "YES"},
])
def test_contradictory_or_overconfident_pair_observations_fail_closed(world, updates):
    normalized, valid = world["c"]._normalize_observation(
        pair_result(**updates), world["c"].PAIR_OBSERVATION_FIELDS
    )
    assert valid is False
    assert normalized == world["c"]._empty_pair_observation()


def test_pair_field_equivalence_allows_secondary_flag_difference_but_keeps_critical_exact(world):
    contract = world["c"]
    leader = {"stage": "OBSERVATION", "failure_code": "", "evidence_ids": [world["a"], world["b"]],
              "digests": ["a" * 64, "b" * 64], "verification_ids": ["va", "vb"],
              "continuity": "NONE", "schema_valid": True,
              "observations": pair_result(viewpoint_confounder="NO")}
    validator = json.loads(json.dumps(leader))
    validator["observations"]["viewpoint_confounder"] = "UNCERTAIN"
    assert contract._observation_equivalent(leader, validator, pairwise=True) is True
    validator["observations"]["visible_difference"] = "YES"
    assert contract._observation_equivalent(leader, validator, pairwise=True) is False


def test_single_field_equivalence_rejects_critical_feature_disagreement(world):
    contract = world["c"]
    leader = {"stage": "OBSERVATION", "failure_code": "", "evidence_id": world["a"],
              "digest": "a" * 64, "verification_id": "va", "schema_valid": True,
              "observations": single_result()}
    validator = json.loads(json.dumps(leader))
    validator["observations"]["occlusion_present"] = "UNCERTAIN"
    assert contract._observation_equivalent(leader, validator) is True
    validator["observations"]["crack_present"] = "NO"
    assert contract._observation_equivalent(leader, validator) is False


def test_ambiguous_mark_remains_explicitly_uncertain(world):
    verify(world, world["a"], URL_A, world["body_a"], "ambiguous-mark")
    world["vm"].run_validator()
    answer = single_result(crack_present="UNCERTAIN", other_mark_present="UNCERTAIN")
    observation_id = observe_single(world, answer=answer)
    assert world["vm"].run_validator() is True
    record = json.loads(world["c"].get_visual_observation_record(observation_id))
    assert record["status"] == "OBSERVED"
    assert record["observations"]["crack_present"] == "UNCERTAIN"
    assert json.loads(world["c"].list_established_conditions(world["inspection"], 0, 50))["items"] == []


def test_observation_validator_rejects_independent_digest_mismatch(world):
    verify(world, world["a"], URL_A, world["body_a"], "equivalence-digest")
    world["vm"].run_validator()
    observation_id = observe_single(world)
    world["vm"].clear_mocks()
    changed = image_bytes(color=(3, 4, 5))
    mock_image(world["vm"], URL_A, changed)
    world["vm"].mock_llm(r"Describe only bounded visible features", json.dumps(single_result()))
    assert world["vm"].run_validator() is False
    assert observation_id


def test_observation_url_policy_rejects_redirect_responses_and_discloses_hidden_redirect_limit(world):
    assert world["c"]._validate_visual_source(URL_A) == URL_A
    response = world["c"]._classify_verification_response(
        302, {"content-type": "image/png", "location": "https://example.org/image.png"},
        world["body_a"], hashlib.sha256(world["body_a"]).hexdigest(),
        hashlib.sha256(URL_A.encode()).hexdigest(),
    )
    assert response["outcome"] != "VERIFIED"
    # Runtime response has no final-URL field. Hidden auto-follow cannot be
    # distinguished here, so only known redirect responses are rejectable.
    assert "final_url" not in response


def test_clean_image_negative_confonder_schema_does_not_infer_edge_as_occlusion(world):
    normalized, valid = world["c"]._normalize_observation(
        single_result(crack_present="NO", occlusion_present="NO", shadow_present="NO",
                      crop_limitation_present="NO"), world["c"].SINGLE_OBSERVATION_FIELDS
    )
    assert valid is True
    assert normalized["occlusion_present"] == "NO"
    assert normalized["shadow_present"] == "NO"
    assert normalized["crop_limitation_present"] == "NO"


def test_observation_only_storage_does_not_create_established_condition(world):
    verify(world, world["a"], URL_A, world["body_a"], "observation-only")
    world["vm"].run_validator()
    observation_id = observe_single(world)
    assert world["vm"].run_validator() is True
    assert json.loads(world["c"].get_visual_observation_record(observation_id))["kind"] == "SINGLE_IMAGE"
    assert json.loads(world["c"].list_established_conditions(world["inspection"], 0, 50))["items"] == []
    manifest = json.loads(world["c"].get_inspection_manifest(world["inspection"]))
    assert manifest["live_membership"]["condition_record_ids"] == []


def test_observations_are_idempotent_append_only_and_paginated(world):
    verify(world, world["a"], URL_A, world["body_a"], "history")
    world["vm"].run_validator()
    first = observe_single(world)
    world["vm"].run_validator()
    evidence_before = world["c"].get_evidence(world["a"])
    second = observe_single(world)
    world["vm"].run_validator()
    assert first == second
    assert world["c"].get_evidence(world["a"]) == evidence_before
    page = json.loads(world["c"].list_visual_observations(world["inspection"], 0, 1))
    assert len(page["items"]) == 1
    assert page["items"][0]["observation_id"] == first
    assert json.loads(world["c"].list_evidence_verifications(world["a"], 0, 10))["items"]


def test_stage3_verification_history_is_preserved(world):
    verify(world, world["a"], URL_A, world["body_a"], "history-preserved")
    world["vm"].run_validator()
    ids_before = json.loads(world["c"].get_evidence_verification_status(world["a"]))
    observation_id = observe_single(world)
    assert world["vm"].run_validator() is True
    ids_after = json.loads(world["c"].get_evidence_verification_status(world["a"]))
    assert ids_before["verification_count"] == ids_after["verification_count"]
    assert json.loads(world["c"].get_visual_observation_record(observation_id))["verification_ids"] == [
        ids_after["latest_verification_id"]
    ]
