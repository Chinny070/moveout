# MoveOut StudioNet MVP Contract Preparation

**Artifact type:** separate restricted StudioNet MVP contract; not deployed.
**Stage result:** local preparation and verification complete; hosted compatibility remains unverified.
**Hosted writes, deployment, paid services, and AI calls:** none.

## 1. Purpose and baseline

The browser MVP is a local Demo Mode. The authoritative protocol source contains public visual-assessment transactions, but real-property image accuracy has not been verified. A user-interface-only block would not stop callers from invoking those public methods directly. This isolated contract artifact keeps the approved non-AI workflow while rejecting those methods at the contract boundary.

Baseline commit: `878660f6f3fc671afa48c95843b69d5195f1b931`. The original contract's reported hash was independently recomputed and matches:

| Artifact | SHA-256 |
|---|---|
| Original `contracts/moveout_protocol_v1.py` | `64D1599DD52F485AF26FF7D1393C6F5345427A49A5471E9E0364CC1FB118582D` |
| Restricted `contracts/moveout_studionet_mvp.py` | `1BCA002294CED3140ED02EADE0E288C8F10DFE1EE5AC08E6C84573B2B139E4BF` |

The original contract file is unchanged. The new file is self-contained and duplicates the compatible protocol implementation to avoid relying on cross-file contract imports or inheritance. It uses the original pinned `py-genlayer` runtime identifier and existing `genlayer` SDK plus Python standard library imports only.

Exact source differences: the contract class and module docstring are renamed/labeled for the restricted StudioNet MVP; the four public AI-dependent method bodies are replaced by the stable deterministic rejection; and the four private methods that performed visual/continuity interpretation are removed. All class storage/type declarations and constants are AST-identical. Every other method is AST-identical to the original. Tests enforce this diff boundary. No changes were made to `moveout_protocol_v1.py`.

## 2. Restriction design

The restricted class is `MoveOutStudioNetMVP(gl.Contract)` with a zero-argument constructor. The four AI/visual entrypoints remain decorated public writes for stable schema discoverability, but their entire bodies immediately call the contract's existing deterministic `_fail` helper:

`MO_ERR_AI_DISABLED:restricted_studionet_mvp`

The rejection occurs before argument validation, remote retrieval, interpretation, idempotency writes, sequence increments, event append, or any other storage mutation. No runtime flag can re-enable the methods. The private evaluator functions that called `gl.nondet.exec_prompt` were removed from the new artifact. Source-level audit finds no `exec_prompt` call or attribute anywhere in the restricted contract. The only retained `gl.vm.run_nondet_unsafe` path is `verify_evidence_provenance`, which independently retrieves and hashes image bytes but does not call a model.

### Disabled AI-dependent public writes (4)

- `observe_nominated_target`
- `observe_evidence`
- `observe_evidence_pair`
- `assess_supplemental_continuity`

These return no synthetic assessment, append no observation/finding, and cannot reach a private evaluator. Existing read-only observation/finding views remain available for schema/read compatibility, but the fresh restricted deployment cannot create those records through any public write.

### Additional unsupported dependent operations

The supplemental request lifecycle methods do not themselves call AI. However, `create_supplemental_request` requires an existing unresolved visual observation; the restricted fresh deployment has no public way to create such an observation. Consequently request creation, linked supplemental inspection/evidence flows, and request closure are not part of the fresh MVP's reachable workflow. Their original validation and terminal-closure code is retained, and regression tests verify the lifecycle behavior separately using a seeded unresolved record. Do not present supplemental visual resolution as available in this MVP.

## 3. Complete public API classification

The SDK validator reports **84 methods: 49 views and 35 writes**, matching the original method surface. Categories:

### Retained non-AI writes (31)

