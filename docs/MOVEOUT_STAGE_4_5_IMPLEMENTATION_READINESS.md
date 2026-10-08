# MoveOut Stage 4.5 — Implementation Readiness Verification

**Stage status: PARTIAL.** The existing record/lifecycle architecture can accommodate nominations additively, but no target-nomination API or storage exists today. More importantly, the Stage 4.4 requirement that *any* safety-critical validator disagreement must prevent acceptance is not guaranteed by GenLayer's documented majority-consensus behavior. Implementation must wait for that requirement/consensus policy to be resolved. No source implementation, deployment, or hosted transaction was performed.

## Baseline and checked state

- Requested baseline `d298a76f0cfc1c66a4ad7bb22fe42d280b02867c` was local `main` HEAD; worktree was clean before this report.
- A read-only remote query confirmed `origin/main` at the same baseline.
- Contract pin: `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6` (from `contracts/moveout_protocol_v1.py` dependency header).
- Installed GenLayer CLI reports `0.39.1`.
- The exact Stage 4.2/4.3/4.4 decisions were reviewed. Stage 4.4's proposed schema is still documentation only.

## 1. Target-nomination compatibility — PASS (additive implementation feasible)

### Current storage and API facts

`MoveOutProtocolV1` stores JSON-serialized records in separate `TreeMap[str, str]` maps. It currently has maps for inspections, Area/Items, evidence, capture slots, visual observations, plus secondary indexes; it has no target map, target sequence, target membership index, or public target nomination/get/list API (`contracts/moveout_protocol_v1.py`, class storage declarations near lines 9–60 and sequence declarations near lines 63–77).

Area/Item records already have stable `area_item_id` and room/property/unit parents. Evidence records bind `inspection_id`, `room_id`, `area_item_id`, `source_ref`, and `expected_sha256`, and become immutable `FROZEN` records through `freeze_evidence` (around lines 1503–1664). Visual observations retain evidence IDs, verification IDs, and source digests (`_record_observation`, around lines 1781–1819). This is a useful provenance base, but none of these fields identify a nominated subregion within an Area/Item.

`create_capture_slot` accepts a slot type/label/instructions and prior slot/evidence references (around lines 1349–1395). `_validate_continuity` requires a prior frozen inspection/evidence and checks tenancy/property/unit/room/Area IDs and chronology (around lines 792–833). The read API explicitly labels slot continuity as `INTENDED_CORRESPONDENCE_NOT_SAME_AREA_PROOF` (around line 2341). A slot can guide overview/close-up capture, but cannot bind a particular target or prove the two views show it.

`submit_evidence` can associate a photo with a capture slot, but that slot contains no `target_id`, nomination version, target region, or role-specific target binding. Evidence digests are required and exact; validators re-fetch and verify them in `_observe_single`/`_observe_pair` and `_prepare_visual_evidence` (around lines 489–564). Hash binding identifies exact bytes; it does not locate a target inside the image.

### Storage/API conclusion

The minimal source-level implementation should be additive:

1. Add a target nomination record map, sequence, and bounded indexes by inspection and Area/Item. Each record should bind existing parent IDs, immutable target version/description, optional user-authored normalized reference box, reference Evidence ID, and reference digest.
2. Add create/get/list APIs. Require participant authorization, open-inspection state, parent membership, bounded text/coordinates, and exact frozen reference-evidence/digest binding when a box is supplied. A nomination without adequate location stays `NOT_LOCATABLE`/`UNCERTAIN`; it does not gain a vision-created locator.
3. Add target membership to the inspection's frozen contents snapshot for new inspections. Read legacy JSON with absent target membership as empty; do not rewrite old records or infer targets for them.
4. Add versioned target-aware observation record(s) and APIs, leaving current single/pair schema and records readable as V1. Bind each candidate/result to the target nomination version/digest and ordered evidence/provenance references.
5. Expose bounded target get/list/read methods and preserve the current append-only observation / separate Established Condition boundary.

The normalized box is metadata on one exact reference image, not an image transform and not proof of target identity in another image. Validation should reject out-of-bounds/reversed/zero-area coordinates deterministically; no minimum target size is selected without evidence.

