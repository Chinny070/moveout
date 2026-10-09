"""Guard the reviewed Stage 4–5.2 nondeterministic scope in MoveOut."""

import ast
from pathlib import Path


CONTRACT = Path("contracts/moveout_protocol_v1.py")
ALLOWED_CALLS = [
    ("gl.nondet.web.get", "_retrieve_and_verify_evidence"),
    ("gl.nondet.web.get", "_observe_single"),
    ("gl.nondet.web.get", "_observe_target_single"),
    ("gl.nondet.web.get", "_evaluate_continuity_pair"),
    ("gl.nondet.web.get", "get_checked"),
    ("gl.nondet.exec_prompt", "_observe_single"),
    ("gl.nondet.exec_prompt", "_observe_pair"),
    ("gl.nondet.exec_prompt", "_observe_target_single"),
    ("gl.nondet.exec_prompt", "_evaluate_continuity_pair"),
    ("gl.vm.run_nondet_unsafe", "verify_evidence_provenance"),
    ("gl.vm.run_nondet_unsafe", "observe_evidence"),
    ("gl.vm.run_nondet_unsafe", "observe_evidence_pair"),
    ("gl.vm.run_nondet_unsafe", "observe_nominated_target"),
    ("gl.vm.run_nondet_unsafe", "assess_supplemental_continuity"),
]


def dotted_name(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


class ScopeVisitor(ast.NodeVisitor):
    def __init__(self):
        self.functions = []
        self.nondeterministic_calls = []
        self.forbidden_writers = []

    def visit_FunctionDef(self, node):
        self.functions.append(node.name)
        if any(dotted_name(item) == "gl.public.write" for item in node.decorator_list):
            if any(word in node.name.lower()
                   for word in ("finding", "established_condition")):
                self.forbidden_writers.append(node.name)
        self.generic_visit(node)
        self.functions.pop()

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_Call(self, node):
        name = dotted_name(node.func)
        if (name.startswith("gl.nondet.") or name.startswith("gl.get_webpage") or
                name.startswith("gl.exec_prompt") or name.startswith("gl.vm.run_nondet")):
            self.nondeterministic_calls.append((name, self.functions[-1] if self.functions else ""))
        self.generic_visit(node)


def main():
    tree = ast.parse(CONTRACT.read_text(encoding="utf-8"), filename=str(CONTRACT))
    visitor = ScopeVisitor()
    visitor.visit(tree)
    errors = []
    expected = sorted(ALLOWED_CALLS)
    actual = sorted(visitor.nondeterministic_calls)
    if actual != expected:
        errors.append(f"nondeterministic API calls differ from Stage 4 allowlist: {actual!r}")
    if visitor.forbidden_writers:
        errors.append(f"visual observation/finding public writers found: {visitor.forbidden_writers!r}")
    if errors:
        raise SystemExit("\n".join(errors))
    print("Stage 4–5.3 scope passed: bounded target/continuity retrieval, vision, and validator; no finding writer")


if __name__ == "__main__":
    main()
