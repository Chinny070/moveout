# MoveOut Live StudioNet Browser E2E

Status: live browser panel implemented and loaded; no wallet was connected and no write transaction was submitted. This is not an end-to-end pass until an owner approves the writes and the panel verifies finalized state.

## Target deployment

- Network: StudioNet, chain ID `61999`.
- RPC: `https://studio.genlayer.com/api`.
- Contract: `0x4F96B354b19541F7087b73c548Dc2db380e09b77`.
- Expected authorized source SHA-256: `1BCA002294CED3140ED02EADE0E288C8F10DFE1EE5AC08E6C84573B2B139E4BF`.
- No contract source was edited or deployed during this work.

## Live workflow

In StudioNet mode the app presents **MoveOut — Live StudioNet Test**. It uses the actual deployed schema and GenLayer JS client, not a mocked contract response. The `?mode=studionet` query parameter opens StudioNet in public read mode and does not touch the wallet.

The visible test sequence is:

1. Connect explicitly with EIP-1193 `eth_requestAccounts`.
2. Read and verify `eth_chainId === 61999`; wrong-chain state blocks writes.
3. Create a unique, fictional property via `create_property`; verify `list_properties` contains its ID, label, and creator.
4. Register a unit via `create_unit`; verify `list_units` shows its parent property and label.
5. Create a tenancy via `create_tenancy`; the owner must enter a second public test-account address. The contract rejects manager-as-tenant. Verify `list_tenancies` reports the expected DRAFT tenancy.
6. Create a MOVE_IN inspection on that DRAFT tenancy via `create_inspection`; the connected manager is a participant under the deployed contract rules. Verify `list_inspections` returns it.
7. Create a room and surface area via `create_room` and `create_area_item`, then include the area via `include_area_in_inspection`; verify each with its contract view.
8. Record a fictional `MAINTENANCE_NOTE` through `create_condition_record`; verify the exact manual note in `list_condition_records`.
9. Read the property, unit, tenancy, inspection, room, area, and condition record individually and compare IDs, parent links, creator/tenant, and labels to the expected values.

The room, area, inclusion, tenancy, and inspection items are individually confirmed transactions. Each write has a unique idempotency request ID and a separate confirmation dialog that shows the exact method, parameters, wallet, network, and contract. The owner must then approve or reject the request in their own wallet.

The panel persists its run metadata in `sessionStorage` under `moveout-studionet-e2e-v1`; this data is separate from Demo Mode's IndexedDB and contains no photographs. A rejected write is marked REJECTED. A returned hash with a missing/unknown final receipt is marked UNRESOLVED. A finalized execution error or state mismatch is FAILED. Each of these freezes downstream steps; there is no automatic retry. A successful step becomes PASS only after `FINALIZED`, `FINISHED_WITH_RETURN`, and an actual matching contract read.

## Test data and role requirements

Generated labels are suffixed with a unique run ID. The tenant address field must be populated by the owner with a different test account from the property manager. It is public address data, not a private key. The test tenancy remains DRAFT; no activation is needed for manager participation in a MOVE_IN inspection. No real people, real tenancies, property photographs, external AI, or disabled AI method is used.

All accepted writes become permanent StudioNet records; the UI warns about that before starting. Do not proceed unless these test records are desired and the connected account has sufficient testnet balance. The application surfaces SDK/wallet errors and retains any transaction hash for manual status investigation.

## Browser and live-read evidence

- Local website: `http://127.0.0.1:5174/?mode=studionet` (Vite development server is running).
- Browser accessibility snapshot confirmed the rendered StudioNet workspace and panel, `Chain 61999`, the exact configured contract address, all ordered test actions, no connected wallet, and locked write steps.
- The page loaded the real deployed contract schema using SDK 1.1.8; the contract schema contained 84 methods.
- A live, read-only `LATEST_FINAL` call to `list_properties` for the authorized manager address returned `{"has_more":false,"items":[],"next_offset":0}`. No transaction was sent.
- Demo Mode still renders separately and remains the default at `/`.
- The browser-control surface used here exposes page accessibility snapshots but no browser-console API. Vite showed no server-side transform/runtime errors during the page load; browser DevTools console was not directly inspected.
- No wallet connection was requested; no wallet extension was opened or approved.

## Verification

- `npm run build`: passed; Vite reports its SDK bundle is above the 500 kB advisory threshold.
- `npm run test:frontend`: 12 passed. Coverage includes explicit confirmation/cancellation, no disabled-AI method in either allowlist, ordered dependency progression, receipt finality classification, and exact state matching.
- `python -m pytest -q`: 386 passed.
- `git diff --check`: passed (line-ending warnings only for existing working-copy normalization; no whitespace errors).

These local tests do not prove owner-wallet approval or hosted write execution. No test transaction hash exists.

## Owner action to continue

1. Open the local URL in the browser profile containing the intended wallet.
2. Confirm StudioNet (61999) is selected and connect deliberately.
3. Verify the manager address shown is the intended disposable/test account.
4. Supply a second test account address for the designated tenant.
5. For each transaction, review both the app’s exact-call dialog and wallet details. Approve only if the network, account, and method are expected. The next test button unlocks only after finalized successful execution and readback.
6. If a hash appears with an uncertain outcome, stop and inspect that hash; do not re-submit.

No owner transaction approvals have occurred. No commit or push was made; the Stage 5.6A/B report changes remain preserved.
