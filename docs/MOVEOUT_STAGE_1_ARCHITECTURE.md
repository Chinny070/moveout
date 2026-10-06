# MoveOut Stage 1 — Deterministic Protocol Foundation

**Status: implemented for local verification; not deployed.** This contract establishes identity, authority, lifecycle, evidence, and history records for MoveOut. It performs no visual or other AI adjudication. It does not make a participant's condition claim into an established finding.

Stage 1 keeps MoveOut's property-inspection product: a Property Condition Passport built from guided inspections, stable room/area identities, frozen evidence, condition records, maintenance and repair context, and later visual comparisons. This stage supplies the protocol records those flows need; it does not implement a frontend, backend, deposit workflow, or production visual decision system.

## GenLayer fit and contract boundary

The single-file contract is [`moveout_protocol_v1.py`](../contracts/moveout_protocol_v1.py), pinned to the StudioNet-supported runner `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`.

This version is deterministic by design. It uses ordinary storage reads/writes, typed persistent `TreeMap` fields, GenLayer transaction context, and deterministic input validation. It contains no web retrieval, prompt execution, render, or nondeterministic equivalence call. Stage 0's image work remains disposable research; this contract does not extend or import a benchmark contract.

GenLayer is materially useful to the future MoveOut protocol when validators must interpret frozen images and related repair evidence. Stage 1's deterministic contract supplies that later process with stable property/area/evidence IDs, frozen digests, authorization, append-only records, and bounded results. It does not invoke validators for that interpretation yet.

## Hierarchy, IDs, and parent binding

The relationship is:

```text
Property
└── Unit
    ├── Room
    │   └── Area / Item
    └── Tenancy
        └── Inspection
            ├── Condition Record
            └── Evidence
```

Each record also stores the parent IDs needed to reconstruct its complete context. Inspections copy the Property and Unit IDs from their Tenancy. Conditions and Evidence copy Property, Unit, Tenancy, Inspection, Room, and Area/Item IDs from validated parents. A caller cannot supply a different parent tuple.

The contract generates monotonically increasing, typed IDs such as `PROP-1`, `UNIT-1`, `TEN-1`, `INSP-1`, `ROOM-1`, `AREA-1`, `COND-1`, `EVID-1`, and `EVT-1`. Each record kind has its own persisted `u256` sequence; the type prefix prevents cross-kind collisions. IDs are stable within this contract instance and are not derived from labels or caller text. The contract never accepts a caller-selected record ID.

Labels are bounded display metadata. Room names do not identify a room; `ROOM-*` does. V1 creates room and area metadata once and exposes no rename, delete, reparent, or reassignment method. A correction to a frozen evidence item is a new evidence record with an explicit supersession relationship.

## Storage layout

Persistent data uses typed `TreeMap[str, str]` record maps; each value is a canonical JSON string. Parent-to-child indexes are also bounded JSON ID arrays stored in `TreeMap[str, str]`. This makes returned pages and record sizes explicit and avoids persisting untyped Python collections or nested user-constructed `DynArray` values. The latter pattern passed static SDK checks but failed in Direct Mode because the GenVM `DynArray` type cannot be instantiated by contract code; the implementation was changed to the tested JSON-index representation.

The maps cover properties, units, tenancies, inspections, rooms, areas/items, participant Condition Records, Evidence, future Visual Observation Records, future Established Condition Records, lifecycle events, request-idempotency entries, manager authority, unit occupancy, open unit/tenant pairs, and supersession links. The observation and established-condition maps have no public write path in Stage 1.

## Authority model

Address strings are parsed as GenLayer `Address` values and stored in checksum form. Read methods are public because contract records are public chain data. A write checks the relevant role; knowing an ID does not grant write authority.

| Action | Authorized actor |
|---|---|
| Create a Property | Any address; it becomes the Property creator and permanent primary manager. |
| Add or revoke managers | Property creator only; creator authority cannot be revoked. |
| Create a Unit, Room, or Area/Item | Active Property manager. |
| Create a Tenancy | Active Property manager; tenant is a designated address. |
| Activate a DRAFT Tenancy | Designated tenant only; this records the tenant's acceptance of the protocol tenancy. |
| Cancel a DRAFT Tenancy | Active Property manager. |
| Request move-out | Either current manager or designated tenant. |
| Confirm tenancy end | The counterparty to the move-out requester. |
| Create an Inspection | Either current manager or the tenancy's tenant, subject to type/state rules. The creator is recorded. |
| Cancel an Inspection | Either tenancy participant, but only while it is OPEN and has no Condition Records or Evidence. |
| Freeze an Inspection | Its recorded Inspection creator. Every included Evidence item must already be frozen. |
| Create a Condition Record or submit Evidence | Either tenancy participant, only into an OPEN Inspection for the matching property/unit/tenancy/area. |
| Freeze Evidence | Its original submitter only. |
| Supersede frozen Evidence | Its original submitter, by submitting a matching replacement into another OPEN Inspection and freezing the replacement. |