`create_property`, `add_manager`, `remove_manager`, `create_unit`, `create_tenancy`, `activate_tenancy`, `cancel_draft_tenancy`, `request_move_out`, `confirm_tenancy_end`, `create_inspection`, `cancel_empty_inspection`, `create_room`, `create_area_item`, `include_area_in_inspection`, `create_target_nomination`, `create_supplemental_request`*, `create_supplemental_inspection`*, `submit_supplemental_evidence`*, `close_supplemental_request`*, `create_capture_slot`, `create_condition_record`, `create_condition_record_with_prior`, `submit_evidence`, `submit_evidence_for_slot`, `submit_counter_evidence`, `freeze_evidence`, `freeze_inspection`, `verify_evidence_provenance`†, `submit_inspection_review`, `create_disagreement`, `create_maintenance_event`.

`*` Retained lifecycle functions, but unreachable in a clean restricted deployment because the required unresolved visual observation cannot be created by the public API.

`†` Nondeterministic public web retrieval and digest verification; it invokes no AI provider. It requires a public HTTPS source and validators' network access.

### Disabled AI-dependent writes (4)

`assess_supplemental_continuity`, `observe_nominated_target`, `observe_evidence`, `observe_evidence_pair`.

### Retained read-only views (49)

`get_target_nomination`, `list_target_nominations`, `list_area_target_nominations`, `get_supplemental_request`, `list_supplemental_requests`, `get_continuity_assessment`, `list_continuity_assessments`, `get_inspection_completeness`, `get_inspection_receipt`, `get_property`, `get_unit`, `get_tenancy`, `get_inspection`, `get_room`, `get_area_item`, `get_condition_record`, `get_evidence`, `get_evidence_verification`, `get_evidence_verification_status`, `get_visual_observation_record`, `get_established_condition_record`, `get_event`, `list_properties`, `list_managers`, `list_units`, `list_tenancies`, `list_inspections`, `list_rooms`, `list_area_items`, `list_condition_records`, `list_condition_references`, `list_evidence`, `list_evidence_verifications`, `list_property_history`, `list_visual_observations`, `list_established_conditions`, `get_inspection_manifest`, `get_capture_slot`, `get_inspection_review`, `get_disagreement`, `get_maintenance_event`, `list_inspection_rooms`, `list_inspection_area_items`, `list_capture_slots`, `list_inspection_reviews`, `list_disagreements`, `list_counter_evidence`, `list_maintenance_events`, `list_inspection_maintenance_events`.

Read APIs do not create a result or revive an evaluator. They expose only whatever state exists at that new contract address. No finding writer, automated liability operation, or deposit-deduction operation exists in the inspected contract.

## 4. Retained non-AI workflow and frontend interface

This is the smallest source-level workflow for manually recorded inspection metadata. Exact return values below are from the contract source; use the deployed `schema` before building the browser adapter.

| Operation | Parameters | Result | Authorization / type |
|---|---|---|---|
| `create_property` | `property_label, request_id` | Property ID (`str`) | Write; caller becomes initial property manager. |
| `create_unit` | `property_id, unit_label, request_id` | Unit ID (`str`) | Write; property manager. |
| `create_tenancy` | `property_id, unit_id, tenant_address, start_metadata, request_id` | Tenancy ID (`str`) | Write; property manager. |
| `activate_tenancy` | `tenancy_id` | `None` | Write; contract checks draft state/authority. |
| `create_inspection` | `tenancy_id, inspection_type, request_id` | Inspection ID (`str`) | Write; tenancy participant; supplemental type is rejected here. |
| `create_room` | `unit_id, room_label, request_id` | Room ID (`str`) | Write; property manager. |
| `create_area_item` | `room_id, subject_type, label, description_ref, request_id` | Area ID (`str`) | Write; property manager. |
| `include_area_in_inspection` | `inspection_id, area_item_id, request_id` | `None` | Write; validates tenancy/property/unit hierarchy and open state. |
| `create_condition_record` | `inspection_id, area_item_id, condition_type, description, claim_ref, request_id` | Condition ID (`str`) | Write; scoped participant; recorded as participant-supplied, not established truth. |
| `submit_evidence` | `inspection_id, area_item_id, condition_record_id, evidence_type, source_ref, expected_sha256, supersedes_evidence_id, request_id` | Evidence ID (`str`) | Write; validates scope, bounds, and record lifecycle. A caller digest is not independent verification. |
| `freeze_evidence` | `evidence_id` | `None` | Write; original submitter; immutable frozen evidence. |
| `freeze_inspection` | `inspection_id` | `None` | Write; inspection creator; requires complete manifest and frozen evidence. |
| `get_inspection` / `get_evidence` | Record ID | JSON string | Read-only. |
| `get_inspection_completeness` | `inspection_id` | JSON string | Read-only. |
| `list_inspections` / `list_evidence` | Parent ID, `offset`, `limit` | JSON page string | Read-only. |