### Freeze and compatibility constraints

Target nomination must be committed before the relevant inspection is frozen. `freeze_inspection` freezes exact room/area/evidence/capture-slot membership and disallows later child additions (around lines 1666–1695); `freeze_evidence` itself requires an open inspection. Therefore an overview and any preplanned close-up must be submitted/frozen before freezing that inspection. The current contract cannot add a late close-up to a frozen inspection.

For a later supplemental close-up, existing capture slots can point forward from a new inspection to an older frozen slot/evidence, with the same tenancy/property/unit/room/Area binding. A separate target-aware record must preserve the original target nomination/version and link the new evidence; same slot/Area IDs alone remain insufficient. Alternatively, a new inspection can re-submit the exact old bytes as a new Evidence record, but that is duplicate provenance work and should not be the default. The implementation plan should prefer a supplemental-inspection link if the target lifecycle permits it; otherwise it must specify a safe migration/re-reference flow before release.

This is source-level backward compatibility, not proof that a deployed contract's storage layout can be upgraded in place. There is no canonical MoveOut deployment. Existing frozen records must remain untouched; an already deployed immutable instance would require an explicit new-version/migration plan. Test legacy records that omit target fields, empty target indexes, and frozen inspections for unchanged reads and no target-level negative result.

Existing APIs alone cannot support the feature without additions. Feasibility is **PASS** because the current parent IDs, JSON record pattern, indexes, capture slots, digest binding, verification records, and append-only observation store provide compatible primitives; target nomination, snapshot membership, and target-aware equivalence are not yet implemented.

## 2. Runtime consensus behavior — BLOCKED for the Stage 4.4 unanimity requirement

### Current MoveOut code path

For single evidence, `observe_evidence` calls `gl.vm.run_nondet_unsafe(leader_fn, validator_fn)` and only then calls `_record_observation` with the returned result (around lines 1822–1855). The validator checks that the leader returned a `gl.vm.Return`, independently calls `_observe_single` (which GETs the URL, rechecks content/digest and runs vision), then returns `_observation_equivalent(...)`. Pairwise flow follows the same ordering and independently re-fetches both sources (around lines 1859–1910). Contract storage writes occur after the nondeterministic call returns.

For same-schema `INCONCLUSIVE` outputs, `_observation_equivalent` currently requires full dictionary equality because it returns `leader == validator` unless both candidates are schema-valid `OBSERVATION` results (around lines 430–478). `_observe_single` converts a vision exception or malformed schema into explicit inconclusive data; a matching inconclusive candidate can therefore be returned and recorded with status `INCONCLUSIVE` by `_record_observation`. A validator callback exception/false return is a disagreement; external web GET failures occur outside the vision exception handler and can throw. The validator returns false on a non-`Return` leader result.

### What local tests establish—and do not

`tests/test_moveout_stage4_observations.py` tests boolean custom-validator behavior. For example, its critical-field mismatch test swaps mocked leader/validator LLM output and asserts `run_validator() is False`; pairwise mismatch and digest tests do likewise. It also verifies that matching schema-invalid/model-uncertain outputs can be stored as `INCONCLUSIVE`.

The installed Direct Mode `gltest` implementation (`.../gltest/direct/vm.py`, `run_validator` around lines 340–386) explicitly captures a prior validator callback and manually replays it against the stored leader result; it returns only the callback boolean. The contract's leader write has already executed in Direct Mode. These tests do **not** simulate Studio's majority quorum, leader rotation, final transaction status, transaction rollback, or absence of an accepted on-chain observation after a rejected evaluation. A passing mock test must not be presented as network-level no-fallback proof.

### Official runtime behavior and hosted history