“Manager” is a protocol role, not a verified title/deed claim. V1 does not independently verify property ownership. A Property creator may authorize at most 8 active managers. Manager history retains at most 128 distinct manager addresses, including revoked addresses, so a frontend can display current status without losing the history.

## Tenancy lifecycle

The lifecycle is `DRAFT → ACTIVE → MOVE_OUT_PENDING → ENDED`; `DRAFT → CANCELLED` is the only cancellation path. Other transitions fail with a stable `MO_ERR_STATE` prefix.

- A manager creates the draft and records the tenant, Property, Unit, and optional `start_metadata`.
- The designated tenant alone activates the draft. Only one ACTIVE or MOVE_OUT_PENDING tenancy may occupy a Unit at a time. Duplicate open records for the same Unit/tenant pair are rejected.
- Either participant can request move-out. The opposite party must confirm the end and may add bounded `end_metadata`.
- Ending or cancelling frees the occupancy/pair indexes. A closed Tenancy cannot accept new Condition Records or Evidence.

The optional start/end metadata is user-supplied context, not protocol time, proof of possession, lease terms, or a verified real-world date.

## Inspection lifecycle and committed contents

Inspection types are `MOVE_IN`, `PERIODIC`, `MAINTENANCE`, and `MOVE_OUT`. `MOVE_OUT` creation requires `MOVE_OUT_PENDING`; `PERIODIC` and `MAINTENANCE` require `ACTIVE`; a `MOVE_IN` inspection may be created for a DRAFT or ACTIVE Tenancy. Closed Tenancies cannot start inspections.

Inspection states are `OPEN`, `FROZEN`, and `CANCELLED`. An empty OPEN inspection can be cancelled by either participant. A nonempty inspection cannot be cancelled, preserving its record and membership. The creator freezes it only after each included Evidence record is individually FROZEN. Freeze stores `frozen_at` and an exact `contents_committed` snapshot of Room IDs, Area/Item IDs, Condition Record IDs, and Evidence IDs.

Condition/Evidence creation requires OPEN status, so no later item can silently join a frozen inspection. Room and Area/Item identities and metadata are immutable in this V1 contract. Individual Evidence records have immutable fields from submission; freeze records the explicit finalization timestamp/status. Existing inspections therefore retain the same parent identities and listed content after freeze.

## Room and Area/Item records

Property managers create Rooms beneath a Unit and Area/Items beneath a Room. A Room stores Property and Unit IDs; an Area/Item copies those IDs and the Room ID. Parent existence and consistency are checked before creation. The labels and bounded `subject_type`/`description_ref` are metadata. Neither text nor user intent can move an Area/Item to another Room or Unit.

Visual Continuity is supported by stable IDs and later-inspection references to the same Area/Item. V1 does not align images, validate a view, or claim that two photos show the same physical area.

## Participant Condition Records

A Condition Record is a participant's record attached to one Area/Item and one OPEN Inspection. Allowed `condition_type` values are `OBSERVED_DAMAGE`, `PRE_EXISTING_CLAIM`, `MAINTENANCE_NOTE`, `REPAIR_CLAIM`, `NO_VISIBLE_ISSUE`, and `OTHER`. It stores bounded `description` and optional `claim_ref`, the participant submitter, all parent IDs, `created_at`, and status `PARTICIPANT_RECORDED`.

That status means only that a participant submitted the record. The text is not protocol truth and does not create an Established Condition. Evidence can be attached to a Condition Record when the evidence and condition refer to the same Inspection and Area/Item; the evidence submitter remains explicit, so attachment does not mean the submitter endorsed the other participant's claim.

## Evidence envelope, freeze, and supersession

