# MoveOut StudioNet Frontend Integration

Status: implementation and local verification complete; real browser-wallet signing remains untested. No hosted write transaction was submitted.

## Network and deployed contract

- Network: GenLayer StudioNet, chain ID `61999`.
- RPC: `https://studio.genlayer.com/api`.
- Contract: `0x4F96B354b19541F7087b73c548Dc2db380e09b77`.
- Deployment transaction: `0x42827f514669e1b8f1ca35b77513d0fc6ca9402aaa0bd92e9d00007e1c6cf809`.
- Authorized deployed source SHA-256: `1BCA002294CED3140ED02EADE0E288C8F10DFE1EE5AC08E6C84573B2B139E4BF`.
- Frontend SDK: pinned `genlayer-js@1.1.8`, the installed SDK version checked against its shipped chain/schema/client types and implementation. Vite is pinned at `8.3.4`.

The frontend obtains the contract schema from StudioNet at runtime before enabling reads. The installed SDK schema shape was inspected (`methods` is a name-keyed record and `params` is an array of `[name,type]` pairs) and the interface is built from those actual entries. The deployed schema has 84 methods. The SDK read verified `list_properties(creator:string, offset:int, limit:int)` and returned `{"has_more":false,"items":[],"next_offset":0}` for the authorized wallet address at `LATEST_FINAL`. This was a read-only request.

## Mode separation

Demo remains the default. Existing `app.js`, IndexedDB database `moveout-demo-v1`, store `inspections`, and browser-local photo workflow were preserved. The app and local-only “New inspection” shortcut are hidden in StudioNet mode. The mode footer also changes with the selected mode. Returning to Demo reveals the existing local app and its existing browser data.

StudioNet mode has its own root element and calls the contract directly. It does not read from IndexedDB and does not display or upload locally stored Demo photos. Contract state is read using `transactionHashVariant: 'latest-final'`. A user may query a creator address in public read mode without connecting a wallet. An empty response is shown as an empty contract state; no records are fabricated.

## Read method mapping

| Frontend record view | Deployed view methods |
| --- | --- |
| Property list/details | `list_properties`, `get_property` |
| Property units | `list_units`, `get_unit` |
| Tenancies and inspection history | `list_tenancies`, `get_tenancy`, `list_inspections`, `get_inspection`, `list_property_history` |
| Unit rooms and room area items | `list_rooms`, `get_room`, `list_area_items`, `get_area_item` |
| Inspection areas and condition notes | `list_inspection_area_items`, `list_condition_records`, `get_condition_record`, `get_inspection_completeness` |
| Evidence metadata | `list_evidence`, `get_evidence` |

Lists request up to the contract’s page maximum (50). This first frontend slice does not yet offer next-page navigation when `has_more` is true. Inspection details display actual returned areas, participant condition records, evidence metadata, and completeness. They carry a visible caution that these records do not constitute AI-verified damage, liability, or deposit conclusions.

## Wallet and prepared writes

Connection uses an explicit EIP-1193 `eth_requestAccounts` action and reads `eth_chainId`; it never asks for keys or seed phrases. Wrong chain blocks writes and offers a user-triggered StudioNet switch/add-chain request. Account and chain change events update the UI without prompting for accounts again. “Disconnect” clears the app’s selected account; it does not revoke wallet-site permission.

The wallet-backed GenLayer JS client is constructed only after an explicit connection and a chain 61999 check. The frontend does not invoke the SDK’s `connect()` helper because the pinned 1.1.8 implementation performs GenLayer Snap setup; it uses the documented EIP-1193 provider/account client configuration after explicit standard account authorization and local chain verification.

Every write method is gated by an application allowlist and a confirmation dialog that shows the network, contract, method and submitted fields. Cancel closes the dialog without calling `writeContract`. The wallet opens a second confirmation step. The installed SDK implementation estimates transaction gas, requests `eth_gasPrice`, then requests wallet submission. This UI does not calculate a separate fee quote or impose a maximum-fee cap; the wallet’s transaction screen is the final review point. If a transaction hash is returned but a finalized receipt cannot be read, the hash remains in the warning and the UI explicitly says not to resubmit.

Prepared operations map to contract methods as follows:

