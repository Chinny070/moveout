# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *

class VisualCapabilityProof(gl.Contract):
    result_json: str

    def __init__(self):
        self.result_json = ""

    @gl.public.write
    def compare_screenshots(self, image_a_url: str, image_b_url: str) -> None:
        """Compare two public web-rendered visual sources; retain compact JSON."""
        def analyze_pair():
            try:
                image_a = gl.nondet.web.render(image_a_url, mode="screenshot")
                image_b = gl.nondet.web.render(image_b_url, mode="screenshot")
                answer = gl.nondet.exec_prompt(
                    "Compare these two images in order. They are separate reference and "
                    "current-state visual evidence. Describe only visible differences. "
                    "Return JSON with exactly: comparison (CHANGED, UNCHANGED, or UNCLEAR), "
                    "observations (array of short strings), confidence (HIGH, MEDIUM, or LOW). "
                    "If the images are unrelated, inaccessible, too ambiguous, or do not "
                    "permit a reliable comparison, use UNCLEAR and LOW. Do not infer facts "
                    "outside the pixels.",
                    images=[image_a, image_b],
                    response_format="json",
                )
                if not isinstance(answer, dict):
                    return '{"comparison":"UNCLEAR","observations":["invalid_model_result"],"confidence":"LOW"}'
                comparison = answer.get("comparison", "UNCLEAR")
                confidence = answer.get("confidence", "LOW")
                observations = answer.get("observations", [])
                if comparison not in ("CHANGED", "UNCHANGED", "UNCLEAR"):
                    comparison = "UNCLEAR"
                if confidence not in ("HIGH", "MEDIUM", "LOW"):
                    confidence = "LOW"
                if not isinstance(observations, list):
                    observations = []
                # Avoid retaining arbitrary narrative or oversized outputs.
                normalized = {
                    "comparison": comparison,
                    "observations": [str(item)[:120] for item in observations[:4]],
                    "confidence": confidence,
                }
                return json.dumps(normalized, sort_keys=True)
            except Exception:
                # Failure to obtain either source is an explicit fail-closed result.
                return '{"comparison":"UNCLEAR","observations":["evidence_unavailable_or_invalid"],"confidence":"LOW"}'

        self.result_json = gl.eq_principle.prompt_comparative(
            analyze_pair,
            principle=(
                "The JSON comparison field must match exactly. Confidence may differ by "
                "one adjacent level only if both agree on the comparison. Observations "
                "must refer only to visible properties shared by the pair. If either run "
                "cannot retrieve/interpret both images or sees unrelated/ambiguous evidence, "
                "the result must be UNCLEAR with LOW confidence. A disagreement on "
                "CHANGED versus UNCHANGED is not equivalent."
            ),
        )

    @gl.public.view
    def get_result(self) -> str:
        return self.result_json
