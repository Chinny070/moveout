# MoveOut StudioNet Deployment Readiness

**Status: PARTIAL — contract identified and StudioNet configuration/reachability verified, but deployment is not authorized and the current contract is not ready to expose its unverified AI operations as a working MVP.**

**Investigation date:** 2026-10-09
**Repository baseline:** `main`, `2dc0b2d8e31bbb99c2da89a61ad4581cb6d7bb24`
**Deployment / hosted writes:** None performed.

## 1. Repository and product baseline

- The current branch is `main`; at inspection time its local commit was `2dc0b2d8e31bbb99c2da89a61ad4581cb6d7bb24`.
- `origin` is `https://github.com/Chinny070/moveout`. A local read-only `git ls-remote origin refs/heads/main` attempt failed because the sandbox could not connect to `github.com:443`; local/remote synchronization could not be freshly confirmed in this investigation. The CLI chain configuration is unrelated to Git access.
- Existing owner work was preserved and not staged: modified `docs/MOVEOUT_STAGE_5_6A_VISION_ENVIRONMENT_SETUP.md` and untracked `docs/MOVEOUT_STAGE_5_6B_FREE_GEMINI_SMOKE_TEST.md`.
- The browser entry point is `index.html`, with `app.js` and `styles.css`. It explicitly identifies itself as **Demo Mode**. Inspection records and photo `Blob`s are stored in browser IndexedDB. The page says they are local only, not sent to GenLayer, not on-chain, and not AI-assessed. There is no wallet or GenLayer client integration.
- This investigation did not inspect the owner's separate interactive browser profile. The MVP behavior described in the assignment is owner-reported; repository inspection confirms the implementation mechanism above.

## 2. Deployable artifact

The current contract source is [`contracts/moveout_protocol_v1.py`](../contracts/moveout_protocol_v1.py), SHA-256 `64D1599DD52F485AF26FF7D1393C6F5345427A49A5471E9E0364CC1FB118582D`. It defines `MoveOutProtocolV1(gl.Contract)` and has a **zero-argument** `__init__(self)`. Its only imports are `from genlayer import *`, `hashlib`, and `json`; no project-specific or third-party Python dependency is imported. The source header pins `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`.

This is the repository's current protocol implementation, but there is no deployment manifest or current StudioNet contract address identifying it as a deployed authoritative instance. Treat this file as the intended candidate artifact, not as an already deployed or hosted-verified contract.

The implementation has a substantial persistent schema (properties, units, tenancies, inspections, evidence, nominations, supplemental records, reviews, and events), all initialized from empty maps/counters in a new deployment. A new contract address starts fresh; existing records are not migrated. No migration is needed to construct a fresh instance, but deploying a new address would not carry over prior disposable/test state.

Local GenVM lint and SDK validation pass for this source (results below). That is evidence of static/tool compatibility only. No fresh hosted deploy or hosted integration test of this exact current source was performed, so StudioNet execution compatibility remains **not verified**.

## 3. StudioNet network and tooling

Installed versions observed:

| Tool | Observed version / value |
|---|---|
| GenLayer CLI | `0.39.1` |
| `genvm-lint` | `0.11.0` |
| Python | `3.12.10` |
| Node.js | `v24.14.0` |
| Contract runtime pin | `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6` |

`genlayer network list` and `genlayer network info` reported active alias `studionet`, RPC `https://studio.genlayer.com/api`, and chain ID `61999`. A read-only JSON-RPC `eth_chainId` request to that endpoint returned `0xf22f` (decimal `61999`). This verifies outbound StudioNet RPC reachability at investigation time and matches the CLI's active network; it does not submit a transaction.

Official GenLayer documentation describes StudioNet as hosted with no local setup and documents direct CLI deployment with `--contract`, optional `--rpc`, and constructor args. That means deployment need not depend on local Docker. We did not run `genlayer init`, `genlayer up`, or any mutating network command.

The CLI's effective network was read, not changed. Do not use `genlayer network set` as part of the first deployment unless a later owner-approved runbook explicitly requires it. Always inspect `genlayer network info` immediately before signing.

