# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import hashlib
import json


class VisualCapabilityProofV4(gl.Contract):
    result_json: str

    def __init__(self):
        self.result_json = ""

    def _fetch(self, url: str):
        response = gl.nondet.web.get(url)
        body = response.body
        raw_type = response.headers.get("content-type", b"")
        if isinstance(raw_type, bytes):
            content_type = raw_type.decode("utf-8", errors="replace")
        else:
            content_type = str(raw_type)
        mime = content_type.split(";", 1)[0].strip().lower()
        prefix = [int(item) for item in body[:16]] if body else []
        digest = hashlib.sha256(body).hexdigest() if body else ""
        return response, body, {
            "status": int(response.status),
            "content_type": content_type[:120],
            "mime": mime,
            "size": len(body),
            "prefix_hex": "".join(format(value, "02x") for value in prefix),
            "sha256": digest,
        }

    def _raw_single(self, url: str):
        def interpret():
            try:
                response, body, metadata = self._fetch(url)
                if response.status != 200:
                    return {"stage": "RESPONSE_VALIDATION", "metadata": metadata,
                            "recognized": False, "observation": "UNCLEAR"}
                if not metadata["mime"].startswith("image/") or not body:
                    return {"stage": "RESPONSE_VALIDATION", "metadata": metadata,
                            "recognized": False, "observation": "UNCLEAR"}
                result = gl.nondet.exec_prompt(
                    "Inspect this single image. Is the main visible object a red square? "
                    "Return JSON only with recognized (true or false) and observation "
                    "(one short visible description, or UNCLEAR). Do not guess.",
                    images=[body], response_format="json",
                )
                return {"stage": "VISION", "metadata": metadata,
                        "recognized": bool(result.get("recognized", False)),
                        "observation": str(result.get("observation", "UNCLEAR"))[:120]}
            except Exception as exc:
                return {"stage": "OTHER", "recognized": False,
                        "observation": (type(exc).__name__ + ":" + str(exc))[:160]}

        self.result_json = json.dumps(
            gl.eq_principle.prompt_comparative(
                interpret,
                principle=("Independently retrieve the same image and inspect it. "
                           "Accept only if the recognized decision agrees and both "
                           "observations are consistent with the retrieved image."),
            ), sort_keys=True,
        )

    def _raw_pair(self, url_a: str, url_b: str):
        def interpret():
            try:
                response_a, body_a, meta_a = self._fetch(url_a)
                response_b, body_b, meta_b = self._fetch(url_b)
                metadata = {"a": meta_a, "b": meta_b}
                if response_a.status != 200 or response_b.status != 200:
                    return {"stage": "RESPONSE_VALIDATION", "metadata": metadata,
                            "comparison": "UNCLEAR", "observations": []}
                if (not meta_a["mime"].startswith("image/") or
                    not meta_b["mime"].startswith("image/") or not body_a or not body_b):
                    return {"stage": "RESPONSE_VALIDATION", "metadata": metadata,
                            "comparison": "UNCLEAR", "observations": []}
                result = gl.nondet.exec_prompt(
                    "Compare image A then image B. Is the central square red in A and "
                    "blue in B? Return JSON only: comparison (CHANGED, UNCHANGED, "
                    "UNCLEAR), observations (at most two short visible facts), "
                    "confidence (HIGH, MEDIUM, LOW). Use UNCLEAR if either image or "
                    "difference is uncertain.",
                    images=[body_a, body_b], response_format="json",
                )
                comparison = result.get("comparison", "UNCLEAR")
                if comparison not in ("CHANGED", "UNCHANGED", "UNCLEAR"):
                    comparison = "UNCLEAR"
                observations = result.get("observations", [])
                if not isinstance(observations, list):
                    observations = []
                return {"stage": "VISION", "metadata": metadata,
                        "comparison": comparison,
                        "observations": [str(x)[:120] for x in observations[:2]],
                        "confidence": result.get("confidence", "LOW")}
            except Exception as exc:
                return {"stage": "OTHER", "comparison": "UNCLEAR",
                        "observations": [(type(exc).__name__ + ":" + str(exc))[:160]]}

        self.result_json = json.dumps(
            gl.eq_principle.prompt_comparative(
                interpret,
                principle=("Independently retrieve and interpret both ordered images. "
                           "The comparison enum must match exactly. Reject any claimed "
                           "certainty if either image cannot be fetched or visually read."),
            ), sort_keys=True,
        )

    @gl.public.write
    def inspect_raw(self, url: str) -> None:
        def inspect():
            try:
                _, _, metadata = self._fetch(url)
                return metadata
            except Exception as exc:
                return {"error": (type(exc).__name__ + ":" + str(exc))[:160]}
        self.result_json = json.dumps(gl.eq_principle.strict_eq(inspect), sort_keys=True)

    @gl.public.write
    def recognize_raw(self, url: str) -> None:
        self._raw_single(url)

    @gl.public.write
    def compare_raw(self, url_a: str, url_b: str) -> None:
        self._raw_pair(url_a, url_b)

    @gl.public.view
    def get_result(self) -> str:
        return self.result_json
