"""Direct Mode tests for deterministic Stage 2 inspection/evidence protocol."""

import json
from pathlib import Path

import pytest


CONTRACT_PATH = "contracts/moveout_protocol_v1.py"
SHA_A = "a" * 64
SHA_B = "b" * 64


def address(value):
    return "0x" + value.hex() if isinstance(value, bytes) else str(value)


@pytest.fixture
def world(direct_deploy, direct_vm, direct_alice, direct_bob, direct_charlie):
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_alice
    prop = contract.create_property("Stage 2 Property", "s2-property")
    unit = contract.create_unit(prop, "Unit One", "s2-unit")
    tenancy = contract.create_tenancy(prop, unit, address(direct_bob), "", "s2-tenancy")
    with direct_vm.prank(direct_bob):
        contract.activate_tenancy(tenancy)
    return {"c": contract, "vm": direct_vm, "alice": direct_alice,
            "bob": direct_bob, "charlie": direct_charlie,
            "property": prop, "unit": unit, "tenancy": tenancy}


def make_area(world, unit_id=None, room_label=None, area_label="North Wall"):
    c = world["c"]
    unit_id = unit_id or world["unit"]
    room_label = room_label or "Bedroom " + area_label
    room_id = c.create_room(unit_id, room_label, "s2-room-" + unit_id + room_label)
    area_id = c.create_area_item(
        room_id, "WALL", area_label, "painted wall surface", "s2-area-" + room_id + area_label
    )
    return room_id, area_id


def make_inspection(world, kind="MOVE_IN", request="s2-inspection"):
    return world["c"].create_inspection(world["tenancy"], kind, request)


def make_slot(world, inspection_id, area_id, *, kind="OVERVIEW", label="North Wall overview",
              prior_slot="", prior_evidence="", request="s2-slot"):
    return world["c"].create_capture_slot(
        inspection_id, area_id, kind, label, "Include the wall and fixed landmarks",
        prior_slot, prior_evidence, request,
    )


def make_slot_evidence(world, inspection_id, area_id, slot_id, *, sha=SHA_A,
                       kind="PHOTO", request="s2-slot-evidence", condition_id="",
                       obstruction="NONE", light="NORMAL", note=""):
    return world["c"].submit_evidence_for_slot(
        inspection_id, area_id, slot_id, condition_id, kind,
        "https://evidence.example/" + request, sha, "", obstruction, light, note, request,
    )


def make_frozen_baseline(world, *, request="s2-baseline", with_condition=False):
    c = world["c"]
    inspection_id = make_inspection(world, "MOVE_IN", request + "-inspection")
    room_id, area_id = make_area(world, room_label="Bedroom " + request)
    c.include_area_in_inspection(inspection_id, area_id, request + "-include-area")
    slot_id = make_slot(world, inspection_id, area_id, request=request + "-slot")
    condition_id = ""
    if with_condition:
        condition_id = c.create_condition_record(
            inspection_id, area_id, "OBSERVED_DAMAGE", "A thin crack is visible",
            "claim-ref-1", request + "-condition",
        )
    evidence_id = make_slot_evidence(
        world, inspection_id, area_id, slot_id, request=request + "-evidence",
        condition_id=condition_id,
    )
    c.freeze_evidence(evidence_id)
    c.freeze_inspection(inspection_id)
    return {"inspection": inspection_id, "room": room_id, "area": area_id,
            "slot": slot_id, "condition": condition_id, "evidence": evidence_id}


def make_followup(world, baseline, kind="PERIODIC", request="s2-followup"):
    c = world["c"]
    inspection_id = make_inspection(world, kind, request + "-inspection")
    slot_id = make_slot(
        world, inspection_id, baseline["area"], kind="OVERVIEW",
        prior_slot=baseline["slot"], prior_evidence=baseline["evidence"],
        request=request + "-slot",
    )
    return inspection_id, slot_id


def test_manifest_includes_explicit_room_and_area_membership(world):
    c = world["c"]
    inspection = make_inspection(world)
    room, area = make_area(world)
    c.include_area_in_inspection(inspection, area, "manifest-area")
    c.include_area_in_inspection(inspection, area, "manifest-area")
    manifest = json.loads(c.get_inspection_manifest(inspection))["live_membership"]
    assert manifest["room_ids"] == [room]
    assert manifest["area_item_ids"] == [area]
    assert json.loads(c.list_inspection_rooms(inspection, 0, 50))["items"][0]["room_id"] == room
    assert json.loads(c.list_inspection_area_items(inspection, 0, 50))["items"][0]["area_item_id"] == area


