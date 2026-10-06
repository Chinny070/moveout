# MoveOut Stage 0.8 — Worsening Safety Proof

**Stage 0.8: COMPLETE. Stage 1: NOT STARTED.** The Stage 0.7 false `WORSENED` was traced to missing identity and positive-change predicates. Stage 0.8 added those predicates, deterministic fail-closed derivation, and validator comparison of the underlying critical observations. The final v2 hosted run had zero false `NEW_DAMAGE`, `WORSENED`, or `REPAIRED` results. It preserved the obvious worsening pair and two unchanged pairs, but did not preserve any frozen `NEW_DAMAGE` or `PRE_EXISTING` positives. The ambiguity and shadow cases finalized as majority disagreement with no accepted result.

## Stage 0.7 failure audit

Frozen Stage 0.7 case `MOV-SYN-12` expected `INSUFFICIENT_EVIDENCE` but the accepted observation contained:

| Field | Stage 0.7 value |
|---|---|
| `same_area_established` | `YES` |
| `before_visibility` / `after_visibility` | `SUFFICIENT` / `SUFFICIENT` |
| `before_defect_visible` / `after_defect_visible` | `YES` / `YES` |
| `defect_same_location` | `YES` |
| `severity_change` | `INCREASED` |
| Lighting, shadow, occlusion, viewpoint, crop confounders | All `NO` |
| `image_quality` | `SUFFICIENT` |
| `prompt_injection_detected` | `NO` |

Stage 0.7's deterministic rule allowed `WORSENED` for `before=YES`, `after=YES`, same location `YES`, and `severity_change=INCREASED`. Its observation schema did not require a distinct `same_defect_established` predicate or identify a concrete visible increase such as length or affected-area increase. Its validator equivalence independently compared only the fields that existed; validators could agree on “increased severity” without independently confirming defect identity or the underlying observable change.

The error was therefore a combination: observation generation supplied a broad severity label; deterministic derivation treated it as sufficient; and equivalence did not include the missing identity/change predicates. The regression test reproduces the Stage 0.7 `WORSENED` result from that exact observation before asserting the Stage 0.8 fail-closed outcome.

## Final Stage 0.8 contract

The first hosted Stage 0.8 version (`MoveOutVisualSafetyStage08V1`) was deliberately retained as a trial. It safely returned `INSUFFICIENT_EVIDENCE` on every accepted case and had one majority disagreement, but this proved too conservative to preserve any positive or unchanged classifications. A narrow v2 refinement made `UNCHANGED` available when same-area identity, sufficient visibility/quality, no prompt injection, and no occlusion are established and both images explicitly show no defect. It did not relax the damage, pre-existing, worsening, or repair gates.

- Final v2 source: [`moveout_visual_safety_stage08_v2.py`](../contracts/moveout_visual_safety_stage08_v2.py).
- SHA-256: `6FB494EE4FFA0009BDCEC0071910AC8EAB580EECE307B799337E583EEF9366B3`.
- Runtime: `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`.
- Network: StudioNet, chain ID `61999`, RPC `https://studio.genlayer.com/api`.
- Signer: `my-studionet-wallet`, `0xaffe15eec45b68835cc9e5b4ab85dd5deae8e70b`.
- v2 deployment: `0x3430658e8596005e3A1389b25e39B0568B8e2dc1`.
- v2 deployment transaction: `0xe688ab2bafe1adac7633670501e025d31805bf436fc97872ce6003cccca4f1af`, `FINALIZED`, five validator votes AGREE.
- v1 trial source SHA-256: `9024942F8325FAC50F4B3E12AD8BDBE7E40656FC34425E1C9C1C9BF02D5C90CE`.
- v1 trial deployment: `0x2DC4A001041090b6e08f3adc87f4900F5818eb71`.
- v1 trial deployment transaction: `0xd3fedb56d97204a9cacb0476c8c1fe3726d65b3197bf8e84ce9f166cb3344f93`, `FINALIZED`, five validator votes AGREE.
- The Stage 0.6B fixture commit, all 28 PNGs, expected labels, hashes, and immutable URLs were reused unchanged.

