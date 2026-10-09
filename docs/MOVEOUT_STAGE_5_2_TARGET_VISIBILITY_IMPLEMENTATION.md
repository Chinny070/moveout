# MoveOut Stage 5.2 — Target-Region Visibility Assessment and Equivalence

**Status: locally implemented and validated.** This stage adds a versioned, single-image target-aware observation path. It does not establish visual-model accuracy or hosted GenLayer behavior. No deployment, migration, hosted transaction, or Stage 5.3 supplemental-capture implementation was performed.

## Baseline and scope

- Starting commit: `4ed9159f69e726aa50c822c43acf89696539e247`.
- Stage 4.7 majority-aware consensus policy is authoritative. An accepted result is a protocol-majority result, not proof of unanimity or real-world truth.
- The implementation uses the existing append-only `visual_observations` store and indexes. Existing V1 records and entry points are unchanged.
- Stage 5.2 evaluates one frozen image per call. If a target nomination is bound to a reference photo, only that exact evidence record may be assessed. Cross-image correspondence, supplemental inspections, and target continuity remain deferred to Stage 5.3.

## Production changes

### Versioned target observation

`observe_nominated_target(tenancy_id, target_id, evidence_id, request_id)` adds one `TARGET_AWARE_SINGLE_V2` record to the existing observation store. The V2 image-level `observations` object uses the exact Stage 4.4 fields and enum values:

| Field | Values |
|---|---|
| `surface_visibility` | `VISIBLE`, `PARTIAL`, `NOT_ESTABLISHED`, `UNCERTAIN` |
| `target_location` | `LOCATED`, `NOT_LOCATABLE`, `UNCERTAIN` |
| `target_visibility` | `ADEQUATE`, `INADEQUATE`, `UNCERTAIN` |
| `foreground_obstruction` | `PRESENT`, `ABSENT`, `UNCERTAIN` |
| `frame_coverage` | `IN_FRAME`, `PARTLY_OUTSIDE`, `OUTSIDE`, `UNCERTAIN` |
| `target_clarity` | `ADEQUATE`, `INADEQUATE`, `UNCERTAIN` |
| `feature_presence` | `PRESENT`, `ABSENT`, `UNCERTAIN` |

Every key is required, unknown keys are rejected, and there is no enum defaulting or repair. The record binds `observation_schema_version=2`, `target_nomination_schema_version`, target ID/version/nomination digest, inspection and area IDs, evidence ID, retrieved image digest, verification ID, and source-reference SHA-256. It is also indexed using the existing observation-by-inspection and observation-by-evidence indexes.

The contract derives `assessment_status` (`ASSESSABLE` or `INSUFFICIENT`) and ordered `insufficiency_reasons` from the approved enum fields; the model does not choose these summary values. Reason codes are bounded, deterministic values: `SURFACE_NOT_ESTABLISHED`, `SURFACE_VISIBILITY_UNCERTAIN`, `TARGET_NOT_LOCATABLE`, `TARGET_LOCATION_UNCERTAIN`, `TARGET_VISIBILITY_INADEQUATE`, `TARGET_VISIBILITY_UNCERTAIN`, `FOREGROUND_OBSTRUCTION_PRESENT`, `FOREGROUND_OBSTRUCTION_UNCERTAIN`, `TARGET_PARTLY_OUTSIDE_FRAME`, `TARGET_OUTSIDE_FRAME`, `FRAME_COVERAGE_UNCERTAIN`, `TARGET_CLARITY_INADEQUATE`, `TARGET_CLARITY_UNCERTAIN`, `FEATURE_PRESENCE_UNCERTAIN`, and `CONFLICTING_PRIOR_TARGET_OBSERVATION`.

A valid but insufficient candidate is appended with `status=INCONCLUSIVE`, retaining its bounded per-image enums and deterministic reason list. If another V2 observation for the same target nomination and same evidence ID already exists with different safety fields, the new record remains append-only and is also marked `INCONCLUSIVE`; it includes the prior conflicting observation IDs and `CONFLICTING_PRIOR_TARGET_OBSERVATION`. This checks repeated interpretations of the same frozen image only; it does not infer continuity across images. A malformed model response, retrieval error, or failed digest recheck is not stored as an observation; after the nondeterministic call, the write fails with an explicit error. No failure is turned into a negative observation.

### Evidence and nomination binding

Before vision execution, the contract requires:

- a valid stored nomination digest and supported nomination schema version;
- a latest target nomination included in the frozen inspection snapshot;
- non-empty description or a user-supplied region box;
- frozen PHOTO evidence included in the same inspection snapshot and matching inspection, property, unit, tenancy, room, and area parents;
- a latest verified provenance record for the evidence and a source URL matching its recorded source hash;
- if a reference evidence ID is present, exact equality between it and the assessed evidence ID, plus matching reference digest and verification ID.

The last restriction deliberately prevents Stage 5.2 from treating a different view as the same physical target. A reference region box is supplied as untrusted JSON nomination metadata to the model (normalized 0–10000 coordinates, origin at image top-left); it is not overlaid onto the image and is not pixel-level proof. If the model cannot map the nominated target, it must return uncertainty.

### AI and retrieval path

The leader and each validating callback independently:

1. call `gl.nondet.web.get(source)`;
2. inspect HTTP status, headers, and body using the existing evidence response classifier;
3. require the retrieved SHA-256 to match the frozen evidence digest;
4. call `gl.nondet.exec_prompt(prompt, images=[response.body], response_format="json")` with one image and the bounded target prompt;
5. parse the exact seven-field V2 result and run deterministic invariant checks.

