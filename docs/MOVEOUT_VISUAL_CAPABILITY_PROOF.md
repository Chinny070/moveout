# MoveOut Visual Capability Proof — Stage 0.5

> **Stage 0.6B addendum:** The 14-pair controlled synthetic benchmark has now run on StudioNet. All 14 transactions finalized; 10 reached `MAJORITY_AGREE` and 4 `MAJORITY_DISAGREE`. Five of the ten accepted classifications matched frozen labels. This result is weak feasibility evidence and does not establish real-world property accuracy. The Stage 0.5 proof below remains unchanged. See [Stage 0.6B results](MOVEOUT_PROPERTY_VISUAL_BENCHMARK.md) and [dataset manifest](MOVEOUT_VISUAL_BENCHMARK_DATASET.md).

**Stage:** Stage 0.5 only  
**Current result:** Direct image-byte mechanism **VERIFIED** for a two-PNG comparison and single-image PNG/JPEG vision on StudioNet. **MoveOut damage-condition policy remains unverified.**  
**Target:** `studionet`, chain ID `61999`, RPC `https://studio.genlayer.com/api`  
**Signer:** `my-studionet-wallet` — `0xaffe15eec45b68835cc9e5b4ab85dd5deae8e70b`  
**Scope:** Disposable visual capability contracts and hosted proof transactions only. No canonical MoveOut contract or Stage 1 work was created.

## Gate decision

# OVERALL MOVEOUT DAMAGE-DECISION POLICY: REQUIRES MORE PROOF

The original screenshot-mode proof remains unchanged: StudioNet finalized a two-screenshot red-to-blue comparison using `gl.nondet.web.render(..., mode="screenshot")` and comparative equivalence. The earlier v3 direct-byte attempt returned `UNCLEAR/LOW`, but it had no response digest/signature telemetry and used `prompt_comparative`; that result did not establish an input-type limitation.

The Stage 0.5 follow-up below now proves the direct-byte mechanism end to end for a two-PNG visual comparison: `web.get` response bytes were hashed, passed together as two vision inputs, independently retrieved and interpreted in leader/validator executions, and finalized with majority consensus and an authoritative state reread. This verifies the *transport and consensus capability*. It does not validate MoveOut's subjective damage/condition criteria, borderline-photo uncertainty behavior, or all JPEG decoding/provider combinations. Do not treat the synthetic color-card result as a completed MoveOut-specific accuracy study.

## Final candidate, runtime, and deployed source

The originally authorized candidate’s expected hash matched before deployment. Two small disposable diagnostic revisions were needed after actual hosted failures:

| Candidate | SHA-256 | Change / outcome |
|---|---|---|
| v1 `contracts/visual_capability_proof.py` | `0ADEF64D58589315E97A3339E657E61F68949F0ECE9E26D33EE964488128BE19` | Original authorized source; its broad exception fallback obscured whether screenshot retrieval or JSON serialization had failed. |
| v2 `contracts/visual_capability_proof_v2.py` | `21EC2C5E3D1DB0D163D130FA0E8A5052AB86870E75095D161A3B779EB8DAF56C` | Added a direct-image GET path with status/MIME/body checks and bounded diagnostic output. Hosted receipt exposed a missing `json` import in this diagnostic revision. |
| **v3 `contracts/visual_capability_proof_v3.py`** | **`1C45914328F79E3578EA74873452BA3676318DB648231CBF28B466B97A2865BF`** | v2 plus the required `import json`; used for the successful screenshot, direct-image, and failure tests. |

The v3 candidate is pinned to `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`. `genlayer code` retrieved its deployed source. After newline normalization, deployed source SHA-256 equaled local source SHA-256: `ADE8CA32A57AC1A6FC43B696B8CCF62EFC2883C4DBC2C767D6B831647F9BA339` for both. The deployed v3 schema contains `compare_screenshots`, `compare_direct_images`, and `get_result`.

### Lint and tests

- GenLayer CLI: `0.39.1`.
- GenVM Linter: `0.11.0`.
- v1 `genvm-lint lint` and `check`: PASS.
- v2 `genvm-lint lint` and `check`: PASS, although runtime execution found the missing `json` import that static checks did not flag.
- v3 `genvm-lint lint` and `check`: PASS (3 lint checks; validation passed; 3 methods).
- Direct/local tests: no project test harness is present, and CLI `0.39.1` has no `test` command. No local mock was counted as proof.
- Separate integration test suite: not present. The hosted StudioNet transactions below are the integration evidence.
- `genlayer trace` attempted on StudioNet returned `Method not found: gen_dbg_traceTransaction`. Transaction receipts were used for execution and consensus evidence instead.

## Deployment record

| Version | Deployment transaction | Contract address | Receipt |
|---|---|---|---|
| v1 | `0x98de59dace79d8ec7732c8d295a0d1c40f1f76b2475559ca336ca7518f84d476` | `0xba0C802EC9C3bde5DDC67D2D0530D9793B370Cb4` | FINALIZED; `MAJORITY_AGREE`, 5 validator votes |
| v2 | `0xefe069d2fda1278009ff3a830a1b68d7be7ed596f40c02ba70888aa65facdce6` | `0xd34D545530d13D0749c1AD969a8FE6A7ff1eE58c` | FINALIZED; `MAJORITY_AGREE`; schema retrieved |
| **v3** | **`0xfc7cadaadd7aaeace206c0103d441b1b01728dca0ac177075e1966696a31de11`** | **`0x75203Bb5aca4b341AE59531618042E548fD20400`** | **FINALIZED; `MAJORITY_AGREE`; schema and deployed code verified** |

