# MoveOut Stage 4.4 — Target-Region Design Review and Decision Lock

**Status: design decisions locked for targeted implementation review; nothing implemented.** This report makes the target-region schema, continuity behavior, safety invariants, and test specification precise enough to implement after authorization. It does not change production contracts, schemas, prompts, fixtures, or hosted state. No deployment or hosted transaction occurred. Stage 5 remains out of scope.

## 1. Baseline and source review

Reviewed:

- [Stage 4.3 target visibility design](MOVEOUT_STAGE_4_3_TARGET_VISIBILITY_DESIGN.md)
- [Stage 4.2 failure analysis](MOVEOUT_STAGE_4_2_FAILURE_ANALYSIS.md)
- [Stage 4.2 verification](MOVEOUT_STAGE_4_2_VERIFICATION.md)
- [Stage 4.2 consensus repair](MOVEOUT_STAGE_4_2_CONSENSUS_REPAIR.md)
- [Visual verdict architecture](MOVEOUT_VISUAL_VERDICT_ARCHITECTURE.md)
- Current `MoveOutProtocolV1` record lifecycle and capture-slot continuity methods.

The stated baseline commit `5126a30552ab693a4f45bb97c8d6fb34ef914770` was HEAD and the worktree was clean before this report. Sandboxed `git ls-remote` could not reach GitHub; a read-only remote check succeeded with the authorized network context and returned the same `5126a30552ab693a4f45bb97c8d6fb34ef914770` for `origin/main`.

The Stage 4.2 SHA discrepancy is resolved: `228a69a2327bce36a2deed1f1a503bb9a0a3a303` was amended to `c7010c3233812d0903289e47c528316c7ad6e1cd`, which has the same parent and message. `c7010c3` is present in current history; `228a69a` is only the superseded pre-amend commit object. No history rewrite is needed.

The key failure remains: StudioNet finalized the Stage 4.2 leader output for MOV-SYN-08 with overall area visibility `VISIBLE`, no obstruction, and no crop, though the target crack region was covered by a chair. The current record schema accepts this combination. Current capture-slot continuity metadata explicitly means intended correspondence, not proof of same-area identity.

## 2. Locked observation schema

### 2.1 Target nomination record

Each target is an append-only, deterministic inspection child with:

| Field | Type / rule | Purpose |
|---|---|---|
| `target_id` | Contract-issued stable ID | Binds an observation to the nominated target; never supplied by the vision model. |
| `inspection_id`, `room_id`, `area_item_id` | Existing parent IDs | Reuses the current Stage 1/2 hierarchy and scope checks. |
| `reference_evidence_id`, `reference_digest` | Required when anchored to a photo | Binds the annotation to exact frozen bytes. |
| `target_description` | Bounded user-authored text; may be empty only if a marked region exists | Identifies an intended inspection patch or feature in plain language. It is a claim, not truth. |
| `region_box` | Optional four unsigned normalized coordinates on the reference image: `x_min`, `y_min`, `x_max`, `y_max`; each in `[0,10000]`, with minima strictly below maxima | User annotation, where 0 and 10000 are the image's left/top and right/bottom boundaries. Coordinates are fixed-point location metadata, not a coverage/confidence threshold. |
| `target_version` | Immutable version/sequence | A corrected nomination creates a new target version; it never mutates a frozen target. |

At least one of `target_description` or `region_box` is required. If only text is supplied and it does not locate one unambiguous surface patch, target location is `UNCERTAIN`; the model must not fill the gap by selecting a similar mark or surface. A box always points to the exact evidence digest where the user drew it. It is a claim about intended pixels and does not by itself prove the real-world target or continuity to another image.

The normalized box is selected over free text alone because it gives both app and validators an explicit reference-image region. It is selected over model-generated boxes because the system must not invent the target. It is not treated as image registration: no geometric transformation from overview pixels to close-up pixels is assumed. The human-entered description remains useful context and an independently verifiable correspondence cue.

### 2.2 Per-image observation enums

All fields are required. No missing/null values are allowed. If a judgment cannot be made, use the named `UNCERTAIN` or `NOT_LOCATABLE` state, not a default negative.

