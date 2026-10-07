# MoveOut Stage 3 verification record

**Status: PASS for Stage 3 validator-side byte provenance on StudioNet. Stage 4 has not started.** This report covers deterministic response validation and independent validator retrieval only. It does not claim visual understanding or property-condition accuracy.

## Source, runtime, network, and disposable deployment

- Contract source: `contracts/moveout_protocol_v1.py`
- Exact source SHA-256 submitted to the StudioNet deployment: `3DAF8D20E82E43B7174BAAEEDA052EEAF7F90F91AA0C8C8EB42BC90C4C2E8624`
- Pinned GenVM runtime: `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`
- Target: StudioNet, chain ID `61999`, RPC `https://studio.genlayer.com/api`
- CLI/linter/SDK/test environment: `genlayer 0.39.1`, `genvm-lint 0.11.0`, `genlayer-py 0.16.3`, `genlayer-test 0.29.2`, bundled `genlayer-js 1.1.8`
- Authorized disposable account: `my-studionet-wallet`, address `0xaffE15eEc45b68835cc9E5B4Ab85dD5deaE8e70b`
- Disposable proof contract: `0x6Fad38356E9ce08c6464542334B71B84E745D7F2`
- Deployment transaction: `0xa75dae2a39b894a7fe9104ae13f776f4adc3ee77de348b50a7db467e71624772`
- Deployment receipt: `FINALIZED`, `MAJORITY_AGREE`, leader execution `SUCCESS`, all five validators `AGREE`.
- No canonical MoveOut contract was deployed.

The deployed contract schema was read back and included the Stage 3 methods. The deployed contract source hash matched the exact source hash above. The deployment and all hosted proof writes below used the same StudioNet chain; no network switch occurred.

## APIs and validator workflow exercised

- Retrieval API: `gl.nondet.web.get(source_url)`.
- Runtime response fields consumed: `response.status`, `response.headers`, and `response.body` (`bytes`).
- Validation: HTTP 200; body nonempty and at most 8 MiB; MIME exactly PNG or JPEG; PNG/JPEG signature/structure; SHA-256 of the exact returned body.
- Consensus mechanism: `gl.vm.run_nondet_unsafe(leader_fn, validator_fn)` with a custom validator callback.
- Leader: independently GETs the URL, validates it, computes the digest, and proposes a compact normalized result.
- Validators: each participating validator callback independently GETs the same URL and re-runs the validation/hash steps; it compares the normalized result with the leader proposal. No raw image bytes are put in the leader proposal or persistent record.
- Equality predicate: exact equality of the normalized response/result dictionary (status, MIME, body size, expected and retrieved digests, outcome/failure, URL-string hash). A different body/digest or response classification does not agree with the leader proposal.
- Storage: the successful nondeterministic call creates an append-only provenance verification record. The record contains no image bytes or full source URL.
- Uncertainty/failure: retrieval exceptions, non-200 status, invalid content, unsupported media and size limits are represented as explicit result states when validators agree on that normalized state. A validator mismatch may prevent quorum/finality; that can leave no new on-chain record rather than fabricate a successful record.

## Public fixtures

All fixtures were public HTTPS resources retrieved by validator-side contract execution. Hashes below are SHA-256 of the image/fixture body as independently checked before the hosted run; the verification contract hashes eligible response bodies again.

