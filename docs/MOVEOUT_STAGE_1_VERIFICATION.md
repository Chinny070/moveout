# MoveOut Stage 1 verification record

**Status:** Local deterministic foundation verified; not deployed.
**Network:** No network deployment or transaction was performed.
**Canonical MoveOut contract:** Not deployed.

## Source and runner

- Contract: `contracts/moveout_protocol_v1.py`
- SHA-256: `164B885F576AB8CE097D091406D9A20521B9E87B341366B8B9FF952F8FCE800E`
- Pinned GenVM dependency: `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`
- Local CLI versions: `genlayer 0.39.1`, `genvm-lint 0.11.0`; `gltest` uses the pinned dependency in the contract header.

## Checks performed

| Check | Result |
|---|---|
| `genvm-lint lint contracts/moveout_protocol_v1.py` | PASS, 3 checks |
| `genvm-lint check contracts/moveout_protocol_v1.py` | PASS; 40 methods (23 views, 17 writes) |
| `gltest tests/test_moveout_protocol_v1.py -q` | PASS, 52 Direct Mode tests |
| `pytest tests --ignore=tests/test_moveout_protocol_v1.py -q` | PASS, 46 existing tests |
| `python -m py_compile contracts/moveout_protocol_v1.py tests/test_moveout_protocol_v1.py` | PASS |
| `git diff --check` | PASS |
| Contract scan for nondeterministic calls and benchmark-specific selectors | No matches |

A combined `gltest tests -q` collection was also attempted and is not a passing gate: legacy tests install a synthetic `genlayer` stub in `sys.modules`, which contaminates collection of the pinned Direct Mode SDK tests. The two suites pass when run in separate processes as above. This is a test isolation limitation, not evidence of StudioNet compatibility.

## Scope and adversarial coverage

The 52 Stage 1 Direct Mode tests cover hierarchy and parent binding; property manager creation, authorization, revocation and limits; tenancy activation, occupancy, move-out request/confirmation and replay; inspection type/state/creator/cancellation/freeze rules; room and area identity; participant Condition Records; Evidence digest shape, duplicate detection, submitter-only freeze, append-only supersession and inspection snapshot; cross-property/unit/tenancy/area rejection; closed tenancy restrictions; idempotency; bounded pagination; protocol timestamps and append-only history; and absence of a public Visual Observation or Established Condition writer.

The Stage 1 suite includes the specified adversarial scenarios, extended with replay, cross-scope, index, and record-separation cases. Test success verifies deterministic behavior in local Direct Mode only.

## Important boundaries

- No StudioNet deployment, hosted transaction, validator consensus, receipt/finality, or authoritative reread was performed.
- No GenLayer vision execution or visual accuracy was tested in Stage 1. Stage 0 experimental results remain separate and do not become production adjudication.
- Evidence is a source reference plus caller-supplied SHA-256 digest. The contract does not retrieve evidence or verify a digest against remote bytes.
- The Visual Observation and Established Condition stores have no public writer. No participant can self-assert a validator observation or protocol finding.
- Manager role is an in-protocol authority designation, not verified legal ownership.
- History and child collections have explicit caps; writes fail closed at the cap. Deployment-scale gas/storage behavior remains unmeasured.
- The aggregate test command has the isolation issue described above; it must be repaired before relying on a single aggregate suite invocation.

## Deployment and next stage

No contract address or transaction ID exists for this Stage 1 source. It is an un-deployed local foundation only. Stage 2 has not started. Before a later visual adjudication stage, implement and verify the trusted observation/finding writer, evidence retrieval and digest binding, consensus/finality references, and its promotion rules; Stage 0.9 did not establish general property-visual accuracy.