## 4. Deployment, wallet, funding, and verification

- A deployment is a consensus transaction and requires a transaction signer/account. Never put its private key or recovery phrase in the frontend, repository, chat, command history, logs, or this report.
- StudioNet documentation lists GEN as its currency and a built-in faucet available from the Studio account selector. This is test-network funding, not a promise that each deployment is costless. Current exact minimum funding/fee was not measured; it depends on live protocol fee requirements and deployment execution. Classify the minimum as **UNKNOWN until the CLI/network fee estimate is obtained immediately before an authorized transaction**. No fiat charge was incurred during this read-only investigation.
- Do not create or fund a new wallet in this readiness task. Before deployment, owner must choose the disposable test account and use the Studio faucet if its balance is insufficient. Confirm the account is on chain ID 61999 in the local wallet/Studio UI.
- The CLI deployment route documented by GenLayer is `genlayer deploy --contract <path> [--rpc <url>] [--args ...]`. For this zero-argument candidate, the exact command to run only after a separate explicit deployment authorization is:

  ```powershell
  genlayer network info
  genlayer deploy --contract contracts/moveout_protocol_v1.py --rpc https://studio.genlayer.com/api
  ```

  Do not run it now. It will sign and submit a deploy transaction using the configured/active signer.
- On success, preserve the returned transaction hash and contract address. Read the receipt and wait for finality according to the installed CLI/Studio workflow; verify a successful finalized execution, then use read-only `genlayer schema <address>`, `genlayer code <address>`, and a no-state-changing `genlayer call <address> <view-method> ...` to check the deployed interface and initial state. A returned address alone is not proof that GenVM deployment execution finalized successfully.
- Official GenLayer documentation notes that deployment can create an EVM Ghost address even when GenVM deployment fails. Never treat that placeholder address as a usable contract without receipt/finality verification.
- The Studio UI provides a browser faucet. The contract may be accessed by a browser application using the documented GenLayerJS SDK and a wallet/EIP-1193 provider. The exact SDK package version/build and browser wallet integration have not been installed or validated in this project.

## 5. Minimum contract operation map

All methods below are from the inspected contract ABI/decorators; parameter names and return types are source-level declarations. Writes require an authorized signer and create state. Views are read-only. AI means `gl.nondet.exec_prompt`; validator-side web retrieval without a prompt is marked separately.