def test_structural_completeness_explains_missing_requirements(world):
    c = world["c"]
    inspection = make_inspection(world)
    report = json.loads(c.get_inspection_completeness(inspection))
    assert report["complete"] is False
    assert "has_room" in report["missing_requirements"]
    _, area = make_area(world)
    c.include_area_in_inspection(inspection, area, "completeness-area")
    report = json.loads(c.get_inspection_completeness(inspection))
    assert report["checks"]["every_room_has_area_item"] is True
    assert "has_evidence" in report["missing_requirements"]
    evidence = c.submit_evidence(
        inspection, area, "", "PHOTO", "https://evidence.example/completeness.png",
        SHA_A, "", "completeness-evidence",
    )
    c.freeze_evidence(evidence)
    report = json.loads(c.get_inspection_completeness(inspection))
    assert report["ready_to_freeze"] is True


def test_freeze_rejects_inspection_without_room_and_area(world):
    inspection = make_inspection(world)
    with world["vm"].expect_revert("MO_ERR_STATE"):
        world["c"].freeze_inspection(inspection)


def test_completeness_requires_evidence_but_not_uniform_per_area_photo_counts(world):
    c = world["c"]
    inspection = make_inspection(world)
    _, area = make_area(world)
    c.include_area_in_inspection(inspection, area, "evidence-completeness-area")
    slot = make_slot(world, inspection, area, request="unfilled-slot")
    report = json.loads(c.get_inspection_completeness(inspection))
    assert "has_evidence" in report["missing_requirements"]
    assert "every_capture_slot_has_evidence" in report["missing_requirements"]
    evidence = make_slot_evidence(world, inspection, area, slot, request="fills-slot")
    c.freeze_evidence(evidence)
    report = json.loads(c.get_inspection_completeness(inspection))
    assert report["ready_to_freeze"] is True


def test_capture_slot_and_participant_metadata_bind_to_evidence(world):
    c = world["c"]
    inspection = make_inspection(world)
    _, area = make_area(world)
    slot = make_slot(world, inspection, area)
    evidence = make_slot_evidence(
        world, inspection, area, slot, obstruction="PARTIAL", light="LOW",
        note="participant says a chair partly blocks the wall",
    )
    record = json.loads(c.get_evidence(evidence))
    assert record["capture_slot_id"] == slot
    assert record["participant_capture_metadata"] == {
        "obstruction": "PARTIAL", "light": "LOW",
        "note_ref": "participant says a chair partly blocks the wall",
    }
    assert json.loads(c.get_capture_slot(slot))["evidence_ids"] == [evidence]
    assert "quality_established" not in record


def test_participant_capture_metadata_is_enum_bounded_not_quality_attestation(world):
    c = world["c"]
    inspection = make_inspection(world)
    _, area = make_area(world)
    slot = make_slot(world, inspection, area)
    with world["vm"].expect_revert("MO_ERR_SCHEMA"):
        make_slot_evidence(world, inspection, area, slot, obstruction="GOOD",
                           request="not-a-quality-claim")


def test_capture_slot_binding_cannot_be_replaced_by_other_submitter(world):
    c = world["c"]
    inspection = make_inspection(world)
    _, area = make_area(world)
    slot = make_slot(world, inspection, area)
    evidence = make_slot_evidence(world, inspection, area, slot)
    c.freeze_evidence(evidence)
    c.freeze_inspection(inspection)
    with world["vm"].expect_revert("MO_ERR_FROZEN_INSPECTION"):
        make_slot_evidence(world, inspection, area, slot, sha=SHA_B, request="late-slot-evidence")
    assert json.loads(c.get_capture_slot(slot))["evidence_ids"] == [evidence]


def test_capture_slot_and_manifest_freeze_snapshot(world):
    c = world["c"]
    baseline = make_frozen_baseline(world)
    manifest = json.loads(c.get_inspection_manifest(baseline["inspection"]))
    assert manifest["contents_committed"]["capture_slot_ids"] == [baseline["slot"]]
    assert json.loads(c.get_inspection_completeness(baseline["inspection"]))["complete"] is True
    assert json.loads(c.get_capture_slot(baseline["slot"]))["status"] == "FROZEN"