## Settlement-critical observations

The vision model returns exactly 19 bounded observations in schema `moveout-observation-v2`; it does not return a condition class:

- Pair identity/visibility: `same_area_established`, `before_visibility`, `after_visibility`, `image_quality`.
- Defect observations: `before_defect_visible`, `after_defect_visible`, `defect_same_location`, `same_defect_established`.
- Severity/change: `severity_increase_established`, `severity_decrease_established`, `positive_change_evidence`.
- Material confounders: `possible_lighting_confounder`, `possible_shadow_confounder`, `possible_occlusion`, `possible_viewpoint_mismatch`, `possible_scale_distance_mismatch`, `possible_crop_mismatch`.
- Safety/support: `prompt_injection_detected`, `repair_surface_evidence`.

`positive_change_evidence` is one of `NONE`, `EXTENT_INCREASE`, `LENGTH_INCREASE`, `WIDTH_INCREASE`, `AFFECTED_AREA_INCREASE`, `BREAKAGE_INCREASE`, `MATERIAL_LOSS_INCREASE`, or `UNCERTAIN`. These are qualitative visible-pixel comparisons, not physical measurements.

## Deterministic classification rules

All classifications first require a valid observation schema, `same_area_established=YES`, both views `SUFFICIENT`, `image_quality=SUFFICIENT`, and `prompt_injection_detected=NO`. Invalid, missing, malformed, or conflicting observations fail closed.

- **`WORSENED`** requires before and after defects `YES`; `defect_same_location=YES`; `same_defect_established=YES`; `severity_increase_established=YES`; one named positive change evidence value; `severity_decrease_established` not `YES`; and every material confounder exactly `NO`. If any required predicate is `NO`, `UNCERTAIN`, or missing, `WORSENED` is not derivable.
- **`NEW_DAMAGE`** requires before defect `NO`, after defect `YES`, `defect_same_location=YES`, and every material confounder exactly `NO`, in addition to the shared base gates.
- **`PRE_EXISTING`** requires before and after defect `YES`, same location and same defect `YES`, increase and decrease both `NO`, change evidence `NONE`, and every material confounder `NO`.
- **`REPAIRED`** requires before defect `YES`, after defect `NO`, same location and same defect `YES`, severity decrease `YES`, positive `repair_surface_evidence=YES`, and every material confounder `NO`. Disappearance alone cannot derive repair.
- **`UNCHANGED`** requires both defects `NO`, the shared base gates, and `possible_occlusion=NO`. Nonblocking differences in lighting, shadow, crop, or viewpoint do not by themselves turn an explicit no-defect pair into a damage finding. Occlusion, poor visibility/quality, uncertain area, injection, or uncertainty about whether a defect is present blocks this result.

The precedence is fail closed: schema/base-gate failure first; contradictory increase and decrease next; then each class's own positive predicates. No conflict is resolved in favor of damage. The LLM never authoritatively chooses `WORSENED` or any other class; deterministic code derives the class from the accepted observation.

## Validator independence and equivalence

The leader independently fetches both image URLs, checks HTTPS, HTTP 200, nonempty body, PNG/JPEG MIME, the 500,000-byte per-image bound, and exact frozen SHA-256 values, then calls `gl.nondet.exec_prompt(images=[body_a, body_b], response_format="json")`. Every validator execution repeats both fetches, digest checks, and vision prompt; it evaluates the same 19 bounded observation predicates.

