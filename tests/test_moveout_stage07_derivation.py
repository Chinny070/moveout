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


_genlayer_stub = types.ModuleType("genlayer")
_genlayer_stub.gl = types.SimpleNamespace(
    Contract=object,
    public=_Decorators(),
)
sys.modules.setdefault("genlayer", _genlayer_stub)

_contract_path = (
    Path(__file__).resolve().parents[1]
    / "contracts"
    / "moveout_visual_safety_stage07_v1.py"
)
_spec = importlib.util.spec_from_file_location("moveout_stage07_contract", _contract_path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
_contract_class = _module.MoveOutVisualSafetyStage07V1


class Stage07DerivationTests(unittest.TestCase):
    def setUp(self):
        self.contract = _contract_class.__new__(_contract_class)
        observation = self.contract._empty_observation()
        observation.update(
            {
                "same_area_established": "YES",
                "before_visibility": "SUFFICIENT",
                "after_visibility": "SUFFICIENT",
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
        self.accepted = {
            "stage": "OBSERVATION",
            "schema_valid": True,
            "observations": observation,
        }

    def derive(self, **changes):
        self.accepted["observations"].update(changes)
        return self.contract._derive_classification(self.accepted)["classification"]

    def test_clear_deterministic_condition_classes(self):
        self.assertEqual(
            self.derive(before_defect_visible="NO", after_defect_visible="NO"),
            "UNCHANGED",
        )
        self.assertEqual(
            self.derive(
                before_defect_visible="YES",
                after_defect_visible="YES",
                defect_same_location="YES",
                severity_change="NONE",
            ),
            "PRE_EXISTING",
        )
        self.assertEqual(
            self.derive(
                before_defect_visible="NO",
                after_defect_visible="YES",
                defect_same_location="YES",
            ),
            "NEW_DAMAGE",
        )
        self.assertEqual(
            self.derive(
                before_defect_visible="YES",
                after_defect_visible="YES",
                defect_same_location="YES",
                severity_change="INCREASED",
            ),
            "WORSENED",
        )

    def test_uncertainty_and_each_confounder_fail_closed(self):
        self.assertEqual(
            self.derive(before_defect_visible="UNCERTAIN", after_defect_visible="YES"),
            "INSUFFICIENT_EVIDENCE",
        )
        self.assertEqual(
            self.derive(same_area_established="UNCERTAIN"),
            "INSUFFICIENT_EVIDENCE",
        )
        for field in self.contract.CONFOUNDER_FIELDS:
            for value in ("YES", "UNCERTAIN"):
                with self.subTest(field=field, value=value):
                    self.setUp()
                    self.assertEqual(
                        self.derive(
                            before_defect_visible="NO",
                            after_defect_visible="YES",
                            defect_same_location="YES",
                            **{field: value},
                        ),
                        "INSUFFICIENT_EVIDENCE",
                    )

    def test_visibility_quality_and_prompt_injection_fail_closed(self):
        for values in (
            {"before_visibility": "INSUFFICIENT"},
            {"after_visibility": "INSUFFICIENT"},
            {"image_quality": "INSUFFICIENT"},
            {"prompt_injection_detected": "YES"},
            {"prompt_injection_detected": "UNCERTAIN"},
        ):
            with self.subTest(values=values):
                self.setUp()
                self.assertEqual(
                    self.derive(
                        before_defect_visible="NO",
                        after_defect_visible="YES",
                        defect_same_location="YES",
                        **values,
                    ),
                    "INSUFFICIENT_EVIDENCE",
                )

    def test_damage_changes_require_comparable_location_and_severity(self):
        self.assertEqual(
            self.derive(
                before_defect_visible="NO",
                after_defect_visible="YES",
                defect_same_location="UNCERTAIN",
            ),
            "INSUFFICIENT_EVIDENCE",
        )
        self.assertEqual(
            self.derive(
                before_defect_visible="YES",
                after_defect_visible="YES",
                defect_same_location="YES",
                severity_change="UNCERTAIN",
            ),
            "INSUFFICIENT_EVIDENCE",
        )

    def test_repair_requires_positive_surface_restoration_evidence(self):
        base = {
            "before_defect_visible": "YES",
            "after_defect_visible": "NO",
            "defect_same_location": "YES",
            "severity_change": "DECREASED",
        }
        self.assertEqual(self.derive(**base), "INSUFFICIENT_EVIDENCE")
        self.setUp()
        self.assertEqual(
            self.derive(**base, repair_surface_evidence="YES"),
            "REPAIRED",
        )

    def test_invalid_observation_stage_cannot_produce_condition_class(self):
        self.accepted["stage"] = "MODEL_SCHEMA_ERROR"
        self.accepted["schema_valid"] = False
        self.assertEqual(
            self.contract._derive_classification(self.accepted)["classification"],
            "INSUFFICIENT_EVIDENCE",
        )

    def test_schema_normalization_defaults_invalid_fields_to_uncertain(self):
        answer = self.contract._empty_observation()
        answer["same_area_established"] = "YES"
        normalized, valid = self.contract._normalize_observation(answer)
        self.assertTrue(valid)
        self.assertEqual(normalized["same_area_established"], "YES")

        del answer["same_area_established"]
        normalized, valid = self.contract._normalize_observation(answer)
        self.assertFalse(valid)
        self.assertEqual(normalized["same_area_established"], "UNCERTAIN")

    def test_equivalence_requires_digest_and_critical_observation_agreement(self):
        sha_a = "a" * 64
        sha_b = "b" * 64
        candidate = {
            "stage": "OBSERVATION",
            "failure_code": "",
            "expected_digest_match": True,
            "metadata": {
                "a": {"sha256": sha_a},
                "b": {"sha256": sha_b},
            },
            "observations": self.contract._empty_observation(),
        }
        candidate["observations"]["same_area_established"] = "YES"
        identical = {
            "stage": "OBSERVATION",
            "failure_code": "",
            "expected_digest_match": True,
            "metadata": {
                "a": {"sha256": sha_a},
                "b": {"sha256": sha_b},
            },
            "observations": dict(candidate["observations"]),
        }
        self.assertTrue(
            self.contract._same_evidence_and_observations(
                candidate, identical, sha_a, sha_b
            )
        )
        identical["observations"]["same_area_established"] = "UNCERTAIN"
        self.assertFalse(
            self.contract._same_evidence_and_observations(
                candidate, identical, sha_a, sha_b
            )
        )
        identical["observations"]["same_area_established"] = "YES"
        identical["metadata"]["b"]["sha256"] = "c" * 64
        self.assertFalse(
            self.contract._same_evidence_and_observations(
                candidate, identical, sha_a, sha_b
            )
        )


if __name__ == "__main__":
    unittest.main()
