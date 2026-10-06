# MoveOut Stage 1.1 — Foundation Hardening

**Status: complete; local verification only. No contract was deployed. Stage 2 has not started.**

## Baseline and isolation failure

The audit started on branch `main`, at Stage 1 commit `e19ef82a24c5e76c4df0addeeb834f4392c889da`, with a clean working tree. The Stage 1 source digest was reproduced as `164B885F576AB8CE097D091406D9A20521B9E87B341366B8B9FF952F8FCE800E`.

Final Stage 1.1 contract SHA-256: `EC5287A8AEE928CB024B44C3E649F45ADD17B811D357918957CF4330663724D6`.

The original combined `gltest tests -q` command was reproduced before edits. During pytest module collection, the historical Stage 0.7 and Stage 0.8 unit tests imported experimental contract classes by inserting a minimal fake `genlayer` module into the process-wide `sys.modules`. The Stage 1 Direct Mode fixture later asked GenLayer's loader to load `moveout_protocol_v1.py`; its `from genlayer import *` therefore received the fake module, which does not export `TreeMap`, and failed with `NameError: name 'TreeMap' is not defined` (reported as 52 setup errors). This was test-process state leakage, not an SDK compatibility failure.

The historical tests still use their lightweight stub to load the legacy pure-Python derivation code, but now install it only for that import and restore the previous `sys.modules['genlayer']` value in `finally`. This cleanup is applied to the Stage 0.7 derivation, Stage 0.7 equivalence, Stage 0.8 safety, and Stage 0.9 positive-signal tests. The production contract and Direct Mode SDK import are not monkeypatched. The complete suite now runs in one `gltest` process and passes.

## Hostile audit and contract changes

The audit reviewed every public write method and parent chain in `MoveOutProtocolV1` against the Stage 1 architecture. Property, Unit, Tenancy, Inspection, Room, Area/Item, Condition Record, and Evidence records use parent IDs loaded from contract storage; callers cannot supply replacement parent tuples. Inspection creation derives Property/Unit from the Tenancy. Condition/Evidence submission checks Property, Unit, Tenancy, Room, and Area against that inspection. Evidence-to-Condition binding requires the same Inspection and Area. Supersession rechecks the complete Property/Unit/Tenancy/Room/Area/type chain.

Two authority hardening changes were made in `contracts/moveout_protocol_v1.py`:

1. A manager cannot be authorized if that address is the tenant of a DRAFT, ACTIVE, or MOVE_OUT_PENDING tenancy for the Property. This prevents one account from holding both sides of the tenancy counter-signature while the tenancy is open.
2. Move-out confirmation now enforces the opposite side specifically: a tenant request must be confirmed by an active manager; a manager request must be confirmed by the designated tenant. A second manager cannot confirm another manager's request.

Both changes fail with stable `MO_ERR_STATE` / `MO_ERR_UNAUTHORIZED` prefixes and are covered by regression tests.

## Audit results