| Field | Exact values | Meaning |
|---|---|---|
| `surface_visibility` | `VISIBLE`, `PARTIAL`, `NOT_ESTABLISHED`, `UNCERTAIN` | `VISIBLE`: named overall Area/Item is identifiable and its relevant surface is substantially in frame; this says nothing by itself about the nominated target. `PARTIAL`: some surface is visible but a material part is obstructed/out of frame. `NOT_ESTABLISHED`: cannot identify the named surface in this image. `UNCERTAIN`: extent/identity cannot be judged. |
| `target_location` | `LOCATED`, `NOT_LOCATABLE`, `UNCERTAIN` | Whether this image contains a defensible mapping to the nominated target, using nomination and visible cues. |
| `target_visibility` | `ADEQUATE`, `INADEQUATE`, `UNCERTAIN` | Whether all of the nominated target needed for the requested feature question is visible with adequate evidence. Visible wall pixels elsewhere do not imply `ADEQUATE`. |
| `foreground_obstruction` | `PRESENT`, `ABSENT`, `UNCERTAIN` | Whether an object/obstacle hides any material part of the nominated target. Ignore furniture outside the target region. |
| `frame_coverage` | `IN_FRAME`, `PARTLY_OUTSIDE`, `OUTSIDE`, `UNCERTAIN` | Whether the nominated target lies within the image bounds. This represents cropping/framing, not object obstruction. |
| `target_clarity` | `ADEQUATE`, `INADEQUATE`, `UNCERTAIN` | Whether focus, resolution, exposure, blur, and other image qualities support the requested visual question at the target. |
| `feature_presence` | `PRESENT`, `ABSENT`, `UNCERTAIN` | Bounded answer about the specifically nominated feature/mark only; never overall property condition or responsibility. |

Uncertainty is explicit in each epistemic field; it is never encoded as `ABSENT`, `NO`, empty string, or omitted field. Schema-invalid model output normalizes only to an inconclusive all-uncertain result with `schema_valid=false`; it cannot be stored as an observation or treated as a negative.

### 2.3 Deterministic validity and absence rules

These invariants can be enforced without judging whether the pixels were interpreted correctly:

1. `feature_presence=ABSENT` is valid only if `target_location=LOCATED`, `target_visibility=ADEQUATE`, `foreground_obstruction=ABSENT`, `frame_coverage=IN_FRAME`, and `target_clarity=ADEQUATE`.
2. `target_location` other than `LOCATED` forbids both `PRESENT` and `ABSENT`; feature presence must be `UNCERTAIN`.
3. `foreground_obstruction=PRESENT`, `frame_coverage` other than `IN_FRAME`, or `target_clarity` other than `ADEQUATE` forbids `target_visibility=ADEQUATE` and forbids `feature_presence=ABSENT`.
4. `target_visibility=ADEQUATE` is valid only when the target is `LOCATED`, obstruction is `ABSENT`, frame coverage is `IN_FRAME`, and clarity is `ADEQUATE`.
5. `surface_visibility=NOT_ESTABLISHED` forbids `target_location=LOCATED` unless the future implementation explicitly supports an independently verified target locator despite the overall surface being unidentifiable; V1 does not support that exception.
6. `foreground_obstruction` and `frame_coverage` remain separate facts. One cannot be inferred from, substituted for, or silently normalized into the other.
7. `feature_presence=PRESENT` may be retained only as a local positive observation if the nominated target is located and the actual feature pixels are clear. It does not assert anything about hidden or unobserved portions.
8. An impossible combination, missing field, malformed value, or invalid nomination yields `UNRESOLVED`/`INCONCLUSIVE`; it must not be repaired by choosing a more favorable field.

No percentage, confidence cutoff, or minimum box size is introduced. There is no empirical basis in the current evidence for such thresholds. `ADEQUATE` is a semantic result that validators must independently reproduce; deterministic validation enforces its consistency with the other fields, but cannot prove visual adequacy.

An image is insufficient for a confident negative whenever any absence precondition above is not met. Preserve the source evidence and the reason for insufficiency; do not infer a clean target.

## 3. Target-region representation alternatives