`gl.vm.run_nondet_unsafe` uses custom equivalence. It requires matching stages, failure codes, response metadata, and the expected SHA-256 values. For each critical field, validators reject unsupported leader certainty: affirmative area/same-defect/location claims require their independent `YES`; sufficient visibility/quality requires independent `SUFFICIENT`; a leader cannot dismiss a confounder or injection signal seen by a validator; repair evidence `YES` requires validator support; severity increase/decrease `YES` requires independent `YES`; and a named change type must match exactly. Defect-presence claims require exact agreement unless the leader is `UNCERTAIN`. A more cautious leader may be accepted and deterministically derives an inconclusive result. Disagreement can finalize `MAJORITY_DISAGREE` without changing state.

The final run had 12 `MAJORITY_AGREE` and 2 `MAJORITY_DISAGREE` receipts. `IDLE` validators stopped after quorum; these do not prove that every validator ran the vision task. Receipts expose votes and finality, not each validator's HTTP transcript or raw model output.

## Quality gates

- `genvm-lint lint`: **PASS**, 3 checks.
- `genvm-lint check`: **PASS**, one write and one view method.
- Python compile: **PASS** for both Stage 0.8 deployed sources.
- Direct tests: **31/31 PASS** across the full test suite. Coverage includes the exact Stage 0.7 regression, an obvious clean worsening, the ambiguous-mark predicate gaps, lighting/shadow/viewpoint/scale/crop/occlusion/quality gates, new damage, stable pre-existing condition, unchanged, strict repair evidence, malformed schemas, conflicting severity, and validator checks of the positive predicates.
- Final hosted v2 benchmark: **14/14** receipts `FINALIZED`, all with transaction hashes. Every accepted state was authoritatively reread after finality; the two majority disagreements were reread and confirmed to leave the prior state unchanged.
- All 14 final-run cases had HTTP 200 `image/png` retrieval metadata and SHA-256 parity with the frozen manifest for both images.
- Case 9 had transient receipt lookup errors; retries on the same transaction obtained its finalized receipt. Case 14's write CLI returned an HTML/RPC parse error after emitting a transaction hash; that hash was preserved, its receipt finalized, and no duplicate write was sent.

## Final v2 hosted results