| Evidence | Source | Declared SHA-256 | Hosted response |
|---|---|---|---|
| EVID-1 | [Commit-pinned PNG](https://raw.githubusercontent.com/Chinny070/moveout/194be2d6c141c76bb9f737ffaaa1fee768c126af/benchmarks/controlled-property-2026-10/images/case-01-before.png) | `cc7df2a785d7b89a3321498a699b13551556e0490d472d89307999ad0f61e33b` | `200`, `image/png`, 63,350 bytes |
| EVID-2 | [Commit-pinned JPEG](https://raw.githubusercontent.com/Chinny070/moveout/8fa5bcbcc4918b28b5ba95ef431542a8d40fb128/benchmarks/stage3-fixtures/sample-photo.jpg) | `c9fcb81c83df208461db666064921602aef4a89fd118879528ea34c46b53d12a` | `200`, `image/jpeg`, 8,858 bytes |
| EVID-3 | Same PNG URL as EVID-1 | 64 zeroes (deliberately wrong) | `200`, `image/png`, 63,350 bytes |
| EVID-4 | [Commit-pinned HTML fixture](https://raw.githubusercontent.com/Chinny070/moveout/8fa5bcbcc4918b28b5ba95ef431542a8d40fb128/benchmarks/stage3-fixtures/not-an-image.html) | `0c424782ad2d585a33fa33b0f34c395cd8db549c1906a8bc3df779536f8674be` | `200`, `text/plain`, 60 bytes |
| EVID-5 | [Commit-pinned missing PNG path](https://raw.githubusercontent.com/Chinny070/moveout/8fa5bcbcc4918b28b5ba95ef431542a8d40fb128/benchmarks/stage3-fixtures/not-present.png) | `d5558cd419c8d46bdc958064cb97f963d1ea793866414c025906ec15033512ed` (preflight 404 body hash) | `404`; body not accepted or hashed by contract |
| EVID-6 | [HTTPS redirect-to-PNG diagnostic](https://httpbin.org/redirect-to?url=https%3A%2F%2Fraw.githubusercontent.com%2FChinny070%2Fmoveout%2F194be2d6c141c76bb9f737ffaaa1fee768c126af%2Fbenchmarks%2Fcontrolled-property-2026-10%2Fimages%2Fcase-01-before.png) | `cc7df2a785d7b89a3321498a699b13551556e0490d472d89307999ad0f61e33b` | `200`, `image/png`, 63,350 bytes after redirect resolution |

The URL source hashes persisted by the contract were:

- EVID-1/EVID-3: `30f157a4cd44bf5af4217afc32099588d95e69c8c2999f3d65d20a5f950fa36f`
- EVID-2: `e1bcf957d19b5a825ab32b5316372f6150f6e4c38bbb7eb1241fdaf416eb5f0f`
- EVID-4: `3579b3c16e4ac6b399665d212a43cd5df5cbfeb878eaa39981942250e0774366`
- EVID-5: `4ea6f57b0eb9bfdb22320c686a9b91c9c2c76267d8e415c07b0b592f1cdfdd2d`
- EVID-6: `10c623a972bafd849374309094f404b422512cf08dcd7c508b116003ed621ddc`

## Hosted provenance transactions and authoritative results

Every verification transaction below reached `FINALIZED` with `MAJORITY_AGREE`. The vote sets had three `AGREE` and two `IDLE` votes; where the runtime receipt represented idle validators as execution errors with `VALIDATOR_QUORUM_REACHED`, the vote result remained the authoritative consensus signal. After each receipt, `get_evidence_verification_status(evidence_id)` was called against StudioNet and returned the stored verification record.

| Evidence | Verification transaction | Votes | Final record | Authoritative result |
|---|---|---|---|---|
| EVID-1 | `0x08c8a1a19e760f40f812ce9c330b1233a1341ced758716c32250e8a3c2ec6191` | 3 AGREE, 2 IDLE | `EVER-1` | `VERIFIED`; HTTP 200; `image/png`; 63,350 bytes; retrieved SHA equals expected `cc7df2…e33b` |
| EVID-2 | `0xa9b3d6f4d1bc723be2cdc354cda39ecf825ce13f39b5f96fd796294c914c1422` | 3 AGREE, 2 IDLE | `EVER-2` | `VERIFIED`; HTTP 200; `image/jpeg`; 8,858 bytes; retrieved SHA equals expected `c9fcb8…3d12a` |
| EVID-3 | `0x7c20d4a2d7b0a427748dcb9211fd042cc61a96c9d7c7d65d27af2cc62273bd8e` | 3 AGREE, 2 IDLE | `EVER-3` | `DIGEST_MISMATCH`; retrieved PNG SHA `cc7df2…e33b`; declared digest was 64 zeroes |
| EVID-4 | `0x388e9e239417a7a04c0ced322ea3f785e37e00a9bfe9eed2488f49c314795281` | 3 AGREE, 2 IDLE | `EVER-4` | `INVALID_CONTENT / NON_IMAGE_CONTENT`; HTTP 200; `text/plain`; 60 bytes; no retrieved digest persisted |
| EVID-5 | `0x2b58ba34e7bf37a6afdca90836f0ffb0e81de214840a583efa8969d8817fd30f` | 3 AGREE, 2 IDLE | `EVER-5` | `UNAVAILABLE / HTTP_STATUS`; status 404; body size 0; no retrieved digest |
| EVID-6 | `0x94757f32723ef34491cbd90bc2ca3f2684c323e1f92aec943ac0c31e3fc68702` | 3 AGREE, 2 IDLE | `EVER-6` | `VERIFIED`; final observed response was HTTP 200 PNG, 63,350 bytes, with expected SHA `cc7df2…e33b` |

All six results were read back authoritatively after finality. The reads confirmed the persistent `verification_id`, evidence binding, status, content type, body size, expected/retrieved digest where eligible, outcome, failure code and URL hash. The finalized transaction hashes above are the verification writes; the source outcome was not inferred from a deployment or a single LLM call.

### Redirect observation

The redirect diagnostic finalized as `VERIFIED` with the target PNG's 200 response and byte digest. Thus the current hosted `gl.nondet.web.get` path resolved this tested redirect before exposing the response fields used by the contract. The current response interface/contract does not record a redirect chain or independently bind a final URL; the proof therefore does not establish safe behavior for every redirect or prevent a redirect target from changing. Redirect policy and destination validation remain production blockers for untrusted URLs.

## Setup/failure diagnosis

- A missing-URL evidence write first reused the same expected digest as EVID-1 in the same area. The contract's duplicate-evidence guard rejected it; no evidence record was created. The case was resubmitted with the preflight 404 body digest in a new inspection and then produced EVID-5.
- Additional writes attempted after INSP-1 was frozen failed and left no records. This is expected lifecycle protection. Contract reads confirmed INSP-1 is frozen and includes only EVID-1 through EVID-4.
- A second-inspection attempt with type `MAINTENANCE` failed while the fixture tenancy was still `DRAFT`; Stage 3 fixture reads showed the tenancy is `DRAFT`, and the contract requires `ACTIVE` for maintenance inspections. A new `MOVE_IN` inspection was accepted instead. It became `INSP-2` for the unavailable-source test; a third `MOVE_IN` inspection became `INSP-3` for the redirect test.
- Earlier in setup, GenLayer CLI positional argument coercion mishandled empty-string `submit_evidence` parameters. Those attempts did not alter the contract. Official GenLayerJS `writeContract` was used for evidence writes so empty strings remained strings. A later SDK receipt poll hit a network connect timeout after a proof write was submitted; the GenLayer CLI receipt command confirmed that transaction's finality, and no duplicate proof was resubmitted.
- One SDK call batch did not return all logs to the caller. On-chain paginated reads and individual receipts were used to establish the actual fixture state before continuing.

## Local/direct verification gates

Run: `scripts/verify_moveout.ps1` (local Direct Mode plus static checks).

| Check | Result |
|---|---|
| Complete local suite: `gltest tests -q` | PASS, 171 tests (87.20s) |
| Stage 3 direct test module: `gltest tests/test_moveout_stage3_provenance.py -q` | PASS, 26 tests (16.57s) |
| `genvm-lint lint contracts/moveout_protocol_v1.py` | PASS, 3 checks |
| `genvm-lint check contracts/moveout_protocol_v1.py` | PASS, 68 methods (42 view, 26 write) |
| `python -m compileall -q contracts tests` | PASS |
| `scripts/check_stage3_scope.py` | PASS; one `web.get` path and one custom validator; no prompt or finding writer |
| Benchmark-production-selector scan | PASS; no benchmark selector in the contract |
| Diff whitespace check | PASS |

Stage 3 Direct Mode coverage includes valid PNG/JPEG, byte digest match/mismatch, HTML, unsupported MIME, signature mismatch, oversize body, 404, fetch exception, malformed source/digest, tenancy authorization/scope, append-only re-verification, validator-side changed-byte rejection, and bounded history. Those direct tests are local mocks, not StudioNet evidence.

## Limitations and remaining verification

- The hosted proof establishes original-byte retrieval/hash consensus for the listed fixtures. It does not establish that the images depict the claimed property, room, area, capture date, or condition.
- Hosted mutable-source divergence was not attempted. Direct Mode simulates a changed response between the leader and validator and shows the validator rejects the different digest. StudioNet stable commit-pinned sources agreed.
- Redirect resolution was tested once and returned the target PNG successfully. No redirect-chain/final-URL provenance is stored; deployments must not treat arbitrary redirects as trusted origins.
- Domain allowlisting, DNS rebinding/private-host defenses, authenticated/private media, signed uploads, object-store access control, range/partial response handling beyond rejecting non-200, and recovery from persistent host outages are not implemented.
- No maximum-size hosted image was sent. The 8 MiB contract boundary is covered locally; hosted runtime/gas/storage behavior near the ceiling remains unverified.
- The contract hashes the URL string and fetched bytes; it does not establish who captured/uploaded the photo or when the original capture occurred.
- An unresolved leader/validator retrieval disagreement may fail consensus rather than append an `INCONCLUSIVE` record. A future version should decide whether to expose a distinct, finalized uncertainty record without accepting a contested proposal.
- No canonical MoveOut contract, Stage 4 flow, frontend, deposits, condition verdict, or semantic visual model was deployed or tested.

## Disposition

**Stage 3 hosted validator-side byte provenance: VERIFIED for the six recorded cases.**

**MoveOut semantic visual adjudication: NOT VERIFIED by Stage 3.** Stage 3 proves bytes and source-response properties only. Continue to keep provenance verification separate from any later visual observation or condition verdict. Stop here; Stage 4 has not started.
