# MoveOut Stage 2 — Inspection, Evidence, and Visual Continuity Protocol

**Status: deterministic implementation and local tests complete; not deployed. No visual AI adjudication or frontend was added.**

Stage 2 extends the Stage 1.1 contract with a deterministic inspection manifest, guided capture metadata, explicit participant review and disagreement records, counter-evidence, and maintenance/continuity references. It keeps the Stage 0 visual accuracy limitation intact. The implementation uses the existing GenLayer contract/storage APIs (`TreeMap`, `gl.public.write/view`, and `gl.message_raw['datetime']`); it adds no GenLayer vision, web-fetch, nondeterministic, or external runtime API calls.

## Inspection manifest and completeness

The live inspection manifest contains stable IDs for Rooms, Area/Items, participant Condition Records, Evidence, Capture Slots, and Maintenance Events. It stores IDs rather than copies of child records. `get_inspection_manifest` returns the live bounded membership and, once frozen, `contents_committed`.

Freeze takes an exact snapshot of those arrays. Later inspections, later evidence, disagreements, reviews, or supersession links do not add to or rewrite an earlier snapshot. Original Evidence remains a member of its original frozen inspection even if a later inspection appends a superseding replacement.

`get_inspection_completeness` reports each structural check and named missing requirements. Freeze requires:

- at least one Room;
- at least one Area/Item, and at least one Area/Item for each included Room;
- at least one Evidence record, with every included Evidence frozen;
- at least one Evidence attached to every declared Capture Slot;
- consistent parent bindings, member indexes, and frozen snapshot arrays.

It does not require a fixed photo count for each Area/Item. An un-slotted Evidence item is permitted. A Capture Slot states that a particular view is expected, so an empty slot blocks freeze until Evidence is attached. No check determines visual quality, whether an image depicts its claimed subject, or whether the property is defect-free.

## Capture Slots and participant metadata

`create_capture_slot` creates a stable Slot ID under one OPEN Inspection, Room, and Area/Item. Slot types are bounded to `OVERVIEW`, `DETAIL`, `FRONT`, `BACK`, `CLOSE_UP`, `CONTEXT`, and `DOCUMENT`. The creator must be a tenancy participant. Labels are capped at 80 characters and instructions at 240. Capture Slots are immutable after creation; there is no rebind or replace operation.

`submit_evidence_for_slot` attaches normal evidence to that Slot and stores bounded participant-declared context: obstruction (`NONE`, `PARTIAL`, `UNKNOWN`), lighting (`NORMAL`, `LOW`, `UNKNOWN`), and a note reference. These are claims supplied by the evidence submitter. They do not set validator-established quality or condition. Multiple evidence records can be appended to a Slot while the Inspection is OPEN; no participant can edit or replace another submitter's Evidence.

Evidence type vocabulary retains the Stage 1 values and adds `DOCUMENT`, `REPAIR_RECEIPT`, `MAINTENANCE_RECORD`, and `INSPECTION_NOTE`. There is no on-chain MIME parser, media decoder, or image-byte storage. Evidence remains a bounded external source reference plus caller-provided SHA-256 and protocol metadata.

## Visual Continuity references

A later Capture Slot can name a prior Slot, prior frozen Evidence, or both. Validation requires the old Inspection to be frozen and earlier by its contract-generated Inspection sequence; it must have the same Property, Unit, Tenancy, Room, and Area/Item. A referenced Evidence record must be frozen and bound to the referenced Slot. A Slot-only reference must resolve to a Slot with at least one frozen Evidence item.

The persisted meaning is **intended correspondence**. `get_capture_slot` states `INTENDED_CORRESPONDENCE_NOT_SAME_AREA_PROOF`. It does not mean `SAME_AREA_PROVEN`; the contract does not inspect pixels, camera pose, landmarks, or physical identity. Future visual adjudication may assess whether the images support the participant's correspondence.

Continuity fields are immutable as part of the Slot. A later Move-Out Inspection can point to a frozen Move-In Slot/Evidence while recording its own new evidence. It cannot rewrite the Move-In membership or bytes digest reference.

## Review, disagreement, and counter-evidence

Reviews are submitted after Inspection freeze so each party reviews the exact committed membership. Each tenant or active manager can append a review as `ACKNOWLEDGED` or `DISPUTED`; absence is reported as `NOT_REVIEWED`. `ACKNOWLEDGED` means “I acknowledge this inspection/evidence record exists.” It does not endorse every participant description. Review revisions append a new Review ID and link the earlier review; prior records remain readable. The Inspection Receipt summarizes tenant and manager-side review state. Agreement is never required to freeze evidence or record a disagreement.

`create_disagreement` is available to either tenancy participant for a frozen whole Inspection, a Condition Record in that Inspection, or Evidence in that Inspection. It stores participant address, target, optional bounded reason reference, protocol timestamp, and a stable Disagreement ID. It neither edits the target nor resolves the disagreement. Records are append-only.

