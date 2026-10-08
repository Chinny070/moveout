# MoveOut Stage 4.2 — Occlusion Failure Analysis

**Scope:** forensic analysis of the existing Stage 4.2 failure and Git recovery. No contract code, schema, visual prompt, fixture, or hosted state was changed by this analysis. No new hosted transaction was sent. Stage 5 remains stopped.

## Git recovery

- Worktree changes preserved: `contracts/moveout_protocol_v1.py`, `tests/test_moveout_stage4_observations.py`, `docs/MOVEOUT_STAGE_4_2_CONSENSUS_REPAIR.md`, and `docs/MOVEOUT_STAGE_4_2_VERIFICATION.md`, plus this analysis document.
- `git status` showed only those four existing Stage 4.2 paths before this report was added. No reset, clean, reclone, or overwrite was performed.
- No `.git/index.lock` file existed at inspection time, and no Git process was running. Therefore an abandoned lock or a live Git process was not the cause.
- `git add` had failed with `Permission denied` creating `.git/index.lock`. ACL inspection showed inherited explicit deny-write/delete entries for the sandbox identity on `.git` and `.git/index`; user/SYSTEM/admin entries have write access, but the current restricted execution identity is denied. This directly explains the failure. The repo lives under OneDrive, but there is no evidence that OneDrive itself caused this denial.
- Recovery completed after confirming there was no lock file or active Git process. An elevated Git helper required command-scoped `safe.directory=C:/Users/USERpc/OneDrive/Desktop/moveout` because the repository owner differed from the helper identity; no global Git configuration was changed. Only the contract, regression tests, and three Stage 4.2 reports were staged and reviewed. Commit `228a69a2327bce36a2deed1f1a503bb9a0a3a303` (`Stage 4.2: record hosted occlusion gate failure`) was pushed to `origin/main`; `git ls-remote` confirmed the same SHA and the worktree was clean. Do not remove an index lock unless a new check finds one and confirms all Git processes have stopped.
- The required local verification script clears the `artifacts/` directory before running. Its rerun removed ignored temporary Stage 4.2 runner/log/inspection files there. The tracked implementation and reports remained intact, and the hosted transaction is still available on-chain; this script behavior is recorded here because those temporary local copies were not preserved.

## Hosted case evidence

- Target: StudioNet chain `61999`, RPC `https://studio.genlayer.com/api`.
- Deployed disposable contract: `0xFD618F945fdb63DB3CA6D2c0F6Fb4E715c3AbeC1`.
- Observation transaction: `0xa46e7ffd60655f6e00ba33b9bbaa7c867de6e0df69a62744bf63e4f27ce9cdf2`.
- The transaction is now confirmed by a read-only StudioNet RPC query as `FINALIZED`, `MAJORITY_AGREE`, round 1. Validator votes were `IDLE, AGREE, AGREE, AGREE, IDLE`.
- Authoritative reread returned `OBS-4`, schema-valid `OBSERVED`, area `VISIBLE`, with `occlusion_present=NO`, `crop_limitation_present=NO`, `shadow_present=NO`, and all defect flags `NO`. Its source digest was `aad6a123750f03999d94dec5494484f43287a8314d92e62649bc7ab767290e88`, matching EVID-4's frozen digest. The observation has verification ID `EVER-4`.
- Source fixture is commit-pinned at asset commit `194be2d6c141c76bb9f737ffaaa1fee768c126af`. Manifest expectation: MOV-SYN-08 after image is `UNOBSERVABLE`; ground truth says a chair blocks the relevant wall area and the crack location cannot be assessed from B. The image is 83,947 bytes.
- Visual inspection of the frozen local before/after PNGs confirms the crack on the wall in A; in B, a recognizable upholstered chair occupies the lower/central-right foreground and covers a substantial section of that wall, while the upper wall remains visible. So the wall is not wholly absent; it is partially visible with a foreground object occluding part of it. The source fixture's intended target is the crack location, which is obscured.

### Leader proposal and validator evidence

