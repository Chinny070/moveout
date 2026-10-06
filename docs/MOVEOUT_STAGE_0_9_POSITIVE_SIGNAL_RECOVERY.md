# MoveOut Stage 0.9 — Positive Signal Recovery

**Stage 0.9 only. Stage 1 has not started.** The v2 hosted run completed all 14 frozen cases, but the primary safety gate **FAILED**: the ambiguous-mark case again finalized as a false `WORSENED`. Positive-signal recovery improved, but Stage 0.9 is not safe to advance.

## Stage 0.8 root-cause audit (pre-change)

The frozen pair images, manifest, expected labels, and Stage 0.8 v2 hosted output were inspected without modifying them. The expected labels remain those in the Stage 0.6B commit-pinned manifest.

| Case | Expected | Stage 0.8 observation relevant to outcome | Blocking field / layer | Finding |
|---|---|---|---|---|
| MOV-SYN-04 | `NEW_DAMAGE` | Same area `YES`; visibility and quality sufficient; before defect `NO`; after defect `YES`; all six confounders `NO`; location `NO` | Derivation required `defect_same_location=YES` for a defect absent from the before image | **Observation/semantics mismatch.** The model observed the key physical fact (crack absent before, present after) but the cross-image location predicate was not meaningful when no before defect existed. Derivation then rejected the case. |
| MOV-SYN-05 | `NEW_DAMAGE` | Same area and both visibilities `UNCERTAIN`; image quality insufficient; defect presence uncertain; confounders uncertain | Observation generation, not derivation | **Observation-generation failure.** The contract correctly failed closed because no required fact was observed. This pair remains a model/fixture recognition issue unless a better bounded prompt or structured observation recovers those facts. |
| MOV-SYN-03 | `PRE_EXISTING` | Before/after visibility insufficient; both defect-presence fields and same-area/identity uncertain; other comparison fields uncertain | Observation generation; then shared derivation base gates | **Observation-generation failure.** The model did not observe the clear crack in the earlier image or establish the pair. No evidence shows deterministic derivation rejected an established positive. |
| MOV-SYN-13 | `PRE_EXISTING` | Later view sufficient, but earlier defect uncertain; same area uncertain; injection detected `YES`; most comparison fields uncertain | Observation generation plus blanket injection gate | **Mixed failure.** The earlier crack was not recognized and the pair was not aligned; independently, treating any detected image-text injection as a global veto suppresses visual evidence even when the text is explicitly untrusted. Injection must not influence the visual observation or make a valid physical observation unusable by itself. |
| MOV-SYN-06 | `WORSENED` | Same area/defect/location `YES`; both views sufficient; severity increase `YES`; named `LENGTH_INCREASE`; all confounders `NO` | None | The strict Stage 0.8 WORSENED path correctly preserved its clear positive. Keep its evidence gates strict. |
| MOV-SYN-01 / 02 | `UNCHANGED` | Same area and view quality sufficient; both defect observations `NO`; case 01 has unrelated lighting/view/crop differences | Existing class-specific derivation | Both clear UNCHANGED cases were preserved. Case 01 demonstrates that non-material scene differences need not prevent a no-defect finding. |

### Diagnosis by failure category

- **NEW_DAMAGE case 04:** the model observed the essential absence/presence transition. The rule incorrectly reused `defect_same_location`, a predicate that is only meaningful for a defect visible in both photos. The schema needs a distinct predicate asserting that a newly observed defect lies in the comparable shared physical area.
- **NEW_DAMAGE case 05:** the model failed to observe the relevant facts; the Stage 0.8 classifier did not reject an otherwise sufficient observation. Do not force a class in code. Improve prompts/observation structure, retain fail-closed behavior, and report if the hosted model still abstains.
- **PRE_EXISTING case 03:** model observation failure, not validator equivalence or deterministic derivation. The expected meaning in this fixed pair is that the defect is visibly present in the earlier/baseline image. It must not be defined as “unchanged”: a baseline-visible defect is pre-existing evidence even if later evidence does not prove no change.
- **PRE_EXISTING case 13:** model observation failure plus overly broad global injection handling. Image text is untrusted content and must never act as instruction; mere detection must not veto unrelated, independently corroborated physical observations.
- **Confounder uncertainty:** Stage 0.8 required every confounder field to equal `NO` for damage and pre-existing classes. This treated unrelated or immaterial lighting, framing, or viewpoint variation as blockers. Stage 0.9 must require bounded class-specific materiality judgments; `MATERIAL` and `UNCERTAIN` block consequential changes, while `NOT_MATERIAL` does not.
- **Validator equivalence:** it did not cause cases 03–05's majority-agreed insufficient outcomes; those transactions accepted the leader observation and deterministic fallback. Keep independent validator retrieval and require validator support for every consequential leader claim.
- **Deterministic derivation:** it correctly failed closed on uncertain positive evidence except the case 04 predicate mismatch described above. Do not use a global confidence threshold.

