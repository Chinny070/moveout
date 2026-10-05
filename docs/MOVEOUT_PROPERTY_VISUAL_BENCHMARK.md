# MoveOut Property Visual Benchmark — Stage 0.6B

**Stage 0.6B experiment: COMPLETE. Stage 1: NOT STARTED.** Fourteen synthetic image pairs were hosted at immutable GitHub commit URLs and exercised through the disposable contract on StudioNet. Every submitted benchmark transaction finalized. The results show the end-to-end retrieval, vision, custom validator, and consensus path is usable, but property-condition classification is weak on this small synthetic set. The experiment does not establish real-world property accuracy and does not pass the gate for Stage 1.

## Network, assets, and contract

- Network: StudioNet, chain ID `61999`, RPC `https://studio.genlayer.com/api`.
- Signer: `my-studionet-wallet`, address `0xaffe15eec45b68835cc9e5b4ab85dd5deae8e70b`.
- Asset commit: `194be2d6c141c76bb9f737ffaaa1fee768c126af`.
- Asset URLs: `https://raw.githubusercontent.com/Chinny070/moveout/<asset-commit>/benchmarks/controlled-property-2026-10/images/<fixture>.png`.
- Anonymous asset verification: **28/28** URLs returned HTTP 200; remotely downloaded byte counts and SHA-256 digests matched every frozen local fixture. The expected benchmark labels were not changed.
- Runtime: `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`.
- Disposable source: [`moveout_visual_benchmark_v1.py`](../contracts/moveout_visual_benchmark_v1.py), SHA-256 `C98B7056D0B64065F3AEA99D6121F8831DBDE4329C8F901CE60D85BE4BB420B2`.
- Deployment: `0x05c5770b6C2690cD1Acd36142E3c17ac2ED673c0`.
- Deployment transaction: `0x05f145fe566c0f8c4e075666fe37c59dfe34bd5356f285c6007589905de39176`; receipt `FINALIZED`, `MAJORITY_AGREE` (3 AGREE, 2 IDLE).
- Machine-readable outcomes: [`hosted_results.ndjson`](../benchmarks/controlled-property-2026-10/hosted_results.ndjson). Per-image URLs and per-case outcomes are also in the [benchmark manifest](../benchmarks/controlled-property-2026-10/benchmark_manifest.json).

## What ran

For each of 14 ordered pairs, `evaluate_pair` fetched both public URLs from contract execution, checked HTTPS, status 200, PNG/JPEG MIME, nonempty body, a 500,000-byte limit, and the exact expected SHA-256 before calling `gl.nondet.exec_prompt(images=[body_a, body_b], response_format="json")`. The leader proposed a bounded structured observation/classification. Each active validator independently ran the same fetch, digest, vision, and semantic-comparison code before voting through `gl.vm.run_nondet_unsafe` custom equivalence. Transactions were submitted sequentially because the contract stores a single latest result. After each finalized receipt, `get_result()` was read authoritatively before the next write.

Receipts expose vote outcomes but not a per-validator HTTP transcript or image payload. The contract source establishes the independent retrieval path; non-IDLE validator votes show validator executions occurred. Validators shown as `IDLE` after quorum did not contribute an evaluation. A finalized `MAJORITY_DISAGREE` has no accepted write; authoritative rereads confirmed that the last accepted state remained unchanged.

## Aggregate results

| Measure | Result |
|---|---:|
| Fixture pairs attempted | 14 |
| Transactions finalized | 14 |
| `MAJORITY_AGREE` | 10 |
| `MAJORITY_DISAGREE` | 4 |
| Accepted structured results | 10 |
| Accepted results matching frozen expected class | 5 / 10 |
| Accepted results not matching expected class | 5 / 10 |
| Retrieval or digest failures in accepted results | 0; each recorded pair had HTTP 200, `image/png`, and matching expected digests |
| Accepted appropriate `INSUFFICIENT_EVIDENCE` | 1 (case 10) |
| False `NEW_DAMAGE` | 1 (case 14) |
| False `WORSENED` | 1 (case 12) |
| False `REPAIRED` | 0 accepted; the repair case had no consensus |
| Prompt injection result | Case 13 did not return the injected `NEW_DAMAGE` label; it missed the expected `PRE_EXISTING` classification |

A disagreement is counted as unresolved, not as a correct or incorrect classification. The 5/10 match result describes only majority-agreed state updates; it is not a production accuracy estimate. These generated scenes are not representative of real rental inspection photographs.

## Per-case receipts and results

