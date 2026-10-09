# MoveOut Stage 4.7 — Final Safety Policy Lock

**Status: policy locked for a separately authorized implementation.** The project owner approved majority-aware consensus and the linked supplemental-inspection/request architecture. This document formalizes those decisions and sets Stage 5 boundaries. It does not change contracts, schemas, prompts, APIs, or records. No deployment, migration, hosted transaction, or Stage 5 implementation occurred.

## 1. Baseline and source documents

The verified starting commit is `7dc7f00869315243ce81a0c42008c5796667e673`. The four completed reports were read in full:

- [Stage 4.3 — Target-Region Visibility Design](MOVEOUT_STAGE_4_3_TARGET_VISIBILITY_DESIGN.md)
- [Stage 4.4 — Target-Region Design Review and Decision Lock](MOVEOUT_STAGE_4_4_TARGET_VISIBILITY_DECISIONS.md)
- [Stage 4.5 — Implementation Readiness Verification](MOVEOUT_STAGE_4_5_IMPLEMENTATION_READINESS.md)
- [Stage 4.6 — Consensus Safety and Supplemental Evidence Resolution](MOVEOUT_STAGE_4_6_CONSENSUS_AND_SUPPLEMENTAL_EVIDENCE.md)

The Stage 4.4 hard “any validator dissent means no accepted result” language is superseded only to the extent stated below. Other Stage 4.4 safety invariants remain in force. Stage 4.3/4.4 target-region enums and nomination details remain the approved design basis; no production implementation is implied.

## 2. Locked majority-aware consensus policy

### 2.1 Policy text replacing the no-dissent rule

> **Consensus and interpretation policy.** For each target-aware visual evaluation, the leader retrieves and interprets the bound frozen evidence. Each validator independently retrieves and verifies the same ordered evidence resources and independently interprets the target. A validator returns agreement only when the leader result and its independently derived result match exactly on the configured safety-critical evidence identities, digests, target nomination/version, target location and visibility, foreground obstruction, frame/crop coverage, clarity, feature observation, continuity, and aggregate unresolved/observable status. GenLayer’s protocol majority determines whether the transaction is accepted. Exact equivalence is the per-validator comparison rule; it is not unanimity. A minority validator may disagree while the protocol accepts a majority-supported leader result. MoveOut contract code cannot inspect or claim knowledge of hidden peer candidate values or individual visual reasons for disagreement. An accepted result is a majority-consensus model observation under the configured comparison rules; it is not proof that the image or interpretation is physically accurate. Application-visible insufficient evidence, uncertain target mapping, digest/provenance failure, or contradictory evidence must remain explicitly unresolved and must never be converted to a confident defect absence. If the protocol does not reach its required majority, the transaction is unresolved/undetermined and the client must not fall back to or display the leader proposal as accepted; it must inspect the final transaction outcome and reread authoritative contract state. No observation establishes liability, causation, maintenance responsibility, or deposit deduction.

### 2.2 Terms that must not be conflated

| Concept | Locked meaning | What it does not mean |
|---|---|---|
| **GenLayer majority consensus** | The protocol accepts or rejects a leader proposal using the network’s configured committee/quorum rule. | Every validator agreed, or the accepted image interpretation is physically true. |
| **Exact equivalence** | Each validating callback checks equality of configured safety-critical fields between the leader candidate and that callback’s independent result. | The contract sees all votes or can turn one dissent into a veto. |
| **Minority validator disagreement** | One or more validators may reject the candidate while the majority accepts it. Peer observations and reasons are not available to the MoveOut contract from the documented callback. | An application-detected contradiction in the evidence set. |
| **Application-detected evidence conflict** | A comparison in the returned candidate, input binding, or aggregate evaluation identifies conflicting images, identities, digests, visibility, or continuity. Preserve the conflict and return unresolved; do not select a preferred image. | Hidden committee dissent that the contract cannot inspect. |
| **Insufficient target coverage/clarity** | The nominated region cannot safely support the requested observation; keep the feature result uncertain/insufficient and block confident absence. | A failed validator vote, or evidence that the feature is absent. |
| **Accepted consensus result** | The protocol accepted the proposal and the resulting state transition is authoritative under chain rules. | Unanimous agreement, photographic authenticity beyond the bound digest, legal finding, or reliable real-world truth. |