## Stage 0.9 revisions and method

Stage 0.9 used two disposable revisions after hosted evidence uncovered a class-specific issue. Both used the same StudioNet network, pinned runtime, frozen 14 pair IDs, 28 PNGs, immutable URLs, exact SHA-256 values, and expected labels. No Stage 0.8 contract or benchmark asset was changed.

The first pilot (v1) completed cases 01–11. It recovered the two `NEW_DAMAGE` positives and the clear `WORSENED` case, but case 11 (lookalike area) incorrectly derived `PRE_EXISTING` from an earlier-image defect even though the later image did not establish the same defect. That pilot result exposed an overly broad origin rule. The pilot was stopped before case 12; it is preserved as a partial diagnostic run and is not counted as the final 14-case gate.

The final v2 rule requires `PRE_EXISTING` to establish the same defect in both sufficiently visible images on the shared area, while allowing severity to remain uncertain. This is distinct from `UNCHANGED`, which requires both views to show no defect. `WORSENED` still requires the Stage 0.8 identity, positive-change, and confounder checks. `REPAIRED` still requires identity, visible decrease, materiality clearance, and surface restoration evidence.

The observation schema reports each confounder's materiality as `NOT_APPLICABLE`, `NOT_MATERIAL`, `MATERIAL`, or `UNCERTAIN`. A damage or repair class requires each relevant materiality field to be resolved as absent or not material. An explicitly unrelated difference does not block a positive; material or uncertain explanations fail closed. No numeric/global confidence score is used.

The final v2 source, deployment, and complete case records are listed below. Source SHA-256 is `0E63BA93464AFF2DF2BA51859E397083FFA3A48ABAE481917869E863694C81E4`; pinned runtime is `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`; network is StudioNet chain `61999`, RPC `https://studio.genlayer.com/api`; signer is `my-studionet-wallet` (`0xaffe15eec45b68835cc9e5b4ab85dd5deae8e70b`). Final disposable address: `0x9a6B147c8f4F8cAB477911A13Fd79dA6225c9bE0`; deployment transaction: `0x7510e83a1ee2c8efd957324270d661c8e277cb134eab838fc869980a8b7964b6`, receipt accepted with five AGREE votes. The partial v1 source hash was `DFD5324DC2AA03CD27D62B7DB240D4CF5F17EF2B9C79C80CA5E17653EC9944C0`; address `0xB535bAeD3bEE84cC4Ed0a934cfb717a205732C1D`; deployment transaction `0x770d09f94551ec92f0d7aaf48151f464d08dc315419977d6e0bbe98978211391`.

### Validator and evidence path

The leader and each active validator independently fetch both source URLs, validate HTTPS response status, image MIME, nonempty bounded body, and the expected image digests, then run the same bounded multimodal observation prompt. Custom equivalence requires exact retrieval metadata/digest agreement. If the leader derives a positive or `UNCHANGED` result, the validator must independently derive the same class from its own observation; a cautious leader can fail closed to insufficient. Idle-after-quorum validators do not prove an additional evaluation. Receipts record vote patterns but do not expose the validators' full HTTP/model traces.

The v2 result function also returns the leader's structured proposal in the transaction receipt. This preserves proposal/observation evidence when consensus or state acceptance differs; all v2 cases reached majority agreement and the proposal matched the authoritative state reread.

## Local quality gates

- `genvm-lint lint`: **PASS**, 3 checks.
- `genvm-lint check`: **PASS**, 1 write and 1 view method.
- Python compile: **PASS**.
- Direct tests: **46/46 PASS**, including all 31 preserved Stage 0.8 tests and 15 Stage 0.9 regressions. The Stage 0.9 tests cover the lost new-damage predicate, pre-existing temporal meaning and same-defect requirement, ambiguous-mark safety, shadow/materiality gates, lighting materiality, irrelevant scene differences, uncertainty, same-area mismatch, WORSENED identity, prompt injection, malformed observations, repair evidence, and independent validator derivation.

## Final v2 hosted case results

All 14 transactions are `FINALIZED` with `MAJORITY_AGREE`; all writes were accepted and followed by authoritative `get_result()` rereads. No transaction was duplicated after a hash existed. Every case's two HTTP responses were status 200 `image/png`, and all 28 response SHA-256 values matched the frozen manifest. Complete machine-readable rows (including each observation, classification, vote sequence, transaction, and authoritative state) are in [`stage09_v2_results.ndjson`](../benchmarks/controlled-property-2026-10/stage09_v2_results.ndjson); pending/submission diagnostics are in [`stage09_v2_pending.ndjson`](../benchmarks/controlled-property-2026-10/stage09_v2_pending.ndjson).

