# MoveOut Stage 5.3 — Supplemental Evidence and Target Continuity

**Status: locally implemented; no hosted verification.** This stage adds a linked supplemental request and a separately frozen supplemental inspection/evidence path. It does not change any original frozen inspection, target nomination, evidence record, or Stage 5.2 observation. No deployment, hosted transaction, or migration was performed. Stage 5.4 remains unauthorized and not started.

## Scope and baseline

- Starting commit: `d2c2796ddedd0769024401fcc0885e6be8439419`; local `main` was clean at that SHA.
- Stage 4.7 majority-aware consensus remains authoritative: validator callbacks compare independently derived candidates; GenLayer protocol majority determines acceptance. Exact equivalence is not unanimity, and MoveOut cannot inspect hidden peer candidates.
- The operation uses the existing `MoveOutProtocolV1` record, authorization, freeze, provenance, and `run_nondet_unsafe` paths.
- No liability, causation, repair responsibility, Established Condition, or deposit-deduction result is produced.

## Supplemental-request schema and APIs

`SUPPLEMENTAL_REQUEST_SCHEMA_VERSION = 1`. Contract-generated `SUPREQ-N` records are immutable and bind:

- original frozen inspection, property, unit, tenancy, room, and area;
- latest frozen target ID/version and canonical nomination digest;
- original frozen PHOTO evidence ID, expected/retrieved SHA-256, and verification ID;
- an existing insufficient `TARGET_AWARE_SINGLE_V2` observation ID;
- one bounded reason from the Stage 5.2 insufficiency vocabulary;
- requester, tenant/manager side, idempotency request key, and timestamp.

`supplemental_request_digest` is SHA-256 over canonical JSON of a fixed immutable-field allowlist. Request lifecycle changes are separate append-only `SREQEV-N` events, not edits to the request. The read view exposes the current event-derived lifecycle plus linked inspection, evidence, assessment, and event IDs.

Public APIs added:

- `create_supplemental_request(original_inspection_id, target_id, target_nomination_digest, original_evidence_id, original_evidence_digest, unresolved_observation_id, reason, request_id)`
- `get_supplemental_request(supplemental_request_id)`
- `list_supplemental_requests(original_inspection_id, offset, limit)`
- `close_supplemental_request(supplemental_request_id, reason, request_id)` — requester-only closure.

Creation validates parent freeze/snapshot membership, current nomination version/digest, original evidence/photo/digest/provenance, and the referenced insufficient target observation. The caller cannot supply a missing ID or substitute a different target/evidence digest. Idempotent exact retries return the original request; changed input under the same key is rejected.

## Separate inspection and evidence lifecycle

The additive `SUPPLEMENTAL` inspection type cannot be created through generic `create_inspection`; only `create_supplemental_inspection(supplemental_request_id, request_id)` may create one. It binds the request and original inspection, and starts with the requested existing room/area membership. The original inspection is not given a back-pointer or new child membership. Inspection freeze snapshots the supplemental request ID only for this new record; legacy snapshot validation remains conditional and unchanged for older records.

`submit_supplemental_evidence(supplemental_request_id, supplemental_inspection_id, source_ref, expected_sha256, capture_slot_id, participant_obstruction, participant_light, participant_note_ref, request_id)` delegates to the existing evidence constructor/freeze/provenance lifecycle after checking the separate inspection/request/area binding. Generic evidence submission is rejected for `SUPPLEMENTAL` inspections so it cannot bypass the request link. Every photo receives a distinct evidence ID and its own caller-asserted expected digest, freeze time, and verification record. A sidecar evidence link binds it to request, supplemental inspection, original inspection, target nomination digest, and expected digest. The digest is explicitly labeled caller-asserted until the ordinary provenance verifier records a matching retrieval. Exact replay is idempotent; another key cannot submit the same digest to the request. Frozen original evidence and membership are never reopened.

Request lifecycle indexes and assessment history are bounded. Supplemental requests, inspections, evidence, request events, and assessments are capped at 64 per parent inspection, 8 inspections/request, 32 evidence/request, and 32 assessments/request (128 request events). Read APIs are bounded/paginated where applicable.

## Continuity assessment and validator path

`CONTINUITY_SCHEMA_VERSION = 1` returns a structured `TARGET_CONTINUITY_V1` record with:

- exact request, original inspection, supplemental inspection, target/version/nomination-digest, area, and both evidence IDs;
- both expected/retrieved digests, provenance verification IDs, and source-reference hashes;
- `target_continuity`: `SUPPORTED | NOT_SUPPORTED | UNCERTAIN`;
- `continuity_basis`: `OVERLAPPING_LANDMARKS | TARGET_APPEARANCE_AND_CONTEXT | CONTRADICTORY_CUES | INSUFFICIENT_CUES | UNCERTAIN`;
- the Stage 4.4 seven-field target observation schema for the supplemental image;
- derived `ASSESSABLE | INSUFFICIENT | CONFLICTED`, deterministic reason codes, and IDs of conflicting earlier continuity assessments.