Current official GenLayer Equivalence Principle documentation says validators independently verify the leader proposal; the leader result is accepted when a majority agrees. If the majority rejects, leadership rotates and retries; if consensus still cannot be reached, the transaction is undetermined and does not modify contract state. It documents that `run_nondet_unsafe` unhandled validator exceptions count as `Disagree` (see [Equivalence Principle](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle), especially “Leader/Validator Pattern” and `run_nondet` vs. `run_nondet_unsafe`). Official [Non-determinism documentation](https://docs.genlayer.com/developers/intelligent-contracts/features/non-determinism) says storage writes occur only after the nondeterministic call returns. Official [Error Handling](https://docs.genlayer.com/developers/intelligent-contracts/features/error-handling) covers validator errors and retries.

The MoveOut Stage 4.1 StudioNet report records finalized `MAJORITY_DISAGREE` attempts with no observation record, and records an accepted `MAJORITY_AGREE` attempt with a receipt even though the vote list contained both `AGREE` and `DISAGREE` (`docs/MOVEOUT_STAGE_4_1_CONSENSUS_DIAGNOSTICS.md`). Stage 4.2 likewise recorded a hosted majority-agree transaction with some `DISAGREE` votes; transaction receipts did not expose the dissenting fields (`docs/MOVEOUT_STAGE_4_2_VERIFICATION.md`). These are actual network observations, but they do not disclose whether a disagreement concerned a particular safety-critical field.

### Critical consensus blocker

The current runtime's ordinary acceptance condition is **majority**, not unanimity. Exact comparison inside each validator callback ensures that a validator returns false when its own independent safety-critical output differs from the leader. It does not ensure that *any* such false vote prevents state acceptance: a majority can still accept the leader candidate while one or more validators disagree. Hosted Stage 4.2 receipts confirm majority-agree transactions can have dissenting votes, while not exposing what those validators disagreed about.

Therefore the current architecture cannot yet certify Stage 4.4's absolute rule “any validator disagreement means unresolved/no accepted target observation.” No contract code can infer hidden validator candidates from a boolean callback after the network has accepted a majority. A unanimous-equivalence/quorum policy or a reviewed reinterpretation of the decision is required; do not weaken the decision implicitly. Verify whether the target runtime/network supports a contract-selectable unanimity policy before feature implementation. If not, the Stage 4.4 acceptance rule must be explicitly revised by the product owner or MoveOut must not store a target-aware result under majority consensus.

Runtime outcome summary:

| Situation | Documented/observed behavior | Evidence boundary |
|---|---|---|
| Majority validators agree | The returned leader result can be stored after `run_nondet_unsafe` returns. | Official docs; multiple hosted majority-agree transactions and authoritative reads. |
| Majority rejects | New leader/retry; if still no consensus, transaction is undetermined and state is unchanged. | Official docs; Stage 4.1 hosted majority-disagree/no observation record. Current targeted flow still needs a test that rereads contract state after final undetermined status. |
| One or more validators disagree but a majority agrees | Leader result can still be accepted. | Official majority rule; hosted majority-agree receipts contain both agree and disagree votes, but dissenting fields are unavailable. This conflicts with a strict unanimity requirement. |
| Same malformed/inconclusive candidate | Full output equality can make validators accept a bounded `INCONCLUSIVE` result, which can be recorded; it is not an `OBSERVED` visual result. | Current source and direct tests. No new hosted malformed-output test in this stage. |
| Different malformed result, missing leader return, validator exception, or differing failure | Callback returns false or exception counts as disagree; network retries/rotates, ultimately undetermined if quorum is not achieved. | Current source plus official docs; exact failure/finality representation is runtime/version-specific and not tested on StudioNet here. |
| No quorum / unresolved validator votes | No accepted result should be stored; UI must surface final attempt as unresolved. | Official docs state undetermined/no state; target-feature StudioNet reread test remains required. |

**Runtime consensus verification: BLOCKED** for the approved strict “any validator dissent blocks acceptance” behavior. The existing majority mechanism's baseline operation is documented and historically observed; strict unanimity and stable UI handling of undetermined attempts are not established.

## 3. Implementation plan (not executed)

### Exact repository files expected

1. `contracts/moveout_protocol_v1.py` — additive versioned target nomination storage/APIs, freeze membership, evidence/target binding validation, V2 target-aware observation, independent retrieval, exact safety-critical equivalence, explicit inconclusive handling. Keep old getters/records readable and don't alter V1 prompt/schema in place.
2. `tests/test_moveout_stage4_5_target_visibility.py` (new) — nomination, geometry, scope/auth, evidence/digest linkage, lifecycle, legacy compatibility, target observability invariants, pair continuity, equivalence, disagreement/error handling, and no promotion.
3. `tests/test_moveout_stage4_observations.py` — only if factoring shared observation validation/equivalence requires updating regression expectations; preserve the Stage 4.2 regression tests.
4. `tests/test_moveout_protocol_v1.py` — only for cross-version lifecycle/freeze/legacy record compatibility assertions.
5. `scripts/verify_moveout.ps1` — include a new test file only if its invocation is not already pytest discovery; preserve lint/SDK/scope/benchmark gates.

There is no frontend or application UI in the current tracked project file list. Capture interaction/client mapping is a separate future integration and must not be assumed implemented by contract APIs.

### Ordered implementation sequence after blocker resolution

1. Resolve the quorum policy conflict in writing. Confirm whether unanimous validation is supported; if it is not, obtain explicit review of a revised product rule before coding. No implicit downgrade to majority is acceptable.
2. Validate GenVM storage and calldata limits for additive target nominations/normalized boxes and legacy inspection snapshots. Decide a versioned sidecar/migration boundary without mutating frozen records.
3. Implement target nomination as an authorized append-only child scoped to a specific inspection/area and digest-bound reference evidence; validate target IDs/versions and bounded coordinate geometry deterministically.
4. Enforce capture/evidence lifecycle: same-inspection overview/close-up collected before inspection freeze, or a new supplemental inspection referencing prior frozen evidence and same target nomination. Do not treat existing continuity-slot intent as proof.
5. Implement the V2 target observation fields and deterministic gates: no confident absence unless target is located, visible enough, in frame, unobstructed, and clear; malformed/unknown/conflicting states stay inconclusive. Keep visual observations separate from Established Conditions.
6. Independently GET and digest-verify every image on each active validator path. Compare exact evidence IDs/order, expected and retrieved digests, verification IDs, target ID/version/reference digest, per-image visibility/obstruction/frame/clarity/location/feature fields, continuity and aggregate status. No leader fallback.
7. Add local deterministic tests described below and run all existing verification gates. Then use a separate, explicitly authorized integration stage to exercise real multi-validator disagreement, finality, and authoritative state rereads; do not use local mocks as a substitute.
8. Separately perform blinded visual-model evaluation against independently reviewed target regions and held-out images. Do not claim visual-model accuracy from deterministic tests or consensus.

### Required deterministic test coverage

- Legacy Inspection/Evidence JSON with no target fields remains readable and unchanged; target absence cannot produce a target-specific `ABSENT` result.
- Authorization/parent scope: wrong property, tenancy, inspection, room, Area/Item, nomination version, or evidence is rejected.
- Nomination bounds: missing both text and reference region, malformed/oversized text, out-of-range/reversed/zero-area box, wrong reference digest, non-frozen reference, duplicate/idempotent request handling.
- Lifecycle: nominations and planned capture slots are created before freeze; membership is snapshotted; no child joins frozen inspection; supplemental inspection references previous frozen target/evidence without rewriting it.
- Evidence identity: changed image bytes, source URL, digest, verification ID, evidence order, target reference digest/version all fail equivalence.
- Target rules: no location, uncertain location, obstruction, frame cropping, inadequate clarity, partial surface with hidden target, unrelated furniture, visible positive local mark, and no confident absence without every required predicate.
- Continuity: matching IDs without visual support are insufficient; mismatched target IDs/versions and misleading close-up are rejected; `SUPPORTED`/`NOT_SUPPORTED`/`UNCERTAIN` remain distinct; conflicting pair remains unresolved.
- Exact equivalence: mutate each safety-critical identity/visibility/obstruction/frame/clarity/feature/continuity field independently and require false; cosmetic/explanatory fields must never override identity/safety mismatches.
- Outcomes: matching invalid outputs may record only explicit INCONCLUSIVE; leader non-return, validator exception, non-quorum and unresolved result cannot store leader proposal. Direct Mode covers callback logic only; real rollback/finality requires Studio integration and authoritative reread.
- No new observation API writes to Established Conditions, liability, or deposit state.

### Separate visual-model evaluation

Human-reviewed blinded evaluation is still required for target localization and coverage on MOV-SYN-08 obstruction, MOV-SYN-04 visible crack, MOV-SYN-02 clean wall/unrelated furniture, a dedicated crop case, MOV-SYN-14 shadow, MOV-SYN-11 lookalikes, misleading close-ups, and MOV-SYN-13 image text. Add rights-cleared varied real-property captures. Measure false `ABSENT`, missed obstruction, false obstruction, wrong-target match, continuity error, and abstention. These are not proven by schema tests.

## 4. Remaining risks and blockers

1. **Hard blocker — quorum vs unanimity:** Stage 4.4's any-dissent rule is stronger than GenLayer majority consensus. Need runtime/config feasibility or explicit product decision before targeted implementation.
2. **Freeze workflow:** on-chain observation requires a frozen inspection, so model-triggered close-up requests cannot be inserted into that same frozen inspection. Same-inspection captures must be gathered before freeze, or a supplemental inspection/reference lifecycle must be implemented.
3. **Storage/API compatibility:** additive sidecars are plausible, but GenVM storage/calldata bounds and deployed-instance migration behavior must be validated; no target CRUD API exists today.
4. **Receipt visibility:** Studio receipts show votes/leader output but have not exposed each validator's private visual fields or fetched digest. An accepted majority can hide dissent details.
5. **Vision limits:** exact schema/equivalence cannot prove the model found the correct pixels; correlated false negatives remain possible. Blinded visual evaluation is separate.
6. **No client application:** tracked repository has contracts/tests/docs only. Capture UX and client handling of undetermined transactions are not present here.

## 5. Existing local checks

Command: `powershell -ExecutionPolicy Bypass -File scripts/verify_moveout.ps1`.

Result: **225 tests passed**; GenVM lint passed (3 checks); SDK validation passed (70 methods, 42 view / 28 write); Python compilation passed; Stage 4 nondeterministic scope scan passed; benchmark-specific production logic scan passed; whitespace check passed.

These are local checks of the existing baseline only. No implementation-specific tests were added, no hosted transaction was run, and no new visual-model accuracy is established. The verification script reports clearing `artifacts/`; no tracked source/report was removed.

## 6. Final readiness

- Target-nomination compatibility: **PASS** as an additive, backward-readable source design; current APIs do not yet provide nominations.
- Runtime consensus verification: **BLOCKED** for the absolute any-validator-disagreement requirement because the runtime accepts majority agreement and does not expose all candidate fields to the contract.
- Required next action: resolve quorum/unanimity policy and same-inspection/supplemental capture lifecycle before implementation authorization.
- Targeted implementation readiness: **NO** until the consensus blocker is resolved.
- Stage 5 readiness: **NO**.
- Production files changed: **NONE**.
- Hosted activity/deployment: **NONE**.

## References

- [GenLayer Equivalence Principle](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle) — independent validators, majority acceptance, leader retry/undetermined behavior, `run_nondet_unsafe` exception semantics.
- [GenLayer Non-determinism](https://docs.genlayer.com/developers/intelligent-contracts/features/non-determinism) — independent execution and storage writes after consensus.
- [GenLayer Error Handling](https://docs.genlayer.com/developers/intelligent-contracts/features/error-handling) — validator errors and retry classification.
- [GenLayer Studio Development Tips](https://docs.genlayer.com/developers/intelligent-contracts/tools/genlayer-studio/development-tips) — transaction status, consensus vote, and leader equivalence output visibility.
- [Stage 4.1 hosted consensus diagnostics](MOVEOUT_STAGE_4_1_CONSENSUS_DIAGNOSTICS.md).
- [Stage 4.2 hosted verification](MOVEOUT_STAGE_4_2_VERIFICATION.md).
- [Stage 4.4 target visibility decisions](MOVEOUT_STAGE_4_4_TARGET_VISIBILITY_DECISIONS.md).