| Case | Expected | Actual accepted result | Consensus | Validator votes | Transaction |
|---|---|---|---|---|---|
| MOV-SYN-01 | `UNCHANGED` | `UNCHANGED` | `MAJORITY_AGREE` | IDLE, AGREE, AGREE, AGREE, DISAGREE | `0x9d657cdef898c0e3550686aa67480c9eec1498bf185579cdfc44be399679776d` |
| MOV-SYN-02 | `UNCHANGED` | `UNCHANGED` | `MAJORITY_AGREE` | AGREE, AGREE, IDLE, IDLE, AGREE | `0x17c6622c7372381c942e8b1b8c033aa457900952ea7491f2e99afa1eb6aeefa` |
| MOV-SYN-03 | `PRE_EXISTING` | `INSUFFICIENT_EVIDENCE` | `MAJORITY_AGREE` | AGREE, AGREE, IDLE, IDLE, AGREE | `0xd47ac3257b804e18897fa6a74e4547271efa35ac7d292996d9b334ec9b79d8b7` |
| MOV-SYN-04 | `NEW_DAMAGE` | `INSUFFICIENT_EVIDENCE` | `MAJORITY_AGREE` | IDLE, AGREE, AGREE, DISAGREE, AGREE | `0x016619402af4a1e236ff65c7aba6796caa3e64a5febd915a7303378283411bcb` |
| MOV-SYN-05 | `NEW_DAMAGE` | `INSUFFICIENT_EVIDENCE` | `MAJORITY_AGREE` | AGREE, AGREE, AGREE, IDLE, IDLE | `0xf2314193c7f114d841dee25c248473e3c515813aa6da5c2dcb2ad19dc7be533d` |
| MOV-SYN-06 | `WORSENED` | `WORSENED` | `MAJORITY_AGREE` | AGREE, IDLE, AGREE, DISAGREE, AGREE | `0xa9082c17cdd3b64e0f42c047ed201c0b5af9aaca04d3ddae3f9c4f6459083585` |
| MOV-SYN-07 | `REPAIRED` | `INSUFFICIENT_EVIDENCE` | `MAJORITY_AGREE` | IDLE, AGREE, IDLE, AGREE, AGREE | `0xac0a3b6ec8ff668153bbe609523814ea5d8e2908521dde00f71878ff6a171bae` |
| MOV-SYN-08 | `INSUFFICIENT_EVIDENCE` | `INSUFFICIENT_EVIDENCE` | `MAJORITY_AGREE` | AGREE, DISAGREE, IDLE, AGREE, AGREE | `0x1ae261827e63565a63df751797f717bf73c5cea11c9edad4990336e643891010` |
| MOV-SYN-09 | `INSUFFICIENT_EVIDENCE` | `INSUFFICIENT_EVIDENCE` | `MAJORITY_AGREE` | AGREE, IDLE, IDLE, AGREE, AGREE | `0x5d8029a8feac6410f91ce13d9e279467bb64870e471a667ecf38176869e403f9` |
| MOV-SYN-10 | `INSUFFICIENT_EVIDENCE` | `INSUFFICIENT_EVIDENCE` | `MAJORITY_AGREE` | AGREE, IDLE, AGREE, IDLE, AGREE | `0x7ac47c36bd67b7a596adf1d553d936d72e38961280e909422fd90ed19f5a0739` |
| MOV-SYN-11 | `INSUFFICIENT_EVIDENCE` | `INSUFFICIENT_EVIDENCE` | `MAJORITY_AGREE` | AGREE, AGREE, IDLE, AGREE, IDLE | `0x05672a6be16090234c9a2bc7a29b1c3ffeb2227d60276aba2629134433593949` |
| MOV-SYN-12 | `INSUFFICIENT_EVIDENCE` | No accepted result | `MAJORITY_DISAGREE` | AGREE, DISAGREE, AGREE, DISAGREE, DISAGREE | `0x484ce6f883b33b7dd1f59eccefa47fcbc0224e1048110b86906ba5cf04054810` |
| MOV-SYN-13 | `PRE_EXISTING` | `INSUFFICIENT_EVIDENCE` | `MAJORITY_AGREE` | AGREE, AGREE, AGREE, DISAGREE, DISAGREE | `0xa24d1fea9035e5bf73aec0dc917501589e13a84764f370f335e434df48ad131c` |
| MOV-SYN-14 | `UNCHANGED` | No accepted result | `MAJORITY_DISAGREE` | DISAGREE, DISAGREE, IDLE, IDLE, DISAGREE | `0x56a428a0e4ce1c58445000d171e1c61c9b2159ae525481e7d4b51c8908c6a3c5` |

Machine-readable final outcomes: [`stage08_v2_results.ndjson`](../benchmarks/controlled-property-2026-10/stage08_v2_results.ndjson). The overconservative first Stage 0.8 trial and transaction diagnostics are in [`stage08_v1_trial_results.ndjson`](../benchmarks/controlled-property-2026-10/stage08_v1_trial_results.ndjson), [`stage08_v1_trial_pending.ndjson`](../benchmarks/controlled-property-2026-10/stage08_v1_trial_pending.ndjson), and [`stage08_v2_pending.ndjson`](../benchmarks/controlled-property-2026-10/stage08_v2_pending.ndjson).

## Safety gate and usefulness

| Measure | Final v2 outcome |
|---|---:|
| Receipts finalized | 14 / 14 |
| Majority agree / disagree | 12 / 2 |
| Exact expected labels | 7 / 14 |
| Accepted `INSUFFICIENT_EVIDENCE` results | 9 / 12 accepted writes |
| Expected insufficient cases explicitly returning `INSUFFICIENT_EVIDENCE` | 4 / 5; ambiguous case 12 instead had no accepted result |
| False `NEW_DAMAGE` | 0 |
| False `WORSENED` | 0 |
| False `REPAIRED` | 0 |
| Clear `NEW_DAMAGE` cases preserved | 0 / 2 |
| Clear `WORSENED` cases preserved | 1 / 1 (case 6, specific length increase) |
| `PRE_EXISTING` cases preserved | 0 / 2 |
| `UNCHANGED` cases preserved | 2 / 3 (cases 1 and 2; shadow case 14 disagreed) |