| MVP action | Exact method and parameters | Kind / result | Authorization and dependency |
|---|---|---|---|
| Create property | `create_property(property_label, request_id)` | Write; property ID string | Creator becomes initial manager; no AI. |
| Add manager (if needed) | `add_manager(property_id, manager_address)` | Write; no return | Current manager; no AI. |
| Create unit | `create_unit(property_id, unit_label, request_id)` | Write; unit ID string | Property manager; no AI. |
| Create tenancy | `create_tenancy(property_id, unit_id, tenant_address, start_metadata, request_id)` | Write; tenancy ID string | Property manager; no AI. |
| Activate tenancy | `activate_tenancy(tenancy_id)` | Write; no return | Contract tenancy state rules; no AI. |
| Create inspection | `create_inspection(tenancy_id, inspection_type, request_id)` | Write; inspection ID string | Tenant or manager recognized by `_require_participant`; `SUPPLEMENTAL` is prohibited here and must use its linked request flow; no AI. |
| Define room/area | `create_room(unit_id, room_label, request_id)`; `create_area_item(room_id, subject_type, label, description_ref, request_id)`; `include_area_in_inspection(inspection_id, area_item_id, request_id)` | Writes; room/area IDs or no return | Room/area creation requires manager; inclusion checks inspection/area parent scope; no AI. |
| Register photo evidence | `submit_evidence_for_slot(inspection_id, area_item_id, capture_slot_id, condition_record_id, evidence_type, source_ref, expected_sha256, supersedes_evidence_id, participant_obstruction, participant_light, participant_note_ref, request_id)` | Write; evidence ID string | Participant-side/open-inspection and scope checks; no image inference at registration. Caller supplies URL and digest. |
| Freeze evidence / inspection | `freeze_evidence(evidence_id)`; `freeze_inspection(inspection_id)` | Writes; no return | Evidence submitter then inspection creator; no AI. Inspection freeze requires evidence frozen and structural completeness. |
| Retrieve records | `get_inspection(inspection_id)`, `get_evidence(evidence_id)`, `get_inspection_completeness(inspection_id)`, `list_evidence(inspection_id, offset, limit)`, plus corresponding property/unit/tenancy/room/area getters and lists | Views; JSON strings | Read-only; no AI. Access/privacy policy still needs product decisions because chain state is public. |
| Verify evidence bytes | `verify_evidence_provenance(tenancy_id, evidence_id, request_id)` | Write / consensus execution; verification ID string | Requires frozen photo and inspection; validators fetch public URL and compare status, MIME, format, size, and SHA-256. No vision model, but requires nondeterministic web access. |
| Nominate target | `create_target_nomination(inspection_id, area_item_id, target_identifier, target_description, reference_evidence_id, reference_capture_slot_id, region_box_json, supersedes_target_id, request_id)` | Write; target ID string | Participant-side/open inspection; optional reference must be a frozen in-scope photo; no AI. |
| Observe a nominated target | `observe_nominated_target(tenancy_id, target_id, evidence_id, request_id)` | Write / nondeterministic; observation ID on accepted result | Requires frozen, provenance-verified evidence; validators refetch and call image-enabled `exec_prompt`. **Real image model response, validator AI availability, and property-observation accuracy are unverified.** |
| Legacy/general visual paths | `observe_evidence(tenancy_id, evidence_id, request_id)`; `observe_evidence_pair(tenancy_id, evidence_id_a, evidence_id_b, request_id)` | Writes / nondeterministic; observation IDs | Validator-side public image fetch and image-enabled `exec_prompt`; not ready to expose for real property conclusions. |

Other AI-free actions include creating condition records, inspection reviews/disagreements, and maintenance events. They record participant submissions and must not be represented as AI-verified truth, liability, or deposit decisions.

The complete exact signatures, overload/tuple rules, sender rules, and return serialization should be checked against deployed `genlayer schema` and a fresh local SDK validation before wiring a frontend. This report abbreviates the tenancy signature rather than guessing it.

## 6. AI operation classes and current safety gate

**A. No AI inference:** property/unit/tenancy/inspection/area/condition/evidence metadata writes; freeze; reviews, disagreements, maintenance; and views. Most are deterministic contract logic, though writes still use GenLayer's consensus transaction system.

**B. GenVM nondeterminism without vision inference:** `verify_evidence_provenance`. It performs public HTTP GET and compares bounded response metadata and the content SHA-256 independently. This requires URL availability and validator web access, but not `exec_prompt`.

**C. Real image-capable AI:** `observe_nominated_target`, `observe_evidence`, `observe_evidence_pair`, and supplemental visual continuity assessment. They retrieve public original bytes, validate against frozen SHA-256, then call image-enabled `gl.nondet.exec_prompt`. Their validators independently repeat retrieval/interpretation and use application-level equivalence. Static checking does not verify the hosted model integration or factual accuracy; the Stage 5.6 real-photo evaluation remains unverified/blocked.

**Do not activate category C in a user-facing StudioNet mode yet.** These are public contract writes in the candidate; hiding buttons in the UI would not technically disable them. The safest pre-deployment path is either (1) deploy only after a separately approved decision accepting that public surface and explicitly gate these calls in the product, or (2) obtain separate approval for a minimal, reviewed contract-level disable/feature gate before deployment. This readiness task makes no code change and does not choose between those alternatives.

Validator consensus and exact application equivalence show agreement under the configured protocol, not unanimity or real-world truth. Uncertainty and insufficient evidence must remain unresolved.

## 7. Photo and evidence constraints