def test_capture_slot_and_manifest_creation_retries_after_freeze_are_noops(world):
    c = world["c"]
    inspection = make_inspection(world)
    _, area = make_area(world)
    c.include_area_in_inspection(inspection, area, "stable-area-include")
    slot = make_slot(world, inspection, area, request="stable-slot-create")
    evidence = make_slot_evidence(world, inspection, area, slot, request="stable-slot-evidence")
    c.freeze_evidence(evidence)
    c.freeze_inspection(inspection)
    assert c.include_area_in_inspection(inspection, area, "stable-area-include") is None
    assert make_slot(world, inspection, area, request="stable-slot-create") == slot
    assert json.loads(c.get_inspection_manifest(inspection))["contents_committed"][
        "capture_slot_ids"
    ] == [slot]


def test_later_inspection_does_not_rewrite_frozen_baseline(world):
    c = world["c"]
    baseline = make_frozen_baseline(world)
    frozen_before = json.loads(c.get_inspection_manifest(baseline["inspection"]))["contents_committed"]
    later, slot = make_followup(world, baseline)
    evidence = make_slot_evidence(world, later, baseline["area"], slot,
                                  sha=SHA_B, request="later-photo")
    c.freeze_evidence(evidence)
    c.freeze_inspection(later)
    frozen_after = json.loads(c.get_inspection_manifest(baseline["inspection"]))["contents_committed"]
    assert frozen_after == frozen_before
    assert frozen_after["evidence_ids"] == [baseline["evidence"]]


def test_valid_visual_continuity_is_intent_only(world):
    c = world["c"]
    baseline = make_frozen_baseline(world)
    later, slot = make_followup(world, baseline)
    record = json.loads(c.get_capture_slot(slot))
    assert record["continuity_slot_id"] == baseline["slot"]
    assert record["continuity_evidence_id"] == baseline["evidence"]
    assert record["continuity_semantics"] == "INTENDED_CORRESPONDENCE_NOT_SAME_AREA_PROOF"
    assert json.loads(c.get_inspection(later))["status"] == "OPEN"


def test_continuity_rejects_cross_property(world):
    c = world["c"]
    baseline = make_frozen_baseline(world)
    other_property = c.create_property("Other Property", "other-property")
    other_unit = c.create_unit(other_property, "Other Unit", "other-unit")
    other_tenancy = c.create_tenancy(
        other_property, other_unit, address(world["charlie"]), "", "other-tenancy"
    )
    with world["vm"].prank(world["charlie"]):
        c.activate_tenancy(other_tenancy)
        inspection = c.create_inspection(other_tenancy, "MOVE_IN", "other-inspection")
    _, other_area = make_area(world, other_unit, "Bedroom", "North Wall")
    with world["vm"].prank(world["charlie"]):
        with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
            make_slot(world, inspection, other_area, prior_slot=baseline["slot"],
                      prior_evidence=baseline["evidence"], request="cross-property-slot")


def test_continuity_rejects_cross_unit(world):
    c = world["c"]
    baseline = make_frozen_baseline(world)
    other_unit = c.create_unit(world["property"], "Other Unit", "continuity-unit")
    other_tenancy = c.create_tenancy(
        world["property"], other_unit, address(world["charlie"]), "", "continuity-tenancy"
    )
    with world["vm"].prank(world["charlie"]):
        c.activate_tenancy(other_tenancy)
        inspection = c.create_inspection(other_tenancy, "MOVE_IN", "continuity-inspection")
    _, other_area = make_area(world, other_unit)
    with world["vm"].prank(world["charlie"]):
        with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
            make_slot(world, inspection, other_area, prior_slot=baseline["slot"],
                      prior_evidence=baseline["evidence"], request="cross-unit-slot")


def test_continuity_rejects_different_area_in_same_unit(world):
    c = world["c"]
    baseline = make_frozen_baseline(world)
    inspection = make_inspection(world, "PERIODIC", "different-area-inspection")
    _, different_area = make_area(world, area_label="East Wall")
    with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
        make_slot(world, inspection, different_area, prior_slot=baseline["slot"],
                  prior_evidence=baseline["evidence"], request="different-area-continuity")