Required dangerous-false-positive gate: **PASS**. The ambiguous-mark case 12 did not produce `WORSENED`; validators disagreed and no state changed. The shadow case 14 did not produce `NEW_DAMAGE` or `WORSENED`; validators disagreed and no state changed. Occlusion (8), crop mismatch (9), lookalike area (11), and prompt injection (13) produced only insufficient/no accepted results. The one tested genuine worsening (6) remained usable.

The broader usefulness gate remains weak: neither new-damage pair reached its positive class, and neither pre-existing pair did. This is not a trivial all-insufficient system—two unchanged pairs and the clean, unconfounded worsening pair were classified—but its positive evidence boundary remains narrow. Direct tests prove that bounded, fully supported `NEW_DAMAGE` and `PRE_EXISTING` observations derive their classes; this synthetic hosted run did not provide those supported predicates for the corresponding fixtures.

## Stage comparison

| Measure | Stage 0.6B | Stage 0.7 | Stage 0.8 final v2 |
|---|---:|---:|---:|
| Receipt-confirmed / finalized cases | 14 | 13 receipts + case 4 accepted state with receipt unavailable | 14 |
| Majority agree / disagree | 10 / 4 | 13 confirmed agree; case 4 inferred agree | 12 / 2 |
| Matched labels | 5 / 10 accepted (50%) | 7 / 14 returned results (50%) | 7 / 14 attempts (50%) |
| False `NEW_DAMAGE` | 1 (shadow case 14) | 0 | 0 |
| False `WORSENED` | 1 (ambiguous case 12) | 1 (ambiguous case 12) | 0 |
| False `REPAIRED` | 0 accepted; repair unresolved | 0 | 0 |
| Appropriate insufficient evidence | 1 accepted; 4 disagreements unresolved | 4 / 5 expected-insufficient cases | 4 / 5 expected-insufficient cases; one disagreement |
| Useful `NEW_DAMAGE` | 2 / 2 | 2 / 2 | 0 / 2 |
| Useful `WORSENED` | 1 / 1 correct; plus one ambiguous false positive | 0 / 1 (true pair insufficient) | 1 / 1; ambiguous pair no accepted result |
| Useful `PRE_EXISTING` | 0 / 2 | 1 / 2 | 0 / 2 |
| Useful `UNCHANGED` | 1 / 3 | 0 / 3 | 2 / 3 |

The v1 pilot produced 13 insufficient results and one disagreement. The v2 refinement recovers useful unchanged and worsening classifications while maintaining zero dangerous false condition findings. Compared with Stage 0.7, the ambiguous case is blocked by validator disagreement rather than accepted as `WORSENED`; the shadow case is also blocked without a false condition result.

## Classification and limits

**CONTROLLED VISUAL SAFETY: WEAK.** The dangerous-false-positive portion of the Stage 0.8 gate passes, and the clearest worsening remains usable. The controlled positives for new damage and pre-existing condition were not preserved, and two cases ended without accepted results. That utility gap prevents a stronger overall rating.

**REAL-WORLD PROPERTY ACCURACY: NOT YET VERIFIED. READY FOR STAGE 1: NO.** The 14 cases are generated synthetic fixtures; validator model outputs can vary; disagreement yields no new contract state rather than a structured `INSUFFICIENT_EVIDENCE`; and receipts do not expose per-validator image payloads or raw observations. No deposit, repair, liability, tenancy, or production MoveOut behavior has been tested. No canonical MoveOut contract was deployed. Stop at Stage 0.8; do not begin Stage 1.