Evidence stores: `evidence_id`, Property/Unit/Tenancy/Inspection/Room/Area IDs, optional `condition_record_id`, submitter, bounded `evidence_type`, opaque `source_ref`, normalized 64-character hexadecimal `expected_sha256`, `submitted_at`, `frozen_at`, status, and optional `supersedes_evidence_id`.

Evidence types are `PHOTO`, `VIDEO_REFERENCE`, `DOCUMENT_REFERENCE`, `RECEIPT`, and `OTHER`. `source_ref` can identify an external resource; V1 does not require it to be a URL, dereference it, follow redirects, retrieve bytes, verify the digest against remote bytes, or store an image/blob. A valid SHA-256 shape proves only that the caller supplied a 32-byte digest in hexadecimal; it does not prove the claimed file, time, author, or capture location.

Evidence status moves from `SUBMITTED` to `FROZEN`. V1 has no evidence edit method even before freeze, so submitter, parent bindings, type, source reference, digest, and submission timestamp cannot be altered through the public ABI. The original submitter freezes it, recording protocol `frozen_at`. Repeating the same freeze is a no-op; another participant cannot freeze on the submitter's behalf.

Supersession is append-only. The same submitter can submit a replacement only in another OPEN Inspection, for the same Property, Unit, Tenancy, Room, Area/Item, and evidence type. The prior item must already be frozen and not superseded. Freezing the replacement adds a separate `superseded_by` index entry and lifecycle event. It does not modify the prior Evidence JSON; reads show both the original and its supersession link. Supersession does not delete or conceal evidence.

## Future Visual Observation and Established Condition schemas

Stage 1 stores the future record maps and defines their bounded field sets, but exposes no write method for either map. This prevents arbitrary users from presenting a self-written observation as validator output or a participant's claim as an established condition. These records can only be added with the later adjudication/provenance path.

The Visual Observation Record schema is: `observation_id`, `area_item_id`, `inspection_ids`, exact frozen `evidence_ids`, bounded `observation_type`, `adjudication_ref`, `consensus_ref`, and `created_at`. Bounded observation vocabulary includes `POSSIBLE_CHANGE`, `VISIBLE_MARK_PRESENT`, `VISIBLE_MARK_APPEARS_LARGER`, `POSSIBLE_NEW_DEFECT`, `POSSIBLE_REPAIR`, `VIEW_NOT_COMPARABLE`, `SHADOW_OR_LIGHTING_CONFOUNDER`, and `AREA_IDENTITY_UNCERTAIN`.

The Established Condition Record schema is: `finding_id`, `area_item_id`, `inspection_ids`, exact frozen `evidence_ids`, `observation_ids`, `condition`, `adjudication_ref`, `promotion_rule_id`, `consensus_ref`, `challenge_status`, `finality_ref`, and `created_at`. Allowed future condition values are `UNCHANGED`, `PRE_EXISTING`, `NEW_DAMAGE`, `WORSENED`, `REPAIRED`, and `INSUFFICIENT_EVIDENCE`.

There is no automatic observation-to-finding conversion. A Condition Record also cannot populate either future map. Creating a record in one layer does not create, approve, or promote a record in another layer. The later adjudication path must bind frozen evidence, observations, consensus, promotion rules, and challenge/finality state.

## Protocol time and append-only history

Protocol lifecycle timestamps read `gl.message_raw["datetime"]`, the deterministic transaction timestamp available during GenVM execution. Every validator/re-execution of that transaction sees the same protocol value. User-provided start/end metadata is stored separately and never treated as trusted protocol time. The timestamp is not host wall-clock time and does not prove when an image was captured.

Each important write appends a bounded event containing event ID, Property ID, event type, record type/ID, actor, and `protocol_at`. Events cover Property creation, manager changes, Unit/Tenancy/Inspection/Room/Area/Condition/Evidence creation, tenancy/inspection lifecycle transitions, Evidence freeze, and Evidence supersession. Records are never deleted. Reads are paginated by Property. At the configured history limit, new event-producing writes fail closed rather than evicting history.

## Replay safety, bounds, reads, and errors

Record-creation writes take a caller request ID, scoped by caller and method. The contract stores a canonical payload digest and resulting record ID: a repeated request with the same payload returns the same record ID; reusing the key with a different payload fails. Evidence also rejects the same submitter/hash/type/area duplicate within one Inspection. Transition repeats either no-op when they repeat the identical one-way action or return a stable state/duplicate error; a completed tenancy end cannot silently change its end metadata.