### 2.3 Exactness and limits

The application will compare exactly, per validator, the following safety-critical information: contract/property/tenancy/inspection/area bindings; target ID/version and nomination digest; ordered evidence IDs, source digests, and provenance-verification IDs; per-image target-location, surface/target visibility, obstruction, frame coverage/cropping, clarity, and feature-presence fields; target-continuity status/basis; and aggregate status. Explanatory prose may not override a mismatch. Schema-invalid or internally contradictory candidates fail closed into explicit unresolved/insufficient behavior or disagreement, never a confident negative.

This comparison requires each validator to independently retrieve and evaluate the resources; validation of leader JSON shape alone is insufficient. Current public GenLayer references describe majority-based agreement, not a MoveOut-selectable unanimity threshold. MoveOut must not say “all validators agreed” based on a successful transaction, matching leader output, a local test, or a majority receipt. Only direct evidence that exposes every participant’s matching result could support such a claim, and current MoveOut/runtime documentation does not establish such evidence.

## 3. Locked evidence safety invariants

The following preserve Stage 4.3/4.4 decisions and incorporate the approved majority semantics:

1. **No confident absence without adequate target evidence.** `feature_presence=ABSENT` is permitted only when the nominated target is located, target visibility and clarity are adequate, the target is in frame, and no foreground object obstructs the requested region. An overall visible wall or visible pixels outside the nominated patch are not enough.
2. **Keep obstruction and crop separate.** Foreground obstruction describes a foreground object hiding the target. Frame coverage describes the target being partly or fully outside the image. Do not substitute one for the other.
3. **Represent missing location as uncertainty.** If the target cannot be mapped to the nominated region, use `NOT_LOCATABLE`/`UNCERTAIN`; do not infer defect absence or invent another target.
4. **Do not invent physical identity or continuity.** Target IDs, descriptions, boxes, room metadata, capture slots, and user assertions express nominations or intended linkage. They do not alone prove that two photos show the same physical feature or place. Continuity needs visual support; otherwise it is `UNCERTAIN` or `NOT_SUPPORTED`.
5. **Do not silently resolve contradictions.** Preserve each image-level result and evidence reference. Conflicting observations, target mappings, digests, or continuity remain unresolved. No “best image wins,” confidence averaging, or overwriting a prior observation.
6. **No consequential conclusions.** Visual observations do not establish liability, causation, new damage, worsening, repair responsibility, normal wear, or deposit deductions. No automatic monetary conclusion.
7. **Frozen evidence is immutable.** Never replace bytes, source, digest, or frozen record. A new photograph receives a new evidence ID, independent freeze/provenance record, and digest.
8. **No leader fallback on unresolved consensus.** If GenLayer reaches no required majority, no leader proposal may be surfaced or stored as accepted. The client maps final unresolved/undetermined status to an unresolved UI state and rereads authoritative state. If the protocol accepts a majority, the accepted leader candidate is treated only as a majority-consensus observation under the exact callback rules—not as unanimous truth.
9. **No unsupported unanimity claim.** A successful transaction or an exact per-callback comparator does not prove unanimity. Never claim that all validators agreed without independent complete evidence.
10. **Do not hide uncertainty.** Missing or malformed fields, ambiguous nomination, inadequate clarity, failed retrieval/provenance, or unresolved contradictions yield an explicit insufficient/unresolved result or a rejected/undetermined transaction. They never default to `ABSENT`.

## 4. Locked supplemental capture architecture