| Area | Finding |
|---|---|
| Property and manager authority | Manager mutations are creator-controlled; creator cannot be revoked. Reads are public chain data. Manager status is only an in-protocol role and makes no legal ownership assertion. An open tenant cannot be promoted to manager. |
| Parent binding | Cross-property, cross-unit, cross-tenancy, cross-inspection, wrong-area Condition/Evidence, and cross-tenancy supersession attacks are rejected. IDs are resolved from storage and ancestry is compared before writes. |
| Tenancy occupancy and lifecycle | Only tenant activates; only one tenancy occupies a Unit; move-out is a one-way pending transition and the counterparty rule is enforced by role and address. Closed tenancy cannot add Condition Records or Evidence. |
| Inspection rules and freeze | Type/state restrictions are checked. Only its creator freezes an OPEN Inspection, and every member Evidence must be frozen first. No record-creation path can add children after freeze. Retries return existing IDs without extending membership. |
| Evidence authority and immutability | Evidence has no edit method. Only its submitter can freeze it; inspection manager/tenant status does not override that rule. Freeze changes only status and protocol `frozen_at`; every other Evidence field is regression-tested unchanged. |
| Supersession and historical freeze | A same-submitter replacement must be frozen, un-superseded evidence from another inspection in the same tenancy and same area/type ancestry. It adds a separate link and events. It does not edit old Evidence or frozen inspection membership. Chain length is bounded by the 32 inspections per tenancy. |
| Condition Records and adjudication separation | Condition Records stay participant-authored and `PARTICIPANT_RECORDED`. The Visual Observation and Established Condition maps have no public write method. There is no writer that accepts user-supplied consensus/finality, and no claim or observation is auto-promoted. |
| Idempotency | Keys are scoped by sender, method, and request ID. Same caller/method/key plus same normalized payload returns the original ID. A different payload fails. Different methods or callers do not collide. Failed/reverted calls do not persist a key. Retries after freeze return the original created object without mutation. |
| Protocol time | Created/submitted/activated/requested/ended/frozen and event timestamps use `_now()`, which reads only `gl.message_raw['datetime']`. User start/end metadata and source references are stored separately. No user-controlled date field is used as a protocol timestamp. |
| Bounds and append-only data | Text, IDs, parent child indexes, manager lists, pages, and property history have explicit caps. Property history never evicts: at 1024 events, event-producing writes fail closed. This protects existing Passport history but stops further writes for that Property. Idempotency entries are persistent and have no global pruning policy; as with normal chain state, aggregate storage growth is not deployment-scale measured. |
| Determinism and source hygiene | Production Stage 1 contains no `gl.nondet`, `web.get`, `web.render`, `exec_prompt`, `run_nondet`, fixture selectors, expected benchmark labels, local filesystem references, credentials, or wallet material. The production source contains only the pinned SDK dependency in its header; it does not import local runner packages. |

Collection caps were checked at practical boundaries for manager count, labels, source-reference length, and page size; the full maximum of every child list and the 1024-event history cap were not generated in Direct Mode because that would require thousands of state writes. The source enforces those limits before appending. This is the remaining local boundary-test limitation.

## One verification entry point

Run from the repository root in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify_stage1.ps1
```

The script fails on any nonzero test, lint, SDK check, or compile result. It runs the complete suite (`gltest tests -q`) after scoped stub cleanup; runs both GenVM checks; compiles all contract and test Python files; scans the Stage 1 contract for nondeterministic and benchmark-specific selectors; and checks `git diff --check`. It needs the local GenLayer/GenVM development tools and Python, but no wallet, RPC, or StudioNet access.

## Final local verification

See [`MOVEOUT_STAGE_1_VERIFICATION.md`](MOVEOUT_STAGE_1_VERIFICATION.md) for exact source digest, versions, commands, test counts, and run results. Final verification passed 109 tests in one run, both GenVM checks, Python compilation, source scans, and diff whitespace checks. No StudioNet transaction, contract deployment, or Stage 2 implementation was performed.

## Remaining limitations

- Direct Mode and static checks do not establish StudioNet deployment compatibility or storage/gas behavior at maximum scale.
- Evidence still consists of a source reference and caller-provided digest; this contract does not fetch bytes or verify the digest against them.
- There is no production visual adjudication writer, validator consensus record, finding-promotion rule, challenge flow, or finality record.
- Stage 0.9 did not establish general real-world property visual accuracy. That result remains separate from this deterministic protocol hardening.

## Stage 2 readiness decision

**READY FOR STAGE 2: YES.** The test isolation failure is fixed and reproduced as passing in the one-command suite; deterministic lint, SDK validation, syntax, source scans, parent bindings, authority boundaries, freeze semantics, and observation/finding separation pass. The remaining limits above are explicit design or deployment-scale limits, not a known broken invariant in this deterministic foundation. This is only a readiness-gate result: Stage 2 has not started, no contract was deployed, and any Stage 2 scope that depends on production visual adjudication must address the still-unverified visual accuracy separately.
