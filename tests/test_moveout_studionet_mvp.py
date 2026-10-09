"""Safety and non-AI workflow tests for the restricted StudioNet MVP artifact.

These are deterministic/direct-mode contract tests. They do not verify hosted
StudioNet execution and do not establish visual-model accuracy.
"""

import ast
import hashlib
import io
import json
from pathlib import Path
import re

from PIL import Image
import pytest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "moveout_studionet_mvp.py"
ORIGINAL = ROOT / "contracts" / "moveout_protocol_v1.py"
ORIGINAL_SHA256 = "64D1599DD52F485AF26FF7D1393C6F5345427A49A5471E9E0364CC1FB118582D"
IMAGE_URL = (
    "https://raw.githubusercontent.com/Chinny070/moveout/"
    "0fb633b74dac5f968984d84b5d12a0765cb65a9d/benchmarks/a.png"
)
AI_WRITES = (
    "observe_nominated_target",
    "observe_evidence",
    "observe_evidence_pair",
    "assess_supplemental_continuity",
)


def address(value):
    return "0x" + value.hex() if isinstance(value, bytes) else str(value)


def png_bytes():
    stream = io.BytesIO()
    Image.new("RGB", (24, 24), (220, 220, 220)).save(stream, format="PNG")
    return stream.getvalue()


def snapshot(contract):
    state = {}
    for name in contract.__class__.__annotations__:
        value = getattr(contract, name)
        if hasattr(value, "items"):
            state[name] = tuple(sorted((repr(k), repr(v)) for k, v in value.items()))
        else:
            state[name] = repr(value)
    return state


@pytest.fixture
def mvp_world(direct_deploy, direct_vm, direct_alice, direct_bob, direct_charlie):
    contract = direct_deploy("contracts/moveout_studionet_mvp.py")
    direct_vm.sender = direct_alice
    property_id = contract.create_property("Restricted MVP House", "mvp-property")
    unit_id = contract.create_unit(property_id, "Unit 1", "mvp-unit")
    tenancy_id = contract.create_tenancy(
        property_id, unit_id, address(direct_bob), "MVP test tenancy", "mvp-tenancy"
    )
    with direct_vm.prank(direct_bob):
        contract.activate_tenancy(tenancy_id)
    return {
        "contract": contract,
        "vm": direct_vm,
        "manager": direct_alice,
        "tenant": direct_bob,
        "outsider": direct_charlie,
        "property": property_id,
        "unit": unit_id,
        "tenancy": tenancy_id,
    }


def test_original_contract_hash_is_preserved():
    assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest().upper() == ORIGINAL_SHA256


def test_public_api_has_no_ai_prompt_or_alternate_ai_path():
    tree = ast.parse(CONTRACT.read_text(encoding="utf-8"))
    class_node = next(node for node in tree.body if isinstance(node, ast.ClassDef))
    public_methods = {}
    for node in class_node.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        decorators = [ast.unparse(item) for item in node.decorator_list]
        if any(item.startswith("gl.public.") for item in decorators):
            public_methods[node.name] = decorators
    assert len(public_methods) == 84
    assert sum("gl.public.write" in items for items in public_methods.values()) == 35
    assert sum("gl.public.view" in items for items in public_methods.values()) == 49
    assert all(name in public_methods for name in AI_WRITES)
    assert "exec_prompt" not in {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }
    defined_methods = {
        node.name for node in class_node.body if isinstance(node, ast.FunctionDef)
    }
    assert not ({"_observe_single", "_observe_target_single", "_observe_pair",
                 "_evaluate_continuity_pair"} & defined_methods)


def test_only_approved_methods_and_class_name_differ_from_original():
    original_tree = ast.parse(ORIGINAL.read_text(encoding="utf-8"))
    restricted_tree = ast.parse(CONTRACT.read_text(encoding="utf-8"))
    original_class = next(node for node in original_tree.body if isinstance(node, ast.ClassDef))
    restricted_class = next(node for node in restricted_tree.body if isinstance(node, ast.ClassDef))
    original_methods = {
        node.name: node for node in original_class.body if isinstance(node, ast.FunctionDef)
    }
    restricted_methods = {
        node.name: node for node in restricted_class.body if isinstance(node, ast.FunctionDef)
    }
    assert set(original_methods) - set(restricted_methods) == {
        "_observe_single", "_observe_target_single", "_observe_pair",
        "_evaluate_continuity_pair",
    }
    assert set(restricted_methods) - set(original_methods) == set()
    for name in set(original_methods) - set(AI_WRITES):
        if name in restricted_methods:
            assert ast.dump(original_methods[name], include_attributes=False) == ast.dump(
                restricted_methods[name], include_attributes=False
            )
    for name in AI_WRITES:
        old, new = original_methods[name], restricted_methods[name]
        assert ast.dump(old.args, include_attributes=False) == ast.dump(
            new.args, include_attributes=False
        )
        assert [ast.dump(node, include_attributes=False) for node in old.decorator_list] == [
            ast.dump(node, include_attributes=False) for node in new.decorator_list
        ]
        assert len(new.body) == 1 and isinstance(new.body[0], ast.Expr)
        call = new.body[0].value
        assert isinstance(call, ast.Call) and ast.unparse(call.func) == "self._fail"
        assert ast.literal_eval(call.args[0]) == "MO_ERR_AI_DISABLED"
    original_metadata = [
        node for node in original_class.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
    ]
    restricted_metadata = [
        node for node in restricted_class.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
    ]
    assert ast.dump(ast.Module(body=original_metadata, type_ignores=[]), include_attributes=False) == (
        ast.dump(ast.Module(body=restricted_metadata, type_ignores=[]), include_attributes=False)
    )