def test_continuity_rejects_unfrozen_source_evidence(world):
    old_inspection = make_inspection(world)
    _, area = make_area(world)
    old_slot = make_slot(world, old_inspection, area)
    evidence = make_slot_evidence(world, old_inspection, area, old_slot)
    later = make_inspection(world, "PERIODIC", "unfrozen-later")
    with world["vm"].expect_revert("MO_ERR_STATE"):
        make_slot(world, later, area, prior_slot=old_slot,
                  prior_evidence=evidence, request="unfrozen-reference")


def test_continuity_rejects_forward_reference(world):
    c = world["c"]
    earlier = make_inspection(world, "MOVE_IN", "forward-old")
    _, area = make_area(world)
    make_slot(world, earlier, area, request="forward-old-slot")
    later = make_inspection(world, "PERIODIC", "forward-new")
    later_slot = make_slot(world, later, area, request="forward-new-slot")
    later_evidence = make_slot_evidence(
        world, later, area, later_slot, request="forward-new-evidence"
    )
    c.freeze_evidence(later_evidence)
    c.freeze_inspection(later)
    with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
        make_slot(world, earlier, area, prior_slot=later_slot,
                  prior_evidence=later_evidence, request="forward-reference")


def test_continuity_rejects_self_reference(world):
    c = world["c"]
    inspection = make_inspection(world)
    _, area = make_area(world)
    predicted_slot_id = "SLOT-" + str(c.capture_slot_seq)
    with world["vm"].expect_revert("MO_ERR_NOT_FOUND"):
        make_slot(world, inspection, area, prior_slot=predicted_slot_id,
                  request="self-reference")


def test_inspection_reviews_are_dual_party_and_acknowledgement_is_limited(world):
    c = world["c"]
    baseline = make_frozen_baseline(world, with_condition=True)
    with world["vm"].prank(world["bob"]):
        tenant_review = c.submit_inspection_review(
            baseline["inspection"], "ACKNOWLEDGED", "record exists; not truth endorsement",
            "tenant-review",
        )
    manager_review = c.submit_inspection_review(
        baseline["inspection"], "ACKNOWLEDGED", "manager confirms record exists",
        "manager-review",
    )
    assert json.loads(c.get_inspection_review(tenant_review))["side"] == "TENANT"
    assert json.loads(c.get_inspection_review(manager_review))["side"] == "MANAGER"
    receipt = json.loads(c.get_inspection_receipt(baseline["inspection"]))
    assert receipt["dual_review"]["both_sides_reviewed"] is True
    assert receipt["interpretation"].startswith("Participant descriptions")
    assert len(c.established_conditions) == 0


def test_draft_movein_can_freeze_and_receive_both_reviews_before_activation(world):
    c = world["c"]
    unit = c.create_unit(world["property"], "Draft Move-In Unit", "draft-movein-unit")
    tenancy = c.create_tenancy(
        world["property"], unit, address(world["charlie"]), "", "draft-movein-tenancy"
    )
    inspection = c.create_inspection(tenancy, "MOVE_IN", "draft-movein-inspection")
    _, area = make_area(world, unit, "Entry Room", "West Wall")
    slot = make_slot(world, inspection, area, request="draft-movein-slot")
    evidence = make_slot_evidence(world, inspection, area, slot, request="draft-movein-photo")
    c.freeze_evidence(evidence)
    c.freeze_inspection(inspection)
    c.submit_inspection_review(inspection, "ACKNOWLEDGED", "manager records snapshot", "draft-manager-review")
    with world["vm"].prank(world["charlie"]):
        c.submit_inspection_review(inspection, "DISPUTED", "tenant contests a note", "draft-tenant-review")
        c.activate_tenancy(tenancy)
    assert json.loads(c.get_tenancy(tenancy))["status"] == "ACTIVE"
    receipt = json.loads(c.get_inspection_receipt(inspection))
    assert receipt["dual_review"]["both_sides_reviewed"] is True
    assert receipt["dual_review"]["tenant_status"] == "DISPUTED"


def test_review_replay_and_revision_preserve_history(world):
    c = world["c"]
    baseline = make_frozen_baseline(world)
    first = c.submit_inspection_review(baseline["inspection"], "ACKNOWLEDGED", "seen", "review-1")
    assert c.submit_inspection_review(
        baseline["inspection"], "ACKNOWLEDGED", "seen", "review-1"
    ) == first
    assert c.submit_inspection_review(
        baseline["inspection"], "DISPUTED", "some observations are contested", "review-2"
    ) != first
    rows = json.loads(c.list_inspection_reviews(baseline["inspection"], 0, 50))["items"]
    assert [row["review_status"] for row in rows] == ["ACKNOWLEDGED", "DISPUTED"]
    assert rows[1]["supersedes_review_id"] == first