| Alternative | Benefit | Safety weakness | Decision |
|---|---|---|---|
| Free-text target description only | Easy to collect and backward compatible | “That wall/crack” can be ambiguous across views; models may choose a lookalike. | Reject as sole locator unless validators can locate it unambiguously; otherwise explicit `UNCERTAIN`. |
| Model-generated bounding box | Could be convenient and support localization | Lets the model invent the subject it is then asked to inspect; output can become circular evidence. | Reject as nomination source. A model may report where it found visible evidence only as a separate observation, never redefine `target_id`. |
| User-drawn normalized region only | Deterministically anchored to one evidence digest and simple to validate | Region alone does not express intended feature and cannot be projected into a different perspective. | Do not use alone; it remains an optional reference-image anchor. |
| User nomination plus optional user-drawn reference-image box | Combines declared intent, stable ID, exact image/digest anchor, and visual correspondence cues without asserting automatic registration. | Still a user claim; target-to-close-up continuity remains semantic and may be unresolved. | **Select.** It is the smallest practical bounded representation consistent with no invented targets. |

### Compatibility with existing inspections

Do not add required fields to or rewrite frozen Inspection, Area/Item, or Evidence records. Add target nomination and target-aware observation records as versioned append-only children referencing existing IDs and digests. A legacy inspection without a target nomination remains valid; it cannot yield a target-specific `feature_presence=ABSENT` under this design. To nominate after inspection/evidence freeze, create a new authorized inspection revision or new inspection that references prior frozen evidence; never unfreeze or mutate the old record. Implementation must confirm the existing evidence lifecycle permits this sidecar pattern before code is written.

Overview and close-up remain distinct Evidence IDs with distinct URLs, digests, freeze times, and provenance verification IDs. `capture_slot_id`, `continuity_slot_id`, and `supplements_evidence_id` express intended workflow linkage, not same-location proof.

## 4. Overview-to-close-up continuity

Continuity is a separate per-pair semantic observation:

| Field | Exact values |
|---|---|
| `target_continuity` | `SUPPORTED`, `NOT_SUPPORTED`, `UNCERTAIN` |
| `continuity_basis` | `OVERLAPPING_LANDMARKS`, `TARGET_APPEARANCE_AND_CONTEXT`, `CONTRADICTORY_CUES`, `INSUFFICIENT_CUES`, `UNCERTAIN` |

The validator examines both frozen images and the immutable nomination/reference annotation. `SUPPORTED` requires visible support that the close-up covers the same nominated physical target, such as compatible overlapping distinctive landmarks and target-relative context. A shared inspection, area, target ID, capture slot, descriptive claim, same wall color, or user assertion is insufficient by itself. No numerical similarity threshold is asserted. `NOT_SUPPORTED` means available evidence contradicts correspondence; `UNCERTAIN` means it cannot be established.

Rules:

- Both records must be frozen, independently provenance-verified, and tied to the same inspection revision, area, target ID/version, and target nomination digest. Any disagreement in these deterministic bindings rejects the pair before semantic comparison.
- Each image receives its own visibility result. A close-up can resolve an earlier blocked target only if the close-up itself passes the target visibility/clarity rules and `target_continuity=SUPPORTED`.
- An unrelated close-up, unlocated close-up, different-looking target, or `NOT_SUPPORTED`/`UNCERTAIN` continuity cannot establish defect absence. The pair remains unresolved.
- Conflicting per-image or continuity outputs never select the most confident image and never overwrite a previous observation. Preserve each accepted image-level observation and append a new aggregate only when the linkage predicates pass.
- Active validators independently retrieve and evaluate both images. Exact mismatch in continuity or either image's safety-critical target fields means no accepted target-aware observation. No leader-proposal fallback.

If validators disagree, the nondeterministic attempt is rejected/inconclusive and cannot append the leader candidate as an accepted observation. The client must present the attempt as unresolved using its final transaction outcome. Any future durable on-chain `DISPUTED_ATTEMPT` record requires a separate deterministic, authorization-checked operation referencing that finalized attempt; it may record only that no agreed observation was accepted, never the leader's disputed vision fields. Whether the runtime exposes final validator disagreement in a stable machine-readable state is an implementation acceptance check, not assumed here.

## 5. Consensus and safety decisions

The following are locked requirements:

