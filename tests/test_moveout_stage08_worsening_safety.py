"""Stage 0.8 safety gates, including an exact Stage 0.7 regression fixture."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path


class _Decorators:
    @staticmethod
    def write(function):
        return function

    @staticmethod
    def view(function):
        return function


if "genlayer" not in sys.modules:
    _genlayer_stub = types.ModuleType("genlayer")
    _genlayer_stub.gl = types.SimpleNamespace(Contract=object, public=_Decorators())
    sys.modules["genlayer"] = _genlayer_stub


ROOT = Path(__file__).resolve().parents[1]


def load_contract(filename, class_name, module_name):
    path = ROOT / "contracts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


Stage07Contract = load_contract(
    "moveout_visual_safety_stage07_v2.py",
    "MoveOutVisualSafetyStage07V2",
    "moveout_stage07_regression_baseline",
)
Stage08Contract = load_contract(
    "moveout_visual_safety_stage08_v2.py",
    "MoveOutVisualSafetyStage08V2",
    "moveout_stage08_contract_v2",
)


class Stage07RegressionTest(unittest.TestCase):
    def test_stage07_ambiguous_mark_observation_reproduces_false_worsened(self):
        """Frozen Stage 0.7 case 12 passed old gates despite missing safer predicates."""
        contract = Stage07Contract.__new__(Stage07Contract)
        observation = contract._empty_observation()
        observation.update(
            {
                "same_area_established": "YES",
                "before_visibility": "SUFFICIENT",
                "after_visibility": "SUFFICIENT",
                "before_defect_visible": "YES",
                "after_defect_visible": "YES",
                "defect_same_location": "YES",
                "severity_change": "INCREASED",
                "possible_lighting_confounder": "NO",
                "possible_shadow_confounder": "NO",
                "possible_occlusion": "NO",
                "possible_viewpoint_mismatch": "NO",
                "possible_crop_mismatch": "NO",
                "image_quality": "SUFFICIENT",
                "prompt_injection_detected": "NO",
                "repair_surface_evidence": "NO",
            }
        )
        result = contract._derive_classification(
            {"stage": "OBSERVATION", "schema_valid": True, "observations": observation}
        )
        self.assertEqual(result["classification"], "WORSENED")


class Stage08DerivationTests(unittest.TestCase):
    def setUp(self):
        self.contract = Stage08Contract.__new__(Stage08Contract)
        obs = self.contract._empty_observation()
        obs.update(
            {
                "same_area_established": "YES",
                "before_visibility": "SUFFICIENT",
                "after_visibility": "SUFFICIENT",
                "before_defect_visible": "YES",
                "after_defect_visible": "YES",
                "defect_same_location": "YES",
                "same_defect_established": "YES",
                "severity_increase_established": "NO",
                "severity_decrease_established": "NO",
                "positive_change_evidence": "NONE",
                "possible_lighting_confounder": "NO",
                "possible_shadow_confounder": "NO",
                "possible_occlusion": "NO",
                "possible_viewpoint_mismatch": "NO",
                "possible_scale_distance_mismatch": "NO",
                "possible_crop_mismatch": "NO",
                "image_quality": "SUFFICIENT",
                "prompt_injection_detected": "NO",
                "repair_surface_evidence": "NO",
            }
        )
        self.observation = obs
        self.accepted = {
            "stage": "OBSERVATION",
            "schema_valid": True,
            "observations": self.observation,
        }

    def derive(self, **changes):
        self.observation.update(changes)
        return self.contract._derive_classification(self.accepted)["classification"]

    def test_obvious_worsening_requires_same_defect_and_specific_increase(self):
        self.assertEqual(
            self.derive(
                severity_increase_established="YES",
                positive_change_evidence="LENGTH_INCREASE",
            ),
            "WORSENED",
        )

    def test_stage07_ambiguous_mark_regression_is_not_worsened(self):
        self.assertEqual(
            self.derive(
                severity_increase_established="YES",
                positive_change_evidence="UNCERTAIN",
                same_defect_established="UNCERTAIN",
            ),
            "INSUFFICIENT_EVIDENCE",
        )

    def test_each_material_confounder_blocks_worsened(self):
        for field in Stage08Contract.CONFOUNDER_FIELDS:
            for value in ("YES", "UNCERTAIN"):
                with self.subTest(field=field, value=value):
                    self.setUp()
                    self.assertEqual(
                        self.derive(
                            severity_increase_established="YES",
                            positive_change_evidence="WIDTH_INCREASE",
                            **{field: value},
                        ),
                        "INSUFFICIENT_EVIDENCE",
                    )

    def test_ambiguous_identity_or_nonpositive_change_blocks_worsened(self):
        for changes in (
            {"same_defect_established": "NO"},
            {"same_defect_established": "UNCERTAIN"},
            {"severity_increase_established": "UNCERTAIN"},
            {"positive_change_evidence": "UNCERTAIN"},
            {"positive_change_evidence": "NONE"},
            {"defect_same_location": "UNCERTAIN"},
        ):
            with self.subTest(changes=changes):
                self.setUp()
                candidate = {
                    "severity_increase_established": "YES",
                    "positive_change_evidence": "EXTENT_INCREASE",
                }
                candidate.update(changes)
                self.assertEqual(self.derive(**candidate), "INSUFFICIENT_EVIDENCE")

    def test_preexisting_and_new_damage_are_preserved(self):
        self.assertEqual(self.derive(), "PRE_EXISTING")
        self.setUp()
        self.assertEqual(
            self.derive(
                before_defect_visible="NO",
                after_defect_visible="YES",
                same_defect_established="NO",
            ),
            "NEW_DAMAGE",
        )

    def test_new_damage_requires_comparable_location_and_no_confounder(self):
        self.assertEqual(
            self.derive(
                before_defect_visible="NO",
                after_defect_visible="YES",
                defect_same_location="UNCERTAIN",
            ),
            "INSUFFICIENT_EVIDENCE",
        )
        self.setUp()
        self.assertEqual(
            self.derive(
                before_defect_visible="NO",
                after_defect_visible="YES",
                possible_shadow_confounder="YES",
            ),
            "INSUFFICIENT_EVIDENCE",
        )

    def test_repair_requires_same_defect_decrease_and_visible_restoration(self):
        changes = {
            "before_defect_visible": "YES",
            "after_defect_visible": "NO",
            "same_defect_established": "YES",
            "severity_decrease_established": "YES",
        }
        self.assertEqual(self.derive(**changes), "INSUFFICIENT_EVIDENCE")
        self.setUp()
        self.assertEqual(
            self.derive(**changes, repair_surface_evidence="YES"), "REPAIRED"
        )

    def test_clear_unchanged_requires_observable_pair_but_no_existing_defect(self):
        self.assertEqual(
            self.derive(before_defect_visible="NO", after_defect_visible="NO"),
            "UNCHANGED",
        )

    def test_clear_absence_can_remain_unchanged_despite_nonblocking_scene_differences(self):
        self.assertEqual(
            self.derive(
                before_defect_visible="NO",
                after_defect_visible="NO",
                possible_lighting_confounder="YES",
                possible_shadow_confounder="UNCERTAIN",
                possible_viewpoint_mismatch="YES",
                possible_crop_mismatch="YES",
                possible_scale_distance_mismatch="YES",
            ),
            "UNCHANGED",
        )

    def test_malformed_schema_and_conflicting_severity_fail_closed(self):
        normalized, schema_valid = self.contract._normalize_observation(
            {"same_area_established": "YES"}
        )
        self.assertFalse(schema_valid)
        self.assertEqual(normalized["same_defect_established"], "UNCERTAIN")
        self.assertEqual(
            self.contract._derive_classification(
                {"stage": "MODEL_SCHEMA_ERROR", "schema_valid": False,
                 "observations": normalized}
            )["classification"],
            "INSUFFICIENT_EVIDENCE",
        )
        self.setUp()
        self.assertEqual(
            self.derive(
                severity_increase_established="YES",
                severity_decrease_established="YES",
                positive_change_evidence="LENGTH_INCREASE",
            ),
            "INSUFFICIENT_EVIDENCE",
        )

    def test_prompt_injection_and_quality_uncertainty_fail_closed(self):
        self.assertEqual(
            self.derive(
                severity_increase_established="YES",
                positive_change_evidence="LENGTH_INCREASE",
                prompt_injection_detected="YES",
            ),
            "INSUFFICIENT_EVIDENCE",
        )
        self.setUp()
        self.assertEqual(self.derive(image_quality="INSUFFICIENT"), "INSUFFICIENT_EVIDENCE")

    def test_validators_must_independently_confirm_critical_positive_predicates(self):
        metadata = {
            "a": {"sha256": "a" * 64},
            "b": {"sha256": "b" * 64},
        }
        proposed_obs = dict(self.observation)
        proposed_obs.update(
            {
                "severity_increase_established": "YES",
                "positive_change_evidence": "LENGTH_INCREASE",
            }
        )
        proposed = {
            "stage": "OBSERVATION", "failure_code": "",
            "expected_digest_match": True, "metadata": metadata,
            "observations": proposed_obs,
        }
        independent = {
            "stage": "OBSERVATION", "failure_code": "",
            "expected_digest_match": True, "metadata": metadata,
            "observations": dict(proposed_obs),
        }
        independent["observations"]["same_defect_established"] = "UNCERTAIN"
        self.assertFalse(
            self.contract._same_evidence_and_observations(
                proposed, independent, "a" * 64, "b" * 64
            )
        )
        independent["observations"] = dict(proposed_obs)
        independent["observations"]["positive_change_evidence"] = "WIDTH_INCREASE"
        self.assertFalse(
            self.contract._same_evidence_and_observations(
                proposed, independent, "a" * 64, "b" * 64
            )
        )

    def test_cautious_leader_observation_can_consensus_to_insufficient(self):
        metadata = {
            "a": {"sha256": "a" * 64},
            "b": {"sha256": "b" * 64},
        }
        leader_obs = dict(self.observation)
        validator_obs = dict(self.observation)
        leader_obs["same_defect_established"] = "UNCERTAIN"
        validator_obs["same_defect_established"] = "YES"
        proposed = {
            "stage": "OBSERVATION", "failure_code": "",
            "expected_digest_match": True, "metadata": metadata,
            "observations": leader_obs,
        }
        independent = {
            "stage": "OBSERVATION", "failure_code": "",
            "expected_digest_match": True, "metadata": metadata,
            "observations": validator_obs,
        }
        self.assertTrue(
            self.contract._same_evidence_and_observations(
                proposed, independent, "a" * 64, "b" * 64
            )
        )