The target identifier and description are serialized as untrusted data. The prompt treats image text and nomination text as data, forbids inferring liability/cause/age/deposit outcomes, distinguishes foreground obstruction from frame clipping, and requires `UNCERTAIN` when the target cannot be located or the negative-absence prerequisites are not met. Prompt instructions do not guarantee visual correctness.

### Deterministic safety rules

The contract rejects an internally contradictory candidate if:

- `surface_visibility=NOT_ESTABLISHED` but the target is `LOCATED`;
- `target_visibility=ADEQUATE` without a located target, absent obstruction, `IN_FRAME`, and adequate clarity;
- `feature_presence=ABSENT` unless target location, target visibility, obstruction, frame coverage, and clarity all satisfy the Stage 4.4 absence predicate;
- the target is not located but the feature is classified `PRESENT` or `ABSENT`;
- a positive feature is classified while target clarity is not adequate.

Obstruction and cropping remain independent fields. A valid `PRESENT` observation may describe a visible local feature even if other target pixels are not assessable; it does not imply anything about hidden areas. An unrelated object outside the nominated region does not mechanically force obstruction. These are consistency rules over supplied model output, not proof that the model correctly interpreted pixels.

### Validator equivalence and consensus

`observe_nominated_target` uses `gl.vm.run_nondet_unsafe`. A validator independently repeats retrieval, digest validation, and vision interpretation. `_target_observation_equivalent` requires exact equality of:

- failure/schema state and observation/nomination schema versions;
- target ID/version/nomination digest;
- property, unit, tenancy, inspection, and area IDs;
- evidence ID, retrieved digest, verification ID, and source-reference hash;
- all seven target observation fields;
- deterministically derived assessment status, insufficiency reasons, and conflicting-prior record IDs.

Missing/malformed safety fields cause `Disagree`; the leader result is not a local fallback for an unresolved protocol operation. Under Stage 4.7's approved GenLayer policy, majority can accept the leader proposal despite hidden minority dissent. The contract cannot inspect private peer observations, and exact equivalence does not establish unanimity. A successful transaction would prove protocol acceptance and stored data only, not visual truth.

## Compatibility and separation of concerns

- Existing V1 observation records are read unchanged. V1 single/pair observation APIs and prompts were not modified.
- The new record is append-only; a new call cannot overwrite evidence, nominations, or earlier observations.
- Legacy inspections without a target nomination remain readable but cannot use this target-aware writer.
- The V2 method writes only to `visual_observations`; no writer to Established Conditions was added. No result automatically establishes damage, liability, maintenance responsibility, or a deposit deduction.
- Existing authorization checks require a tenancy participant, frozen evidence, and matching hierarchy/snapshot membership. There is no unrestricted write path.

## Tests and verification

Added `tests/test_moveout_stage52_target_visibility.py` with **64 Direct Mode test cases** covering assessable and insufficient candidates; partial surface; obstruction; cropping; both together; unclear and unknown target location; unrelated furniture flags; absent-feature gates for coverage/clarity/location; malformed and missing schema fields; wrong target/evidence/digest/nomination bindings; unsupported nomination schema; frozen snapshot requirements; exact-equivalence mutation of identity, digest, versions, reasons, parent IDs, and each safety-critical field; matching uncertainty; conflicting repeated observations for the same image; authorization; malformed AI output without persistence; append-only V1 compatibility; frozen evidence immutability; and observation/finding separation.

Updated `scripts/check_stage4_scope.py` only to allow the new `_observe_target_single` GET/prompt calls and `observe_nominated_target` custom nondeterministic callback. The allowlist remains exact; unlisted nondeterministic APIs continue to fail the scan.

Final `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify_moveout.ps1` result:

- Direct/local suite: **318 passed, 0 failed** (254 baseline plus 64 Stage 5.2 cases).
- GenVM lint: **PASS** (3 checks).
- SDK validation: **PASS** (Contract `MoveOutProtocolV1`, 75 methods: 45 view, 30 write).
- Python syntax compilation: **PASS**.
- Nondeterministic scope scan: **PASS**.
- Benchmark-specific production logic scan: **PASS**.
- Secret scan: **PASS**.
- Diff whitespace checks: **PASS**. Git printed only its line-ending conversion warning for the two changed Python files.

These Direct Mode cases test deterministic behavior and a single locally replayed callback only. They do **not** prove StudioNet validator quorum, hidden-dissent behavior, finality, rollback, independent live retrieval by the hosted validator set, or visual-model accuracy.

## Limitations and deferred verification

- No blinded human-reviewed visual evaluation was run; no target-localization, obstruction, crop, clarity, or false-absence accuracy rate is claimed.
- No hosted runtime transaction was run in this stage. StudioNet compatibility, validator execution, consensus/finality, and authoritative reread remain unverified for this new method.
- Region boxes are prompt metadata rather than image overlays; coordinate grounding by the vision model is unverified.
- Target continuity across two distinct photographs is not implemented. A nomination with a reference photo is restricted to that exact photo; nomination-only text may still be ambiguous and must abstain. Stage 5.3 must add independently evaluated continuity before another image can resolve visibility.
- Majority consensus can accept a candidate despite hidden dissent. This is the owner-approved policy, not unanimity.
- Exact schema/equivalence agreement cannot prevent correlated semantic errors or prove authenticity, capture time/location, physical target identity, causation, or legal responsibility.

## Stage boundary

Stage 5.2 implements only target nomination use, single-image target visibility observations, deterministic safety validation, exact per-callback equivalence, tests, and this report. Supplemental requests, new supplemental inspections, cross-image target continuity, migration, deployment, hosted transactions, and Stage 5.3 remain out of scope. No canonical contract was deployed and no hosted transaction was submitted.