All writes return GenLayer transaction lifecycle outcomes through the network/SDK, not an immediate guarantee of accepted final state. The browser must wait for finalization, check the authoritative status/result, and reread the record before displaying success. Rejected, undetermined, or failed execution is not successful; never fall back to a leader proposal.

Condition descriptions, claims, evidence references, and digests remain participant/caller-supplied. No call establishes physical truth, authenticity, liability, causation, maintenance responsibility, or deductions. Because contract storage is public, do not store confidential tenant details or private image URLs.

## 5. Evidence and privacy boundary

The existing browser stores original photos locally as IndexedDB `Blob`s; the contract does not receive those bytes. The contract evidence record stores caller-supplied metadata, public URL, and claimed SHA-256. `verify_evidence_provenance` makes validators independently retrieve the image, validate response status/type/format/size, and compare the digest. This verifies fetched bytes against a claim at that time; it does not prove authenticity, capture time, ownership, consent, or availability at a later date.

The visual assessment methods' byte-fetch and image prompt code is removed from this restricted artifact. Thus no public image can reach AI interpretation here, even if provenance verification succeeds. Do not upload private tenant photos to GitHub or other public hosting. The restricted MVP can register metadata only where a suitable public source already exists and consent/security requirements are met; private local photo storage remains Demo Mode only.

## 6. Test and verification results

| Check | Result |
|---|---|
| Restricted-contract Direct Mode tests | PASS — 6 passed in 3.63s |
| Prohibited AI calls / all disabled entries | PASS — four public writes return stable error; state snapshots unchanged; AST verifies no `exec_prompt` attribute and no evaluator helper definitions |
| No alternate public AI path | PASS — audited all 84 public methods; source contains no AI prompt mechanism; the only nondeterministic public write left is byte provenance verification |
| Non-AI record workflow | PASS — property/unit/tenancy, participant inspection, room/area, manual condition, evidence registration, and freezing exercised without a model provider |
| Authorization / frozen lifecycle | PASS for targeted restricted test — outsider freeze rejected; late evidence after inspection freeze rejected; existing frozen evidence remains byte-for-byte unchanged |
| Supplemental terminal closure | PASS for focused lifecycle test — create/close then supplemental inspection/evidence retries rejected. The test seeds the required pre-existing unresolved record; it does not claim that a clean restricted contract can create one |
| Original source hash | PASS — exact baseline SHA-256 preserved |
| `genvm-lint lint` on MVP artifact | PASS — 3 checks |
| SDK validation on MVP artifact | PASS — `MoveOutStudioNetMVP`, 84 methods (49 views, 35 writes) |
| Python syntax | PASS — compile check |
| Full regression suite (including the 6 new tests) | PASS — 386 passed in 70.21s |
| Existing Stage 4 scope / benchmark scan | PASS — no benchmark-specific contract logic; target/continuity scope scan passed |
| Secret / whitespace scans | PASS — no credential pattern in the three new files; no trailing whitespace; repository verification script's configured secret scan also passed |

Direct-mode tests prove deterministic contract gates and local state behavior only. They do not prove StudioNet execution, real validator behavior, AI accuracy, image truth, consensus finality, or unanimity.

The existing test runner logs that it clears the `artifacts` directory. It was not inventoried before the run; after verification it existed but was empty. The verification script's credential scan is scoped to the original contract and Stage 1.1 document; a separate focused credential-pattern scan passed on the new contract, test, and report.

## 7. StudioNet deployment requirements (preparation only)