Counter-evidence uses the normal Evidence schema and submitter-only freeze rule. It is attached to a Disagreement by reference, and must be submitted into a later Inspection in the same Tenancy. If the Disagreement targets a Condition Record or Evidence, the counter-evidence must use that same Area/Item. For an Inspection-wide disagreement, the later Inspection may supply evidence for any valid Area/Item in the same Unit. The earlier Inspection remains frozen. Counter-evidence is indexed separately and capped at 64 items per Disagreement.

## Inspection Receipt and Condition Passport reads

`get_inspection_receipt` returns a bounded summary: Property, Unit, Tenancy, Inspection type and ID, creator and lifecycle timestamps, freeze status, manifest counts, dual-review state, disagreement count, completeness, and page-method names. It does not embed unbounded history or every child record. Bounded list calls retrieve Rooms, Area/Items, Conditions, Evidence, Slots, Reviews, Disagreements, counter-evidence, and Maintenance Events. Evidence pages expose source references, hashes, submitter, participant metadata, slot, and freeze state.

`list_inspections` reconstructs the Tenancy chronology (MOVE_IN, PERIODIC, MAINTENANCE, MOVE_OUT) with paging. `list_maintenance_events` adds the repair/service timeline by Tenancy. Pages remain limited to 50 records; inspection and child collection sizes have explicit caps. Together, these reads let a future Passport show participant claims, who submitted them and when, frozen evidence, dissent, and later evidence/continuity references without presenting those claims as protocol truth.

## Maintenance, RepairCheck, and Same Damage Guard foundations

`create_maintenance_event` is restricted to an OPEN `MAINTENANCE` Inspection. It stores one bounded report type (`MAINTENANCE_REPORTED`, `REPAIR_REPORTED`, `SERVICE_REPORTED`), Area/Item, participant/manager creator, protocol timestamp, note reference, and references to at least one Condition Record or Evidence item. A referenced earlier Condition Record or Evidence must be from the same Property, Unit, Tenancy, and Area/Item and its earlier Inspection must be frozen. Same-inspection references are also supported. This creates a traceable sequence such as prior condition → maintenance event → repair receipt/photo → later Inspection.

Maintenance event types and `REPAIR_RECEIPT` are participant evidence labels. They do not establish that a repair succeeded. There is no `REPAIRED` finding writer.

`create_condition_record_with_prior` permits a later participant Condition Record to reference an earlier Condition Record from the same frozen Inspection lineage and exact Area/Item. The field is explicitly `participant_asserted_prior_condition_id`; it records which claim the participant says is related. `list_condition_references` makes those links queryable for future Same Damage Guard logic. It does not establish that the earlier and later claims describe the same physical defect. Established Condition records still have no public writer and cannot be referenced as if they existed.

## Authority, bounds, and protocol time

Room inclusion, slots, reviews, disagreements, counter-evidence, and maintenance events require a current tenancy participant. Evidence continues to be frozen by its original submitter; Inspection freeze continues to be performed by its recorded creator. Counter-evidence is new Evidence, never an edit. Review/disagreement records have no update or delete method.

Stage 2 limits include: 64 Rooms per Inspection; 256 Area/Items; 64 Slots; 64 Condition Records and 64 Evidence items; 64 Reviews and Disagreements; 8 review revisions per actor; 64 counter-evidence records per Disagreement; and 64 Maintenance Events per Tenancy/Inspection. Existing Stage 1 limits, including 32 Inspections per Tenancy, 1,024 history events per Property, bounded text/source references, and pages of 1–50, remain. Writes fail closed at their caps; no history is evicted. Protocol timestamps use `gl.message_raw['datetime']`. Caller metadata remains separate.

## Explicit non-goals and limitations

- No public Visual Observation or Established Condition writer; no condition classification, deposit responsibility, legal ownership verification, or repair-success determination.
- No `gl.nondet` call, remote image fetch, URL content validation, digest verification against remote bytes, or image-byte storage. A source reference plus caller digest does not prove that the URL returns those bytes.
- Continuity labels record intended correspondence, not proof of physical identity.
- Participant obstruction, lighting, note, review, claim, and disagreement fields are not independently verified facts.
- Direct Mode, lint, and local compilation do not establish StudioNet deployment/storage cost or real-world visual accuracy. No Stage 2 deployment was performed.

## GenLayer references

- [Storage Quick Reference](https://docs.genlayer.com/developers/intelligent-contracts/features/storage)
- [Persisting Data on the Blockchain](https://docs.genlayer.com/developers/intelligent-contracts/storage)
- [Transaction Context](https://docs.genlayer.com/developers/intelligent-contracts/features/transaction-context)
- [Testing Intelligent Contracts](https://docs.genlayer.com/developers/intelligent-contracts/testing)