### 4.1 Request and parent linkage

When a frozen inspection’s observation is insufficient, create a separate append-only supplemental request. It binds:

- a unique supplement request ID and idempotency/request key;
- the original frozen inspection ID and its property, unit, tenancy, room, and area IDs;
- the original target ID, target version, and nomination digest;
- the original frozen evidence ID(s), exact digest(s), and prior unresolved observation ID;
- the specific unresolved predicate (visibility, obstruction, crop, clarity, location, continuity, or conflict), creator/authority, creation time, and bounded status.

The request is not a mutation of the original inspection and does not itself prove anything about new evidence. Parent authorization and all scope IDs must be checked deterministically.

### 4.2 New inspection and evidence records

Capture supplemental images in a new inspection or explicitly versioned supplemental inspection/revision linked backward to the original frozen inspection. Link it to the existing target nomination version by reference; a corrected target requires a new immutable target version and cannot silently inherit a previous negative observation. Preserve every original record unchanged.

Each supplemental photograph is a distinct Evidence record with a new evidence ID, source reference, expected digest, capture metadata, immutable frozen bytes, freeze time, and separate provenance verification result. Validators independently retrieve the bound bytes and validate the digest. A retry is idempotent. A changed image, URL, digest, or target version is a new record/request or is rejected; never overwrite the original.

An append-only supplement relation/bundle indexes the request and includes original and supplemental inspection IDs, target/version/nomination digest, ordered original and supplemental evidence IDs/digests, and intended purpose. Store the relation on the new request/supplement side. Do not add a late pointer or child to the frozen parent inspection.

### 4.3 Continuity, conflicts, and rejection

Target continuity is independently evaluated using target appearance and distinctive visual context/overlap. Shared IDs, same room/area, user statements, common wall color, or capture-slot metadata are not enough. Store tri-state `SUPPORTED`, `NOT_SUPPORTED`, or `UNCERTAIN` and a bounded basis. A supplemental view clears only the relevant current visibility blocker when continuity is supported and the new image independently meets target location, target visibility, in-frame, unobstructed, and clarity requirements.

Reject or retain unresolved any supplement with wrong parent/target/version, missing freeze/provenance, digest mismatch, stale or ambiguous nomination, unsupported continuity, unrelated lookalike surface, conflicting overview/close-up output, malformed result, or insufficient target view. Preserve rejected/conflicting evidence as separate immutable records when authorization/lifecycle permits; never let an unrelated or rejected close-up establish absence. Append a new observation referencing all relevant old/new evidence; retain prior unresolved observations and reasons.

### 4.4 Legacy compatibility and API/storage requirements

- Legacy frozen inspection/evidence JSON without target or supplement fields remains readable and unchanged. Missing target data means no target-specific confident absence.
- Add versioned sidecar records/maps and bounded indexes for target nominations, supplement requests, relations, and target-aware observations; do not make new fields mandatory in legacy records.
- Required operations include create/read/list target nomination; create/read/list supplement request; create/read supplemental inspection relation; evidence create/freeze/provenance verification through existing lifecycle; append target-aware observation; and bounded read APIs for relation/history. Each write needs participant/scope authorization, parent validation, idempotency, size limits, and event/index updates.
- Snapshot any relevant target membership before the original inspection is frozen. Supplemental membership belongs only to the new inspection/request relation. Enforce status transitions and request closure deterministically; do not remove or rewrite submissions.
- Check GenVM storage, serialization, calldata, per-index, and return-size limits before choosing exact bounds. Preserve existing V1 getters and observations. No deployed canonical MoveOut instance or in-place migration is authorized or assumed; any future deployed-version migration needs separate approval and a concrete compatibility plan.

## 5. Stage 5 plan and acceptance gates

Each substage is a separate authorization boundary. Passing one stage does not authorize the next. Every stage ends with a report and hard stop for review.

### Stage 5.1 — Target nomination and versioned storage

