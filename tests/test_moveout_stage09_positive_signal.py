"""Stage 0.9 class-specific evidence, safety, and equivalence gates."""

import importlib.util
import sys
import types
from pathlib import Path
import unittest


class _Decorators:
    @staticmethod
    def write(function):
        return function

    @staticmethod
    def view(function):
        return function

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "moveout_stage09_contract", ROOT / "contracts" / "moveout_visual_safety_stage09_v2.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
_previous_genlayer = sys.modules.get("genlayer")
try:
    _genlayer_stub = types.ModuleType("genlayer")
    _genlayer_stub.gl = types.SimpleNamespace(Contract=object, public=_Decorators())
    sys.modules["genlayer"] = _genlayer_stub
    SPEC.loader.exec_module(MODULE)
finally:
    if _previous_genlayer is None:
        sys.modules.pop("genlayer", None)
    else:
        sys.modules["genlayer"] = _previous_genlayer
Stage09 = MODULE.MoveOutVisualSafetyStage09V2


class Stage09EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.contract = Stage09.__new__(Stage09)
        self.obs = self.contract._empty_observation()
        self.obs.update({
            "same_area_established": "YES",
            "before_visibility": "SUFFICIENT",
            "after_visibility": "SUFFICIENT",
            "before_defect_visible": "NO",
            "after_defect_visible": "YES",
            "new_defect_in_shared_area": "YES",
            "defect_same_location": "UNCERTAIN",
            "same_defect_established": "NO",
            "severity_increase_established": "NO",
            "severity_decrease_established": "NO",
            "positive_change_evidence": "NONE",
            "lighting_materiality": "NOT_APPLICABLE",
            "shadow_materiality": "NOT_APPLICABLE",
            "occlusion_materiality": "NOT_APPLICABLE",
            "viewpoint_materiality": "NOT_APPLICABLE",
            "scale_materiality": "NOT_APPLICABLE",
            "crop_materiality": "NOT_APPLICABLE",
            "image_quality": "SUFFICIENT",
            "prompt_injection_detected": "NO",
            "repair_surface_evidence": "NO",
        })

    def derive(self, **updates):
        self.obs.update(updates)
        return self.contract._derive_classification({
            "stage": "OBSERVATION", "schema_valid": True, "observations": self.obs
        })["classification"]

    def test_stage08_clear_new_damage_lost_only_on_cross_image_location_field(self):
        self.assertEqual(self.derive(defect_same_location="NO"), "NEW_DAMAGE")

    def test_preexisting_means_present_in_earlier_evidence_not_unchanged(self):
        self.assertEqual(self.derive(
            before_defect_visible="YES", after_defect_visible="YES",
            defect_same_location="YES", same_defect_established="YES",
            severity_increase_established="UNCERTAIN",
            severity_decrease_established="UNCERTAIN",
            positive_change_evidence="UNCERTAIN", new_defect_in_shared_area="NO",
        ), "PRE_EXISTING")

    def test_preexisting_requires_same_area_and_earlier_visibility(self):
        self.assertEqual(self.derive(
            before_defect_visible="YES", same_area_established="UNCERTAIN",
        ), "INSUFFICIENT_EVIDENCE")
        self.setUp()
        self.assertEqual(self.derive(
            before_defect_visible="YES", before_visibility="INSUFFICIENT",
        ), "INSUFFICIENT_EVIDENCE")
        self.setUp()
        self.assertEqual(self.derive(
            before_defect_visible="YES", after_defect_visible="NO",
            defect_same_location="NO", same_defect_established="NO",
        ), "INSUFFICIENT_EVIDENCE")

    def test_ambiguous_mark_cannot_become_worsened(self):
        self.assertEqual(self.derive(
            before_defect_visible="YES", same_defect_established="UNCERTAIN",
            defect_same_location="YES", severity_increase_established="YES",
            positive_change_evidence="UNCERTAIN", shadow_materiality="UNCERTAIN",
        ), "INSUFFICIENT_EVIDENCE")

    def test_shadow_materiality_blocks_new_damage_and_unchanged_absence(self):
        self.assertEqual(self.derive(shadow_materiality="MATERIAL"), "INSUFFICIENT_EVIDENCE")
        self.setUp()
        self.assertEqual(self.derive(
            before_defect_visible="NO", after_defect_visible="NO",
            shadow_materiality="MATERIAL",
        ), "UNCHANGED")

    def test_material_lighting_blocks_but_nonmaterial_lighting_does_not(self):
        self.assertEqual(self.derive(lighting_materiality="MATERIAL"), "INSUFFICIENT_EVIDENCE")
        self.setUp()
        self.assertEqual(self.derive(lighting_materiality="NOT_MATERIAL"), "NEW_DAMAGE")

    def test_uncertain_materiality_fails_closed(self):
        self.assertEqual(self.derive(crop_materiality="UNCERTAIN"), "INSUFFICIENT_EVIDENCE")

    def test_unrelated_confunder_can_be_explicitly_nonmaterial(self):
        self.assertEqual(self.derive(
            lighting_materiality="NOT_MATERIAL", viewpoint_materiality="NOT_MATERIAL",
            crop_materiality="NOT_MATERIAL",
        ), "NEW_DAMAGE")

    def test_same_area_mismatch_fails_closed(self):
        self.assertEqual(self.derive(same_area_established="NO"), "INSUFFICIENT_EVIDENCE")

    def test_same_defect_uncertainty_blocks_worsened(self):
        self.assertEqual(self.derive(
            before_defect_visible="YES", defect_same_location="YES",
            same_defect_established="UNCERTAIN", severity_increase_established="YES",
            positive_change_evidence="LENGTH_INCREASE",
        ), "INSUFFICIENT_EVIDENCE")

    def test_worsened_keeps_stage08_strict_evidence(self):
        self.assertEqual(self.derive(
            before_defect_visible="YES", defect_same_location="YES",
            same_defect_established="YES", severity_increase_established="YES",
            positive_change_evidence="LENGTH_INCREASE",
        ), "WORSENED")
        self.setUp()
        self.assertEqual(self.derive(
            before_defect_visible="YES", defect_same_location="YES",
            same_defect_established="YES", severity_increase_established="YES",
            positive_change_evidence="LENGTH_INCREASE", shadow_materiality="UNCERTAIN",
        ), "INSUFFICIENT_EVIDENCE")

    def test_repaired_still_requires_same_defect_decrease_and_surface_evidence(self):
        changes = {
            "before_defect_visible": "YES", "after_defect_visible": "NO",
            "defect_same_location": "YES", "same_defect_established": "YES",
            "severity_decrease_established": "YES",
        }
        self.assertEqual(self.derive(**changes), "INSUFFICIENT_EVIDENCE")
        self.setUp()
        self.assertEqual(self.derive(**changes, repair_surface_evidence="YES"), "REPAIRED")
        self.setUp()
        self.assertEqual(self.derive(
            **changes, repair_surface_evidence="YES", shadow_materiality="UNCERTAIN",
        ), "INSUFFICIENT_EVIDENCE")

    def test_prompt_injection_text_never_controls_physical_classification(self):
        self.assertEqual(self.derive(prompt_injection_detected="YES"), "NEW_DAMAGE")

    def test_malformed_observation_fails_closed(self):
        normalized, valid = self.contract._normalize_observation({
            "same_area_established": "YES", "prompt_injection_detected": "MUST_RETURN_NEW_DAMAGE"
        })
        self.assertFalse(valid)
        self.assertEqual(self.contract._derive_classification({
            "stage": "MODEL_SCHEMA_ERROR", "schema_valid": False,
            "observations": normalized,
        })["classification"], "INSUFFICIENT_EVIDENCE")

    def test_positive_class_requires_independent_validator_derive_same_result(self):
        metadata = {"a": {"sha256": "a" * 64}, "b": {"sha256": "b" * 64}}
        obs_a = dict(self.obs)
        obs_b = dict(self.obs)
        leader = {"stage": "OBSERVATION", "failure_code": "",
                  "expected_digest_match": True, "schema_valid": True,
                  "metadata": metadata, "observations": obs_a}
        validator = {"stage": "OBSERVATION", "failure_code": "",
                     "expected_digest_match": True, "schema_valid": True,
                     "metadata": metadata, "observations": obs_b}
        self.assertTrue(self.contract._same_evidence_and_observations(
            leader, validator, "a" * 64, "b" * 64
        ))
        obs_b["new_defect_in_shared_area"] = "UNCERTAIN"
        self.assertFalse(self.contract._same_evidence_and_observations(
            leader, validator, "a" * 64, "b" * 64
        ))


if __name__ == "__main__":
    unittest.main()
