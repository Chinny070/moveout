# MoveOut Browser Demo

## What works

This repository did not have a web frontend. The current MVP is a lightweight, static **Demo Mode** browser application for the basic inspection journey:

- Create a property inspection with optional property and unit labels.
- Add rooms or other inspection areas.
- Record manual, dated visible-condition notes per area.
- Attach and preview photographs per area.
- Review counts, records, status, and prior inspections from the history screen.
- Mark a review complete or reopen it.
- Remove a note, photo, area, or inspection from this browser.
- Refresh the page and return to locally saved records.

Notes are user-entered. The app does not assess property condition with AI and does not make legal, liability, deposit, or deduction decisions.

## Run locally

From the project root in PowerShell, run:

```powershell
python -m http.server 5173 --bind 127.0.0.1
```

Then open <http://127.0.0.1:5173> in a current desktop or mobile browser. Stop the server with `Ctrl+C`.

No package installation or build step is required. The app consists of `index.html`, `styles.css`, and `app.js`.

## Data, photographs, and network behavior

- This is **Demo Mode**, not the GenLayer contract application. It does not connect to StudioNet or any blockchain, does not write to chain, and does not claim validator consensus.
- Inspection metadata, condition notes, and photo blobs are stored in the current browser profile using IndexedDB. Refresh persistence is supported. Clearing browser site data, using another browser/profile/device, or browser storage eviction can remove the records. This is not a server backup or a durable evidence archive.
- Photos are not uploaded to an AI provider, MoveOut server, or blockchain by this app. The static app makes no third-party font, analytics, or model requests. Browser/network tooling may still fetch the app itself from the local HTTP server.
- Browser-local records are not encrypted by MoveOut. Use demonstration data only; do not enter sensitive personal information or use a shared browser profile for private evidence.
- Accepted photo formats are JPEG, PNG, WebP, and HEIC/HEIF where the browser supports previewing them; the per-file upload limit is 15 MB. Actual preview format support depends on the browser.

## Verify the complete workflow

1. Start the local server and open the URL above.
2. Confirm the `DEMO MODE` banner and `Local only · Not on-chain` status are visible.
3. Select **Start an inspection**, add optional property/unit labels, and create it.
4. Add a room such as “Living room”; select it in the area list.
5. Enter a visible condition note and category, then add it. Confirm it appears with a timestamp.
6. Attach a small JPG or PNG. Confirm the thumbnail and timestamp appear. Try another room to confirm evidence is area-scoped.
7. Return to **All inspections** and confirm the record, status, area, and photo counts appear. Reopen it and review the notes/photo.
8. Refresh the browser. Confirm the inspection and its photo remain available in that same browser profile.
9. Optionally mark the review complete, reopen it, and remove demo records when finished.

Do not interpret a local demo record as a frozen, verified, or on-chain evidence record.

## Not available

- GenLayer wallet, contract read/write, validator execution, transaction submission, or consensus.
- AI inference, visual verdicts, evidence digests/provenance verification, or frozen-evidence semantics.
- User accounts, landlord/tenant roles, collaboration, remote synchronization, access control, or cloud backups.
- Production privacy, encryption-at-rest, legal compliance review, or export/import recovery.

## Production requirements

A production release needs a separately authorized and reviewed integration to deployed GenLayer contract addresses and wallet flows, secure authentication/authorization, server or client evidence digest/freeze behavior matching the approved protocol, privacy/security review, backup and recovery, accessibility and cross-browser testing, and actual runtime/validator verification. None of those capabilities is implied or implemented by this local browser demo.

## Verification performed (2026-10-09)

- `node --check app.js`: **PASS**.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify_moveout.ps1`: **PASS** — 380 tests passed; GenVM lint passed (3 checks); SDK validation passed (`MoveOutProtocolV1`, 84 methods); Python syntax and nondeterministic scope/benchmark scans passed.
- Dedicated frontend test/build scripts: **NOT PRESENT**; this is a no-build static app with no JavaScript test framework.
- Local server: **STARTED** on `http://127.0.0.1:54321/`; HTTP returned 200 and the browser fetched the app, CSS, and JavaScript successfully.
- Browser smoke workflow: application load **PASS**; inspection creation **PASS**; area creation **PASS**; manual condition entry **PASS**; history listing/reopen **PASS**; reload and IndexedDB record/condition persistence **PASS**; review-complete status transition **PASS**.
- Browser photo file selection and preview: **NOT VERIFIED**. The in-app browser automation did not expose a usable native file chooser. The file input/preview/storage code is present, but photo attachment is not counted as an E2E pass. Use the manual workflow above with a small JPG or PNG; then refresh and check that the preview remains.
- Complete browser E2E: **PARTIAL**, due to the photo-picker limitation. No GenLayer, AI, network, or production behavior was exercised.
- One local test record (“MVP Demo Property”) was created during the browser smoke test and remains in the local in-app browser profile as a demonstration record. It contains no photograph or personal data. The user can remove it using the app's normal delete flow.