def test_review_and_disagreement_require_tenancy_participant(world):
    c = world["c"]
    baseline = make_frozen_baseline(world)
    with world["vm"].prank(world["charlie"]):
        with world["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
            c.submit_inspection_review(baseline["inspection"], "ACKNOWLEDGED", "", "outsider-review")
        with world["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
            c.create_disagreement(baseline["inspection"], "INSPECTION",
                                  baseline["inspection"], "", "outsider-dispute")


def test_disagreement_is_append_only_and_does_not_change_evidence(world):
    c = world["c"]
    baseline = make_frozen_baseline(world, with_condition=True)
    before = json.loads(c.get_evidence(baseline["evidence"]))
    with world["vm"].prank(world["bob"]):
        disagreement = c.create_disagreement(
            baseline["inspection"], "CONDITION_RECORD", baseline["condition"],
            "tenant disputes the claimed origin", "disagree-condition",
        )
    after = json.loads(c.get_evidence(baseline["evidence"]))
    assert after == before
    record = json.loads(c.get_disagreement(disagreement))
    assert record["participant"].lower() == address(world["bob"]).lower()
    assert record["area_item_id"] == baseline["area"]
    assert len(c.established_conditions) == 0


def test_disagreement_target_must_belong_to_inspection(world):
    c = world["c"]
    baseline = make_frozen_baseline(world)
    other = make_frozen_baseline(world, request="other-frozen")
    with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
        c.create_disagreement(baseline["inspection"], "EVIDENCE", other["evidence"],
                              "wrong target", "wrong-dispute-target")


def test_counter_evidence_appends_in_later_inspection(world):
    c = world["c"]
    baseline = make_frozen_baseline(world, with_condition=True)
    with world["vm"].prank(world["bob"]):
        disagreement = c.create_disagreement(
            baseline["inspection"], "EVIDENCE", baseline["evidence"],
            "tenant provides contrary context", "counter-disagreement",
        )
    later, slot = make_followup(world, baseline, "PERIODIC", "counter-later")
    with world["vm"].prank(world["bob"]):
        counter = c.submit_counter_evidence(
            disagreement, later, baseline["area"], slot, "", "PHOTO",
            "https://evidence.example/tenant-counter.png", SHA_B,
            "NONE", "NORMAL", "tenant says crack predates tenancy", "counter-photo",
        )
        c.freeze_evidence(counter)
    record = json.loads(c.get_evidence(counter))
    assert record["disagreement_id"] == disagreement
    assert record["submitter"].lower() == address(world["bob"]).lower()
    assert json.loads(c.list_counter_evidence(disagreement, 0, 50))["items"][0]["evidence_id"] == counter
    assert json.loads(c.get_disagreement(disagreement))["counter_evidence_ids"] == [counter]
    assert json.loads(c.get_evidence(baseline["evidence"]))["expected_sha256"] == SHA_A


def test_counter_evidence_cannot_cross_tenancy(world):
    c = world["c"]
    baseline = make_frozen_baseline(world)
    disagreement = c.create_disagreement(
        baseline["inspection"], "INSPECTION", baseline["inspection"], "reason", "counter-dispute"
    )
    other_unit = c.create_unit(world["property"], "Other Unit", "counter-other-unit")
    other_tenancy = c.create_tenancy(
        world["property"], other_unit, address(world["charlie"]), "", "counter-other-tenancy"
    )
    with world["vm"].prank(world["charlie"]):
        c.activate_tenancy(other_tenancy)
        inspection = c.create_inspection(other_tenancy, "MOVE_IN", "counter-other-inspection")
    _, area = make_area(world, other_unit)
    with world["vm"].prank(world["charlie"]):
        with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
            c.submit_counter_evidence(
                disagreement, inspection, area, "", "", "PHOTO", "https://x.example/b.png",
                SHA_B, "UNKNOWN", "UNKNOWN", "", "counter-cross-tenancy",
            )


def test_maintenance_event_links_prior_condition_and_current_repair_evidence(world):
    c = world["c"]
    baseline = make_frozen_baseline(world, with_condition=True)
    maintenance, slot = make_followup(world, baseline, "MAINTENANCE", "repair-flow")
    repair_evidence = make_slot_evidence(
        world, maintenance, baseline["area"], slot, sha=SHA_B,
        kind="REPAIR_RECEIPT", request="repair-receipt",
    )
    event = c.create_maintenance_event(
        maintenance, baseline["area"], "REPAIR_REPORTED", baseline["condition"],
        repair_evidence, "participant reports patching the crack", "repair-event",
    )
    c.freeze_evidence(repair_evidence)
    c.freeze_inspection(maintenance)
    record = json.loads(c.get_maintenance_event(event))
    assert record["condition_record_id"] == baseline["condition"]
    assert record["evidence_id"] == repair_evidence
    assert record["event_type"] == "REPAIR_REPORTED"
    assert "REPAIRED" not in record
    assert json.loads(c.list_maintenance_events(world["tenancy"], 0, 50))["items"][0][
        "maintenance_event_id"
    ] == event


def test_maintenance_rejects_wrong_tenancy_condition_reference(world):
    c = world["c"]
    baseline = make_frozen_baseline(world, with_condition=True)
    other_unit = c.create_unit(world["property"], "Unit Two", "maintenance-other-unit")
    other_tenancy = c.create_tenancy(
        world["property"], other_unit, address(world["charlie"]), "", "maintenance-other-tenancy"
    )
    with world["vm"].prank(world["charlie"]):
        c.activate_tenancy(other_tenancy)
        maintenance = c.create_inspection(other_tenancy, "MAINTENANCE", "maintenance-other-inspection")
    _, area = make_area(world, other_unit)
    with world["vm"].prank(world["charlie"]):
        with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
            c.create_maintenance_event(
                maintenance, area, "REPAIR_REPORTED", baseline["condition"], "",
                "wrong tenancy", "maintenance-cross-tenancy",
            )


def test_maintenance_event_requires_maintenance_inspection_and_reference(world):
    c = world["c"]
    inspection = make_inspection(world, "PERIODIC", "not-maintenance")
    _, area = make_area(world)
    with world["vm"].expect_revert("MO_ERR_STATE"):
        c.create_maintenance_event(inspection, area, "REPAIR_REPORTED", "", "", "", "wrong-kind")
    maintenance = make_inspection(world, "MAINTENANCE", "maintenance-empty")
    with world["vm"].expect_revert("MO_ERR_SCHEMA"):
        c.create_maintenance_event(
            maintenance, area, "REPAIR_REPORTED", "", "", "", "missing-reference"
        )


def test_receipt_is_bounded_summary_with_paginated_members(world):
    c = world["c"]
    baseline = make_frozen_baseline(world, with_condition=True)
    receipt = json.loads(c.get_inspection_receipt(baseline["inspection"]))
    assert receipt["manifest_counts"]["evidence"] == 1
    assert receipt["manifest_counts"]["capture_slots"] == 1
    assert receipt["membership_pages"]["evidence"] == "list_evidence"
    assert "evidence_hashes" not in receipt
    assert json.loads(c.list_evidence(baseline["inspection"], 0, 50))["items"][0][
        "expected_sha256"
    ] == SHA_A


def test_condition_passport_lists_inspections_and_maintenance_without_rewriting_baseline(world):
    c = world["c"]
    baseline = make_frozen_baseline(world, with_condition=True)
    maintenance, slot = make_followup(world, baseline, "MAINTENANCE", "passport-maintenance")
    evidence = make_slot_evidence(
        world, maintenance, baseline["area"], slot, sha=SHA_B, request="passport-repair-photo"
    )
    c.create_maintenance_event(
        maintenance, baseline["area"], "MAINTENANCE_REPORTED", baseline["condition"],
        evidence, "service visit noted", "passport-maint-event",
    )
    c.freeze_evidence(evidence)
    c.freeze_inspection(maintenance)
    history = json.loads(c.list_inspections(world["tenancy"], 0, 50))["items"]
    assert [row["inspection_type"] for row in history] == ["MOVE_IN", "MAINTENANCE"]
    frozen = json.loads(c.get_inspection_manifest(baseline["inspection"]))["contents_committed"]
    assert frozen["evidence_ids"] == [baseline["evidence"]]


def test_move_out_capture_references_move_in_baseline_without_mutating_it(world):
    c = world["c"]
    baseline = make_frozen_baseline(world)
    with world["vm"].prank(world["bob"]):
        c.request_move_out(world["tenancy"])
    moveout = make_inspection(world, "MOVE_OUT", "moveout-followup")
    slot = make_slot(world, moveout, baseline["area"], prior_slot=baseline["slot"],
                     prior_evidence=baseline["evidence"], request="moveout-slot")
    evidence = make_slot_evidence(world, moveout, baseline["area"], slot,
                                  sha=SHA_B, request="moveout-evidence")
    c.freeze_evidence(evidence)
    c.freeze_inspection(moveout)
    assert json.loads(c.get_evidence(baseline["evidence"]))["expected_sha256"] == SHA_A
    assert json.loads(c.get_capture_slot(slot))["continuity_slot_id"] == baseline["slot"]
    assert json.loads(c.get_inspection_manifest(baseline["inspection"]))[
        "contents_committed"
    ]["evidence_ids"] == [baseline["evidence"]]


def test_existing_condition_and_future_finding_stores_stay_separate(world):
    c = world["c"]
    baseline = make_frozen_baseline(world, with_condition=True)
    condition = json.loads(c.get_condition_record(baseline["condition"]))
    assert condition["status"] == "PARTICIPANT_RECORDED"
    assert len(c.visual_observations) == 0
    assert len(c.established_conditions) == 0
    assert not hasattr(c, "record_visual_observation")
    assert not hasattr(c, "promote_established_condition")


def test_later_condition_can_reference_prior_condition_as_participant_claim(world):
    c = world["c"]
    baseline = make_frozen_baseline(world, with_condition=True)
    later = make_inspection(world, "PERIODIC", "linked-condition-inspection")
    linked = c.create_condition_record_with_prior(
        later, baseline["area"], baseline["condition"], "REPAIR_CLAIM",
        "tenant says the same crack was patched", "claim-ref-repair", "linked-condition",
    )
    record = json.loads(c.get_condition_record(linked))
    assert record["participant_asserted_prior_condition_id"] == baseline["condition"]
    assert record["status"] == "PARTICIPANT_RECORDED"
    assert json.loads(c.list_condition_references(baseline["condition"], 0, 50))["items"][0][
        "condition_record_id"
    ] == linked
    assert len(c.established_conditions) == 0


def test_prior_condition_link_rejects_unfrozen_and_wrong_area_sources(world):
    c = world["c"]
    old_inspection = make_inspection(world, "MOVE_IN", "unfrozen-condition-inspection")
    _, old_area = make_area(world)
    old_condition = c.create_condition_record(
        old_inspection, old_area, "OBSERVED_DAMAGE", "claim", "", "unfrozen-prior-condition"
    )
    later = make_inspection(world, "PERIODIC", "unfrozen-condition-later")
    with world["vm"].expect_revert("MO_ERR_STATE"):
        c.create_condition_record_with_prior(
            later, old_area, old_condition, "REPAIR_CLAIM", "repair", "", "unfrozen-link"
        )
    baseline = make_frozen_baseline(world, with_condition=True, request="wrong-area-prior")
    later_b = make_inspection(world, "PERIODIC", "wrong-area-later")
    _, other_area = make_area(world, area_label="South Wall")
    with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
        c.create_condition_record_with_prior(
            later_b, other_area, baseline["condition"], "REPAIR_CLAIM", "repair", "",
            "wrong-area-link",
        )


def test_capture_slot_bound_is_enforced(world):
    c = world["c"]
    inspection = make_inspection(world)
    _, area = make_area(world)
    for index in range(int(c.MAX_CAPTURE_SLOTS_PER_INSPECTION)):
        make_slot(world, inspection, area, kind="DETAIL", label="Detail", request="slot-" + str(index))
    with world["vm"].expect_revert("MO_ERR_BOUNDS"):
        make_slot(world, inspection, area, kind="DETAIL", label="One too many", request="slot-overflow")


def test_stage11_manager_counterparty_and_open_tenant_rules_remain(world):
    c = world["c"]
    c.add_manager(world["property"], address(world["charlie"]))
    with world["vm"].expect_revert("MO_ERR_STATE"):
        c.add_manager(world["property"], address(world["bob"]))
    c.request_move_out(world["tenancy"])
    with world["vm"].prank(world["charlie"]):
        with world["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
            c.confirm_tenancy_end(world["tenancy"], "not tenant")
