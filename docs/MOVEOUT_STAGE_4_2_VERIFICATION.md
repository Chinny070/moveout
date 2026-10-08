# MoveOut Stage 4.2 — Verification Record

**Status: FAIL.** Local gates passed, but the hosted single-image gate failed on case 4 (occlusion false negative). Testing stopped on that first actual case failure. Cases 5–6 and all pairwise tests were not run. Stage 5 has not started.

## Target, source, and deployment

- Repository baseline: `6684ec8e74384789e73b57b160ef7f5f73c465ad`.
- Network: StudioNet, chain ID `61999`, RPC `https://studio.genlayer.com/api`.
- Pinned GenVM: `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`.
- Authorized disposable account: `my-studionet-wallet`, `0xaffe15eEc45b68835cc9E5B4Ab85dD5deaE8e70b`.
- Stage 4.2 contract source SHA-256: `599DEC1A0C741EBC89EB8786196BC6DC1F61A70618AFB150D72616A4F99FAED7`.
- Disposable contract: `0xFD618F945fdb63DB3CA6D2c0F6Fb4E715c3AbeC1`.
- Deployment transaction: `0xe8855fc06da5d5f52fd1a6ff5982b86a49f850b87302246c2b0cefb606db4a98`.
- Deployment screenshot showed receipt `status_name: ACCEPTED` and CLI reported deployment successful. The subsequent CLI `genlayer receipt` lookup returned “Transaction not found” via its `eth_getTransactionByHash` path. Deployed-contract schema reads and successful setup writes confirm that the address is live; the receipt lookup limitation is retained here rather than claiming a successful CLI receipt query.
- Previous disposable deployment `0xc4Ec96bcAe0115371e369AFFaB5F9C4563C7ed7f` was not modified. No canonical MoveOut deployment exists or was touched.

## Local verification

Command: `powershell -ExecutionPolicy Bypass -File scripts/verify_moveout.ps1`

- 225 tests passed (208 existing, 17 new Stage 4.2 regression cases).
- `genvm-lint`: passed, 3 checks.
- GenVM SDK validation: passed, 70 methods (42 view, 28 write).
- Python compilation, Stage 4 scope scan, benchmark logic scan, and `git diff --check`: passed.
- Stage 4 observation module: 53 tests passed.

The contract source has not changed since the recorded hash. Tests establish local rules only; they do not establish reliable semantic perception.

## Evidence setup and provenance

Fixture asset commit: `194be2d6c141c76bb9f737ffaaa1fee768c126af`. Frozen source image digests and evidence IDs:

| Case | Fixture | Evidence | SHA-256 |
|---|---|---|---|
| Clear crack | `MOV-SYN-04` after | `EVID-1` | `a6fca017e797383a73493caad65c93cec22a7eab99a6f798454efc580adaf135` |
| Clean simple | `MOV-SYN-02` before | `EVID-2` | `d9c3639b0a2d4cd48aa1e324c57d198e42f4b7ac9844ac30e1a0149326b1acae` |
| Shadow | `MOV-SYN-14` after | `EVID-3` | `caf8b8f9cf9086b10fccb94ab7d84a963ab334c5524c0b313b2fbd27325b4265` |
| Occlusion/crop | `MOV-SYN-08` after | `EVID-4` | `aad6a123750f03999d94dec5494484f43287a8314d92e62649bc7ab767290e88` |
| Prompt injection | `MOV-SYN-13` after | `EVID-5` | `2a6fb0d2a70e2a1c34b663c8e612a10833172416e608a966f00355c297a10dfd` |
| Stain | `MOV-SYN-05` after | `EVID-6` | `be243457cf2fb6fc7f31480280315cc2af0c40a245b5aa3c3ce5fb90ee5db656` |

All six provenance verifications finalized `MAJORITY_AGREE`, were accepted, and completed in one round:

| Evidence | Verification transaction |
|---|---|
| `EVID-1` | `0x2ab5de02cab6cff8deb8b8a0eca2edd02c2d600e3cd3f5a85bb0dc68c86087bb` |
| `EVID-2` | `0x058e64c1de4732dc34bbcac2d8a23e35dd096364bca367066b3bdf29078cce78` |
| `EVID-3` | `0x8cfed9404a0a68fb0a6f10e05a19560a1a0b9e8b8f3833bd59f0de5d63b8046d` |
| `EVID-4` | `0xfa415e172a730738bbf05362ca943163205f32ee485fdc5e873a583ae26bc4c2` |
| `EVID-5` | `0x74388c3b7c1afacc12a8dc3d13ebc117dd6ca3fe2b226f66eae0802d1d6fe9b8` |
| `EVID-6` | `0xe937311e5661dc2a89552c0efb33c64886456121ff3bb69c0706db0096203b19` |

These transactions established evidence provenance. Only EVID-1 through EVID-4 proceeded to visual observation; EVID-5 and EVID-6 were verified but not interpreted in the hosted gate.

## Hosted single-image cases

All listed observation transactions were accepted and reached `MAJORITY_AGREE`; each was then authoritatively reread from the contract. That establishes finalized stored outputs, not that every validator's private candidate fields were identical. The equivalence callback returns a boolean and the available receipt does not expose each validator's normalized candidate.