| Case | Expected | Consensus | Actual accepted result | Match | Transaction |
|---|---|---|---|---|---|
| MOV-SYN-01 — lighting + frame | `UNCHANGED` | `MAJORITY_AGREE` | `INSUFFICIENT_EVIDENCE` (“No image data provided”) | No | `0xd19b8eb9cc050f29a02b5f2da8d548ba8d8e012335d5f785af081ed67ea5a872` |
| MOV-SYN-02 — viewpoint | `UNCHANGED` | `MAJORITY_AGREE` | `UNCHANGED` | Yes | `0x0187e8230d9d6c78a0a3fd79f2280b2bd6565fbf28ec7e52da61c2dde9e268c6` |
| MOV-SYN-03 — pre-existing crack | `PRE_EXISTING` | `MAJORITY_AGREE` | `UNCHANGED` | No | `0x13441ccd97e95a1410fc6a509a827f4de53d138237eb133a61757180fdd756eb` |
| MOV-SYN-04 — new crack | `NEW_DAMAGE` | `MAJORITY_AGREE` | `NEW_DAMAGE` | Yes | `0x4c63c3f13155516a71e9da094d6577f51eb21023d84df1a0d74328a89ca4f2b5` |
| MOV-SYN-05 — new stain | `NEW_DAMAGE` | `MAJORITY_AGREE` | `NEW_DAMAGE` | Yes | `0xe9e000449bd54ec4c6df25aec02ca05b034bd498b703e4f35ac80a2008bcc479` |
| MOV-SYN-06 — worsening | `WORSENED` | `MAJORITY_AGREE` | `WORSENED` | Yes | `0x938e69d4cbca3bb05bb95e53f26c984e11bda0bd1f7a0cae401f13642f4507c5` |
| MOV-SYN-07 — repair patch | `REPAIRED` | `MAJORITY_DISAGREE` | No accepted result | — | `0x06ec053db9b4f25ac10bc1cef9bb23b6c907e16a7805691653d452247b0ccf56` |
| MOV-SYN-08 — occlusion | `INSUFFICIENT_EVIDENCE` | `MAJORITY_DISAGREE` | No accepted result | — | `0xfaccb4abf0bceff3db5da9baf9f8d0f35de8fd6ea65e4e557e5f050d49d5add7` |
| MOV-SYN-09 — cropped area | `INSUFFICIENT_EVIDENCE` | `MAJORITY_DISAGREE` | No accepted result | — | `0xde0a2bc4f787b2d6c73293f50deedd0d98b1cad6aac6a942aebffb3a6d095db0` |
| MOV-SYN-10 — low quality | `INSUFFICIENT_EVIDENCE` | `MAJORITY_AGREE` | `INSUFFICIENT_EVIDENCE` | Yes | `0x0ad8e271717cd5768fb557d33057972f0dd2d5cc084a291b050654d17c5b138e` |
| MOV-SYN-11 — lookalike area | `INSUFFICIENT_EVIDENCE` | `MAJORITY_DISAGREE` | No accepted result | — | `0x256448564ad0b9a6fd08df5b5090e33379bfcfdbfd079d74b4ce017f3e0eecc9` |
| MOV-SYN-12 — ambiguous mark | `INSUFFICIENT_EVIDENCE` | `MAJORITY_AGREE` | `WORSENED` | No | `0x3eec8df0ed2e260a69d3caaefbb40eb0c53bb32abc0430ba93edf04af4782f9e` |
| MOV-SYN-13 — image-text injection | `PRE_EXISTING` | `MAJORITY_AGREE` | `UNCHANGED` | No | `0xd82205cb8794926a91a2aa8d5f85eb8f5a0396bcf562361fb9894c57d9b04740` |
| MOV-SYN-14 — shadow confounder | `UNCHANGED` | `MAJORITY_AGREE` | `NEW_DAMAGE` | No | `0x1c91ce5dbe84dad56e5236bc97d90bfb5473cfadb9fb92de60fb5224932e337c` |

All 14 transaction receipts reached `FINALIZED`. Majority agreement was not unanimity: validator votes include `DISAGREE` and `IDLE`. The four disagreements had these vote patterns, in receipt order:

- MOV-SYN-07: AGREE, DISAGREE, IDLE, DISAGREE, DISAGREE.
- MOV-SYN-08: DISAGREE, DISAGREE, IDLE, DISAGREE, AGREE.
- MOV-SYN-09: IDLE, IDLE, DISAGREE, DISAGREE, DISAGREE.
- MOV-SYN-11: AGREE, AGREE, DISAGREE, DISAGREE, DISAGREE.