All deployments used the requested StudioNet and signer. No other wallet or network was used.

## Sources and retrieval

Source A and Source B used the public `placehold.co` image generator. The URL parameters make the visual content deterministic for this test, although no image-content hash was captured on-chain.

- **Red:** `https://placehold.co/256x256/ff0000/ffffff.png?text=RED`
- **Blue:** `https://placehold.co/256x256/0000ff/ffffff.png?text=BLUE`
- Host for both: `placehold.co`.
- Screenshot retrieval: `gl.nondet.web.render(url, mode="screenshot")` returns the GenLayer image object.
- Direct retrieval: `gl.nondet.web.get(url)` returns a response; v3 checks status `200`, `Content-Type` beginning `image/`, and non-empty body, then passes each body byte sequence to `images=[image_a, image_b]`.
- The successful direct test passed the code’s status/MIME/non-empty gates and reached a structured LLM response. The exact MIME header values were not persisted by this proof contract.

## Prompt and equivalence

The prompt compares two ordered images, requests bounded JSON fields `comparison`, `observations`, and `confidence`, limits comparison to visible pixels, and tells the model to use `UNCLEAR`/`LOW` for unrelated, ambiguous, inaccessible, or unreliable evidence. The contract normalizes the result to `CHANGED | UNCHANGED | UNCLEAR`, `HIGH | MEDIUM | LOW`, and at most four observations of 120 characters each. Retrieval/model exceptions become explicit `UNCLEAR`/`LOW` results with a bounded error observation.

The contract uses `gl.eq_principle.prompt_comparative(analyze_pair, principle=...)`:

- Leader: retrieves both URLs with the selected path, passes both images together to one multimodal prompt, and proposes the normalized JSON result.
- Validator: comparative equivalence reruns the supplied `analyze_pair` independently, which in v3 retrieves both URLs again and evaluates both images; it compares the leader and validator outputs under the written principle.
- Agreement: the `comparison` field must match exactly; confidence may differ by one adjacent level only if comparison matches; CHANGED and UNCHANGED are never equivalent; observations must be grounded in the pair. Missing/ambiguous evidence should resolve UNCLEAR/LOW.
- Disagreement: validator vote is DISAGREE; Optimistic Democracy continues/rotates as needed, and the accepted state follows consensus. The low-contrast test shows a majority can accept a confident outcome even with two dissenting votes.

This proves comparative equivalence participated in actual hosted consensus. It does **not** prove every selected validator fetched both sources: receipts show validators that agreed and validators that were idle after quorum. For the successful screenshot round, three validators agreed and two were idle. StudioNet did not expose per-validator image payloads or URL-fetch logs through its trace endpoint, so retrieval-by-validator is supported by the deployed callable and comparative execution semantics, not independently itemized in receipts.

## Hosted visual and failure tests

All listed transaction receipts reached `FINALIZED`; each result below was reread using `get_result()` after its write.

| Test | Transaction | Evidence / result | Outcome |
|---|---|---|---|
| Original v1 red/blue screenshot attempt | `0x4d3448b4006296fd4ca2a73d8d115427580e652582957c23e090a278f0c56ef2` | Finalized consensus, but v1’s catch-all stored `UNCLEAR/LOW`; this did not establish a visual comparison. An explicit finalize call first returned `'dict' object has no attribute args'`; subsequent receipt confirmed FINALIZED. | Superseded by v3 test |
| v2 red/blue diagnostic screenshot | `0xac22d85b646384249f8d4cef7de7a2303d5b0f77476e0abb641f6539a92e68c7` | Finalized with leader execution error. Receipt traceback: `NameError: name 'json' is not defined`; the exception handler also failed for the same reason. | Failed proof-code revision |
| **A. Valid red/blue screenshots (v3)** | **`0x35076c2482089448f7570c7f182eeb69ed8450b5bddc09997e75bae1350e4ffd`** | Finalized, `MAJORITY_AGREE`. Leader execution SUCCESS. Final round: 3 AGREE, 2 IDLE; transaction had two consensus rounds. Authoritative reread: `{"comparison":"CHANGED","confidence":"HIGH","observations":["The color of the central square changed from red to blue.","The text inside the square changed from 'RED' to 'BLUE'."]}` | **Screenshot visual path passed** |
| B. Initial v3 valid red/blue direct image GET | `0x762840bd6a6aeeb6004bd154463386604fb7e5b73e9f2524d3e69d0a901b9534` | Finalized, `MAJORITY_AGREE`; three validators agreed, two idle. GET status/MIME/body guards passed; raw response bodies reached `exec_prompt(images=[...])`. Authoritative reread: `UNCLEAR`, `LOW`, empty observations. | At the time, raw semantic comparison was not established; superseded by Stage 0.5 v5 raw-byte pair proof below |
| C. Unavailable source | `0x63111653436f9d83c1ab902de3b87ecec49c248fee92808a6e6a9e0c6d2b9bdd` | Source A used `.invalid` TLD. Runtime error `TLD_FORBIDDEN`; finalized consensus. Authoritative reread: `UNCLEAR`/`LOW`, bounded `evidence_error:NondetException...` observation. | Fail-closed behavior passed |
| D. Invalid/non-image source | `0x99cf5b9f7accefb8b10d0b06034f83d2e11f0f5e370a1cdbcc2362018f7bedee` | Direct GET of `https://example.com/` returned HTML. Finalized consensus. Authoritative reread: `UNCLEAR`/`LOW`, observation `not_image_mime:text/html`. | MIME rejection and fail-closed behavior passed |
| E. Ambiguous/low-contrast pair | `0x78d031169cee5e9ada103862df4d7863d487da4aab6692081a7bcf1f49d1f96c` | White versus `#fefefe` placeholder squares, both labeled BLANK. Finalized majority consensus; 3 validators agreed and 2 disagreed. Authoritative reread: `UNCHANGED`/`HIGH`, observations say no visible differences. | **Uncertainty handling not demonstrated**; outcome may be visually reasonable, but confidence remained high amid validator disagreement |