The finalized transaction's leader receipt exposes the nondeterministic result (`OBS-4`) and its `eq_outputs[0]` proposal. Decoding that receipt shows `area_visibility=VISIBLE`, `occlusion_present=NO`, and `crop_limitation_present=NO` before equivalence. The incorrect negative was therefore already in the leader proposal; post-consensus observation normalization did not introduce it.

Three validator executions completed successfully and voted `AGREE`; the transaction metadata exposes model identifiers for two of them (`policy:prd-kimi`, `policy:prd-gpt-5-4`, `policy:prd-gpt-5-4`) and successful LLM execution accounting. Two validator slots were `IDLE` (one was cancelled after quorum). The transaction does **not** expose those validators' candidate observation dictionaries, fetched response bytes/digests, or their occlusion judgments. Thus it proves validator execution/agreement, but not that every validator independently saw or classified occlusion identically.

The contract's callback independently calls `_observe_single(...)` for validators, and that function executes evidence retrieval, digest validation, then vision interpretation. Source therefore requires the active validators to take the independent path. The public transaction data does not provide a per-validator external-fetch trace, so successful fetch of the same bytes by each validator cannot be proven from receipt metadata alone. The reported exact digest is the authoritative leader result's digest.

## Confirmed findings vs hypotheses

### Confirmed

1. The frozen image contains a clearly recognizable chair and a partly visible wall; the chair hides the target crack region.
2. The leader vision result said the wall was `VISIBLE` and returned `occlusion_present=NO` and `crop_limitation_present=NO`.
3. The leader output passed normalization with `schema_valid=true`; the authoritative record retains the same values. `_normalize_observation` does not rewrite valid enum values. It only replaces malformed/invalid schema answers with an all-uncertain output, and its single-image semantic guard does not connect visibility, occlusion, and crop fields.
4. `_observation_equivalent` treats area visibility plus defect flags as critical for a single observation, but does not include `occlusion_present`, `crop_limitation_present`, `shadow_present`, or other secondary flags in exact comparison. Those secondary values may differ while both candidates remain schema-valid. The three AGREE votes therefore cannot establish that validators shared the leader's `occlusion=NO`; a validator reporting `YES` could still agree under this rule, provided critical fields and provenance matched.
5. The faulty value was present before consensus in the leader proposal. Consensus finalized that proposal rather than correcting the visual judgment.
6. This is a semantic false negative, not an image retrieval/hash failure: the finalized source digest matches the frozen expected digest and the transaction completed the model path.

### Unresolved

- The exact validator candidate values, including whether any validator recognized the chair as an occluder.
- Per-validator external HTTP response status, bytes, and digest; the transaction receipt does not expose them.
- Whether the leader's miss was driven by visual attention, an implicit interpretation of “relevant part,” the label `VISIBLE`, prompt brevity, target-area localization, or model-specific perception. The receipt cannot distinguish these.
- Whether silent automatic redirect behavior affected an independent fetch; the contract rejects visible non-200/3xx responses but the runtime response abstraction lacks final-URL/redirect-chain detail. Matching expected digest strongly binds returned content, but not route provenance.

## Observation vocabulary assessment

The current vocabulary has `area_visibility` (`VISIBLE`, `PARTIAL`, `NOT_ESTABLISHED`, `UNCERTAIN`) and separate `occlusion_present` / `crop_limitation_present` flags. The prompt defines an affirmative occlusion as an object hiding a relevant part of the assessed surface, but does not define when a surface can be `VISIBLE` versus `PARTIAL`, or explicitly make “visible overall but target area hidden” an unresolved state. It also does not identify the target region within the area item.

There is no invariant such as `occlusion_present=YES` requiring partial/unresolved visibility, and no rule that a defect judgment about an unobservable target must be `UNCERTAIN`. Conversely, `VISIBLE` and `occlusion_present=NO` can pass as valid even when the target feature is hidden. This is a schema/validation blind spot that permits the failure; it is not proof that the schema caused the model's initial miss.

For review, a safer future representation would keep distinct bounded facts: (a) visibility of the specific target surface/region, (b) foreground obstruction of that region, (c) region outside the frame/crop, and (d) uncertainty about any of those assessments. Avoid one overloaded `area_visibility` answer. Any obstruction/crop/uncertain target visibility should force defect status for the affected region to `UNCERTAIN` and prevent downstream comparison from treating the image as an unobstructed view. This is a recommendation only; no schema change is implemented here.