The installed GenLayer CLI is `0.39.1`; the contract pins `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`. The active CLI configuration was previously verified as `studionet`, chain ID `61999`, RPC `https://studio.genlayer.com/api`. Do not change it. GenLayer documents direct deployment without local Docker. A transaction signer/wallet is required; never expose a key or recovery phrase. GenLayer documentation identifies GEN as the Studio currency and the Studio account selector's faucet as the test-funding path: open Studio's account selector and use its faucet control if the selected test account needs GEN. Exact funding amount is unknown.

The installed CLI's deployment syntax is `genlayer deploy --contract <path> [--rpc <url>] [--args ...]`. No fee-estimation-only invocation was verified for the installed CLI; the documented `deploy` command submits a transaction, so do not use it to obtain an estimate. The exact proposed command for this zero-argument artifact is below and **must not be run without a later explicit owner deployment authorization**:

```powershell
genlayer network info
genlayer deploy --contract contracts/moveout_studionet_mvp.py --rpc https://studio.genlayer.com/api
```

No non-mutating deployment-fee estimate was verified in the installed CLI. The exact minimum GEN balance/fee is unknown. Do not use `deploy` to estimate: it submits. After separately authorized deployment, retain the real transaction hash/address, wait for actual finalization and successful execution, then check `genlayer receipt <transaction-hash>`, `genlayer schema <contract-address>`, `genlayer code <contract-address>`, and a safe read-only `genlayer call` to verify schema and initial state. A returned Ghost address without a successful finalized GenVM result is not a usable deployment.

Current docs consulted: [Networks](https://docs.genlayer.com/developers/networks), [Network Configuration](https://docs.genlayer.com/developers/intelligent-contracts/deploying/network-configuration), [CLI Deployment](https://docs.genlayer.com/developers/intelligent-contracts/deploying/cli-deployment), [Deploying Intelligent Contracts](https://docs.genlayer.com/developers/intelligent-contracts/deploying), [GenLayer CLI](https://docs.genlayer.com/api-references/genlayer-cli), [Accounts and Addresses](https://docs.genlayer.com/understand-genlayer-protocol/core-concepts/accounts-and-addresses).

## 8. Remaining risks and future path

- Local lint/SDK compatibility is **not** StudioNet runtime verification. No hosted deployment or write is authorized or performed here.
- Public methods still have a sufficiently large API and storage schema for non-AI records; source duplication creates maintenance drift risk. Any future production changes must remain separately reviewed and never silently replace `moveout_protocol_v1.py`.
- Users can still submit public evidence URLs/digests, but no privacy-preserving image host has been approved. Do not claim local photos are registered or available to validators.
- Supplemental request creation depends on an unresolved AI observation; it is not reachable in the clean restricted contract. A future manually initiated supplemental workflow needs a separately designed, authorized non-AI basis rather than synthetic findings.
- No real-photo model evaluation, GenVM image inference, visual consensus, AI finding, liability, or deposit automation is enabled or verified.
- Future visual capability should use a separately reviewed artifact only after rights-cleared real-photo evaluation, conservative target visibility/continuity tests, and separately authorized hosted validator verification. Never add a switch that makes this restricted deployment's AI methods caller-reenableable.

## 9. Final status

**STAGE STATUS: PASS for the restricted local MVP artifact and offline verification; BLOCKED for hosted compatibility until a separately authorized StudioNet execution.**

The new artifact SHA-256 is `1BCA002294CED3140ED02EADE0E288C8F10DFE1EE5AC08E6C84573B2B139E4BF`. The original production contract SHA-256 remains `64D1599DD52F485AF26FF7D1393C6F5345427A49A5471E9E0364CC1FB118582D`.

The active CLI network was previously read as StudioNet (`https://studio.genlayer.com/api`, chain ID `61999`); the readiness investigation made a read-only chain-ID request and did not alter that configuration. A transaction signer is required for deployment. Studio documentation lists GEN and a built-in account-selector faucet. Exact current deployment funding remains unknown, and the installed deployment command is not a non-mutating fee estimator. Do not deploy to obtain an estimate.

No deployment, StudioNet write transaction, wallet operation, model call, paid provider, Docker initialization, or production contract modification was performed. This is not a claim of StudioNet compatibility, hosted finality, model accuracy, or image evidence truth.