The screenshot test’s expected visual relationship was manually apparent: a red labeled square versus a blue labeled square. The authoritative result matches that relationship. The initial v3 direct-byte test did not return that useful semantic result despite passing retrieval guards; the later v5 raw-byte pair test below did. The near-white screenshot case did not return UNCLEAR and had validator disagreement, so MoveOut policy must not rely on the generic prompt to conservatively classify borderline evidence.

## Mutable-source test

No same-URL content mutation test was run in the original screenshot proof. The Stage 0.5 follow-up below hashes direct image bytes and has agreeing v5 validators require a matching digest, but does not guarantee that a URL remains unchanged later or that all eligible validators execute before quorum.

## Runtime errors and execution constraints

- v2 runtime error: missing `json` import in both normal serialization and its exception handler. A receipt exposed the full `NameError` traceback.
- StudioNet trace RPC: `gen_dbg_traceTransaction` is unavailable (`Method not found`), limiting per-validator execution diagnosis.
- StudioNet RPC connectivity was intermittent: multiple read/write attempts failed before transaction submission with `ECONNRESET`, connection timeouts, or DNS failures. Three direct-path attempts failed at `eth_getTransactionCount` and created no transaction; a later direct test succeeded. One initial failure-test call was rejected because automatic permission review timed out; retry succeeded.
- `genlayer finalize` on the first screenshot transaction returned an internal `'dict' object has no attribute args'` RPC error, but a later receipt showed the transaction finalized.
- CLI wallet diagnosis: `genlayer account unlock` succeeded in the embedded terminal running as `USERpc`, while the sandboxed command process ran as `achinnys\codexsandboxoffline`. Windows Credential Manager is per-user; the sandbox process could not see the cached credential, which caused repeated password prompts. Running the already-authorized deploy in the host-user context resolved this. No password was requested in chat.

## Transaction inventory

**Submitted hosted transactions: 10 total** — three disposable deployments and seven write tests listed above. No production MoveOut transaction was submitted.

Pre-submission failures with no transaction ID:

- Three direct-image test attempts failed to reach `eth_getTransactionCount` due to intermittent RPC connection resets/timeouts.
- One first unavailable-source test attempt did not launch because auto-review timed out; retry launched successfully.
- Initial local signer creation had earlier failed with sandbox EPERM when trying to write a new keystore. This authorization follow-up used only the authorized existing wallet.

## Initial proof limitations (updated by Stage 0.5 direct-byte follow-up below)

- Screenshot mode is experimentally supported on StudioNet for this public two-image comparison under comparative validator consensus.
- The initial v3 direct image GET resolved UNCLEAR/LOW. That single result was insufficient; the later v5 hosted proof below verified a raw PNG pair with independent validator execution and consensus.
- Unavailable and HTML responses fail closed. The ambiguous low-contrast example did not resolve UNCLEAR and validators split; strengthen the contract’s evidence-quality criteria and rerun the ambiguous case before treating the visual core as production-ready.
- Receipts confirm consensus votes and finality but do not expose a per-validator image retrieval transcript. The trace endpoint is unavailable on StudioNet.
- A controlled mutable-source test remains outstanding; digest equality mitigates same-transaction cross-validator drift but not future URL changes.
- No separate direct/local or scripted integration harness exists in the workspace. The actual StudioNet transactions are the only integration proof.

**Ready for MoveOut Stage 1:** NO. Stop at Stage 0.5 and wait for review. Do not start Stage 1.

## Stage 0.5 direct-image-byte investigation (2026-10-05)

### Gate result