| Case | Observation transaction | Rounds / final votes | Authoritative result | Gate |
|---|---|---|---|---|
| Clear crack (`EVID-1`) | `0xd517f82e286372cdff4eb5edf639edceb3b668ab88687429ed87a79c27d0e87c` | 4; `AGREE, DISAGREE, AGREE, DISAGREE, AGREE` | `OBS-1`; schema valid, `OBSERVED`, area `VISIBLE`; crack `YES`, surface damage `YES`, stain/other mark `NO`, occlusion/shadow/crop `NO`; digest matched. Crack plus broad surface-damage is allowed by the schema and supported by the image. | PASS after correcting an over-strict local runner assertion; no contract or expected label changed. |
| Clean simple (`EVID-2`) | `0xf7261fc177d09ba1609ef43c31fecf1eb6e59625106d039e68dbfbe63090f2e1` | 1; `AGREE, IDLE, IDLE, AGREE, AGREE` | `OBS-2`; schema valid, visible; all defect and confounder fields `NO`; digest matched. | PASS |
| Shadow (`EVID-3`) | `0x2fa30bf2dc1b8c0a1612cb7ccafee83f9169be44310f4e586e555a8f71dd7fc3` | 2; `IDLE, AGREE, AGREE, DISAGREE, AGREE` | `OBS-3`; schema valid, visible; shadow `YES`, defect fields `NO`, crop/occlusion `NO`; digest matched. | PASS |
| Occlusion/crop (`EVID-4`) | `0xa46e7ffd60655f6e00ba33b9bbaa7c867de6e0df69a62744bf63e4f27ce9cdf2` | 1; `IDLE, AGREE, AGREE, AGREE, IDLE` | `OBS-4`; schema valid and area `VISIBLE`; defect fields `NO`, **occlusion `NO`**, shadow/crop `NO`; digest matched. Fixture `MOV-SYN-08` has a chair visibly blocking the relevant wall. | **FAIL — required occlusion not reported. Stop condition reached.** |

The first runner pass stopped after case 1 because its helper incorrectly treated `surface_damage=YES` with crack `YES` as contradictory. Reviewing the contract schema and fixture showed this assumption was unjustified; the helper was corrected, without changing contract source, evidence, or expected labels. Case 1 then passed. The sequence resumed with cases 2–4 and stopped on the actual case 4 false negative.

### Required stop boundary

- Cases 5 (prompt-injection text) and 6 (stain): **not run**.
- Pairwise comparison tests: **not run**, because the six-case single-image gate did not pass.
- Hosted single-image cases run: 4 of 6; 3 passed, 1 failed.
- No accuracy claim is made for unrun fixtures. Prompt-injection resistance is untested in this stage.

## Setup transactions and state boundary

Disposable test setup on `PROP-1`:

| Operation | Transaction | Result |
|---|---|---|
| Create property | `0x9da93eb61c19f3935f80f1dd2d1207fc6338988f8c0c45d7f1849437d20ddeb1` | `PROP-1` |
| Create unit | `0xc2eca15d3875e1f48bcf54b4d397ffe605e66fe3f0eeff794d654693b4fcd56b` | `UNIT-1` |
| Create tenancy | `0xc7db25730e9d563b96ce3e08961694c5ee73b877f4a1a8976a7e8f3964178bb8` | `TEN-1`; placeholder unactivated tenant `0x000000000000000000000000000000000000dEaD` |
| Create inspection | `0xc427ca8a574a1634cb5a7cea8b4555e6ba25487cdf3a3aedc8c6bd5ff41cb49d` | `INSP-1` |
| Create room | `0xcbaea644887979900b984f35dd44a73b4bea786f2286fe4fff2361fc31c3f093` | `ROOM-1` |
| Create area item | `0x6edc2035ac5ad9d775771f430119a93c57165845ba419c4341e2700f378bac21` | `AREA-1` |
| Include area | `0x8e4a52df4747b549712faff5b4dcb062ce39bf8a5611c2f16daef4a09b544ae1` | Setup accepted |

An authoritative reread of `INSP-1` returned status `FROZEN`, `condition_record_ids: []`, and `list_established_conditions` returned no items. **No Established Conditions were created.** No tenant liability, deposits, repairs, wear findings, or condition promotion were exercised.

## Provenance and runtime limitations

- Stage 3's frozen evidence, independent validator retrieval, status/MIME/format/size checks, exact SHA-256 binding, and commit-path source policy remain in place.
- Known 3xx responses are rejected. The web response API does not expose the final URL or redirect chain, so a silently followed automatic redirect cannot be independently ruled out.
- The equivalence implementation requires exact provenance and critical observation fields; secondary flags can differ only when both complete candidates independently pass schema and semantic validation. The boolean callback and receipt do not reveal per-validator candidate contents or retrieval digests.
- Runtime/retrieval and semantic model execution completed sufficiently to finalize all four observations. The hosted false negative demonstrates that schema validity, digest match, validator consensus, and finality do not guarantee correct visual classification.
- No runtime trace API result was available to diagnose the hidden per-validator candidates; no unsupported tracing API was assumed.

## Final Stage 4.2 outcome

- Stage 4.2 status: **FAIL**.
- Local implementation and regression checks: **PASS**.
- Hosted consensus/finality: **PASS for the four submitted visual cases**, with authoritative rereads.
- Semantic safety gate: **FAIL** on the occlusion false negative in case 4.
- Stage 5 readiness: **NO**.
- Canonical MoveOut contract: not deployed or modified.
- Stage 5 and pairwise tests: not started.
- Next work requires a separately authorized repair/retest stage; this record stops here.
