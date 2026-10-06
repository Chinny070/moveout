# MoveOut Stage 1 verification record

**Historical status:** Stage 1.1 local hardening passed. Stage 2 is now implemented and locally verified; its results are recorded in [`MOVEOUT_STAGE_2_VERIFICATION.md`](MOVEOUT_STAGE_2_VERIFICATION.md). No deployment has been performed.

## Source and runner

- Contract: `contracts/moveout_protocol_v1.py`
- Stage 1 baseline SHA-256: `164B885F576AB8CE097D091406D9A20521B9E87B341366B8B9FF952F8FCE800E`
- Stage 1.1 final SHA-256: `EC5287A8AEE928CB024B44C3E649F45ADD17B811D357918957CF4330663724D6`
- Pinned GenVM dependency: `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`
- Local CLI: `genlayer 0.39.1`, `genvm-lint 0.11.0`; GenVM dependency is pinned by the contract header.

## Single verification entry point

From the repository root in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify_stage1.ps1
```

The script checks the complete test suite, GenVM lint, SDK validation, Python syntax compilation, production-source nondeterminism/benchmark scans, and `git diff --check`. It needs local development tools, but no wallet, RPC, or StudioNet.

## Final results

| Check | Result |
|---|---|
| `gltest tests -q` | Historical Stage 1.1 result: PASS, 109 total (63 Stage 1 Direct Mode + 46 historical regression tests). Current combined Stage 1 + historical + Stage 2 run: PASS, 145 total; see Stage 2 verification record. |
| `gltest tests/test_moveout_protocol_v1.py -q` | PASS, 63 Stage 1 Direct Mode tests |
| `pytest tests --ignore=tests/test_moveout_protocol_v1.py -q` | PASS, 46 historical tests |
| `genvm-lint lint contracts/moveout_protocol_v1.py` | PASS, 3 checks |
| `genvm-lint check contracts/moveout_protocol_v1.py` | Historical Stage 1.1 result: PASS; 40 methods (23 views, 17 writes). Current contract method count: 64; see Stage 2 verification record. |
| `python -m compileall -q contracts tests` | PASS |
| Production source scan | PASS; no nondeterministic or benchmark-specific selectors |
| `git diff --check` | PASS |

The previously combined suite failed because Stage 0.7, 0.8, and 0.9 historical tests left a fake `genlayer` module in `sys.modules` after importing experimental contract classes. The Stage 1 Direct Mode loader then received that incomplete stub and raised `NameError: TreeMap`. Stage 1.1 scopes each legacy stub to the import using `try/finally` and restores the prior module state. The aggregate run now passes without changing the production loader or weakening Stage 1 tests. See [`MOVEOUT_STAGE_1_1_HARDENING.md`](MOVEOUT_STAGE_1_1_HARDENING.md) for reproduction and audit findings.

## Boundaries

- No StudioNet deployment, hosted transaction, consensus, receipt/finality, or authoritative reread was performed.
- No Stage 1 contract or canonical MoveOut contract was deployed.
- Evidence remains a source reference plus caller-provided SHA-256; remote bytes are not fetched or checked against the digest.
- No production visual adjudication or observation/finding writer exists.
- Direct Mode and static checks do not prove StudioNet execution or max-scale storage/gas behavior. Exact maxima of all child collections and the 1024-event history cap were not exercised because that would require thousands of state writes; the implementation checks limits before appending.
- History is append-only and never evicts; event-producing writes fail closed once a Property reaches 1024 events. Idempotency storage is persistent and has no global pruning mechanism.
- General real-world property visual accuracy remains unverified, separate from this deterministic foundation.
