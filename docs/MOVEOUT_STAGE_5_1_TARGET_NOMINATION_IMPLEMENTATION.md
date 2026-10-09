# MoveOut Stage 5.1 — Target Nomination and Versioned Storage

**Status: locally implemented and validated.** This stage adds immutable target-nomination metadata and snapshot membership only. It does not interpret or classify image content. There was no deployment, hosted transaction, migration, or Stage 5.2/5.3 work.

## Scope and baseline

Stage 5.1 started from `5cd9859d464d2569a964e60714cac7023f69857f`, after reading Stage 4.3–4.7 reports. Stage 4.7 remains authoritative: majority consensus is not unanimity; no target identity is invented; uncertainty remains explicit; observations do not determine liability or deposits; frozen records are immutable.

Changed files:

- `contracts/moveout_protocol_v1.py` — additive target nomination storage, APIs, digest, validation, and inspection freeze snapshot support.
- `tests/test_moveout_stage51_target_nomination.py` — deterministic Direct Mode tests for the new storage/API invariants.
- `docs/MOVEOUT_STAGE_5_1_TARGET_NOMINATION_IMPLEMENTATION.md` — this implementation and validation record.

No existing inspection, evidence, digest, visual observation, finding, Established Condition, or prompt was rewritten. No supplemental-photo API was added.

## Target nomination record

Each record is stored in `target_nominations` under a contract-generated `TARG-N` ID. Its immutable fields are:

| Field | Rule |
|---|---|
| `digest_domain`, `schema_version` | Fixed to `MOVEOUT_TARGET_NOMINATION_V1` and schema version `1`. |
| `target_id`, `target_version` | Contract-generated ID and integer version beginning at 1. IDs are not caller-supplied. |
| `target_identifier` | Required lowercase ASCII slug (letters, digits, `-`, `_`), max 64 chars; unique within one inspection+area. It is the participant’s nomination label, not a model-generated location. |
| `target_description` | Bounded participant-authored text, max 240 chars; it may be empty when the nominated identifier itself is used. |
| `inspection_id`, `property_id`, `unit_id`, `tenancy_id`, `room_id`, `area_item_id` | Resolved from existing contract records and checked against the inspection/area hierarchy. |
| `reference_evidence_id`, `reference_digest` | Optional reference photo binding. If present, the evidence must be a frozen PHOTO in the same inspection/area. The digest is copied from stored `expected_sha256`; the caller cannot submit or substitute a digest through this API. |
| `reference_digest_status` | `CALLER_ASSERTED_EXPECTED_SHA256` when a reference photo is present, otherwise `NONE`. This records the digest’s status at nomination time; it is not a claim that the bytes were fetched. |
| `reference_verification_id` | Empty in the immutable nomination. Provenance verification requires the entire inspection to be frozen, so it cannot be embedded at the pre-freeze nomination boundary. |
| `reference_capture_slot_id` | Optional same-inspection/area capture-slot association. If omitted but the reference photo has a slot, that slot is resolved from the frozen evidence record. This records workflow association only. |
| `region_box` | Optional user-supplied normalized region anchored to the exact reference evidence ID+digest. The API encoding is a four-item JSON tuple `[x_min,y_min,x_max,y_max]`; stored form uses named fields. Each coordinate is an integer in `[0,10000]`; minima must be less than maxima. A box requires a reference photo. |
| `creator`, `creator_side`, `created_at` | Sender and tenant/manager participant side, plus contract timestamp. |
| `supersedes_target_id` | Empty for version 1; otherwise points to the latest same-identity nomination in the same inspection and area. |
| `target_nomination_digest` | Computed SHA-256 digest described below. |

The box and identifier are participant claims about what to inspect. The contract does not infer physical position, validate pixels, or establish that another photograph depicts the same physical target.

## APIs

- `create_target_nomination(inspection_id, area_item_id, target_identifier, target_description, reference_evidence_id, reference_capture_slot_id, region_box_json, supersedes_target_id, request_id) -> target_id` — authorized, idempotent creation. There is no caller-selected target ID.
- `get_target_nomination(target_id) -> JSON` — returns the immutable record plus derived lifecycle and current reference-provenance status.
- `list_target_nominations(inspection_id, offset, limit) -> JSON page` — stable ordered, bounded pagination.
- `list_area_target_nominations(inspection_id, area_item_id, offset, limit) -> JSON page` — scoped ordered pagination.

No public update or delete endpoint exists. A correction while the inspection is open creates a new version by explicitly superseding the current version; prior fields/digest remain unchanged. Reusing the superseded version, another identity, or a target from another inspection/area is rejected. The logical identity key is a canonical JSON array of `(inspection_id, area_item_id, target_identifier)`, not ambiguous string concatenation.

The `region_box_json` encoding is positional JSON array form in fixed field order, rather than a JSON object, so duplicate object keys cannot produce a different parse/canonicalization interpretation. The returned record always uses named coordinates.

## Authorization, scope, and lifecycle