| Case | Expected | Accepted result | Votes | Transaction |
|---|---|---|---|---|
| MOV-SYN-01 | `UNCHANGED` | `UNCHANGED` | IDLE, AGREE, IDLE, AGREE, AGREE | `0x2a9372516c70a4de1a7e75fd3f7dd23f644603eb8f3893724d787097af0cdcdf` |
| MOV-SYN-02 | `UNCHANGED` | `UNCHANGED` | AGREE, DISAGREE, AGREE, AGREE, IDLE | `0x2b8269c97eb6b66a1db69f81cc40fe5a2067f9e20d9e88b5143ca4e1c75b4f42` |
| MOV-SYN-03 | `PRE_EXISTING` | `INSUFFICIENT_EVIDENCE` | AGREE, AGREE, IDLE, IDLE, AGREE | `0x3f4e77bd5cfb02fe50061fc2389d6cfde5d5702424a6519ff44d6959d53f20b5` |
| MOV-SYN-04 | `NEW_DAMAGE` | `NEW_DAMAGE` | AGREE, IDLE, IDLE, AGREE, AGREE | `0xeddba37ffae5f773baab77cb3d7a789020f12f861afc744d3f289535a9a21b5d` |
| MOV-SYN-05 | `NEW_DAMAGE` | `NEW_DAMAGE` | AGREE, IDLE, AGREE, AGREE, DISAGREE | `0x96332a8a0394271f104b62cfea91c38f6686352e9c1c7b65498e99bf244e264c` |
| MOV-SYN-06 | `WORSENED` | `WORSENED` | IDLE, IDLE, AGREE, AGREE, AGREE | `0xb16ef2e50fc203a4592f24973d5ec64c4c6807ce700ea7b90293c612b84f67df` |
| MOV-SYN-07 | `REPAIRED` | `INSUFFICIENT_EVIDENCE` | AGREE, AGREE, AGREE, IDLE, IDLE | `0xf21ecff35fd3502453a493234cb249f7963fbe71fd2dff9c1a5f9a5b21cba6c8` |
| MOV-SYN-08 | `INSUFFICIENT_EVIDENCE` | `INSUFFICIENT_EVIDENCE` | AGREE, IDLE, AGREE, AGREE, IDLE | `0xe08e10fd989521a4f3d84a648114ab208ded3b0a029a2f54f1228a14815fde8f` |
| MOV-SYN-09 | `INSUFFICIENT_EVIDENCE` | `INSUFFICIENT_EVIDENCE` | AGREE, AGREE, IDLE, AGREE, IDLE | `0xb8ee015c5202b5960e338d2fbf5c67675a442acb0a8be2e3f0b73e1433779ba6` |
| MOV-SYN-10 | `INSUFFICIENT_EVIDENCE` | `INSUFFICIENT_EVIDENCE` | AGREE, AGREE, IDLE, AGREE, IDLE | `0x2447fb5bba747652e5f403a97b5f574b99eada383397081dce7482773969fefe` |
| MOV-SYN-11 | `INSUFFICIENT_EVIDENCE` | `INSUFFICIENT_EVIDENCE` | AGREE, IDLE, IDLE, AGREE, AGREE | `0xa1d97fb2f1fb8a1cde54fa6ac3be895f621ebd46c74d5774f9aed3d338bf01d5` |
| MOV-SYN-12 | `INSUFFICIENT_EVIDENCE` | **`WORSENED` (false positive)** | AGREE, AGREE, IDLE, AGREE, DISAGREE | `0x278b38646d92cde8f724298cdab887f9aafd3e23558b2bc42234e9d17eaaec51` |
| MOV-SYN-13 | `PRE_EXISTING` | `INSUFFICIENT_EVIDENCE` | IDLE, AGREE, IDLE, AGREE, AGREE | `0x44d588c4cb5f8ee83643d5e7d92822388a4d6886ecb4760902d668179fea1d61` |
| MOV-SYN-14 | `UNCHANGED` | `INSUFFICIENT_EVIDENCE` | AGREE, IDLE, AGREE, AGREE, IDLE | `0x4574311acb364c871a1ad82193211f8af783173474b1136fc384ad7a1b2a4e83` |

### Stage 0.9 gate results

| Measure | Final v2 |
|---|---:|
| Hosted cases / finalized receipts / accepted writes | 14 / 14 / 14 |
| `MAJORITY_AGREE` / `MAJORITY_DISAGREE` | 14 / 0 |
| Matched expected labels | 9 / 14 |
| Unresolved cases | 0 (though some accepted classifications were wrong) |
| False `NEW_DAMAGE` | 0 |
| False `WORSENED` | **1** (MOV-SYN-12, ambiguous mark) |
| False `REPAIRED` | 0 |
| Clear `NEW_DAMAGE` preserved | 2 / 2 |
| Clear `WORSENED` preserved | 1 / 1, plus false ambiguous `WORSENED` |
| Clear `PRE_EXISTING` preserved | 0 / 2 |
| Clear `UNCHANGED` preserved | 2 / 3 (shadow case 14 abstained) |
| Expected insufficient cases explicitly returned insufficient | 4 / 5 (case 12 was false `WORSENED`) |
| Retrieval/digest parity | 28 / 28 |

