"""Direct Mode tests for MoveOut's deterministic Stage 1 protocol."""

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = "contracts/moveout_protocol_v1.py"
SHA = "a" * 64


def address(value):
    if isinstance(value, bytes):
        return "0x" + value.hex()
    return str(value)


@pytest.fixture
def world(direct_deploy, direct_vm, direct_alice, direct_bob, direct_charlie):
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_alice
    property_id = contract.create_property("MoveOut House", "prop-create-1")
    unit_id = contract.create_unit(property_id, "Main House", "unit-create-1")
    tenancy_id = contract.create_tenancy(
        property_id, unit_id, address(direct_bob), "tenant says start date is June 4", "tenancy-create-1"
    )
    with direct_vm.prank(direct_bob):
        contract.activate_tenancy(tenancy_id)
    return {
        "contract": contract,
        "vm": direct_vm,
        "alice": direct_alice,
        "bob": direct_bob,
        "charlie": direct_charlie,
        "property": property_id,
        "unit": unit_id,
        "tenancy": tenancy_id,
    }


def make_inspection(world, kind="MOVE_IN", request="inspection-1"):
    return world["contract"].create_inspection(world["tenancy"], kind, request)


def make_room_area(world, unit_id=None, room_label="Bedroom 1", area_label="North Wall"):
    contract = world["contract"]
    unit_id = unit_id or world["unit"]
    room_id = contract.create_room(unit_id, room_label, "room-" + unit_id + "-" + room_label)
    area_id = contract.create_area_item(
        room_id, "WALL", area_label, "capture the window edge", "area-" + room_id + "-" + area_label
    )
    return room_id, area_id


def make_evidence(world, inspection_id, area_id, *, condition_id="", sha=SHA,
                  source="https://evidence.example/photo.png", supersedes="",
                  request="evidence-1"):
    return world["contract"].submit_evidence(
        inspection_id, area_id, condition_id, "PHOTO", source, sha,
        supersedes, request,
    )


def test_create_property_generates_unique_ids_and_keeps_records_isolated(world):
    c = world["contract"]
    first = world["property"]
    second = c.create_property("Other House", "prop-create-2")
    assert first != second
    assert json.loads(c.get_property(first))["property_label"] == "MoveOut House"
    assert json.loads(c.get_property(second))["property_label"] == "Other House"
    assert json.loads(c.get_unit(world["unit"]))["property_id"] == first


def test_property_create_is_idempotent_for_same_request(world):
    c = world["contract"]
    creator = json.loads(c.get_property(world["property"]))["creator"]
    before = json.loads(c.list_properties(creator, 0, 50))["items"]
    replay = c.create_property("MoveOut House", "prop-create-1")
    after = json.loads(c.list_properties(creator, 0, 50))["items"]
    assert replay == world["property"]
    assert len(before) == len(after)


def test_reused_request_id_with_different_payload_fails(world):
    with world["vm"].expect_revert("MO_ERR_DUPLICATE"):
        world["contract"].create_property("Different House", "prop-create-1")


def test_idempotency_scopes_keys_by_caller_and_method(world):
    c = world["contract"]
    bob_property = ""
    with world["vm"].prank(world["bob"]):
        bob_property = c.create_property("Bob House", "shared-key")
    alice_unit = c.create_unit(world["property"], "Shared Key Unit", "shared-key")
    assert bob_property != world["property"]
    assert json.loads(c.get_unit(alice_unit))["property_id"] == world["property"]


def test_failed_creation_does_not_consume_idempotency_key(world):
    c = world["contract"]
    with world["vm"].expect_revert("MO_ERR_BOUNDS"):
        c.create_property("x" * (c.MAX_LABEL + 1), "retry-after-failure")
    property_id = c.create_property("Valid After Failure", "retry-after-failure")
    assert json.loads(c.get_property(property_id))["property_label"] == "Valid After Failure"


def test_create_unit_and_reject_nonexistent_property(world):
    c = world["contract"]
    unit_id = c.create_unit(world["property"], "Apartment 4B", "unit-create-2")
    assert json.loads(c.get_unit(unit_id))["property_id"] == world["property"]
    with world["vm"].expect_revert("MO_ERR_NOT_FOUND"):
        c.create_unit("PROP-999999", "Nowhere", "unit-bad-parent")