The browser MVP stores photos as `Blob`s in local IndexedDB. The contract does **not** receive those local bytes. It stores an evidence record with a caller-supplied HTTPS `source_ref`, claimed expected SHA-256, scope/metadata, and status; validators later retrieve the body from that URL. Visual source validation currently allowlists commit-pinned files on `raw.githubusercontent.com/Chinny070/moveout/<40-hex-commit>/...` for the visual paths. Provenance verification validates public HTTPS retrieval with `gl.nondet.web.get`.

Therefore, a locally attached image is not chain evidence, and an on-chain digest/reference does not itself make image bytes available. A content hash is a binding/check, not storage, access permission, authenticity, capture-time proof, or proof that validators saw a live source at the same time. URL content must match the frozen digest at retrieval; validators can fail if it changes/disappears or cannot be reached.

**Minimum technical flow** (not yet implemented): freeze the user-selected image bytes in an evidence process; calculate SHA-256 locally; place the exact bytes at an owner-approved immutable HTTPS location reachable to validators; verify anonymous retrieval and digest parity; submit URL+digest and metadata; freeze evidence and inspection; invoke provenance verification; only then allow the visual operation if separately cleared. Any public image host can expose private property photographs. No storage provider, access-control model, consent flow, retention/deletion policy, or private-to-public export has been approved. Do not upload photographs until the owner explicitly selects and approves a storage/privacy model and specific image.

The frontend currently allows JPEG, PNG, WebP, HEIC/HEIF up to 15 MiB. Contract byte validation supports only PNG/JPEG up to 8 MiB; other formats or larger images become unsupported/invalid in contract provenance validation. The frontend must enforce the narrower contract limits or a separate reviewed format/size path before registering evidence.

## 8. Frontend connection plan

The smallest safe connection is a separate, explicit `StudioNet` mode backed by the supported `genlayer-js` client, leaving the current Demo Mode and its IndexedDB records separate and untouched. Add a clear mode badge/network identifier; never merge local and chain record lists. Connect through a browser wallet provider and show actual chain ID, account, deployed address, real pending/accepted/finalized/rejected state, transaction hash and error as returned. Request explicit wallet confirmation for every write. Do not put private keys in frontend code or browser storage.

The initial connected screen should limit actions to non-AI property/tenancy/inspection metadata, and label participant-entered content as such. It must not upload a local photo automatically, claim the photo is on-chain, or invoke AI observation methods while category C remains uncleared. If the browser wallet/API cannot enforce method allowlisting, keep the contract unconnected until the contract-level AI gate question above is resolved. Maintain an opt-in, user-confirmed export step if an approved evidence host is later selected.

The source has no `package.json` or installed `genlayer-js` dependency, and no browser SDK adapter. Browser integration is consequently a separate implementation task after contract/runtime decisions, not an already supported capability.

## 9. Checks run

The requested suite `scripts/verify_moveout.ps1` and the following additional checks were run after authoring this report:

| Check | Result |
|---|---|
| `gltest tests -q` through the verification script | PASS — 380 passed in 110.40s |
| `genvm-lint lint contracts/moveout_protocol_v1.py` | PASS — 3 checks |
| `genvm-lint check contracts/moveout_protocol_v1.py` (SDK validation) | PASS — 84 methods (49 views, 35 writes) |
| `python -m compileall -q contracts tests` | PASS |
| `scripts/check_stage4_scope.py` | PASS — bounded target/continuity retrieval, vision, and validator scope; no finding writer |
| Benchmark selector scan | PASS — no benchmark-specific production contract reference |
| Configured secret scan | PASS — no match in the contract or Stage 1.1 hardening document (this script's narrow scope) |
| `node --check app.js` | PASS |
| `git diff --check`, `git diff --cached --check` | PASS — Git emitted only a line-ending normalization warning for the pre-existing Stage 5.6A report |
| StudioNet read-only `eth_chainId` | PASS — returned `0xf22f` = 61999 |
| `git ls-remote origin refs/heads/main` | BLOCKED — outbound GitHub 443 connection denied by sandbox; synchronization unknown |

The verification script runs GenLayer direct/local tests plus lint, SDK, syntax, scope, benchmark, and configured secret checks; it does **not** submit transactions and does not prove hosted StudioNet runtime behavior. It reports that it clears the `artifacts` directory before testing. The directory was not inventoried before this run, so its pre-run contents cannot be established from this investigation; the directory was present but empty when checked after the run. The runner did not report an error. The script's secret scan is intentionally narrow (contract and Stage 1.1 hardening document), not a repository-wide credential audit.

## 10. Risks and blockers

1. **Owner transaction approval:** this assignment does not authorize even a disposable contract deployment or any hosted write. First deployment needs a separate explicit approval naming the exact artifact, network, signer, and action.
2. **Unverified public AI surface:** category C methods remain publicly callable on the candidate; hiding UI controls is insufficient to disable them. Stage 5.6 has not validated real-photo accuracy.
3. **Evidence hosting/privacy:** visual methods require validators to fetch public, immutable image bytes. No approved hosting/consent/retention design exists; local IndexedDB photos are unavailable to GenVM.
4. **Cost/funding amount:** a signer and GEN are required; Studio has a faucet, but the exact current minimum/fee is unmeasured. Obtain a current estimate and confirm test GEN availability before any approved write.
5. **Exact current contract hosted compatibility:** local checks pass, but this exact source has not been freshly deployed/exercised on StudioNet in this readiness assignment.
6. **Browser SDK integration:** no SDK dependency, wallet adapter, or chain mode exists in the web MVP.
7. **Legacy format mismatch:** frontend accepts formats/sizes beyond the contract's validated visual evidence boundary.
8. **Remote Git sync:** a subsequent permitted read-only `git ls-remote` succeeded and confirmed `origin/main` at `2dc0b2d8e31bbb99c2da89a61ad4581cb6d7bb24`, matching local HEAD before documentation commit.

## 11. Approval required before the first hosted transaction

Before any deploy/write, obtain owner approval for the exact contract SHA/artifact and StudioNet chain ID 61999; the disposable signer account (never its secret); accepting test-GEN use and any displayed fee estimate; whether to gate public AI methods contract-side; and the selected evidence storage/privacy model before any photograph is uploaded. No approval is implied by this readiness assignment.

## 12. Documentation references

Current official GenLayer references consulted:

- [Networks](https://docs.genlayer.com/developers/networks) — StudioNet endpoint, chain ID, GEN currency, built-in faucet.
- [Network Configuration](https://docs.genlayer.com/developers/intelligent-contracts/deploying/network-configuration) — supported network aliases and hosted/local setup distinctions.
- [CLI Deployment](https://docs.genlayer.com/developers/intelligent-contracts/deploying/cli-deployment) — documented direct deployment syntax and arguments.
- [Deploying Intelligent Contracts](https://docs.genlayer.com/developers/intelligent-contracts/deploying) — deployment is a consensus transaction; fees and finalization must be checked.
- [Development Setup](https://docs.genlayer.com/developers/intelligent-contracts/tooling-setup) — hosted Studio requires no local setup and localnet requires initialization.
- [GenLayerJS SDK](https://docs.genlayer.com/developers/decentralized-applications/genlayer-js) — browser/application SDK overview.
- [Accounts and Addresses](https://docs.genlayer.com/understand-genlayer-protocol/core-concepts/accounts-and-addresses) — signer/key security and contract/Ghost behavior.
- [GenLayer CLI reference](https://docs.genlayer.com/api-references/genlayer-cli) — installed CLI command surface.

## Readiness conclusion

**READINESS STATUS: PARTIAL.** The intended contract, zero-argument constructor, local compatibility checks, active StudioNet alias, chain ID, RPC endpoint, and read-only network reachability are verified. The project is not ready for a safe user-facing connected MVP because transaction authorization, unverified public AI methods, private-photo hosting, wallet flow, fee amount, exact-source hosted execution, and frontend SDK integration remain unresolved. **No deployment, transaction, wallet operation, model call, image upload, Docker initialization, or production code change was performed.**

**Actual deployment performed: NO.**
