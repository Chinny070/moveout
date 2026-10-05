# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *

class VisualCapabilityProof(gl.Contract):
    result_json: str

    def __init__(self):
        self.result_json = ""

    def _compare(self, image_a_url: str, image_b_url: str, retrieval: str) -> None:
        def unavailable(reason: str) -> str:
            return json.dumps({
                "comparison": "UNCLEAR",
                "observations": [reason[:120]],
                "confidence": "LOW",
            }, sort_keys=True)

        def analyze_pair():
            try:
                if retrieval == "screenshot":
                    image_a = gl.nondet.web.render(image_a_url, mode="screenshot")
                    image_b = gl.nondet.web.render(image_b_url, mode="screenshot")
                else:
                    response_a = gl.nondet.web.get(image_a_url)
                    response_b = gl.nondet.web.get(image_b_url)
                    for response in (response_a, response_b):
                        if response.status != 200:
                            return unavailable(f"http_status:{response.status}")
                        raw_type = response.headers.get("content-type", b"")
                        if isinstance(raw_type, bytes):
                            content_type = raw_type.decode("utf-8", errors="replace")
                        else:
                            content_type = str(raw_type)
                        mime = content_type.split(";", 1)[0].strip().lower()
                        if not mime.startswith("image/"):
                            return unavailable(f"not_image_mime:{mime or 'missing'}")
                        if response.body is None or len(response.body) == 0:
                            return unavailable("empty_image_body")
                    image_a = response_a.body
                    image_b = response_b.body
                answer = gl.nondet.exec_prompt(
                    "Compare these two images in order. Describe only visible differences. "
                    "Return JSON with exactly: comparison (CHANGED, UNCHANGED, or UNCLEAR), "
                    "observations (array of short strings), confidence (HIGH, MEDIUM, or LOW). "
                    "If the images are unrelated, ambiguous, inaccessible, or do not permit "
                    "a reliable comparison, use UNCLEAR and LOW. Do not infer facts outside "
                    "the pixels.",
                    images=[image_a, image_b],
                    response_format="json",
                )
                if not isinstance(answer, dict):
                    return unavailable("invalid_model_result")
                comparison = answer.get("comparison", "UNCLEAR")
                confidence = answer.get("confidence", "LOW")
                observations = answer.get("observations", [])
                if comparison not in ("CHANGED", "UNCHANGED", "UNCLEAR"):
                    comparison = "UNCLEAR"
                if confidence not in ("HIGH", "MEDIUM", "LOW"):
                    confidence = "LOW"
                if not isinstance(observations, list):
                    observations = []
                return json.dumps({
                    "comparison": comparison,
                    "observations": [str(item)[:120] for item in observations[:4]],
                    "confidence": confidence,
                }, sort_keys=True)
            except Exception as exc:
                # Disposable diagnostic proof: retain bounded exception class/message.
                return unavailable(f"evidence_error:{type(exc).__name__}:{str(exc)}")

        self.result_json = gl.eq_principle.prompt_comparative(
            analyze_pair,
            principle=(
                "The comparison field must match exactly. Confidence may differ by one "
                "adjacent level only if comparison matches. Observations must be grounded "
                "in the two images. If either run cannot retrieve or interpret both images, "
                "or sees unrelated/ambiguous evidence, require UNCLEAR with LOW confidence. "
                "CHANGED and UNCHANGED are never equivalent."
            ),
        )

    @gl.public.write
    def compare_screenshots(self, image_a_url: str, image_b_url: str) -> None:
        self._compare(image_a_url, image_b_url, "screenshot")

    @gl.public.write
    def compare_direct_images(self, image_a_url: str, image_b_url: str) -> None:
        self._compare(image_a_url, image_b_url, "direct")

    @gl.public.view
    def get_result(self) -> str:
        return self.result_json