| UI operation | Contract method and notes |
| --- | --- |
| Create property | `create_property(property_label, request_id)` |
| Register unit | `create_unit(property_id, unit_label, request_id)` |
| Create draft tenancy | `create_tenancy(property_id, unit_id, tenant_address, start_metadata, request_id)`; user must select/enter an existing unit ID. Only the designated tenant may activate. |
| Activate draft tenancy | `activate_tenancy(tenancy_id)`; shown only when the connected address matches the returned tenant field and chain is correct; the contract remains authoritative. |
| Request move-out | `request_move_out(tenancy_id)`; shown for ACTIVE tenancy. |
| Create inspection | `create_inspection(tenancy_id, inspection_type, request_id)`; UI maps DRAFT to MOVE_IN, ACTIVE to PERIODIC, and MOVE_OUT_PENDING to MOVE_OUT. The contract rejects invalid state/type combinations. |
| Add room / area | `create_room(unit_id, room_label, request_id)` / `create_area_item(room_id, subject_type, label, description_ref, request_id)` |
| Include area in inspection | `include_area_in_inspection(inspection_id, area_item_id, request_id)` |
| Record participant note | `create_condition_record(inspection_id, area_item_id, condition_type, description, claim_ref, request_id)`; this is explicitly a participant assertion, not a verified finding. |
| Register evidence metadata | `submit_evidence(inspection_id, area_item_id, condition_record_id, evidence_type, source_ref, expected_sha256, supersedes_evidence_id, request_id)`; metadata only. The contract requires an allowed immutable image source and digest for PHOTO evidence. |

These are prepared interfaces only. No hosted writes were made during this task. Write transactions have not been exercised in a browser wallet.

## AI safety and evidence boundaries

The UI has an explicit allowlist for view and write calls. It contains none of the disabled AI methods `observe_nominated_target`, `observe_evidence`, `observe_evidence_pair`, or `assess_supplemental_continuity`; these are not reachable from the interface. There is no photo upload, AI assessment, damage automation, liability determination, or deposit deduction operation. Evidence registration is a URL/digest metadata operation only and relies on the contract’s pinned-source validation.

## Setup and verification

From the repository root:

```sh
npm install
npm run dev
npm run build
npm run test:frontend
python -m pytest -q
```

Verified in this implementation:

- Production build succeeded with Vite 8.3.4. Vite reports the GenLayer SDK bundle exceeds its 500 kB advisory threshold; output is about 552 kB uncompressed / 120 kB gzip.
- Eight deterministic frontend tests passed: chain ID parsing, explicit public-account request, wrong-network reporting, missing-provider behavior, add/switch network behavior, disabled AI allowlist exclusion, cancel-without-write and confirm-once behavior.
- Existing Python suite: `386 passed`.
- Read-only StudioNet SDK schema and `list_properties` query succeeded as recorded above.
- Local browser opened and rendered the Demo Mode home screen. Full wallet interaction was not performed.
- No hosted transaction or wallet prompt occurred.

The package install generated ignored `node_modules/`, `dist/`, and `package-lock.json` is tracked as the reproducible dependency lock. No `app.js` behavior or contract source was changed.

## Remaining limitations and owner actions

1. Test connection in the owner’s browser wallet, verify StudioNet is selected, then test only public reads first. Actual wallet account events and network switching are covered by mocks, not a real wallet.
2. Review the wallet’s fee/gas fields before approving any first write. Although SDK 1.1.8 estimates gas and asks for `eth_gasPrice`, StudioNet’s wallet prompt is authoritative and this integration has not exercised it.
3. Obtain separate authorization before any write transaction. This work intentionally submitted none.
4. For an end-to-end first inspection, use the manager wallet to create a property and unit, create a tenancy with the tenant’s public address, connect as that tenant to activate, then create a MOVE_IN inspection. Create rooms and area items; include each desired item in that inspection. Record participant notes as such. Only register evidence metadata after an immutable permitted URL and matching SHA-256 are independently ready. Read finalized state back after each approved operation.
5. Contract method failures, participant role enforcement, and transaction finality should be verified through a separately authorized disposable or owner-approved StudioNet write sequence. This integration has not claimed those hosted write behaviors as browser-tested.
6. Pagination, search filters, and deeper cross-navigation can be added after the first read/write smoke test. There are no frontend writes to disabled AI methods.

## References

- [GenLayerJS API reference](https://docs.genlayer.com/api-references/genlayer-js)
- [GenLayerJS contract methods](https://docs.genlayer.com/api-references/genlayer-js/contracts)
- [Reading from Intelligent Contracts](https://docs.genlayer.com/developers/decentralized-applications/reading-data)
- [Writing data from decentralized applications](https://docs.genlayer.com/developers/decentralized-applications/writing-data)
- [Transaction methods](https://docs.genlayer.com/api-references/genlayer-js/transactions)
- [GenLayer JS 1.1.8 package](https://www.npmjs.com/package/genlayer-js/v/1.1.8)