Public APIs: `assess_supplemental_continuity(supplemental_request_id, supplemental_evidence_id, request_id)`, `get_continuity_assessment(id)`, and `list_continuity_assessments(request_id, offset, limit)`.

The leader and each validator callback independently retrieve the original and supplemental URLs, classify HTTP status/content type/body under the existing bounded PNG/JPEG rules, and require each fetched SHA-256 to match its frozen verified digest. Each execution sends the ordered pair `[original_bytes, supplemental_bytes]` to one `gl.nondet.exec_prompt(..., images=bodies, response_format="json")`. The prompt treats nomination metadata and image text as untrusted data. It requires distinctive visual landmarks/context for `SUPPORTED`, separates continuity from supplemental-image visibility, and requires uncertain feature presence unless continuity is supported. The contract also applies the deterministic feature-absence gates.

`gl.vm.run_nondet_unsafe` invokes an independent validating callback which repeats both retrievals and the vision assessment. Exact per-callback equivalence includes request/inspection/target identities and versions, nomination digest, both evidence identities, digests, verification IDs, source hashes, schema version, continuity status/basis, all seven safety observation fields, derived status/reasons, and conflicting-observation references. A callback mismatch votes disagreement under GenLayer’s majority-aware protocol. If protocol consensus is unresolved, the contract does not get to append an assessment; it has no leader-result fallback. Acceptance does not prove unanimity or physical truth.

## Conservative outcomes and compatibility

- `NOT_SUPPORTED` or `UNCERTAIN` continuity forces effective `feature_presence=UNCERTAIN`; no absence is established from an unlinked close-up.
- Unlocated, obstructed, cropped, unclear, uncertain, and malformed observations cannot support an absence result.
- Repeated evaluations of the same frozen pair that disagree are appended as `CONFLICTED`, with uncertain continuity and feature status; the earlier result remains available.
- Different supplemental photos under one request are also checked against earlier assessments. Opposing `PRESENT`/`ABSENT` observations for pairs each classified as continuity `SUPPORTED` produce `CONFLICTED` and an effective `feature_presence=UNCERTAIN`; contradictory continuity classifications also remain unresolved. Earlier assessment records are never removed.
- Failed retrieval, digest mismatch, or malformed model output fails with `MO_ERR_INCONCLUSIVE` and writes no continuity assessment.
- Target continuity is an observation only. No “best image wins” aggregate or Established Condition promotion is introduced.
- Legacy inspection/evidence/V1 and Stage 5.2 target-aware records are not rewritten. No historical migration is required at the source/storage-schema level; an existing deployed instance was not upgraded.

An important limit remains: each supplemental pair is assessed and indexed independently, and the contract does not aggregate separate photos into one final defect verdict. It marks directly contradictory supported feature observations as `CONFLICTED`; it does not infer damage changes, cause, or liability. Clients must present the append-only observations and unresolved/conflicted state without selecting a preferred image. Broader cross-photo product aggregation and adversarial/model-accuracy evaluation belong to separately authorized Stage 5.4.

## Files changed

- `contracts/moveout_protocol_v1.py` — append-only request/event/link/continuity stores, linked supplemental inspection/evidence writes, independent two-image continuity path and equivalence, and conditional supplemental snapshot validation.
- `tests/test_moveout_stage53_supplemental.py` — Direct Mode lifecycle, authorization, binding, schema, uncertainty, conflict, equivalence, immutability, and failure tests.
- `scripts/check_stage4_scope.py` — exact allowlist additions for the two-image retrieval/prompt and custom nondeterministic callback.
- `docs/MOVEOUT_STAGE_5_3_SUPPLEMENTAL_EVIDENCE_IMPLEMENTATION.md` — this report.

The Direct Mode tests use mocked responses/interpretations only. They verify deterministic bindings, error paths, structured-output validation, and one locally replayed callback. They do not prove actual visual continuity accuracy, validator independence on StudioNet, protocol quorum, finality, or authoritative hosted reads.

## Validation and known limitations

The Stage 5.3 test file completed with **58 passed**. The full repository suite completed with **376 passed, 0 failed**. GenVM lint, SDK validation, Python syntax, nondeterministic-scope scan, benchmark/security scan, and whitespace checks all passed. The SDK reported 84 methods (49 view, 35 write).

No StudioNet transaction was submitted. Hosted compatibility, independent live retrieval by the committee, quorum/finality, transaction receipts, and authoritative rereads are unverified. No visual-model accuracy rate is claimed. URL/digest equality binds retrieved bytes to the submitter-asserted hash; it does not establish camera capture, time, location, or target authenticity. Majority acceptance may conceal minority disagreement under the approved Stage 4.7 policy.

Stage 5.4 remains not started. This report does not authorize deployment, migration, hosted transactions, or later-stage work.