## Architecture assessment

Classification: **B is demonstrated; C is an important product constraint, not proven as an absolute impossibility.**

- It is not just a narrow, demonstrated coding bug. The leader's candidate itself contains the wrong semantic fact, so equivalence/consensus cannot repair it. The validator comparator does have a separate coverage gap because occlusion is non-critical, but even strict equivalence would only reject disagreement; it cannot correct a unanimous false negative.
- The result demonstrates unstable/inadequate single-image interpretation for this case. Earlier benchmark generations recorded MOV-SYN-08 as insufficient evidence and sometimes emitted positive occlusion flags, but those used different pair tasks, prompts, and contract versions; they are useful context, not controlled repeat evidence for this exact Stage 4.2 transaction.
- A single image can establish some visible observations, but one photograph cannot establish an inspection-quality view of areas hidden by objects or outside its frame. Therefore a robust inspection product needs capture guidance and an explicit unresolved path, not confidence inferred from image consensus alone.

Continue the visual architecture only as a conservative evidence-observation component: guided multiple views of the same nominated area, clear capture requirements, target-region coverage checks, and unresolved results when coverage is incomplete. Do not treat repeated LLM interpretation of the same obstructed image as a substitute for missing evidence. This recommendation does not authorize production prompt/schema changes or Stage 5.

## Recommended smallest correction for review

Do not make another speculative visual-model prompt edit. The smallest defensible next design is to clarify and enforce the observation contract before any new hosted test:

1. Represent target-region observability independently from generic room/wall visibility.
2. Require a positive, bounded target-visibility determination before asserting feature absence or comparing condition state.
3. Bind the observation to an explicit area/region and requested capture view; if the region is behind a foreground object, outside frame, or uncertain, return an explicit unresolved result.
4. Make occlusion/crop/target-visibility fields critical under equivalence so validators cannot accept contradictory safety-relevant visibility assessments. A failed equivalence must stay inconclusive/rejected; it must not promote the leader answer.
5. Add deterministic local cases for partial wall visibility with target region occluded, out-of-frame crop, unrelated furniture, and genuinely unobstructed coverage; preserve all existing evidence hash/provenance invariants.

Exact enum design, fail-closed behavior, and how guided multiple views are linked remain approval decisions. No implementation has begun.

## Acceptance criteria for any further hosted test

- First pass the full local test/lint/SDK/scope gates; review a diff and frozen fixture labels before deployment.
- Use a new authorized disposable deployment only after explicit approval; do not alter existing hosted records or canonical deployment.
- Validator independently retrieves and verifies the same frozen evidence; where per-validator fetch traces are unavailable, label that limitation accurately.
- The hidden-target fixture must resolve to explicit unresolved/insufficient visibility, never a confident absent-defect or fully-visible result.
- A genuinely visible, unobstructed target remains observable; unrelated furniture must not trigger obstruction; an out-of-frame target must be distinguished from foreground obstruction.
- Equivalence must include all safety-critical visibility/obstruction/crop judgments, and an interpretation disagreement must fail closed rather than inherit the leader proposal.
- Read final receipt and authoritative record after consensus/finality. Stop on the first mismatch. Do not run remaining hosted cases or pairwise tests unless the authorized test plan explicitly permits them and the prerequisite gate passes.
- No condition promotion, liability/deposit action, canonical deployment, or Stage 5 work.

## Final state

- Git: commit `228a69a2327bce36a2deed1f1a503bb9a0a3a303` is pushed to `origin/main`; remote SHA matches and worktree is clean.
- Hosted occlusion failure: confirmed false negative; leader proposed `VISIBLE`, `occlusion=NO`, `crop=NO`.
- Validator evidence: three AGREE executions, two IDLE; candidate outputs and per-validator fetch evidence unavailable.
- New deployment/hosted transaction: **NONE** in this analysis.
- Production visual reasoning: unchanged.
- Stage 5 readiness: **NO**.
