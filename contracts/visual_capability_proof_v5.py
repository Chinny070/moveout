# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import hashlib
import json


class VisualCapabilityProofV5(gl.Contract):
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
        metadata = {
            "status": int(response.status),
            "content_type": content_type[:120],
            "mime": mime,
            "size": len(body),
            "prefix_hex": "".join(format(value, "02x") for value in prefix),
            "sha256": hashlib.sha256(body).hexdigest() if body else "",
        }
        return response, body, metadata

    def _analyze_one(self, url: str):
        try:
            response, body, metadata = self._fetch(url)
            if response.status != 200 or not body or not metadata["mime"].startswith("image/"):
                return {"stage": "RESPONSE_VALIDATION", "metadata": metadata,
                        "recognized": None, "observation": "UNCLEAR"}
            answer = gl.nondet.exec_prompt(
                "Inspect this one image. Is its central square red? Return JSON only "
                "with recognized (true/false) and observation (one short visible fact). "
                "If you cannot visually inspect the image, return recognized false and "
                "observation UNCLEAR.",
                images=[body], response_format="json",
            )
            recognized = answer.get("recognized", False)
            if not isinstance(recognized, bool):
                recognized = False
            return {"stage": "VISION", "metadata": metadata,
                    "recognized": recognized,
                    "observation": str(answer.get("observation", "UNCLEAR"))[:120]}
        except Exception as exc:
            return {"stage": "OTHER", "metadata": {}, "recognized": None,
                    "observation": (type(exc).__name__ + ":" + str(exc))[:160]}

    def _analyze_two(self, url_a: str, url_b: str):
        try:
            response_a, body_a, metadata_a = self._fetch(url_a)
            response_b, body_b, metadata_b = self._fetch(url_b)
            metadata = {"a": metadata_a, "b": metadata_b}
            if (response_a.status != 200 or response_b.status != 200 or not body_a or not body_b or
                not metadata_a["mime"].startswith("image/") or
                not metadata_b["mime"].startswith("image/")):
                return {"stage": "RESPONSE_VALIDATION", "metadata": metadata,
                        "comparison": "UNCLEAR", "observations": [], "confidence": "LOW"}
            answer = gl.nondet.exec_prompt(
                "Compare image A followed by image B. Is the central square red in A "
                "and blue in B? Return JSON only with comparison (CHANGED, UNCHANGED, "
                "or UNCLEAR), observations (at most two short visible facts), and "
                "confidence (HIGH, MEDIUM, or LOW). Do not guess; use UNCLEAR if the "
                "images cannot be visually inspected.",
                images=[body_a, body_b], response_format="json",
            )
            comparison = answer.get("comparison", "UNCLEAR")
            if comparison not in ("CHANGED", "UNCHANGED", "UNCLEAR"):
                comparison = "UNCLEAR"
            observations = answer.get("observations", [])
            if not isinstance(observations, list):
                observations = []
            confidence = answer.get("confidence", "LOW")
            if confidence not in ("HIGH", "MEDIUM", "LOW"):
                confidence = "LOW"
            return {"stage": "VISION", "metadata": metadata,
                    "comparison": comparison,
                    "observations": [str(x)[:120] for x in observations[:2]],
                    "confidence": confidence}
        except Exception as exc:
            return {"stage": "OTHER", "metadata": {}, "comparison": "UNCLEAR",
                    "observations": [(type(exc).__name__ + ":" + str(exc))[:160]],
                    "confidence": "LOW"}

    @gl.public.write
    def recognize_raw(self, url: str) -> None:
        def leader_fn():
            return self._analyze_one(url)

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            proposed = leader_result.calldata
            independent = self._analyze_one(url)
            if proposed.get("stage") != independent.get("stage"):
                return False
            if proposed.get("stage") == "VISION":
                return (proposed["metadata"].get("sha256") == independent["metadata"].get("sha256")
                        and proposed.get("recognized") == independent.get("recognized"))
            return proposed.get("metadata") == independent.get("metadata")

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        self.result_json = json.dumps(result, sort_keys=True)

    @gl.public.write
    def compare_raw(self, url_a: str, url_b: str) -> None:
        def leader_fn():
            return self._analyze_two(url_a, url_b)

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            proposed = leader_result.calldata
            independent = self._analyze_two(url_a, url_b)
            if proposed.get("stage") != independent.get("stage"):
                return False
            if proposed.get("stage") == "VISION":
                leader_meta = proposed.get("metadata", {})
                validator_meta = independent.get("metadata", {})
                same_bytes = all(
                    leader_meta.get(key, {}).get("sha256") == validator_meta.get(key, {}).get("sha256")
                    for key in ("a", "b")
                )
                return same_bytes and proposed.get("comparison") == independent.get("comparison")
            return proposed.get("metadata") == independent.get("metadata")

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        self.result_json = json.dumps(result, sort_keys=True)

    @gl.public.write
    def inspect_raw(self, url: str) -> None:
        def inspect():
            try:
                _, _, metadata = self._fetch(url)
                return metadata
            except Exception as exc:
                return {"error": (type(exc).__name__ + ":" + str(exc))[:160]}
        self.result_json = json.dumps(gl.eq_principle.strict_eq(inspect), sort_keys=True)

    @gl.public.view
    def get_result(self) -> str:
        return self.result_json