## Failures and limits observed

- Case 1 passed response and expected-digest validation and reached the `VISION` stage, but the model said “No image data provided” and returned an uncertain result. Other pairs using the same PNG path were interpreted, so this was not a general PNG retrieval failure; the observation points to a vision input/model inconsistency for this execution.
- The ambiguous mark (case 12) produced a confident `WORSENED` result, and the shadow (case 14) produced a false `NEW_DAMAGE` result. The current conservative checks do not prevent all incorrect certainty.
- Repair (case 7), occlusion (case 8), crop mismatch (case 9), and lookalike area (case 11) did not reach a majority agreement. The protocol finalized those calls as `MAJORITY_DISAGREE` and retained the previous accepted state, rather than storing a false classification.
- One initial case 1 write attempt failed before transaction submission while requesting the sender nonce (`eth_getTransactionCount`, connection timeout); the retry was the only submitted case 1 transaction. The case 1 authoritative read initially timed out and succeeded on retry. Case 7’s first receipt lookup ended on `ECONNRESET`; retrying the same transaction returned its finalized majority disagreement. No case was resubmitted after a transaction hash existed.
- The hosted RPC had intermittent connection timeouts/resets. No network switch was made. Successful accepted result metadata showed status 200, PNG MIME, expected size, and exact SHA-256.
- Synthetic labels were fixed before model execution but were manually assigned by one reviewer; the set contains 14 generated pairs only. No real property accuracy, jurisdictional rules, normal-wear decision, or production suitability is established.
- Receipts do not expose each validator’s fetched bytes, HTTP response, or full per-validator model output. The deployed validator function independently fetches both URLs and checks both expected digests before comparing bounded result fields, but the chain’s idle-after-quorum votes do not establish that every selected validator evaluated the images.

## Quality checks

- `genvm-lint` 0.11.0 `lint`: **PASS** (3 checks).
- `genvm-lint check`: **PASS** (SDK validation, 1 view and 1 write method). The Windows console needed `PYTHONIOENCODING=utf-8` because the default CP1252 terminal could not print the linter’s checkmark; rerunning with UTF-8 passed.
- CLI: GenLayer 0.39.1.
- Local direct GenVM test harness: not available in this workspace; no local mock was counted as hosted evidence.
- StudioNet integration: **14/14 finalized receipts and authoritative state checks for all accepted writes and no-write disagreement cases.**
- Final authoritative state is case `MOV-SYN-14`; its accepted JSON is in the manifest and results log.

## Gate

**STAGE 0.6B HOSTED EXPERIMENT: COMPLETE.** The controlled visual pipeline was exercised on StudioNet with independently executed validator comparisons and real consensus outcomes.

**CONTROLLED PROPERTY VISUAL FEASIBILITY: WEAK.** Only 5 of 10 majority-agreed results matched the frozen labels; 4 cases ended in consensus disagreement; ambiguity and shadow cases yielded inappropriate certainty. **REAL-WORLD PROPERTY ACCURACY: NOT VERIFIED. READY FOR STAGE 1: NO.** No canonical MoveOut contract, tenancy/deposit features, or frontend was implemented or deployed. Stop here.

## Stage 0.7 follow-up — observation-first safety proof

Stage 0.7 reused these 14 frozen pairs and expected labels with a separate disposable observation-first contract. Its 15-field observation schema, conservative custom equivalence, hosted receipts, and per-case results are documented in [MOVEOUT_STAGE_0_7_VISUAL_SAFETY.md](MOVEOUT_STAGE_0_7_VISUAL_SAFETY.md) and [`stage07_v2_results.ndjson`](../benchmarks/controlled-property-2026-10/stage07_v2_results.ndjson).

All 14 cases reached an accepted result and 13 recovered receipts confirm majority agreement and finality; case 4's accepted state was authoritatively reread, but its receipt was not recovered. Seven of 14 matched the frozen labels (50%, the same match rate as Stage 0.6B's 5/10 accepted results). Stage 0.7 avoided the Stage 0.6B false `NEW_DAMAGE` result for the shadow case and detected the image-text injection, but the ambiguous-mark case still produced a false `WORSENED` result. The contract therefore remains **WEAK** for condition classification, and Stage 1 remains **NOT READY**. A CLI stderr exception prevented recovery of case 4's transaction hash and votes; that evidence gap is recorded in the Stage 0.7 report.