def test_duplicate_unit_label_is_rejected(world):
    with world["vm"].expect_revert("MO_ERR_DUPLICATE"):
        world["contract"].create_unit(world["property"], "Main House", "unit-duplicate")


def test_unit_label_string_boundary(world):
    c = world["contract"]
    accepted = c.create_unit(world["property"], "x" * c.MAX_LABEL, "unit-label-max")
    assert len(json.loads(c.get_unit(accepted))["unit_label"]) == c.MAX_LABEL
    with world["vm"].expect_revert("MO_ERR_BOUNDS"):
        c.create_unit(world["property"], "x" * (c.MAX_LABEL + 1), "unit-label-max-plus-one")


def test_tenant_cannot_create_units_or_manage_property(world):
    with world["vm"].prank(world["bob"]):
        with world["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
            world["contract"].create_unit(world["property"], "Tenant Unit", "tenant-unit")
        with world["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
            world["contract"].add_manager(world["property"], address(world["charlie"]))


def test_open_tenant_cannot_be_promoted_to_manager(world):
    with world["vm"].expect_revert("MO_ERR_STATE"):
        world["contract"].add_manager(world["property"], address(world["bob"]))


def test_creator_can_authorize_and_revoke_manager_without_changing_creator(world):
    c = world["contract"]
    c.add_manager(world["property"], address(world["charlie"]))
    with world["vm"].prank(world["charlie"]):
        unit_id = c.create_unit(world["property"], "Manager Unit", "manager-unit")
    assert json.loads(c.get_unit(unit_id))["property_id"] == world["property"]
    c.remove_manager(world["property"], address(world["charlie"]))
    with world["vm"].prank(world["charlie"]):
        with world["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
            c.create_room(unit_id, "Unauthorized Room", "manager-room-after-revoke")
    with world["vm"].expect_revert("MO_ERR_STATE"):
        c.remove_manager(world["property"], address(world["alice"]))
    managers = json.loads(c.list_managers(world["property"]))["items"]
    charlie = next(row for row in managers if row["address"].lower() == address(world["charlie"]).lower())
    assert charlie["active"] is False


def test_manager_authority_boundary_includes_creator(world):
    c = world["contract"]
    for index in range(1, int(c.MAX_MANAGERS_PER_PROPERTY)):
        manager = "0x" + format(index, "040x")
        c.add_manager(world["property"], manager)
    assert len(json.loads(c.list_managers(world["property"]))["items"]) == c.MAX_MANAGERS_PER_PROPERTY
    with world["vm"].expect_revert("MO_ERR_BOUNDS"):
        c.add_manager(world["property"], "0x" + format(99, "040x"))


def test_manager_action_replay_is_rejected(world):
    c = world["contract"]
    c.add_manager(world["property"], address(world["charlie"]))
    with world["vm"].expect_revert("MO_ERR_DUPLICATE"):
        c.add_manager(world["property"], address(world["charlie"]))


def test_create_and_activate_tenancy_with_protocol_time(world):
    record = json.loads(world["contract"].get_tenancy(world["tenancy"]))
    assert record["status"] == "ACTIVE"
    assert record["created_at"]
    assert record["activated_at"]
    assert record["start_metadata"] == "tenant says start date is June 4"
    assert record["created_at"] != record["start_metadata"]


def test_only_designated_tenant_can_activate_tenancy(world):
    c = world["contract"]
    unit_id = c.create_unit(world["property"], "Activation Test Unit", "activation-unit")
    tenancy_id = c.create_tenancy(
        world["property"], unit_id, address(world["charlie"]), "", "tenancy-charlie"
    )
    with world["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
        c.activate_tenancy(tenancy_id)
    with world["vm"].prank(world["charlie"]):
        c.activate_tenancy(tenancy_id)
    assert json.loads(c.get_tenancy(tenancy_id))["status"] == "ACTIVE"


def test_one_active_tenancy_per_unit(world):
    c = world["contract"]
    tenancy_id = c.create_tenancy(
        world["property"], world["unit"], address(world["charlie"]), "", "tenancy-other"
    )
    with world["vm"].prank(world["charlie"]):
        with world["vm"].expect_revert("MO_ERR_STATE"):
            c.activate_tenancy(tenancy_id)


def test_open_tenancy_duplicate_unit_tenant_rejected(world):
    with world["vm"].expect_revert("MO_ERR_DUPLICATE"):
        world["contract"].create_tenancy(
            world["property"], world["unit"], address(world["bob"]), "", "tenancy-replay"
        )


def test_tenancy_move_out_requires_other_party_confirmation(world):
    c = world["contract"]
    with world["vm"].prank(world["bob"]):
        c.request_move_out(world["tenancy"])
        with world["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
            c.confirm_tenancy_end(world["tenancy"], "tenant end note")
    c.confirm_tenancy_end(world["tenancy"], "manager end note")
    assert json.loads(c.get_tenancy(world["tenancy"]))["status"] == "ENDED"


def test_manager_move_out_request_requires_tenant_even_with_multiple_managers(world):
    c = world["contract"]
    c.add_manager(world["property"], address(world["charlie"]))
    c.request_move_out(world["tenancy"])
    with world["vm"].prank(world["charlie"]):
        with world["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
            c.confirm_tenancy_end(world["tenancy"], "other manager cannot counter-sign")
    with world["vm"].prank(world["bob"]):
        c.confirm_tenancy_end(world["tenancy"], "tenant counter-signs")
    assert json.loads(c.get_tenancy(world["tenancy"]))["ended_by"].lower() == address(world["bob"]).lower()


def test_tenancy_end_replay_cannot_silently_change_metadata(world):
    c = world["contract"]
    with world["vm"].prank(world["bob"]):
        c.request_move_out(world["tenancy"])
    c.confirm_tenancy_end(world["tenancy"], "original end note")
    with world["vm"].expect_revert("MO_ERR_DUPLICATE"):
        c.confirm_tenancy_end(world["tenancy"], "different end note")


def test_move_out_request_is_idempotent_but_invalid_transition_is_rejected(world):
    c = world["contract"]
    c.request_move_out(world["tenancy"])
    c.request_move_out(world["tenancy"])
    assert json.loads(c.get_tenancy(world["tenancy"]))["status"] == "MOVE_OUT_PENDING"
    with world["vm"].prank(world["bob"]):
        with world["vm"].expect_revert("MO_ERR_STATE"):
            c.activate_tenancy(world["tenancy"])


def test_draft_tenancy_can_be_cancelled_by_manager(world):
    c = world["contract"]
    tenancy_id = c.create_tenancy(
        world["property"], world["unit"], address(world["charlie"]), "", "tenancy-cancel"
    )
    c.cancel_draft_tenancy(tenancy_id)
    c.cancel_draft_tenancy(tenancy_id)
    assert json.loads(c.get_tenancy(tenancy_id))["status"] == "CANCELLED"
    with world["vm"].prank(world["charlie"]):
        with world["vm"].expect_revert("MO_ERR_STATE"):
            c.activate_tenancy(tenancy_id)


def test_inspection_types_and_move_out_state_rules(world):
    c = world["contract"]
    with world["vm"].expect_revert("MO_ERR_STATE"):
        c.create_inspection(world["tenancy"], "MOVE_OUT", "moveout-too-early")
    inspection_id = c.create_inspection(world["tenancy"], "PERIODIC", "periodic-1")
    assert json.loads(c.get_inspection(inspection_id))["status"] == "OPEN"
    with world["vm"].expect_revert("MO_ERR_SCHEMA"):
        c.create_inspection(world["tenancy"], "UNKNOWN", "unknown-inspection")


def test_tenant_can_create_inspection_but_nonparticipant_cannot(world):
    c = world["contract"]
    with world["vm"].prank(world["bob"]):
        inspection_id = c.create_inspection(world["tenancy"], "MOVE_IN", "tenant-movein")
    assert json.loads(c.get_inspection(inspection_id))["created_by"] == json.loads(
        c.get_tenancy(world["tenancy"])
    )["tenant"]
    with world["vm"].prank(world["charlie"]):
        with world["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
            c.create_inspection(world["tenancy"], "MOVE_IN", "outsider-movein")


def test_room_ids_are_stable_and_unit_bound(world):
    c = world["contract"]
    first, _ = make_room_area(world)
    second_unit = c.create_unit(world["property"], "Unit 2", "unit-2")
    second, _ = make_room_area(world, second_unit, "Bedroom 1", "East Wall")
    assert first != second
    assert json.loads(c.get_room(first))["unit_id"] == world["unit"]
    assert json.loads(c.get_room(second))["unit_id"] == second_unit


def test_duplicate_room_label_under_same_unit_rejected(world):
    make_room_area(world)
    with world["vm"].expect_revert("MO_ERR_DUPLICATE"):
        world["contract"].create_room(world["unit"], "Bedroom 1", "room-duplicate")


def test_wrong_property_manager_cannot_mutate_other_property_room(world):
    c = world["contract"]
    with world["vm"].prank(world["charlie"]):
        other_property = c.create_property("Other", "other-prop")
        other_unit = c.create_unit(other_property, "Other Unit", "other-unit")
        other_room = c.create_room(other_unit, "Kitchen", "other-room")
    with world["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
        c.create_area_item(other_room, "WALL", "North", "", "wrong-manager-area")


def test_area_item_is_permanently_bound_to_its_room_and_unit(world):
    room_id, area_id = make_room_area(world)
    area = json.loads(world["contract"].get_area_item(area_id))
    room = json.loads(world["contract"].get_room(room_id))
    assert area["room_id"] == room_id
    assert area["unit_id"] == room["unit_id"]
    assert area["property_id"] == room["property_id"]


def test_condition_record_is_participant_evidence_not_finding(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    _, area_id = make_room_area(world)
    condition_id = c.create_condition_record(
        inspection_id, area_id, "OBSERVED_DAMAGE", "A mark is visible", "claim-1", "condition-1"
    )
    condition = json.loads(c.get_condition_record(condition_id))
    assert condition["status"] == "PARTICIPANT_RECORDED"
    assert len(c.established_conditions) == 0
    assert len(c.visual_observations) == 0


def test_only_tenancy_participants_can_create_condition_records(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    _, area_id = make_room_area(world)
    with world["vm"].prank(world["charlie"]):
        with world["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
            c.create_condition_record(
                inspection_id, area_id, "OTHER", "", "", "outsider-condition"
            )


def test_condition_record_duplicate_request_returns_same_record(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    _, area_id = make_room_area(world)
    args = (inspection_id, area_id, "OTHER", "", "", "condition-idempotent")
    first = c.create_condition_record(*args)
    second = c.create_condition_record(*args)
    assert first == second
    assert len(json.loads(c.list_condition_records(inspection_id, 0, 50))["items"]) == 1


def test_condition_create_retry_after_inspection_freeze_returns_original_id(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    _, area_id = make_room_area(world)
    args = (inspection_id, area_id, "OTHER", "", "", "condition-before-freeze")
    condition_id = c.create_condition_record(*args)
    c.freeze_inspection(inspection_id)
    assert c.create_condition_record(*args) == condition_id


def test_submit_evidence_validates_digest_and_stores_provenance_only(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    _, area_id = make_room_area(world)
    evidence_id = make_evidence(world, inspection_id, area_id)
    evidence = json.loads(c.get_evidence(evidence_id))
    assert evidence["status"] == "SUBMITTED"
    assert evidence["expected_sha256"] == SHA
    assert evidence["source_ref"] == "https://evidence.example/photo.png"
    assert evidence["frozen_at"] == ""
    assert "body" not in evidence


def test_source_reference_accepts_exact_limit(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    _, area_id = make_room_area(world)
    source_ref = "x" * c.MAX_SOURCE_REF
    evidence_id = make_evidence(world, inspection_id, area_id, source=source_ref)
    assert len(json.loads(c.get_evidence(evidence_id))["source_ref"]) == c.MAX_SOURCE_REF


def test_malformed_sha256_rejected(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    _, area_id = make_room_area(world)
    with world["vm"].expect_revert("MO_ERR_SHA256"):
        make_evidence(world, inspection_id, area_id, sha="not-a-digest")


def test_source_ref_over_limit_rejected(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    _, area_id = make_room_area(world)
    with world["vm"].expect_revert("MO_ERR_BOUNDS"):
        make_evidence(world, inspection_id, area_id, source="x" * 513)


def test_duplicate_evidence_payload_in_same_inspection_rejected(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    _, area_id = make_room_area(world)
    make_evidence(world, inspection_id, area_id, request="photo-a")
    with world["vm"].expect_revert("MO_ERR_DUPLICATE"):
        make_evidence(world, inspection_id, area_id, request="photo-b")


def test_evidence_freeze_is_submitter_only_and_immutable(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    _, area_id = make_room_area(world)
    with world["vm"].prank(world["bob"]):
        evidence_id = make_evidence(world, inspection_id, area_id, request="tenant-photo")
    before = json.loads(c.get_evidence(evidence_id))
    with world["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
        c.freeze_evidence(evidence_id)
    with world["vm"].prank(world["bob"]):
        c.freeze_evidence(evidence_id)
        c.freeze_evidence(evidence_id)
    after = json.loads(c.get_evidence(evidence_id))
    assert after["status"] == "FROZEN"
    for field in (
        "evidence_id", "property_id", "unit_id", "tenancy_id", "inspection_id",
        "room_id", "area_item_id", "condition_record_id", "submitter",
        "evidence_type", "source_ref", "expected_sha256", "submitted_at",
        "supersedes_evidence_id",
    ):
        assert after[field] == before[field]
    assert after["submitter"] == json.loads(c.get_tenancy(world["tenancy"]))["tenant"]


def test_evidence_not_editable_even_by_property_creator(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    _, area_id = make_room_area(world)
    with world["vm"].prank(world["bob"]):
        evidence_id = make_evidence(world, inspection_id, area_id, request="tenant-photo-2")
        c.freeze_evidence(evidence_id)
    assert not hasattr(c, "update_evidence")
    assert json.loads(c.get_evidence(evidence_id))["submitter"] == json.loads(
        c.get_tenancy(world["tenancy"])
    )["tenant"]


def test_evidence_supersession_preserves_old_frozen_record(world):
    c = world["contract"]
    old_inspection = make_inspection(world, request="old-inspection")
    _, area_id = make_room_area(world)
    old_id = make_evidence(world, old_inspection, area_id, request="old-evidence")
    c.freeze_evidence(old_id)
    c.freeze_inspection(old_inspection)
    new_inspection = c.create_inspection(world["tenancy"], "MAINTENANCE", "new-inspection")
    replacement_id = make_evidence(
        world, new_inspection, area_id, sha="b" * 64,
        source="https://evidence.example/corrected.png", supersedes=old_id,
        request="replacement-evidence",
    )
    c.freeze_evidence(replacement_id)
    old = json.loads(c.get_evidence(old_id))
    new = json.loads(c.get_evidence(replacement_id))
    frozen_membership = json.loads(c.get_inspection(old_inspection))["contents_committed"]
    assert old["status"] == "FROZEN"
    assert old["expected_sha256"] == SHA
    assert old["superseded_by_evidence_id"] == replacement_id
    assert new["supersedes_evidence_id"] == old_id
    assert frozen_membership["evidence_ids"] == [old_id]


def test_evidence_cannot_be_superseded_inside_its_own_inspection(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    _, area_id = make_room_area(world)
    old_id = make_evidence(world, inspection_id, area_id, request="same-inspection-old")
    c.freeze_evidence(old_id)
    with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
        make_evidence(
            world, inspection_id, area_id, supersedes=old_id,
            sha="b" * 64, request="same-inspection-replacement",
        )


def test_different_submitter_cannot_supersede_frozen_evidence(world):
    c = world["contract"]
    old_inspection = make_inspection(world, request="sup-old-inspection")
    _, area_id = make_room_area(world)
    old_id = make_evidence(world, old_inspection, area_id, request="sup-old-evidence")
    c.freeze_evidence(old_id)
    c.freeze_inspection(old_inspection)
    next_inspection = c.create_inspection(world["tenancy"], "MAINTENANCE", "sup-next-inspection")
    with world["vm"].prank(world["bob"]):
        with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
            make_evidence(world, next_inspection, area_id, sha="b" * 64,
                          supersedes=old_id, request="tenant-supersede-manager")


def test_inspection_freeze_requires_each_evidence_frozen(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    _, area_id = make_room_area(world)
    evidence_id = make_evidence(world, inspection_id, area_id)
    with world["vm"].expect_revert("MO_ERR_STATE"):
        c.freeze_inspection(inspection_id)
    c.freeze_evidence(evidence_id)
    c.freeze_inspection(inspection_id)
    frozen = json.loads(c.get_inspection(inspection_id))
    assert frozen["status"] == "FROZEN"
    assert frozen["contents_committed"]["evidence_ids"] == [evidence_id]
    assert frozen["contents_committed"]["area_item_ids"] == [area_id]


def test_frozen_inspection_rejects_new_condition_and_evidence(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    _, area_id = make_room_area(world)
    evidence_id = make_evidence(world, inspection_id, area_id)
    c.freeze_evidence(evidence_id)
    c.freeze_inspection(inspection_id)
    with world["vm"].expect_revert("MO_ERR_FROZEN_INSPECTION"):
        c.create_condition_record(inspection_id, area_id, "OTHER", "", "", "late-condition")
    with world["vm"].expect_revert("MO_ERR_FROZEN_INSPECTION"):
        make_evidence(world, inspection_id, area_id, sha="b" * 64, request="late-evidence")


def test_evidence_create_retry_after_inspection_freeze_returns_original_id(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    _, area_id = make_room_area(world)
    evidence_id = make_evidence(world, inspection_id, area_id, request="before-freeze-retry")
    c.freeze_evidence(evidence_id)
    c.freeze_inspection(inspection_id)
    assert make_evidence(world, inspection_id, area_id, request="before-freeze-retry") == evidence_id


def test_only_inspection_creator_can_freeze(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    with world["vm"].prank(world["bob"]):
        with world["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
            c.freeze_inspection(inspection_id)
    with world["vm"].prank(world["charlie"]):
        with world["vm"].expect_revert("MO_ERR_UNAUTHORIZED"):
            c.freeze_inspection(inspection_id)


def test_inspection_cancel_requires_empty_open_inspection(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    _, area_id = make_room_area(world)
    c.create_condition_record(inspection_id, area_id, "OTHER", "", "", "cancel-cond")
    with world["vm"].expect_revert("MO_ERR_STATE"):
        c.cancel_empty_inspection(inspection_id)
    empty_inspection = c.create_inspection(world["tenancy"], "MAINTENANCE", "empty-inspection")
    c.cancel_empty_inspection(empty_inspection)
    assert json.loads(c.get_inspection(empty_inspection))["status"] == "CANCELLED"


def test_cross_property_area_reference_rejected(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    other_prop = c.create_property("Second Property", "second-property")
    other_unit = c.create_unit(other_prop, "Second Unit", "second-unit")
    other_room = c.create_room(other_unit, "Kitchen", "second-room")
    other_area = c.create_area_item(other_room, "WALL", "Sink Wall", "", "second-area")
    with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
        c.create_condition_record(inspection_id, other_area, "OTHER", "", "", "cross-prop-cond")


def test_cross_property_room_area_cannot_be_added_to_other_tenancy_inspection(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    other_property = c.create_property("Foreign Property", "foreign-property")
    other_unit = c.create_unit(other_property, "Foreign Unit", "foreign-unit")
    other_room = c.create_room(other_unit, "Bedroom", "foreign-room")
    other_area = c.create_area_item(other_room, "WALL", "North", "", "foreign-area")
    with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
        make_evidence(world, inspection_id, other_area, request="foreign-area-evidence")
    with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
        c.create_condition_record(inspection_id, other_area, "OTHER", "", "", "foreign-area-condition")


def test_cross_unit_area_reference_rejected(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    second_unit = c.create_unit(world["property"], "Unit 2", "cross-unit")
    _, area_id = make_room_area(world, second_unit, "Kitchen", "Sink")
    with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
        make_evidence(world, inspection_id, area_id, request="cross-unit-evidence")
    with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
        c.create_condition_record(
            inspection_id, area_id, "OTHER", "", "", "cross-unit-condition"
        )


def test_cross_tenancy_condition_evidence_binding_rejected(world):
    c = world["contract"]
    inspection_a = make_inspection(world, request="tenancy-a-inspection")
    _, area_id = make_room_area(world)
    condition_id = c.create_condition_record(
        inspection_a, area_id, "OTHER", "", "", "tenancy-a-condition"
    )
    second_unit = c.create_unit(world["property"], "Unit 2", "tenancy-b-unit")
    tenancy_b = c.create_tenancy(
        world["property"], second_unit, address(world["charlie"]), "", "tenancy-b"
    )
    with world["vm"].prank(world["charlie"]):
        c.activate_tenancy(tenancy_b)
        inspection_b = c.create_inspection(tenancy_b, "MOVE_IN", "tenancy-b-inspection")
    with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
        c.submit_evidence(inspection_b, area_id, condition_id, "PHOTO",
                          "https://evidence.example/cross.png", "b" * 64, "",
                          "cross-tenancy-evidence")


def test_condition_record_must_match_evidence_area_and_inspection(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    _, area_a = make_room_area(world)
    _, area_b = make_room_area(world, room_label="Kitchen", area_label="Sink")
    condition_id = c.create_condition_record(
        inspection_id, area_a, "OTHER", "", "", "condition-for-a"
    )
    with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
        make_evidence(world, inspection_id, area_b, condition_id=condition_id,
                      sha="b" * 64, request="condition-wrong-area")


def test_evidence_cannot_attach_condition_from_another_inspection(world):
    c = world["contract"]
    inspection_a = make_inspection(world, request="claim-inspection-a")
    inspection_b = c.create_inspection(world["tenancy"], "MAINTENANCE", "claim-inspection-b")
    _, area_id = make_room_area(world)
    condition_id = c.create_condition_record(
        inspection_a, area_id, "OTHER", "", "", "claim-on-inspection-a"
    )
    with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
        make_evidence(
            world, inspection_b, area_id, condition_id=condition_id,
            sha="b" * 64, request="evidence-cross-inspection-condition",
        )


def test_evidence_cannot_supersede_across_tenancies(world):
    c = world["contract"]
    old_inspection = make_inspection(world, request="tenant-a-old-inspection")
    _, old_area = make_room_area(world)
    old_evidence = make_evidence(world, old_inspection, old_area, request="tenant-a-old-evidence")
    c.freeze_evidence(old_evidence)
    c.freeze_inspection(old_inspection)
    other_unit = c.create_unit(world["property"], "Other Unit", "tenant-b-unit")
    other_tenancy = c.create_tenancy(
        world["property"], other_unit, address(world["bob"]), "", "tenant-b-tenancy"
    )
    with world["vm"].prank(world["bob"]):
        c.activate_tenancy(other_tenancy)
    other_inspection = c.create_inspection(other_tenancy, "MOVE_IN", "tenant-b-inspection")
    _, other_area = make_room_area(world, other_unit, "Bedroom", "Wall")
    with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
        make_evidence(
            world, other_inspection, other_area, supersedes=old_evidence,
            sha="b" * 64, request="cross-tenancy-supersession",
        )


def test_visual_observation_and_established_finding_have_no_public_writer(world):
    c = world["contract"]
    assert not hasattr(c, "record_visual_observation")
    assert not hasattr(c, "promote_established_condition")
    _, area_id = make_room_area(world)
    inspection_id = make_inspection(world)
    c.create_condition_record(inspection_id, area_id, "OBSERVED_DAMAGE", "", "", "obs-separation")
    assert len(c.visual_observations) == 0
    assert len(c.established_conditions) == 0


def test_either_participant_can_attach_evidence_to_another_participants_claim(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    _, area_id = make_room_area(world)
    claim_id = c.create_condition_record(
        inspection_id, area_id, "OBSERVED_DAMAGE", "Manager claim", "", "manager-claim"
    )
    with world["vm"].prank(world["bob"]):
        evidence_id = make_evidence(
            world, inspection_id, area_id, condition_id=claim_id, request="tenant-supporting-photo"
        )
    assert json.loads(c.get_evidence(evidence_id))["submitter"] == json.loads(
        c.get_tenancy(world["tenancy"])
    )["tenant"]
    assert json.loads(c.get_evidence(evidence_id))["condition_record_id"] == claim_id
    with world["vm"].expect_revert("MO_ERR_NOT_FOUND"):
        c.get_visual_observation_record("OBS-1")
    with world["vm"].expect_revert("MO_ERR_NOT_FOUND"):
        c.get_established_condition_record("FIND-1")
    assert "consensus_ref" in c.OBSERVATION_RECORD_SCHEMA
    assert "promotion_rule_id" in c.ESTABLISHED_CONDITION_RECORD_SCHEMA
    assert "INSUFFICIENT_EVIDENCE" in c.FUTURE_ESTABLISHED_CONDITIONS


def test_room_and_area_records_are_not_reassigned(world):
    c = world["contract"]
    room_id, area_id = make_room_area(world)
    before_room = c.get_room(room_id)
    before_area = c.get_area_item(area_id)
    assert not hasattr(c, "move_room")
    assert not hasattr(c, "reassign_area_item")
    assert c.get_room(room_id) == before_room
    assert c.get_area_item(area_id) == before_area


def test_protocol_timestamps_are_not_taken_from_user_claim_metadata(world):
    c = world["contract"]
    record = json.loads(c.get_tenancy(world["tenancy"]))
    assert record["start_metadata"] == "tenant says start date is June 4"
    assert record["created_at"] != record["start_metadata"]
    event_rows = json.loads(c.list_property_history(world["property"], 0, 50))["items"]
    assert all(row["protocol_at"] for row in event_rows)


def test_history_is_append_only_and_records_lifecycle_events(world):
    c = world["contract"]
    before = json.loads(c.list_property_history(world["property"], 0, 50))["items"]
    inspection_id = make_inspection(world)
    after = json.loads(c.list_property_history(world["property"], 0, 50))["items"]
    assert len(after) == len(before) + 1
    assert after[-1]["event_type"] == "INSPECTION_CREATED"
    assert after[-1]["record_id"] == inspection_id
    assert after[0] == before[0]


def test_paginated_reads_are_bounded_and_return_next_cursor(world):
    c = world["contract"]
    c.create_unit(world["property"], "Unit 2", "page-unit-2")
    c.create_unit(world["property"], "Unit 3", "page-unit-3")
    page = json.loads(c.list_units(world["property"], 0, 2))
    assert len(page["items"]) == 2
    assert page["has_more"] is True
    assert page["next_offset"] == 2
    with world["vm"].expect_revert("MO_ERR_BOUNDS"):
        c.list_units(world["property"], 0, 51)


def test_wrong_parent_and_wrong_room_references_fail_deterministically(world):
    c = world["contract"]
    with world["vm"].expect_revert("MO_ERR_NOT_FOUND"):
        c.create_room("UNIT-999999", "Lost Room", "no-parent-room")
    inspection_id = make_inspection(world)
    _, area_id = make_room_area(world)
    condition_id = c.create_condition_record(
        inspection_id, area_id, "OTHER", "", "", "right-room-condition"
    )
    bad_inspection = c.create_inspection(world["tenancy"], "MAINTENANCE", "other-inspection")
    with world["vm"].expect_revert("MO_ERR_WRONG_SCOPE"):
        make_evidence(world, bad_inspection, area_id, condition_id=condition_id,
                      sha="b" * 64, request="wrong-inspection-condition")


def test_closed_tenancy_cannot_accept_new_records(world):
    c = world["contract"]
    inspection_id = make_inspection(world)
    _, area_id = make_room_area(world)
    with world["vm"].prank(world["bob"]):
        c.request_move_out(world["tenancy"])
    c.confirm_tenancy_end(world["tenancy"], "done")
    with world["vm"].expect_revert("MO_ERR_STATE"):
        c.create_condition_record(inspection_id, area_id, "OTHER", "", "", "ended-condition")
    with world["vm"].expect_revert("MO_ERR_STATE"):
        make_evidence(world, inspection_id, area_id, request="ended-evidence")


def test_separate_tenancies_do_not_share_inspections_or_evidence(world):
    c = world["contract"]
    second_unit = c.create_unit(world["property"], "Separate Unit", "separate-unit")
    tenancy_b = c.create_tenancy(
        world["property"], second_unit, address(world["charlie"]), "", "separate-tenancy"
    )
    with world["vm"].prank(world["charlie"]):
        c.activate_tenancy(tenancy_b)
        inspection_b = c.create_inspection(tenancy_b, "MOVE_IN", "separate-inspection")
    inspection_a = make_inspection(world)
    _, area_a = make_room_area(world)
    _, area_b = make_room_area(world, second_unit, "Bedroom", "North Wall")
    evidence_a = make_evidence(world, inspection_a, area_a, request="separate-evidence-a")
    with world["vm"].prank(world["charlie"]):
        evidence_b = make_evidence(world, inspection_b, area_b, request="separate-evidence-b")
    assert json.loads(c.get_evidence(evidence_a))["tenancy_id"] == world["tenancy"]
    assert json.loads(c.get_evidence(evidence_b))["tenancy_id"] == tenancy_b
    assert json.loads(c.list_evidence(inspection_a, 0, 50))["items"][0]["evidence_id"] == evidence_a