def test_all_ai_writes_fail_before_any_state_or_event_mutation(mvp_world):
    c, vm = mvp_world["contract"], mvp_world["vm"]
    calls = (
        (c.observe_nominated_target, ("", "", "", "blocked-target")),
        (c.observe_evidence, ("", "", "blocked-single")),
        (c.observe_evidence_pair, ("", "", "", "blocked-pair")),
        (c.assess_supplemental_continuity, ("", "", "blocked-continuity")),
    )
    for method, args in calls:
        before = snapshot(c)
        with vm.expect_revert("MO_ERR_AI_DISABLED"):
            method(*args)
        assert snapshot(c) == before


def test_non_ai_inspection_condition_and_evidence_workflow_is_retained(mvp_world):
    c, vm = mvp_world["contract"], mvp_world["vm"]
    inspection_id = c.create_inspection(mvp_world["tenancy"], "MOVE_IN", "mvp-inspection")
    room_id = c.create_room(mvp_world["unit"], "Bedroom", "mvp-room")
    area_id = c.create_area_item(room_id, "WALL", "North Wall", "", "mvp-area")
    c.include_area_in_inspection(inspection_id, area_id, "mvp-include-area")
    condition_id = c.create_condition_record(
        inspection_id, area_id, "MAINTENANCE_NOTE", "Participant-entered note", "", "mvp-note"
    )
    assert json.loads(c.get_condition_record(condition_id))["status"] == "PARTICIPANT_RECORDED"

    digest = "a" * 64
    evidence_id = c.submit_evidence(
        inspection_id, area_id, condition_id, "PHOTO", "https://evidence.example/photo.png",
        digest, "", "mvp-evidence",
    )
    c.freeze_evidence(evidence_id)
    c.freeze_inspection(inspection_id)
    assert json.loads(c.get_inspection(inspection_id))["status"] == "FROZEN"
    frozen_evidence = c.get_evidence(evidence_id)
    with vm.expect_revert("MO_ERR_FROZEN_INSPECTION"):
        c.submit_evidence(
            inspection_id, area_id, condition_id, "PHOTO", "https://evidence.example/other.png",
            "b" * 64, "", "mvp-late-evidence",
        )
    assert c.get_evidence(evidence_id) == frozen_evidence

    with vm.prank(mvp_world["outsider"]):
        with vm.expect_revert("MO_ERR_UNAUTHORIZED"):
            c.freeze_evidence(evidence_id)


def test_supplemental_request_closure_remains_terminal(mvp_world):
    c, vm = mvp_world["contract"], mvp_world["vm"]
    image = png_bytes()
    digest = hashlib.sha256(image).hexdigest()
    inspection_id = c.create_inspection(mvp_world["tenancy"], "MOVE_IN", "mvp-sup-inspection")
    room_id = c.create_room(mvp_world["unit"], "Living Room", "mvp-sup-room")
    area_id = c.create_area_item(room_id, "WALL", "Feature Wall", "", "mvp-sup-area")
    c.include_area_in_inspection(inspection_id, area_id, "mvp-sup-area-link")
    evidence_id = c.submit_evidence(
        inspection_id, area_id, "", "PHOTO", IMAGE_URL, digest, "", "mvp-sup-evidence"
    )
    c.freeze_evidence(evidence_id)
    target_id = c.create_target_nomination(
        inspection_id, area_id, "feature-wall-mark", "Nominated feature", evidence_id,
        "", "", "", "mvp-sup-target",
    )
    target = json.loads(c.get_target_nomination(target_id))
    c.freeze_inspection(inspection_id)
    vm.mock_web(re.escape(IMAGE_URL), {"method": "GET", "response": {
        "status": 200, "headers": {"content-type": b"image/png"}, "body": image,
    }})
    c.verify_evidence_provenance(mvp_world["tenancy"], evidence_id, "mvp-sup-verify")
    assert vm.run_validator() is True

    # Seed the prior, already-unresolved observation prerequisite so this test
    # can exercise the independent close/reopen protection without AI inference.
    unresolved_id = "OBS-MVP-UNRESOLVED"
    c.visual_observations[unresolved_id] = c._json({
        "kind": "TARGET_AWARE_SINGLE_V2", "target_id": target_id,
        "target_nomination_digest": target["target_nomination_digest"],
        "status": "INCONCLUSIVE", "assessment_status": "INSUFFICIENT",
        "evidence_ids": [evidence_id],
        "insufficiency_reasons": ["TARGET_VISIBILITY_INADEQUATE"],
    })
    request_id = c.create_supplemental_request(
        inspection_id, target_id, target["target_nomination_digest"], evidence_id, digest,
        unresolved_id, "TARGET_VISIBILITY_INADEQUATE", "mvp-sup-request",
    )
    supplemental_inspection_id = c.create_supplemental_inspection(
        request_id, "mvp-sup-inspection-child"
    )
    c.close_supplemental_request(request_id, "Request closed", "mvp-sup-close")
    assert c._supplemental_request_is_closed(request_id)
    with vm.expect_revert("MO_ERR_STATE"):
        c.create_supplemental_inspection(request_id, "mvp-sup-after-close")
    with vm.expect_revert("MO_ERR_STATE"):
        c.submit_supplemental_evidence(
            request_id, supplemental_inspection_id, IMAGE_URL, digest, "", "UNKNOWN",
            "UNKNOWN", "", "mvp-sup-evidence-after-close",
        )