1. No confident defect absence without adequate target coverage and clarity: **required by deterministic invariant 1**.
2. No invented target locations: target IDs and annotations are user/protocol-created; model cannot rewrite nomination; missing location is unresolved.
3. No silent conflict resolution: preserve per-image outputs; pair/validator disagreement is unresolved and cannot select one output.
4. No leader proposal fallback: exact equivalence mismatch rejects/inconcludes the attempt; leader output is not stored as accepted evidence.
5. No liability/deposit conclusions: target-aware observations remain observations, separate from Established Conditions, legal responsibility, normal wear, and money.
6. Exact safety-critical equivalence: exact identity/digest/provenance/target bindings and all fields `surface_visibility`, `target_location`, `target_visibility`, `foreground_obstruction`, `frame_coverage`, `target_clarity`, `feature_presence`, `target_continuity`, and `continuity_basis`, per evidence item and in stable order.

Invalid schema, digest mismatch, invalid evidence binding, model/source failure, validator disagreement, or inactive validators do not count as a successful target observation. IDLE participants are not independent evaluations. Agreement still does not prove physical truth or eliminate correlated model error.

## 6. Deterministic test specification

These tests exercise pure validation and lifecycle logic using supplied candidates. Passing them proves only that code enforces the specified rules; no row is a vision-model success.

| ID | Deterministic input | Required result |
|---|---|---|
| D01 | `surface_visibility=PARTIAL`, target obstructed, upper wall visible | Candidate may be schema-valid as `INADEQUATE`; `feature_presence=ABSENT` rejected; unresolved. |
| D02 | Clear nominated crack pixels, remaining target partly hidden | `PRESENT` may be retained only as local observation; unseen remainder not inferred absent. |
| D03 | All absence prerequisites satisfied, clean target candidate | Schema permits `ABSENT`; this is not proof that image is clean. |
| D04 | Furniture present outside nominated region; target otherwise adequate | Does not force obstruction; valid only if candidate obstruction is `ABSENT` and other predicates pass. |
| D05 | Target fully outside frame | `frame_coverage=OUTSIDE`, target inadequate, absence rejected; cropping not labeled as foreground obstruction. |
| D06 | Target partly outside frame | `PARTLY_OUTSIDE`; absence rejected. |
| D07 | Chair over target but candidate says adequate/absent | Contradictory enum combination rejected. |
| D08 | Target nomination missing, empty description and no box | Reject nomination / target `NOT_LOCATABLE`; no target ID invented; no absence. |
| D09 | Bounding-box coordinates out of `[0,10000]`, reversed, or zero-area | Reject nomination deterministically. |
| D10 | Nomination reference evidence ID/digest does not match frozen record | Reject evidence binding; do not interpret target. |
| D11 | Close-up shares IDs but continuity is `UNCERTAIN` | Cannot clear prior obstruction; unresolved. |
| D12 | Close-up explicitly targets a different `target_id` or target version | Reject pair linkage; close-up cannot establish absence. |
| D13 | Misleading close-up shows similar surface but no continuity support | `NOT_SUPPORTED`/`UNCERTAIN`; no target-specific negative. |
| D14 | Overview and close-up have conflicting image-level visibility statuses | Preserve separate records; aggregate unresolved; no “best image wins.” |
| D15 | Leader and validator differ only on obstruction, frame coverage, target visibility, or target ID | Equivalence false; no accepted leader fallback. |
| D16 | Leader and validator match target fields but source digest differs | Equivalence false. |
| D17 | Malformed/missing enum or contradictory candidate | Inconclusive/rejected; never coerced to `ABSENT`. |
| D18 | Validator candidate is IDLE/missing | Not counted as independent support; apply configured consensus threshold; otherwise unresolved. |
| D19 | Two validators disagree; attempt rejected | Client-visible state unresolved; no disputed leader result becomes an accepted observation. |
| D20 | Prompt-injection strings in image text / structured field | Image pixels treated as untrusted data; schema exact; no command or condition promotion. |
| D21 | New target added after freeze | Existing frozen record unchanged; require a new authorized inspection revision/inspection. |
| D22 | Attempt to promote target observation directly to liability/deposit finding | No observation API or storage path can perform promotion. |

## 7. Visual-model evaluation (separate, not proven by D-tests)

Use existing benchmark images only as candidate sources for a separately reviewed blinded evaluation. Deterministic fixture labels must not enter contract prompts or production logic. Where current assets do not isolate one factor, create and independently review additional rights-cleared fixtures before making accuracy claims.