**Scope:** implement only append-only target nomination/version records, target IDs, inspection/room/area bindings, optional user-drawn normalized reference box bound to exact evidence ID/digest, indexes/read APIs, authorization, and inspection snapshot compatibility. No visual prompt/assessment or supplemental request implementation.

**Acceptance criteria:**

- Existing legacy JSON and V1 reads remain unchanged; missing nominations cannot produce target-specific absence.
- Nomination is authorized and bound to correct open inspection/area and, for image boxes, a frozen reference image/digest. Corrected nominations create a new version; no model-generated target IDs/coordinates.
- Reject missing locators, malformed/oversized descriptions, out-of-range/reversed/zero-area boxes, wrong parent, wrong digest, non-frozen image, unauthorized actor, and post-freeze original-inspection mutation.
- Storage/index/serialization and response bounds are measured against documented runtime limits; bounded paging and idempotency are tested.
- All existing tests plus new deterministic Stage 5.1 tests, GenVM lint, SDK validation, syntax, scope, benchmark scan, and whitespace gates pass.

**Hard stop:** no visual observation schema/prompt change, supplemental capture implementation, deployment, or Stage 5.2 until reviewed and explicitly authorized.

### Stage 5.2 — Target-region visibility assessment and safety-critical equivalence

**Scope:** add a versioned per-image observation schema and pure deterministic invariants for target location, surface/target visibility, obstruction, frame/crop, clarity, bounded feature presence, and aggregate insufficient/unresolved status. Integrate independent validator-side retrieval and interpretation for frozen nominated evidence; compare exact configured safety fields per callback under majority-aware policy. Preserve existing V1 observation API/records.

**Acceptance criteria:**

- No confident `ABSENT` unless all Stage 4.4 visibility/location/clarity predicates pass; incompatible enum combinations and malformed outputs fail closed.
- Obstruction and crop remain separate; missing target location is uncertain; no model-created target identity; no direct promotion to established condition/liability/deposit.
- Leader and every validating callback independently retrieve and digest-check evidence and independently evaluate; exact equality covers evidence identity/order/digests/verification, target nomination/version/digest, each safety-critical visibility/continuity/feature field, and aggregate state.
- A callback mismatch returns disagreement; documentation/UI says protocol majority, not unanimity. No claim that all peers agreed; the contract does not fabricate hidden dissent data.
- Local deterministic mismatch, uncertainty, malformed output, and fail-closed tests pass. Blinded human-reviewed visual evaluation is reported separately and cannot be inferred from unit tests.
- Existing full local verification gates pass.

**Hard stop:** no supplemental-inspection APIs, hosted deployment/transaction, production expansion, or Stage 5.3 until review and explicit authorization.

### Stage 5.3 — Supplemental evidence and target-continuity verification

**Scope:** implement append-only supplemental requests, new supplemental inspection linkage, independent new evidence records/digests/provenance, relationship indexes, tri-state target continuity, conflict/rejection outcomes, and append-only new observations. Original frozen records remain immutable.

**Acceptance criteria:**

- Request is bound to original frozen inspection/target/version/evidence/digests and the unresolved reason; authorization, scope, status, and idempotency are enforced.
- Supplemental inspection points backward; each new photo has separate ID, digest, freeze and provenance verification; original record bytes/membership remain unchanged.
- Same target requires independently supported visual continuity. IDs/claims alone fail. Unrelated/misleading close-ups, stale versions, wrong parent, duplicate/mutated content, and unresolved/conflicting pair remain rejected or unresolved and cannot establish absence.
- Every attempt and observation is append-only and queryable; prior unresolved status remains available; no “best image wins.” Legacy reads work.
- Deterministic adversarial/lifecycle tests, all existing verification gates, and review of storage limits pass.

**Hard stop:** no StudioNet transaction, deployment, or Stage 5.4 until separately authorized.

