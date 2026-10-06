# MoveOut Stage 2 verification record

**Status: PASS locally; not deployed. Stage 3 has not started.** Stage 2 adds the deterministic inspection, evidence, review, disagreement, continuity, and maintenance protocol documented in [`MOVEOUT_STAGE_2_INSPECTION_EVIDENCE.md`](MOVEOUT_STAGE_2_INSPECTION_EVIDENCE.md).

## Source and scope

- Contract: `contracts/moveout_protocol_v1.py`
- Stage 1.1 baseline source SHA-256: `EC5287A8AEE928CB024B44C3E649F45ADD17B811D357918957CF4330663724D6`
- Stage 2 source SHA-256: `596318A50FDE982E79EC5BDAF3EE7469D7D9EC5F1E776BB1C665FEE8480FA9AA`
- Pinned GenVM dependency: `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`
- Local CLI and linter: `genlayer 0.39.1`, `genvm-lint 0.11.0` (inherited from the Stage 1.1 verification environment)
- Network: local Direct Mode test runner only. No StudioNet call or deployment.
- Contract methods after extension: 64 (39 views, 25 writes).

## Verification results

| Check | Result |
|---|---|
| `gltest tests -q` | PASS: 145 tests; includes 63 Stage 1 Direct Mode, 46 historical regression, and 36 Stage 2 tests |
| `gltest tests/test_moveout_stage2_protocol.py -q` | PASS: 36 Stage 2 tests |
| Stage 1.1 regressions | PASS: all 109 pre-Stage-2 tests are included in the 145-test run |
| `genvm-lint lint contracts/moveout_protocol_v1.py` | PASS: 3 checks |
| `genvm-lint check contracts/moveout_protocol_v1.py` | PASS: validation; 64 methods (39 view, 25 write) |
| `python -m compileall -q contracts tests` | PASS |
| `git diff --check` | PASS |
| Determinism / production scope scan | PASS: no `gl.nondet`, web fetch/render, prompt execution, nondeterministic runner, or benchmark selector in the production contract |
| Secret scan | PASS for production contract and Stage 1.1 hardening document; the Stage 2 script does not expand the scan to the full repository |
| `scripts/verify_stage1.ps1` | PASS: complete combined suite, lint, SDK check, syntax compile, source/scope and secret scans, staged/unstaged whitespace checks |

The linter was run with `PYTHONIOENCODING=utf-8` because the default Windows CP1252 console cannot print the linter's Unicode checkmark. With UTF-8 enabled, lint and SDK validation both completed successfully.

## Test coverage and result

The Stage 2 suite has 36 tests covering manifest membership and freeze snapshots; structural completeness and explanation of missing requirements; capture-slot binding and freeze behavior; valid and invalid visual-continuity references; frozen baseline preservation; Move-In/Move-Out chronology; dual-party review and acknowledgement semantics; append-only disputes and counter-evidence; inspection receipts and bounded reads; participant condition claims and prior-condition references; maintenance/repair links; authority checks; replay/idempotency; and the absence of observation/finding promotion paths.

The direct test runner uses local Direct Mode and mock/test state. It establishes contract behavior in that environment; it does not establish deployed StudioNet gas, storage sizing, cross-validator behavior, or real-world visual accuracy. Maximum collection capacities were not exhaustively filled with thousands of state writes.

## Deployment and boundaries

- No canonical or disposable contract was deployed.
- No wallet transaction was submitted.
- No visual AI, nondeterministic call, remote source fetch, MIME validation, digest-to-remote-byte verification, or image classification was added.
- Participant descriptions, capture-quality metadata, reviews, and continuity references remain claims/intent. They are not protocol-established visual facts.
- The current architecture has no public Visual Observation or Established Condition writer.
- Source URLs and caller-supplied digests do not prove that a source currently returns those bytes.
- Stage 3 readiness means only that this local deterministic Stage 2 gate passed; hosted compatibility and visual adjudication remain separate requirements.

## Final disposition

Stage 2 success criteria A–J are satisfied by the implementation and local checks. The contract remains undeployed. The repository verification entry point is `scripts/verify_moveout.ps1`; the original Stage 1 entry point remains available and runs the complete combined suite.