| Visual question | Candidate evidence | Must be independently judged |
|---|---|---|
| Does chair hide target crack while part of wall remains visible? | MOV-SYN-08 before/after | Target localization, foreground obstruction, and unresolved negative. |
| Is nominated crack actually in view? | MOV-SYN-04 after | Positive feature detection without overclaiming unseen surface. |
| Is a clean target fully inspectable? | MOV-SYN-02 before | Adequate target coverage and false-negative rate on held-out samples. |
| Does unrelated furniture remain outside a nominated target? | Select/curate a reviewed clean view | Furniture relevance, not mere furniture presence. |
| Is target cropped out vs obstructed? | MOV-SYN-09 is only a noncomparability proxy | Curate a pure out-of-frame target example and an object-occluded counterpart. |
| Does shadow obscure detail? | MOV-SYN-14 after | Separate shadow from obstruction/crop and assess target clarity. |
| Can a target be located among lookalikes? | MOV-SYN-11 pair | Location and same-target correspondence; do not assume Area ID proves identity. |
| Does a close-up depict the nominated target? | Create blinded overview/close-up pairs | Correctly identify overlap landmarks; reject misleading/unrelated close-ups. |
| Does disagreement remain unresolved? | Deliberately divergent validator candidates in an offline harness | Consensus logic, candidate preservation limits, and no leader fallback. |
| Does image text alter instructions? | MOV-SYN-13 after | Prompt-injection resistance under bounded schema. |

Measure model errors on held-out, independently labeled data, including false `ABSENT`, missed obstruction, false obstruction from unrelated furniture, continuity errors, and abstention quality. Report denominators and uncertainty. Deterministic D-tests cannot substitute for these measures.

## 8. Preserved architecture and implementation boundary

The next targeted implementation, if authorized, must preserve:

- Stage 1 deterministic Property/Unit/Tenancy authorization, hierarchy, IDs, and append-only history.
- Stage 2 inspection, Area/Item, Evidence, capture slots, lifecycle, and freeze rules.
- Stage 3 source validation, provenance checks, frozen bytes, and exact digest binding.
- Independent validator-side retrieval and interpretation of every referenced image.
- Append-only target nominations, image-level observations, and pair/aggregate observations.
- Strict separation of Visual Observation from Established Condition; no direct damage, liability, wear, responsibility, or deposit decision.
- Existing legacy inspections and evidence unchanged; absent target nomination cannot silently acquire target-level negatives.

Implementation acceptance criteria:

1. A reviewed schema/version and storage-size/API feasibility check for target nomination and normalized boxes; no mutation of prior frozen records.
2. Pure invariant/normalizer and exact-equivalence tests D01–D22 (or documented inapplicable cases) pass.
3. Failure/rejection runtime behavior is verified locally: disagreement never accepts leader calldata, and client state renders unresolved. A separate persisted attempt record is not required unless its safe lifecycle is designed and tested.
4. Existing 225-test suite, GenVM lint, SDK validation, scope, benchmark, syntax, and whitespace gates continue passing.
5. No production prompt or hosted behavior changes until the deterministic schema and test results are reviewed. Model evaluation is separately authorized and reported; it cannot be inferred from unit tests.

No numeric visual-confidence threshold is a blocker for these deterministic invariants: uncertainty remains explicit and no threshold is fabricated. Remaining implementation checks are storage/API fit for the nomination sidecar and the runtime's stable representation of disagreement/rejected attempts. They are bounded feasibility checks, not reasons to weaken the safety decisions.

## 9. Decision lock and status

- Schema choice: user/protocol-created target record, bound to existing inspection/area and optionally to a digest-bound user-drawn normalized reference-image box; vision model cannot nominate or move it.
- Observation choice: separate overall surface and target observability from foreground obstruction, frame coverage, clarity, and target location; all uncertainty explicit.
- Absence rule: all target coverage/location/clarity preconditions must be adequate; otherwise no confident absence.
- Continuity choice: distinct tri-state semantic finding requiring visual support; shared IDs/claims are not proof.
- Consensus choice: exact equality on evidence, target, visibility, obstruction, crop, clarity, feature, and continuity fields; any disagreement rejects the candidate and is presented unresolved, with no leader fallback.
- Compatibility: append-only versioned sidecars; never mutate frozen legacy inspections/evidence.
- No deployment, hosted transaction, production change, or Stage 5 work.
- Targeted implementation: **ready after this design report is reviewed/authorized**, subject to the feasibility checks above.
- Stage 5: **NO**.