### Stage 5.4 — Adversarial testing and runtime verification

**Scope:** adversarial local schema/equivalence/lifecycle tests, blinded visual-model evaluation on independently labeled/rights-cleared images, then—only under separate explicit authorization—StudioNet integration of majority success, validator dissent, failure/undetermined behavior, finality, and authoritative rereads. This stage does not authorize canonical deployment.

**Acceptance criteria:**

- Deterministic suite covers chair occlusion, unobstructed target, clean target, unrelated furniture, crop, shadow/clarity, uncertain target, lookalikes, conflicting views, prompt injection, wrong target, misleading close-up, changed digest, duplicate/retry, frozen-parent mutation, malformed/missing outputs, and validator mismatch.
- Reports distinguish local deterministic checks, visual-model measured outcomes, and hosted protocol evidence. Model metrics include denominators and false-absence/obstruction/continuity errors; no expected label is injected into runtime prompts.
- Any hosted no-majority result is finality-checked and followed by authoritative reads showing no observation was committed; a majority-accepted dissent case is labeled majority-accepted, never unanimous.
- A successful majority transaction confirms only protocol acceptance and the stored bounded observation. It does not prove image correctness, unanimity, legal truth, or real-world accuracy.
- All applicable local checks pass; unresolved safety failure blocks the affected feature and is documented.

**Hard stop:** Stage 5.4 ends with a review report. No canonical MoveOut deployment, money/liability logic, or next stage without new explicit authorization.

## 6. Limitations and remaining blockers

- The owner-approved majority policy resolves Stage 4.5's product-policy conflict. The protocol may still accept a leader candidate despite minority validator dissent; MoveOut cannot inspect hidden peer outputs.
- Independent models/providers may have correlated errors; even unanimous hypothetical agreement would not establish real-world truth.
- Semantic adequacy and same-target continuity remain visual-model judgments. Deterministic gates can reject inconsistent answers, not prove the model located the right pixels.
- Supplemental request, relation, status, target storage, and target-aware APIs do not exist yet. Frozen inspection lifecycle and deployed-version migration require implementation validation.
- No frontend/client capture experience is represented by these contract documents. Client transaction-state behavior, finality handling, and authoritative rereads must be implemented/tested in the relevant later stage.
- Current design has no empirically justified numerical image-coverage or confidence threshold. Do not invent one during implementation; use explicit bounded uncertainty unless separately validated and approved.

## 7. Preserved requirements and stage status

This policy preserves Stage 1 property/tenancy authorization and hierarchy; Stage 2 inspection/evidence lifecycle; Stage 3 source/provenance validation and exact frozen digests; target-specific uncertainty and no invented identities; append-only observations; exact per-validator safety-field comparisons; no leader fallback when the protocol itself is unresolved; and separation of observations from Established Conditions and all liability/deposit decisions.

- Stage 4.7 policy: **LOCKED** per owner authorization above.
- Production changes: **NONE**.
- Hosted activity/deployment/migration: **NONE**.
- Stage 5 automatic progression: **NONE**.
- Ready for Stage 5.1: **YES, for explicit authorization only.**
- Stage 5.2, 5.3, 5.4: **NOT AUTHORIZED by this document**; each requires its own review/authorization boundary.

## References

- [GenLayer Equivalence Principle](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle) — per-validator equivalence callback, majority protocol acceptance, leader retry/undetermined behavior, and returned leader result.
- [GenLayer Non-determinism](https://docs.genlayer.com/developers/intelligent-contracts/features/non-determinism) — independent validator execution and post-consensus writes.
- [GenLayer Error Handling](https://docs.genlayer.com/developers/intelligent-contracts/features/error-handling) — disagreement and failure handling.
- [GenLayer Studio validator configuration](https://docs.genlayer.com/developers/intelligent-contracts/tools/genlayer-studio/validators) — configurable validator participants/providers/models; does not document a contract-level unanimity option.