**Primary safety gate: FAIL.** Case 12's leader observation said same area, both views sufficient, defect present in both, same location and same defect established, severity increase `YES`, positive evidence `LENGTH_INCREASE`, and all materiality fields `NOT_MATERIAL` or `NOT_APPLICABLE`. Its custom validator received enough matching independent evaluations for majority agreement (three active AGREE votes, one DISAGREE, one IDLE). The error is an observation/model ambiguity failure with correlated validator agreement; deterministic derivation followed the stated predicates correctly. The source has no case-specific branch that could identify this fixture. This shows the current bounded fields do not separate an ambiguous superficial mark from a clear worsening reliably.

Case 14 did not become `NEW_DAMAGE` or `WORSENED`; the model marked the after defect uncertain and shadow materiality `MATERIAL`, so it failed closed. Case 08 occlusion, case 09 crop mismatch, and case 11 lookalike area all returned insufficient. Case 13's embedded instruction was not followed, but the model did not identify it (`prompt_injection_detected=NO`) and returned all key visual fields uncertain; injection resistance therefore did not recover the expected pre-existing class.

The final **SAFETY** assessment is **FAILED / NOT VIABLE under the Stage 0.9 gate** because false `WORSENED` must be zero. **USEFULNESS** improved for both new-damage cases, the obvious worsening case, and two unchanged cases, but both pre-existing cases and the repair case remain unresolved or unpreserved. No overall accuracy or production claim is warranted.

## Stage 0.6B vs. Stage 0.7 vs. Stage 0.8 vs. Stage 0.9

`Unresolved` means consensus disagreement or no accepted result; a wrong majority-agreed class is counted as a mismatch, not as unresolved.

| Measure | Stage 0.6B | Stage 0.7 | Stage 0.8 v2 | Stage 0.9 v2 |
|---|---:|---:|---:|---:|
| Label matches | 5 / 10 accepted | 7 / 14 returned | 7 / 14 attempts | 9 / 14 |
| Unresolved | 4 | 0 (one receipt unavailable) | 2 | 0 |
| False `NEW_DAMAGE` | 1 | 0 | 0 | 0 |
| False `WORSENED` | 1 | 1 | 0 | **1** |
| False `REPAIRED` | 0 accepted | 0 | 0 | 0 |
| Clear `NEW_DAMAGE` preserved | 2 / 2 | 2 / 2 | 0 / 2 | 2 / 2 |
| Clear `WORSENED` preserved | 1 / 1 (+1 false) | 0 / 1 (+1 false) | 1 / 1 | 1 / 1 (+1 false) |
| Clear `PRE_EXISTING` preserved | 0 / 2 | 1 / 2 | 0 / 2 | 0 / 2 |
| Clear `UNCHANGED` preserved | 1 / 3 | 0 / 3 | 2 / 3 | 2 / 3 |
| Expected insufficient behavior | 1 / 5 explicit; 3 disagreements; 1 false class | 4 / 5 explicit | 4 / 5 explicit; 1 disagreement | 4 / 5 explicit; 1 false class |

## Anti-overfitting and limits

The v2 source and prompt contain no `MOV-SYN-*` case identifiers, fixture filenames, fixture hashes as class selectors, expected labels, or URL-specific classification branches. Expected SHA-256 values are only used to bind fetched evidence bytes to the frozen manifest. Expected labels are used by the external evaluation logger only and are not passed to the contract or model. The contract has no tenancy, deposit, repair-cost, liability, or canonical MoveOut behavior.

The 14 cases are synthetic. Validator model outputs can vary; majority agreement did not prevent a correlated false `WORSENED`; receipt votes do not reveal every validator's raw prompt/image/model output; and the visual observation is not evidence of physical truth. **REAL-WORLD PROPERTY ACCURACY: NOT YET VERIFIED. READY FOR STAGE 1: NO.** Stage 0.9 ends as a failed safety gate. Do not begin Stage 1.

## Architecture review disposition (2026-10-06)

The Stage 0.9 **visual safety gate remains FAILED** as recorded above. A subsequent authority-model review authorizes readiness for Stage 1's deterministic protocol foundation only; it does not start Stage 1, approve production visual adjudication, or change any Stage 0.9 result. See [MoveOut Visual Verdict Architecture](MOVEOUT_VISUAL_VERDICT_ARCHITECTURE.md) for the revised scope and decision. **Real-world property visual accuracy remains NOT YET VERIFIED.**
