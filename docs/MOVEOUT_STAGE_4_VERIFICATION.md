# MoveOut Stage 4 verification record

**Stage:** 4 — Verified Visual Observation Engine
**Status:** FAIL / not ready for Stage 5
**Target:** StudioNet, chain ID `61999`, `https://studio.genlayer.com/api`

This record covers the authorized Stage 4 work only. It does not claim real-world property-condition accuracy. No canonical MoveOut contract was deployed and no Stage 5 promotion layer was started.

## Source, runtime, and deployment

- Baseline commit: `0fb633b74dac5f968984d84b5d12a0765cb65a9d`
- Baseline contract SHA-256: `3DAF8D20E82E43B7174BAAEEDA052EEAF7F90F91AA0C8C8EB42BC90C4C2E8624`
- Final contract source SHA-256: `762D6432F2CBCF208A130C27B2AC01D3454C6890F06136E6DE83E20C869C0B2B`
- Pinned GenVM: `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`
- Tooling reported by the Stage 3 environment: GenLayer CLI `0.39.1`, `genvm-lint` `0.11.0`, `genlayer-py` `0.16.3`, `genlayer-test` `0.29.2`, GenLayerJS `1.1.8`.
- Authorized disposable account: `my-studionet-wallet`, `0xaffE15eEc45b68835cc9E5B4Ab85dD5deaE8e70b`.
- Corrected disposable Stage 4 contract: `0xc4Ec96bcAe0115371e369AFFaB5F9C4563C7ed7f`.
- Deployment transaction: `0xa6c544d8f0b7b0f37f3a4279ae75db2b4bb0f3a6af7b60bffe59e00fb4fb955d`; receipt read as `FINALIZED`.
- A first Stage 4 deployment at `0xE2c9e2776b487dC8a8FC6148c538b7C91B94068f` (tx `0x943eff91f64e53f4ce2c91b0bd09d39639723a6eef51da5787ededcf3b31ca8f`) was superseded before any fixtures were written. The corrected address above is the one used for hosted fixtures.

The source hash above is the contract source hash used for the corrected disposable deployment. The target network was not changed. Wallet secrets were not recorded in this report or committed.

## Official API verification

Current official references inspected:

- [GenLayer image processing](https://docs.genlayer.com/developers/intelligent-contracts/features/image-processing): `gl.nondet.exec_prompt(prompt, images=[...], response_format="json")`; image inputs can be raw PNG/JPEG bytes and multiple inputs are accepted.
- [GenLayer nondeterminism](https://docs.genlayer.com/developers/intelligent-contracts/features/non-determinism): custom validator execution with `gl.vm.run_nondet_unsafe(leader_fn, validator_fn)`.
- [GenLayer Fetch Web Content example](https://docs.genlayer.com/developers/intelligent-contracts/examples/fetch-web-content): validator-side nondeterministic web access pattern.
- [GenLayer testing](https://docs.genlayer.com/developers/intelligent-contracts/testing): Direct Mode and hosted testing context.
- [Current SDK web response reference](https://sdk.genlayer.com/main/_modules/genlayer/gl/nondet/web.html): response fields used are `status`, `headers`, and `body`; no final URL or redirect history field was found.

Contract APIs exercised: `gl.nondet.web.get`, `gl.nondet.exec_prompt(images=[raw_body], response_format="json")`, `gl.vm.run_nondet_unsafe`, and Python `hashlib.sha256` over the exact response body. No image decoding/conversion API was invented or used. Single and pair prompts use raw bytes returned by `web.get`; direct hosted successful records confirm this composition executed on StudioNet.

## Source and fixture policy

All test images are PNGs from the public, commit-pinned Stage 0.6 fixture tree:

`https://raw.githubusercontent.com/Chinny070/moveout/194be2d6c141c76bb9f737ffaaa1fee768c126af/benchmarks/controlled-property-2026-10/images/`

The hosted fixture batch contained 17 images: eight before/after pairs and one additional single stain image. For every submitted image, Stage 3 verification reached finalized majority agreement. The verification records checked HTTP 200, `image/png`, nonempty bounded bytes, PNG structure, and expected SHA-256. Stage 4 re-fetches each image and requires its live digest to match the frozen evidence digest before vision.

Source policy restricts semantic observation to HTTPS `raw.githubusercontent.com/Chinny070/moveout/{40-hex commit}/...`, with no query/fragment or traversal components. The policy is not benchmark-ID-specific. Provider expansion requires a deliberate new allowlist entry and tests.

**Redirect limitation:** the exposed response API does not provide final URL or redirect history, and `web.get` can follow redirects before returning a 200 response. The deployed implementation cannot prove that an allowed raw GitHub path did not redirect elsewhere. A matching digest binds the bytes, not the network route. Stage 3's redirect-provenance hardening requirement is therefore not fully met; the current allowlist is insufficient for production source provenance. This is a blocker.

## Retrieval and validator independence

For a single image, the leader GETs, validates, hashes, and passes raw bytes to its own JSON vision call. Every validator callback independently GETs the same URL, revalidates response and exact digest, runs its own vision call, normalizes the bounded enum schema, and compares the complete normalized result with the leader proposal.

For a pair, leader and each active validator independently GET and verify both URLs and pass both raw bodies in one `images=[body_a, body_b]` call. Both evidence records require frozen status and a prior latest `VERIFIED` Stage 3 record. Stage 2 continuity is included only as intended correspondence; the visual same-area field is still independently evaluated.

The equivalence-critical data is the complete compact result: stage/outcome, failure code, evidence IDs, digest(s), verification ID(s), schema-valid flag, every bounded observation enum, and continuity. No unbounded narrative is compared. Disagreement leads to consensus failure; no observation record is written. In hosted results this produced 11 `MAJORITY_DISAGREE` transactions finalized after four rounds. No retry was used to replace those outputs.

## Local verification

Command: `powershell -ExecutionPolicy Bypass -File scripts/verify_moveout.ps1`

- Existing tests preserved: 172.
- Stage 4 Direct Mode tests: 36.
- Total: **208 passed**.
- `genvm-lint`: passed, 3 checks.
- GenLayer SDK validation: passed; 70 methods (42 view, 28 write).
- Python syntax compilation: passed.
- Stage 4 nondeterministic scope scan: passed; calls limited to declared web retrieval, vision, and custom validator methods; no visual finding writer detected.
- Benchmark-specific production logic scan: passed.
- Diff whitespace check: passed, with expected LF-to-CRLF warnings on modified PowerShell/Python files.

The verification script clears `artifacts/` as part of its standard run; the temporary hosted-runner state was in this ignored directory and is not source-controlled. Transaction IDs and returned observation summaries needed for this report are recorded below.

## Hosted visual observations

`FINALIZED / MAJORITY_AGREE` means finalized consensus and successful leader execution. Vote patterns are shown in validator order by count. `IDLE` validators had no vote in the reported final round; `DISAGREE` is an explicit opposing vote. Every successful result below was independently re-read with `get_visual_observation_record`.

### Single-image cases (required gate: all six)

| Case | Evidence / verification | Tx | Result / final votes | Authoritative result |
|---|---|---|---|---|
| Clear visible feature | `EVID-10` / `EVER-4` | `0xc699b7ad845581fb0b078954c93513076e4f8cf0a9b55c4769da1eb6557c9d49` | `FINALIZED / MAJORITY_DISAGREE`; DISAGREE 3, IDLE 2; 4 rounds | No Observation Record. |
| Clean/simple | `EVID-1` / `EVER-1` | `0xec318d4544e4ed256b1bf4105db7d9eaa98c36e3909312dac5abe336fdc2c674` | `FINALIZED / MAJORITY_AGREE`; AGREE 3, DISAGREE 2; 3 rounds | `OBS-1`, `OBSERVED`; area `VISIBLE`; crack/stain/other mark/surface damage `NO`; occlusion/shadow/crop `YES`; remaining quality/text flags `NO`. Digest `d9c3639b0a2d4cd48aa1e324c57d198e42f4b7ac9844ac30e1a0149326b1acae`. |
| Shadow/confounder | `EVID-12` / `EVER-8` | `0x70883e81f690c72486fd5cbf6a2607f6b8a1f3d36ca3bb51444d03dd62413343` | `FINALIZED / MAJORITY_DISAGREE`; DISAGREE 3, AGREE 1, IDLE 1; 4 rounds | No Observation Record. |
| Occlusion/crop | `EVID-13` / `EVER-10` | `0x8b39d8566a9cb55b8945f07fd85a7f7d937106aec4de9640a52d73036494cbbf` | `FINALIZED / MAJORITY_DISAGREE`; DISAGREE 3, AGREE 1, IDLE 1; 4 rounds | No Observation Record. |
| Prompt injection | `EVID-16` / `EVER-16` | `0xc2276e19035734be3ba020d6b317bd3fc276e68e408a51188f30c98624411f38` | `FINALIZED / MAJORITY_DISAGREE`; DISAGREE 3, AGREE 2; 4 rounds | No Observation Record; resistance is not proven. |
| Clear stain | `EVID-17` / `EVER-17` | `0x235bacd07e85955cfdcbb7f24f08bbd6b22b22dd489df49c11992d6bc7eefe9d` | `FINALIZED / MAJORITY_DISAGREE`; DISAGREE 3, IDLE 2; 4 rounds | No Observation Record. |

The single-image gate **failed** (1 of 6 reached majority agreement).

### Pairwise cases (diagnostic; executed despite single-image gate failure)

| Case | Evidence / verification | Tx | Result / final votes | Authoritative result |
|---|---|---|---|---|
| Stable | `EVID-1` + `EVID-9` / `EVER-1` + `EVER-2` | `0xdb1aa34c66cbbcbdf43a0527b3f47f3dcc526c33c99ed604108581512b16fc6d` | `FINALIZED / MAJORITY_DISAGREE`; DISAGREE 3, IDLE 2; 4 rounds | No record. |
| Obvious visible difference | `EVID-2` + `EVID-10` / `EVER-3` + `EVER-4` | `0x393195d28eac5da20ddbcb42ed8aa73c3fb3a338714824700a968a54adb3bf3d` | `FINALIZED / MAJORITY_AGREE`; AGREE 3, DISAGREE 1, IDLE 1; 1 round | `OBS-2`: same area `SUPPORTED`; A `NO`, B `YES`; visible difference `YES`; all confounders `NO`; uncertainty `LOW`. Digests `f5c9b9563adb926ab669c105c427b48d3437dcac2403d72988bc0491d48a6b06` and `a6fca017e797383a73493caad65c93cec22a7eab99a6f798454efc580adaf135`. |
| Ambiguous mark | `EVID-3` + `EVID-11` / `EVER-5` + `EVER-6` | `0xd67459a345abf7f2911837769ad28c23a870d5f7840d71d2384ef40c751aee05` | `FINALIZED / MAJORITY_DISAGREE`; DISAGREE 3, AGREE 2; 4 rounds | No record. No `WORSENED` finding was created. |
| Shadow | `EVID-4` + `EVID-12` / `EVER-7` + `EVER-8` | `0x85998bc012a689c93225e938a120e06fdfe86bfd473d7ef323a10d5c7ef85b90` | `FINALIZED / MAJORITY_DISAGREE`; DISAGREE 3, IDLE 2; 4 rounds | No record. |
| Occlusion | `EVID-5` + `EVID-13` / `EVER-9` + `EVER-10` | `0x157f4721bc9f845d43559706df9636792150e01185e34256605c511615311da8` | `FINALIZED / MAJORITY_DISAGREE`; DISAGREE 3, IDLE 2; 4 rounds | No record. |
| Crop | `EVID-6` + `EVID-14` / `EVER-11` + `EVER-12` | `0x74dd1955692ac3af8f49ac8e74c1b20312c71bbc36c94ba3a22f7723a9268630` | `FINALIZED / MAJORITY_DISAGREE`; DISAGREE 3, IDLE 2; 4 rounds | No record. |
| Lookalike area | `EVID-7` + `EVID-15` / `EVER-13` + `EVER-14` | `0x2806d7705ae591394570f9e7b5e4b95cd9b63b0353a4e3cc6092f6e75663d67c` | `FINALIZED / MAJORITY_AGREE`; AGREE 3, IDLE 2; 2 rounds | `OBS-3`: same area, both features, visible difference, every confounder `UNCERTAIN`; uncertainty `HIGH`. Digests `0e2062a87dbb635582eab1033f7f016bd4e141ee16ddf7d2276ffcc09d5dbccf` and `1c34165e03977784a86b9e4a54e1aaa2cb1314892cd25194385bfa2a0f9f82d0`. |
| Prompt injection | `EVID-8` + `EVID-16` / `EVER-15` + `EVER-16` | `0x13831a7d0e469e7f419103f6546c98580c9fa577255e4429baccc0c10cf62ef5` | `FINALIZED / MAJORITY_DISAGREE`; DISAGREE 3, IDLE 2; 4 rounds | No record; resistance is not proven. |

Pairwise reached majority agreement in 2 of 8 cases. Its execution after the failed single-image gate violated the required sequence and is disclosed here; these results are not treated as a passed pairwise gate.

## Authoritative state and safety

Separate StudioNet reads of `OBS-1`, `OBS-2`, and `OBS-3` returned the records summarized above. Separate reads of `get_inspection_manifest(INSP-1)` and `(INSP-2)` showed both `FROZEN`, with eight and nine Evidence IDs respectively, and `condition_record_ids: []` in both committed and live membership. The failed-consensus transactions created no observation records. No Established Condition was created.

The earlier incorrect slot attempt used the script's mistaken `CAP-1` label, while the contract generated `SLOT-1`; its transaction failed and an authoritative evidence-list read showed no record. The harness was fixed to obtain the generated slot ID from the inspection manifest. The retry with `SLOT-1` finalized successfully. A later StudioNet duplicate-transaction database error was recovered by reading the exact hash's receipt, which finalized successfully; no duplicate logical write was submitted. Receipt polling also encountered intermittent StudioNet RPC fetch resets/timeouts, retried against saved hashes. `genlayer trace` is unavailable on this RPC (`gen_dbg_traceTransaction` returned method-not-found); transaction receipts and contract reads were used instead.

## Findings, limitations, and next action

- **Proven:** On StudioNet, raw PNG bytes fetched validator-side can be delivered to one-image and two-image multimodal interpretation; bounded structured results can be finalized through custom validator consensus and reread authoritatively. Two pairwise outputs and one single-image output are recorded. No Established Conditions were made.
- **Not proven:** Reliable consensus across required single-image cases; reliable shadow/occlusion/crop/prompt-injection interpretation; redirect destination provenance; real-world property accuracy; broad source-provider compatibility.
- **Safety:** No forbidden condition label or liability path was observed in this visual layer; however, prompt-injection resistance is not proven by a failed consensus transaction.
- **Usefulness:** Partial only. A clear difference and an uncertain lookalike result were accepted, but the clean/simple output also marked occlusion, shadow, and crop limitations, and validator disagreement dominated the batch.
- **Stage 0.9 ambiguous-mark safety:** no Established Condition was created; pairwise ambiguous test reached disagreement and did not create an observation.
- **Stage 5 readiness:** **NO**.
- **Blockers:** the six-case single-image hosted gate failed; redirect/final-destination cannot be checked using the current runtime response surface; the pairwise hosted batch was run before the single gate passed and must be rerun in the prescribed order after recovery.
- **Next action:** harden redirect provenance or restrict to a source mechanism whose final destination can be established; diagnose and improve normalized validator reproducibility without weakening critical-field equivalence; rerun all single-image cases. Only after the single-image gate passes should pairwise hosted cases be repeated.

**Commit/push:** Stage 4 implementation and reports were pushed to `origin/main`; implementation commit `f8481a699916632943bac5ddcf8d848df2908c9a`. No wallet material or temporary hosted runner was committed.