| Bound | Limit | Reason |
|---|---:|---|
| Property/unit/room display labels | 80 characters | Enough for a short property or room label; labels remain display metadata. |
| Condition description, Area/Item description, and start/end metadata | 240 characters | Short claim, feature note, or lifecycle context only. |
| Area/Item subject type | 32 characters | A bounded category, not an open-ended schema. |
| Request ID | 64 characters | Caller idempotency key, scoped by method and address. |
| Evidence source and claim reference | 512 characters | Identifier/reference only; no arbitrary blob storage. |
| Properties per creator | 64 | Bounds each creator index. |
| Units and Tenancies per Property | 64 each | Bounds Property child lists. |
| Inspections per Tenancy | 32 | Bounds inspection history. |
| Rooms per Unit and Areas/Items per Room | 64 each | Supports ordinary room/feature capture without unbounded single-parent lists. |
| Condition Records and Evidence per Inspection | 64 each | Caps each inspection payload and membership. |
| Active managers / distinct manager addresses in history | 8 / 128 | Bounds authority lookup and its read view. |
| Events per Property | 1024 | Preserves history to a fixed cap; writes stop at the cap. |
| Read page | 1–50 records | Frontend can reconstruct large collections over bounded calls. |

IDs are capped at 64 characters on lookup. SHA-256 accepts exactly 64 hexadecimal characters and is normalized to lowercase. All values are metadata/reference fields, not images or arbitrary blobs. Pages return `items`, `next_offset`, and `has_more`.

Read methods include `get_*` for each record; lists for Properties by creator, Units/Tenancies by Property, Inspections by Tenancy, Rooms by Unit, Areas/Items by Room, Condition Records/Evidence by Inspection, and Property history; plus future observation/finding reads and `list_managers`. Record and list reads are public chain data.

Stable contract error prefixes are `MO_ERR_UNAUTHORIZED`, `MO_ERR_NOT_FOUND`, `MO_ERR_PARENT`, `MO_ERR_WRONG_SCOPE`, `MO_ERR_STATE`, `MO_ERR_FROZEN_INSPECTION`, `MO_ERR_DUPLICATE`, `MO_ERR_SHA256`, `MO_ERR_BOUNDS`, and `MO_ERR_SCHEMA`. Frozen Evidence has no mutation entrypoint at all; freeze operations are submitter-gated and one-way. Page-limit and record-bound errors use `MO_ERR_BOUNDS`. There is no undocumented edit path for frozen records.

## Later visual adjudication and product integration

A later stage can use the frozen Evidence and stable Area/Item references in move-in/move-out comparisons. It should write a Visual Observation only from a verifiable adjudication execution and keep an Established Condition separate behind the reviewed deterministic promotion rules. `INSUFFICIENT_EVIDENCE` must remain available. A majority vote cannot override weak visibility, uncertain identity, a material confounder, or incomplete provenance.

The Property Condition Passport can later reconstruct each inspection and evidence set from bounded reads; Visual Continuity can point to the same Room/Area IDs; maintenance/RepairCheck records can be added as related history; and future Condition Receipts can display evidence, observations, consensus, finding, unresolved elements, and challenge/finality. This foundation makes no claim about physical truth, tenant responsibility, normal wear, policy, liability, or deposit allocation.

**REAL-WORLD PROPERTY VISUAL ACCURACY: NOT YET VERIFIED.** No production visual adjudication, frontend, backend, external evidence service, StudioNet transaction, or canonical deployment is part of Stage 1.

## Official GenLayer references consulted

- [Official GenLayer `write-contract` skill](https://github.com/genlayerlabs/skills/blob/main/plugins/genlayer-dev/skills/write-contract/SKILL.md)
- [Official GenLayer `direct-tests` skill](https://github.com/genlayerlabs/skills/blob/main/plugins/genlayer-dev/skills/direct-tests/SKILL.md)
- [Storage Quick Reference](https://docs.genlayer.com/developers/intelligent-contracts/features/storage)
- [Persisting Data on the Blockchain](https://docs.genlayer.com/developers/intelligent-contracts/storage)
- [Transaction Context and timestamps](https://docs.genlayer.com/developers/intelligent-contracts/features/transaction-context)
- [Testing Intelligent Contracts](https://docs.genlayer.com/developers/intelligent-contracts/testing)