**DIRECT IMAGE BYTE PATH: VERIFIED** for the demonstrated StudioNet path: two public PNG bodies fetched with `gl.nondet.web.get`, checked and SHA-256 fingerprinted, submitted together as raw `bytes` to `gl.nondet.exec_prompt(images=[body_a, body_b])`, independently re-fetched and vision-evaluated by validators, accepted by consensus, finalized, and authoritatively reread. Single-image PNG and JPEG byte-to-vision were also exercised. JPEG pair comparison and MoveOut-specific damage classification were not exercised.

The exact supported API contract is documented in the current GenLayer SDK: `gl.nondet.web.get(url, *, headers=...) -> Response`; `Response(status: int, headers: dict[str, bytes], body: bytes | None)`; `gl.nondet.exec_prompt(..., images: Sequence[bytes | Image] | None)`; and the image guide states a maximum of two images per prompt. The official image guide explicitly permits raw PNG/JPEG bytes. References: [GenLayer Image Processing](https://docs.genlayer.com/developers/intelligent-contracts/features/image-processing), [GenLayer Web Access](https://docs.genlayer.com/developers/intelligent-contracts/features/web-access), [GenLayer Equivalence Principle](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle), [SDK web module source/reference](https://sdk.genlayer.com/main/_modules/genlayer/gl/nondet/web.html), [SDK API signatures (v0.2.9)](https://sdk.genlayer.com/v0.2.9/api/genlayer.html).

The earlier v3 red/blue raw result's most precise diagnosis is: **not fetch or MIME validation** (the prior write passed its HTTP 200, image MIME, and nonempty-body gates), and **not transaction consensus failure** (it finalized and stored the explicit `UNCLEAR/LOW` answer). It failed at the **vision interpretation/answer-normalization layer**: the stored model result was unclear or normalized to the unclear fallback. The prior contract/receipt did not preserve raw model output or a trace, so we cannot distinguish a genuine model `UNCLEAR` from a malformed/missing response field that the code normalized to `UNCLEAR`. Follow-up success with a decision-field custom validator proves the raw-byte composition is supported; it does not retroactively reveal the exact hidden v3 model response.

### Disposable v4/v5 proof sources

No existing screenshot candidate was changed. The two new compatibility contracts are diagnostics only:

| Source | SHA-256 | Hosted use |
|---|---|---|
| [`contracts/visual_capability_proof_v4.py`](../contracts/visual_capability_proof_v4.py) | `B956DEC0A879287544FD34F4417152A6E892964430E69415FA0F248423C440AB` | Raw metadata/signature/hash + one-image prompt using `prompt_comparative`; isolated a validator disagreement. |
| [`contracts/visual_capability_proof_v5.py`](../contracts/visual_capability_proof_v5.py) | `87C4BBD821AF95FBACEC12932875969B25FC3C4EA795443C81FE153EABCF302F` | Raw metadata/hash + one/two-image prompts + custom `run_nondet_unsafe` validator. |

Both declare the same pinned dependency already used by v3: `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`. GenLayer CLI was `0.39.1`; GenVM Linter was `0.11.0`. v4 and v5 both passed `genvm-lint lint` (3 checks) and `genvm-lint check` (SDK validation). v5 deployed successfully on the requested StudioNet 61999 only. No local mock was treated as evidence.

The workspace has no direct/local contract test harness, and the installed CLI has no `test` command; no local mock test was run. The direct-vision and failure evidence below comes from hosted StudioNet transactions, not local simulation.

### Exact retrieval and hashing observations

The deployed probe observed the documented response object fields directly. On successful image GETs, `status` was integer `200`; `headers["content-type"]` was bytes and decoded to the values below; `body` was nonempty and behaved as raw bytes (slicing, byte-index conversion, length, SHA-256, and `images=[body]` all ran in GenVM). The contract recorded the first 16 bytes as hex and `hashlib.sha256(body).hexdigest()`.

| Resource | Final response | Size | First bytes (hex) | SHA-256 |
|---|---:|---:|---|---|
| Red PNG, `https://placehold.co/256x256/ff0000/ffffff.png?text=RED` | 200, `image/png` | 2,941 bytes | `89504e470d0a1a0a0000000d49484452` | `aac650a6a42c2bbaa731c795a6ff762c64a8bf86df4d1c4106563a96959c82ed` |
| Blue PNG, `https://placehold.co/256x256/0000ff/ffffff.png?text=BLUE` | 200, `image/png` | 2,794 bytes | `89504e470d0a1a0a0000000d49484452` | `1a0a5a60f0d44471a07beb5c36f8a3841cfb259ae2f1e4644a5dfac6c2e6ff1f` |
| Placeholder JPEG, `https://placehold.co/256x256/ff0000/ffffff.jpg?text=RED` | 200, `image/jpeg` | 4,024 bytes | `ffd8ffdb004300060405060504060605` | `98b10d400588854e69b3f693b7f5daacac473314bdb864d9bd8f53cf1c6bebb8` |
| Unsplash JPEG, `https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=256&q=80&fm=jpg` | 200, `image/jpeg` | 9,966 bytes | `ffd8ffe000104a464946000101010048` | `42f8199442e87199e2226c6489151e2aa998a2b269ee06c4f034f9293b59a134` |
| HTML, `https://example.com/` | 200, `text/html; charset=utf-8` | 577 bytes | `3c21646f63747970652068746d6c3e3c` | `25ddf2c883e0d1958ea971d279a7e4f0fd446724ee3db7db19dadabd4a62e484` |

`hashlib.sha256` was not assumed from type compatibility; it ran in the hosted GenVM read/write executions and returned the stable digests above. This binds a digest to the exact body retrieved within each execution. In the custom validator tests, a validator's vote to agree required its own retrieval's digest(s) to equal the leader proposal digest(s), in addition to matching the vision decision. That is meaningful provenance evidence for the bytes accepted during that transaction.

The `Response` API does not expose a redirect chain or final effective URL field. A safe redirect test used `https://httpbin.org/redirect-to?url=https%3A%2F%2Fplacehold.co%2F256x256%2Fff0000%2Fffffff.png%3Ftext%3DRED&status_code=302`. `web.get` returned the final red PNG response (200, `image/png`, 2,941 bytes, same digest as direct retrieval), so the hosted HTTP stack followed that redirect. Because the API does not report redirect history/final URL, a production contract cannot bind that information from this response object alone. The original requested URL can be stored, but redirect destination provenance remains a limitation.

### Validator implementation and interpretation

v4 initially used `gl.eq_principle.prompt_comparative` around the raw-byte one-image function. The leader execution succeeded, but the transaction ended **UNDETERMINED** after three validator DISAGREE votes and two IDLE votes; there was no committed state to reread. The receipt did not expose intermediate model responses. That showed that a generic comparative template can fail to reach agreement here, but did not show that byte input failed.

v5 follows the official custom validator pattern (`gl.vm.run_nondet_unsafe(leader_fn, validator_fn)`). The leader retrieves its input body/bodies, records status/MIME/length/prefix/digest, validates response metadata, passes raw bytes to vision, and proposes bounded structured output. Each validating execution calls the same fetch-and-interpret function itself, which retrieves both URLs again where applicable and makes its own `exec_prompt` call. The validator checks the stage, requires raw SHA-256 digest(s) to match the leader proposal, and compares the single-image boolean or pair comparison enum. The accepted leader result is stored; validators' intermediate answers are not separately stored. If the digest or decision differs, the validator rejects; the protocol may rotate the leader and retry. A failed URL/image becomes an explicit structured `OTHER`/`RESPONSE_VALIDATION` or `UNCLEAR` path rather than a fabricated positive result.

Consensus receipts still do not expose per-validator URL payloads, image bytes, model output, or complete traces (`genlayer trace` for StudioNet previously returned method-not-found). The validator independence evidence is therefore the deployed custom validator code plus actual agree/disagree votes and the accepted digest/decision checks—not an auditor-visible per-validator network transcript. For accepted decisions, validators that voted AGREE executed the checks encoded in v5; IDLE validators after quorum and validators that disagreed are not evidence of universal participation.

### Hosted StudioNet test record

All hosted deployment and write transactions below used `studionet`, chain `61999`, RPC `https://studio.genlayer.com/api`, and the already-authorized `my-studionet-wallet` (`0xaffe15eec45b68835cc9e5b4ab85dd5deae8e70b`). Each accepted write was finalized and followed by a `get_result()` read, unless stated as undetermined. Test-only deployments: v4 tx `0xbc87c10adda56852d8b99c6b9a742dcc96186a4a96902d4b619eb1b1fa5e4524`, address `0x90e5559c34dAc280bf41F4Ec47056124dd6b6F20`; v5 tx `0xdfd26062d92127262a9db5d5cb9a526818fe5e9d5ff4b151ce351c6755d86ff8`, address `0xaCC87512DD361EEcf329E85762C67194ae436C9a`. Both deployment receipts were accepted with majority agreement.

| Test | Transaction | Consensus/finality | Authoritative result / conclusion |
|---|---|---|---|
| v4 raw red PNG metadata | `0x06d22b23412370bd74cefede1ce457714e26a45e6186f1e97e79d41a901658b9` | Accepted, 3 AGREE / 2 IDLE | Exact PNG metadata, 2,941-byte size and digest above; proves status/header/body/hash operations. |
| v4 raw red PNG, single vision, comparative wrapper | `0x8c3c632fc868cf4aac48fbab14fbf8836d801610d6e8d97d4e28320e4c2c4c58` | **UNDETERMINED**, 3 DISAGREE / 2 IDLE | No authoritative state update. Leader execution SUCCESS; validators did not agree. No trace/model answer to attribute the disagreement more specifically. |
| v5 single red PNG, custom validator | `0xd0e43153bbea191724a36aab91d0df1169e0f0adf80ccd116320bd30db489016` | Accepted after 2 rounds; final 3 AGREE / 1 DISAGREE / 1 IDLE | `{"stage":"VISION","recognized":true,"observation":"The image shows a red square with the word RED in white."}`; metadata SHA matched independently. |
| v5 red/blue PNG pair, custom validator | `0x9c6e5cbeafc92143c7b7a2aed848f2befb02da8dbd9264e3ec582cf8b8cd86c2` | Accepted/finalized; 3 AGREE / 2 IDLE | `{"stage":"VISION","comparison":"CHANGED","confidence":"HIGH","observations":["Image A is entirely red with white 'RED' text","Image B is entirely blue with white 'BLUE' text"]}`. Both input digests in the authoritative state match the independently recorded retrieval results above. **This is the core two-raw-image consensus proof.** |
| v5 placeholder JPEG raw GET | `0xe695ed72bf46706d89060995a72a7c90c883a73f64551f8fc48552485b7f92a2` | Accepted/finalized; 3 AGREE / 2 IDLE | Valid-looking JPEG content-type/signature and nonempty 4,024-byte body; digest recorded above. |
| v5 placeholder JPEG single-image vision | `0x024c7d019e7cac92cbe72621c1de6524ec59ba90122bdd4b79d6c838412242fd` | Accepted; majority agreement | Authoritative result `stage:"OTHER"`, `recognized:null`, exception `NondetException:{'causes':['INVALID_IMAGE'],'ctx':{}}`. The MIME and JPEG SOI/DQT signature alone did not establish that this particular response was accepted by image preprocessing/provider handling. |
| v5 independent Unsplash JPEG raw GET | `0x0dfee2843f032fd5c53abb0161176483a6b36fd1674b192cd501d4265faaa196` | Accepted/finalized; 3 AGREE / 2 IDLE | 9,966-byte `image/jpeg`, JFIF marker, digest above. |
| v5 independent Unsplash JPEG single vision | `0xf1283eae56fcd35d653bde241605e6002836a8dd07f1ae8dbce291f9f58f7b09` | Accepted after 3 rounds; final 3 AGREE / 2 DISAGREE | `stage:"VISION"`, observation `"A red shoe is shown on a red background."`; raw JPEG bytes reached vision and produced a visual observation. The fixed diagnostic's `recognized` question was about a red square, so its `recognized:true` on this sneaker image is not a correct classification for that question; this is a prompt/model quality warning, not a JPEG transport proof. |
| v5 HTML raw GET | `0xa02db8d9d18571877966cd51f646218b91ec11ac52dc8bc0c6545b0337c1adaa` | Accepted/finalized; 3 AGREE / 2 IDLE | 200 `text/html; charset=utf-8`, 577 bytes, HTML `DOCTYPE` signature; rejected as non-image in comparison flow. |
| v5 HTML + valid PNG pair | `0x4f25f7ab45738baace97783402a0932460e1325f9dbaebca23e51eef7f7fc7a9` | Accepted/finalized; 3 AGREE / 2 IDLE | Explicit `{"stage":"RESPONSE_VALIDATION","comparison":"UNCLEAR","confidence":"LOW"}`; HTML body was not passed into vision. |
| v5 forbidden-TLD unavailable source | `0x7862a9fae255ca1c97daa35edb50196c7d2bae72eef5716f857d217de877a550` | Accepted/finalized; 3 AGREE / 2 IDLE | `TLD_FORBIDDEN` for `.invalid`; API did not attempt an ordinary DNS lookup. |
| v5 syntactically valid nonexistent host | `0xd77f98616530c92369eb519984026775a1a63575b46ab11ecef969e3fcad1270` | Accepted/finalized; 3 AGREE / 2 IDLE | `SENDING_REQUEST`, with rust request error context for `https://moveout-stage05-no-such-host-20261005.example.com/image.png`; explicit fetch failure returned rather than image certainty. |
| v5 HTTP 302 redirect to red PNG | `0x00322052f1f69c759e099729bf483e132ab7a470eca1804f7ae3489de5e2bcf3` | Accepted/finalized; 3 AGREE / 2 IDLE | Final response was the same 200 PNG and same SHA-256 as direct red PNG. Response contains no redirect history/effective URL. |

RPC connectivity was intermittently reset during one HTML reread (`ECONNRESET`); a read-only retry succeeded. Hosted calls later succeeded without switching networks. No oversize-image probe was attempted: official SDK material describes a host response-body cap but does not publish a numeric StudioNet limit, so deliberately large retrieval would not be a safely bounded test.

### Evidence identity, mutable sources, and provenance

The supported `hashlib.sha256` result can be recorded with an evidence ID, requested source URL, MIME, byte length, and the transaction timestamp (`gl.message.datetime`/`gl.message_raw['datetime']` per the current [Transaction Context reference](https://docs.genlayer.com/developers/intelligent-contracts/features/transaction-context)). The transaction timestamp is deterministic context shared during re-execution; it is not a per-validator wall-clock fetch timestamp. Because validators retrieve live URLs independently, a stored leader digest alone does not prove every validator saw identical bytes. v5 improves this by making each validator re-fetch and compare the digest to the leader's digest before agreeing. A changed body therefore tends toward disagreement/rotation/undetermined rather than silently treating different versions as the same evidence.

## Stage 0.6A — Real property visual benchmark source audit (2026-10-05; historical, superseded by Stage 0.6B)

**Stage 0.6A result: BLOCKED before evaluation.** No 0.6A contract was deployed. That no-case source-audit result was superseded when Stage 0.6B adopted a controlled synthetic dataset. The existing Stage 0.5 contracts and finalized results above are unchanged. They establish synthetic visual transport and consensus only; they do not establish property-condition accuracy.

An audit of candidate sources found no image set admitted under the Stage 0.6 criteria of same-area property pairs, defensible visible labels, rights for remote automated evaluation, stable direct HTTPS image resources, and frozen per-image digests:

- The CollectDataIO “Tidy Up” dataset lists 20 before/after real-kitchen captures, but requires account/form access and acceptance of its custom sample-data license. No account was used and no license was accepted. Cleaning/clutter changes do not establish damage or repair labels.
- MIRL Aftermath’s repository README describes six generated fictional heritage images under an MIT-licensed sample project, but the sample is not residential inspection photography, its image content is embedded in dossier JSON as data URLs rather than documented standalone image URLs, and one before image is explicitly marked restricted. No image was used.
- A commercial foundation-repair gallery lacks established open image-reuse rights; a street-view damage dataset is labeled CC BY-NC; disaster satellite imagery is not a valid proxy for room-level rental inspection. None was used.

At the end of Stage 0.6A there were **0 admitted cases**. That no-case source audit was superseded by the Stage 0.6B controlled synthetic dataset and hosted evaluation. The 0.6B transactions, consensus, finality, authoritative reads, and measured synthetic results are documented in [the Stage 0.6 evaluation report](MOVEOUT_PROPERTY_VISUAL_BENCHMARK.md).

**Historical Stage 0.6A result:** no real-source property pairs were admitted. Stage 0.6B later established controlled synthetic behavior only; it does not demonstrate real-world accuracy or authorize Stage 1.

## Stage 0.6B — controlled synthetic fixture package (2026-10-05)

The Stage 0.6A real-source blocker prompted a revised synthetic strategy. A 1024×1536 source contact sheet was created with the built-in image-generation tool, then mechanically cropped into 28 PNG fixtures (14 ordered pairs) with no image retouching. Contact-sheet SHA-256: `7817020e02849c0de257154d8465d824216bae38b47640623337defe74b99eab`. The per-image SHA-256 digests, expected labels, layer-1 ground truth, local paths, and commit-pinned public URLs are frozen in [`benchmarks/controlled-property-2026-10/benchmark_manifest.json`](../benchmarks/controlled-property-2026-10/benchmark_manifest.json). The 28 raw GitHub URLs were anonymously retrieved and every remote SHA-256 matched the local fixture.

The cases cover two unchanged variations, pre-existing crack, new crack, new stain, worsening, visible patch/repair, occlusion, cropped/noncomparable area, dark/blurred evidence, lookalike area, ambiguous mark, instruction text embedded in an image, and a shadow that resembles a defect. The prompt explicitly treats all visible text as untrusted evidence. Ground truth was set after visual inspection and before any GenLayer call. The dataset is synthetic and controlled; it does not establish real-world property accuracy.

### Disposable benchmark contract and quality checks

New source: [`contracts/moveout_visual_benchmark_v1.py`](../contracts/moveout_visual_benchmark_v1.py). SHA-256: `C98B7056D0B64065F3AEA99D6121F8831DBDE4329C8F901CE60D85BE4BB420B2`. Runtime pin: `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`. It composes the previously hosted-verified raw-byte APIs with expected-digest input and a two-layer structured result. The leader checks HTTPS URL shape, response `200`, PNG/JPEG MIME, nonempty body, 500,000-byte cap, and exact expected SHA-256 before invoking vision. Its validator independently repeats both fetches and vision execution, checks each digest against both leader and frozen expected hashes, and compares bounded semantic fields. The contract downgrades mismatched observations, weak same-area/visibility/quality evidence, and a missing repair indicator to `INSUFFICIENT_EVIDENCE`. It reports model classification separately to make prompt-injection outcomes auditable.

- `genvm-lint lint`: PASS (3 checks).
- `genvm-lint check`: PASS (SDK validation; 1 write and 1 view method).
- `python -m py_compile`: PASS.
- Local fixture integrity check: PASS (14 records; 28 SHA-256 values match local bytes).
- Local GenVM/direct tests: no direct test runner or harness is configured; no local mock was counted as proof.
- Hosted/integration tests: 14/14 StudioNet transactions finalized; accepted state writes were reread authoritatively, and disagreement cases were verified not to change the last accepted state. See [the Stage 0.6 evaluation report](MOVEOUT_PROPERTY_VISUAL_BENCHMARK.md) and [`hosted_results.ndjson`](../benchmarks/controlled-property-2026-10/hosted_results.ndjson).

### Hosting and completed StudioNet evaluation

The project was pushed to `https://github.com/Chinny070/moveout` using normal noninteractive Git authentication. The 28 image assets are pinned to commit `194be2d6c141c76bb9f737ffaaa1fee768c126af`; anonymous raw URL retrieval and SHA-256 parity passed for every fixture. The hosted benchmark completed on the requested StudioNet and signer. Its receipt outcomes and limitations are summarized in [MOVEOUT_PROPERTY_VISUAL_BENCHMARK.md](MOVEOUT_PROPERTY_VISUAL_BENCHMARK.md).

### Current classification

**STAGE 0.6B HOSTED EXPERIMENT: COMPLETE. CONTROLLED PROPERTY VISUAL FEASIBILITY: WEAK.** Ten of fourteen cases reached majority agreement; five of those ten matched frozen labels, and four transactions finalized as majority disagreement. The ambiguity and shadow cases produced incorrect damage classifications. **REAL-WORLD PROPERTY ACCURACY: NOT VERIFIED. READY FOR STAGE 1: NO.** No canonical MoveOut code or deployment was touched.

No source was deliberately mutated between leader and validator executions. The successful same-digest votes demonstrate that the tested static URLs were byte-identical across the participating retrievals at that time; they do not guarantee future URL immutability. For MoveOut, store the source URL and SHA-256 (and optionally MIME/size) as part of an evidence record, reject validators whose digest differs, and prefer immutable/content-addressed or contract-submitted evidence when feasible. Do not treat URL alone or HTTP MIME as provenance: redirects can obscure the final location, a MIME header can lie, and remote content can later change.

### Direct bytes versus screenshot mode and MoveOut recommendation

| Dimension | A. `web.render(url, mode="screenshot")` | B. `web.get(url).body` → vision |
|---|---|---|
| Fidelity | Browser-rendered page screenshot; can crop, scale, or include page chrome and is not necessarily the original photograph pixels. | Preserves retrieved original image bytes; best match to the submitted JPEG/PNG file if source URL serves it directly. |
| Validator reproducibility | Validators independently render the page; browser/render differences and changing page state can vary. | Validators independently fetch bytes; SHA-256 equality is a concrete reproducibility gate. |
| Provenance/fingerprint | No screenshot digest was captured in the earlier proof. | Hosted SHA-256 works; store it beside requested URL and transaction timestamp. Redirect chain still unavailable. |
| Changing source | Dynamic pages and embedded image URLs can change; screenshot digest/source snapshot not currently bound. | Same live URL can change; digest check detects cross-validator drift during a transaction, but does not make the URL immutable afterward. |
| Format/error handling | Renderer produced an `Image` object for the prior hosted red/blue test. | PNG pair and single JPEG vision succeeded. MIME must be checked; one placeholder JPEG failed `INVALID_IMAGE`, while Unsplash JPEG succeeded. Fail closed on decoding/provider errors. |
| StudioNet evidence | Earlier screenshot pair finalized `CHANGED/HIGH` under comparative equivalence. | Two PNG raw bodies finalized `CHANGED/HIGH` under custom independent validation; single JPEG also reached vision. |
| Complexity | Simpler for pages; browser render hides source-byte details. | Requires status/MIME/size/prefix checks, digesting, explicit URL/redirect policy, format boundaries, and digest equality in validators. |

**Recommended MoveOut V1 visual-evidence path: direct original image bytes via `gl.nondet.web.get(url).body`, with validators independently re-fetching both evidence URLs and requiring exact SHA-256 equality before comparing normalized visual decisions.** This recommendation is based on hosted StudioNet evidence and the product's photo-evidence use case: raw bytes preserve the original photo and produce a digest that can be bound to its claim. Restrict accepted formats to tested PNG/JPEG, enforce a conservative documented application byte limit, validate status/MIME and image decoding by successfully invoking vision, and map any retrieval/decoding/disagreement issue to `UNCLEAR`/inconclusive. Keep screenshot rendering for evidence that is itself a rendered webpage, not as a silent transformation of a tenant's source photograph.

This is a capability-level recommendation, not a MoveOut contract implementation. Before treating damage/condition decisions as production-ready, test representative real room-condition photo pairs, viewpoint/lighting changes, same-damage cases, borderline ambiguity, large supported image sizes, and validator variance. The current diagnostic revealed one bad semantic boolean on an out-of-domain sneaker input and a fixture-specific JPEG `INVALID_IMAGE`; these show why decision prompts and failure policies require dedicated MoveOut accuracy tests.

### Remaining limits and Stage boundary

- **Direct image bytes:** VERIFIED for the hosted PNG pair comparison and single-image PNG/JPEG vision path stated above; do not generalize to all JPEG encodings, image dimensions, MIME claims, or provider/model policies.
- **JPEG two-image pair:** Not tested. JPEG single-image vision passed with an independent Unsplash source; the placeholder JPEG failed with `INVALID_IMAGE`.
- **Mutable-source behavior:** No controlled content mutation was run. Digests detect body mismatch at validation time, not future mutation.
- **Redirect provenance:** Redirect-following was observed, but the API does not return redirect chain or final effective URL.
- **Oversized evidence:** Not tested due the absence of a documented numeric StudioNet body cap.
- **Independent auditability:** Consensus receipts expose votes/finality, not each validator's fetched bytes or model output; the custom validator's source and digest checks are auditable, but no per-validator retrieval transcript was exposed.
- **MoveOut policy:** No property, tenancy, deposit, damage-condition, Same Damage Guard, challenge, or frontend implementation was started. No canonical MoveOut deployment was touched.

**Stage 0.5 disposition:** the raw image-byte capability question is answered **VERIFIED** for this bounded tested envelope. The broader MoveOut damage-decision policy still requires its own evidence-quality and accuracy proof. Stop here; do not start Stage 1 without the user's instruction.
