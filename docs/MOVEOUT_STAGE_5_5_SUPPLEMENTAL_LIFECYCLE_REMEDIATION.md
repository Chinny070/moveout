# MoveOut Stage 5.5 — Supplemental Request Lifecycle Remediation

**Stage status: PASS locally; remote synchronization pending.** The confirmed closure bypass is fixed and covered by local regressions. The full offline verification gate passed. No deployment, hosted transaction, migration, or Stage 5.6/5.7 work occurred.

## Scope and baseline

- Baseline verified before edits: `fe676754546a009ee8ce0e107cf5c2a2957236bb` on `main`.
- Only the supplemental request lifecycle implementation and its regression tests changed, plus this report.
- The requested Stage 5.5 scope permits a normal fast-forward push only after all checks pass. A sandboxed read of `origin/main` could not reach GitHub (HTTPS port 443 unavailable), so no commit or push has yet been attempted.

## Original vulnerability and reproduction

The Stage 5.4 test reproduced this sequence: create request, create linked supplemental inspection and evidence, freeze the evidence, close the request, assess the already-frozen evidence, then create another inspection and submit a new photograph. The assessment itself was valid and append-only, but changed the reported lifecycle state to `ASSESSMENT_APPENDED`; the later creation/submission checks looked only at the latest event and therefore allowed capture to resume.

The root cause was event-order-dependent state derivation in `_supplemental_request_view`, plus last-event-only closure guards in `create_supplemental_inspection`, `close_supplemental_request`, and `_submit_evidence_internal` (`contracts/moveout_protocol_v1.py`). An audit event was incorrectly treated as undoing closure.

## Remediation

- Added `_supplemental_request_is_closed`, which deterministically scans the bounded append-only event ID list for a `CLOSED` event.
- Request views now report `CLOSED` whenever closure exists, regardless of later assessment/audit events. Those later events remain visible in the event history.
- New supplemental inspection creation and new evidence submission reject a request with `MO_ERR_STATE:supplemental_request_closed`, even if post-closure assessments have since been appended.
- A close retry with the same idempotency key and identical payload returns the prior outcome. A new close request after closure is rejected.
- Assessment of already-frozen supplemental evidence remains possible under the existing verification, authorization, and continuity rules. It appends observations and does not modify frozen evidence or inspection records.
- No reopening API or implicit reopening path was added.

## Regression coverage and safety review

The Stage 5.4 exploit reproducer is now a multi-step Stage 5.5 regression. It verifies two post-closure assessments (including contradictory output retained as `CONFLICTED`), stable `CLOSED` status, rejected new inspection creation, rejected late evidence submission to an inspection created before closure, idempotent close replay, rejection of a new close key, and byte-for-byte unchanged original and supplemental frozen records. Additional tests cover malformed post-close model output causing no appended event/assessment, unauthorized closure rejection, and cross-request evidence binding failures leaving the closed request history unchanged.

The suite retains the existing Stage 5.3 legacy-inspection, evidence custody, authorization, provenance, visibility, and continuity tests. Together the existing suite and new regression cases continue to enforce no frozen evidence mutation, no silent conflict resolution, no unsupported target continuity, and no liability/deposit determination. The existing majority-aware consensus/equivalence policy is untouched; local mocks do not prove hosted validator behavior or real-world visual accuracy.

### Requested audit paths

| Path | Result |
|---|---|
| Multiple and conflicting assessments | Append-only; conflict remains `CONFLICTED`; request stays `CLOSED`. |
| Repeated closure | Exact idempotent replay returns safely; a new close key fails after closure. |
| Duplicate event ordering/status reads | Closure is terminal for derived lifecycle status; assessment events remain in history. |
| Late inspection/evidence creation | Rejected after closure, including use of an inspection created before closure. |
| Malformed assessment | Reverts without adding assessment IDs or request events. |
| Cross-request evidence | Existing binding validation rejects it; the request remains unchanged. |
| Authorization | Request must be a tenancy participant and the requester must be the closer. |
| Existing supplemental membership and frozen records | Existing records remain unchanged; no new evidence membership is added after closure. |
| Legacy inspection behavior | Existing Stage 5.3 legacy compatibility tests pass. |

## Validation results

Focused new Stage 5.5 tests: **3 passed**.

Full `scripts/verify_moveout.ps1`: **380 passed, 0 failed, 0 skipped**. GenVM lint passed (3 checks); SDK validation passed (84 methods: 49 views, 35 writes); Python syntax compilation passed; Stage 4–5.3 scope scan passed; benchmark production-logic scan passed; secret scan passed; `git diff --check` and staged whitespace check passed. The runner used localnet Direct Mode; it did not contact StudioNet.

## Backward compatibility and limitations

Existing request records already store append-only event IDs. The fix derives terminal status from that event history and introduces no storage migration or changes to frozen record formats. The event scan is bounded by the existing request-event limit. Legacy inspection records remain readable as confirmed by regression tests.

Local Direct Mode verifies contract logic with mocked retrieval/model responses only. It does not prove StudioNet committee execution, majority consensus, finality, visual interpretation quality, or the availability of public image sources. Further visual evaluation and hosted runtime verification remain deferred to their separately authorized stages.

## Changed files

- `contracts/moveout_protocol_v1.py`
- `tests/test_moveout_stage53_supplemental.py`
- `docs/MOVEOUT_STAGE_5_5_SUPPLEMENTAL_LIFECYCLE_REMEDIATION.md`

No deployment or hosted transactions were performed. **Ready for Stage 5.6: NO** (await explicit authorization).