- Creation reuses `_record_parent_context`: the inspection must be open, the tenancy must be live, and property/unit/room/area relationships must match.
- The sender must be a tenant or authorized property manager participant. The creator address and participant side are stored. No unrestricted actor path was introduced.
- A reference evidence ID must resolve to a frozen PHOTO under exactly the same inspection, room, area, and tenancy. An explicit capture slot must match those parents and the reference evidence’s slot if one exists.
- The target identifier is unique per inspection+area. A later version must explicitly supersede the latest same-identity target. Generated target IDs are global within the contract sequence and cannot be selected/reused by users.
- New targets are added only while the parent inspection is open. `freeze_inspection` copies target IDs into `contents_committed.target_nomination_ids`. This is the freeze boundary; there is no standalone mutable target-freeze operation.
- Target records themselves are not rewritten at freeze. Read APIs derive `lifecycle_status` as `NOMINATED`, `FROZEN`, or `SUPERSEDED`, plus `is_latest_version`. Corrections do not erase prior records.
- Existing frozen inspections/evidence are not edited. Legacy inspections missing nomination fields are read with an empty nomination set and freeze/read compatibility behavior; historical evidence digests remain untouched.

## Digest and evidence-provenance guarantees

`target_nomination_digest` is SHA-256 over a canonical JSON object containing a fixed allowlist of immutable record fields, including schema/domain, generated target ID/version, target identifier/description, all parent IDs, evidence ID and expected digest, digest-status label, slot/box references, creator/side/time, and supersession link. Serialization uses the contract’s existing `_json`: `json.dumps(..., sort_keys=True, separators=(",", ":"))`, then UTF-8 bytes. The SHA-256 implementation is the same Python `hashlib.sha256(...).hexdigest()` already used by this contract’s idempotency/provenance logic. Field ordering is canonical; no raw concatenation is used.

The image digest and the nomination digest mean different things:

1. The evidence’s `expected_sha256` is a value supplied when evidence is submitted. At nomination time, the target record binds that stored expected digest and explicitly marks it `CALLER_ASSERTED_EXPECTED_SHA256`.
2. Evidence provenance verification is only available after the whole inspection is frozen. The target read API therefore exposes a **derived** `reference_provenance` object using the latest existing evidence-verification record (`CALLER_ASSERTED_UNVERIFIED`, `VERIFIED_RETRIEVED_SHA256`, `DIGEST_MISMATCH`, or the recorded failure outcome) without mutating the target record or its digest.
3. A digest match proves the retrieved bytes match the submitted expected digest under the provenance verifier. It does not prove who physically captured the image, when it was captured, where it was captured, or that it depicts the nominated target.

Thus target creation does not claim a verified image hash when only a caller assertion exists. Stage 5.2+ must require the appropriate verified provenance state before using the image for visual interpretation.

## Backward compatibility

- Existing inspection records do not need target keys to be read or listed.
- Legacy frozen snapshots retain their prior field set; completeness checking accepts legacy snapshots without `target_nomination_ids` while checking the new field in snapshots created by this version.
- New inspections include target nomination membership in the freeze snapshot, including an empty list when none exist.
- Existing evidence IDs, expected digests, verification records, and observations are untouched.
- This is source/schema compatibility only. No deployed-instance migration or storage-layout upgrade was performed or authorized. A later deployment plan must handle existing contract addresses explicitly.

## Tests added

`tests/test_moveout_stage51_target_nomination.py` contains **29 passing test cases** (including parameterized malformed-coordinate variants) covering:

- authorized tenant creation and outsider rejection;
- invalid inspection/area; exact parent/evidence/slot scope;
- duplicate identity, explicit immutable next version, latest/superseded state, and global contract-generated IDs;
- schema version, identifier constraints, canonical digest determinism, fixed-order box validation, and coordinate bounds;
- digest status distinction for caller assertion, successful later retrieval verification, and digest mismatch;
- frozen inspection membership, late-write rejection, no update/delete API, and unchanged evidence/digests;
- legacy records with no nomination field;
- multiple targets, inspection/area listing, paging, idempotency, and incompatible supersession rejection.

These Direct Mode tests establish deterministic storage and callback/API behavior only. They do not establish StudioNet/hosted compatibility, consensus, target localization, physical continuity, or visual-model accuracy.

## Validation and deferred scope

Full `scripts/verify_moveout.ps1` results are recorded in the completion response. No hosted check is included or implied.

Deferred explicitly:

- **Stage 5.2:** target visibility observation schema, image interpretation, no-absence gates, exact safety-critical equivalence, and majority-aware unresolved semantics.
- **Stage 5.3:** supplemental request/inspection creation, new supplemental evidence lifecycle, relation/index storage, and visual target-continuity judgments.
- **Stage 5.4:** adversarial evaluation, blinded visual accuracy study, and separately authorized hosted consensus/finality/reread verification.

No visual prompt, damage classification, finding promotion, liability/deposit handling, deployment, migration, or hosted transaction was performed. Stage 5.2 and later stages are not started or authorized by this implementation report.
