# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""Deterministic MoveOut protocol records. No visual adjudication is performed here."""

from genlayer import *
import hashlib
import json


class MoveOutProtocolV1(gl.Contract):
    # JSON strings keep records bounded and avoid exposing mutable storage objects.
    properties: TreeMap[str, str]
    units: TreeMap[str, str]
    tenancies: TreeMap[str, str]
    inspections: TreeMap[str, str]
    rooms: TreeMap[str, str]
    area_items: TreeMap[str, str]
    condition_records: TreeMap[str, str]
    evidence_records: TreeMap[str, str]

    # Future adjudication record stores intentionally have no public writer in Stage 1.
    visual_observations: TreeMap[str, str]
    established_conditions: TreeMap[str, str]

    events: TreeMap[str, str]
    idempotency: TreeMap[str, str]
    manager_authority: TreeMap[str, bool]
    current_tenancy_by_unit: TreeMap[str, str]
    open_tenancy_by_unit_tenant: TreeMap[str, str]
    superseded_by: TreeMap[str, str]

    properties_by_creator: TreeMap[str, str]
    active_manager_count: TreeMap[str, u256]
    manager_addresses_by_property: TreeMap[str, str]
    units_by_property: TreeMap[str, str]
    tenancies_by_property: TreeMap[str, str]
    inspections_by_tenancy: TreeMap[str, str]
    rooms_by_unit: TreeMap[str, str]
    areas_by_room: TreeMap[str, str]
    conditions_by_inspection: TreeMap[str, str]
    evidence_by_inspection: TreeMap[str, str]
    observations_by_inspection: TreeMap[str, str]
    findings_by_inspection: TreeMap[str, str]
    events_by_property: TreeMap[str, str]

    property_seq: u256
    unit_seq: u256
    tenancy_seq: u256
    inspection_seq: u256
    room_seq: u256
    area_seq: u256
    condition_seq: u256
    evidence_seq: u256
    event_seq: u256

    MAX_TEXT = 240
    MAX_LABEL = 80
    MAX_REQUEST_ID = 64
    MAX_SOURCE_REF = 512
    MAX_UNITS_PER_PROPERTY = 64
    MAX_TENANCIES_PER_PROPERTY = 64
    MAX_INSPECTIONS_PER_TENANCY = 32
    MAX_ROOMS_PER_UNIT = 64
    MAX_AREAS_PER_ROOM = 64
    MAX_CONDITIONS_PER_INSPECTION = 64
    MAX_EVIDENCE_PER_INSPECTION = 64
    MAX_MANAGERS_PER_PROPERTY = 8
    MAX_MANAGER_HISTORY_PER_PROPERTY = 128
    MAX_HISTORY_PER_PROPERTY = 1024
    MAX_PAGE_SIZE = 50
    ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

    INSPECTION_TYPES = ("MOVE_IN", "PERIODIC", "MAINTENANCE", "MOVE_OUT")
    CONDITION_TYPES = (
        "OBSERVED_DAMAGE", "PRE_EXISTING_CLAIM", "MAINTENANCE_NOTE",
        "REPAIR_CLAIM", "NO_VISIBLE_ISSUE", "OTHER",
    )
    EVIDENCE_TYPES = ("PHOTO", "VIDEO_REFERENCE", "DOCUMENT_REFERENCE", "RECEIPT", "OTHER")
    TENANCY_STATES = ("DRAFT", "ACTIVE", "MOVE_OUT_PENDING", "ENDED", "CANCELLED")
    INSPECTION_STATES = ("OPEN", "FROZEN", "CANCELLED")
    FUTURE_OBSERVATION_TYPES = (
        "POSSIBLE_CHANGE", "VISIBLE_MARK_PRESENT", "VISIBLE_MARK_APPEARS_LARGER",
        "POSSIBLE_NEW_DEFECT", "POSSIBLE_REPAIR", "VIEW_NOT_COMPARABLE",
        "SHADOW_OR_LIGHTING_CONFOUNDER", "AREA_IDENTITY_UNCERTAIN",
    )
    FUTURE_ESTABLISHED_CONDITIONS = (
        "UNCHANGED", "PRE_EXISTING", "NEW_DAMAGE", "WORSENED", "REPAIRED",
        "INSUFFICIENT_EVIDENCE",
    )
    OBSERVATION_RECORD_SCHEMA = (
        "observation_id", "area_item_id", "inspection_ids", "evidence_ids",
        "observation_type", "adjudication_ref", "consensus_ref", "created_at",
    )
    ESTABLISHED_CONDITION_RECORD_SCHEMA = (
        "finding_id", "area_item_id", "inspection_ids", "evidence_ids",
        "observation_ids", "condition", "adjudication_ref", "promotion_rule_id",
        "consensus_ref", "challenge_status", "finality_ref", "created_at",
    )

    def __init__(self):
        self.property_seq = u256(1)
        self.unit_seq = u256(1)
        self.tenancy_seq = u256(1)
        self.inspection_seq = u256(1)
        self.room_seq = u256(1)
        self.area_seq = u256(1)
        self.condition_seq = u256(1)
        self.evidence_seq = u256(1)
        self.event_seq = u256(1)

    def _now(self) -> str:
        return str(gl.message_raw["datetime"])

    def _sender(self) -> str:
        return gl.message.sender_address.as_hex

    def _fail(self, prefix: str, detail: str) -> None:
        raise gl.vm.UserError(prefix + ":" + detail)

    def _text(self, value: str, maximum: u256, field: str, allow_empty: bool = False) -> str:
        if not isinstance(value, str):
            self._fail("MO_ERR_SCHEMA", field)
        if len(value) > int(maximum) or (not allow_empty and len(value) == 0):
            self._fail("MO_ERR_BOUNDS", field)
        return value

    def _enum(self, value: str, allowed: tuple, field: str) -> str:
        if not isinstance(value, str) or value not in allowed:
            self._fail("MO_ERR_SCHEMA", field)
        return value

    def _json(self, record: dict) -> str:
        return json.dumps(record, sort_keys=True, separators=(",", ":"))

    def _load(self, records: TreeMap[str, str], record_id: str, kind: str) -> dict:
        self._text(record_id, u256(64), kind)
        if record_id not in records:
            self._fail("MO_ERR_NOT_FOUND", kind)
        return json.loads(records[record_id])

    def _new_id(self, prefix: str, sequence: u256) -> str:
        return prefix + "-" + str(sequence)

    def _append(self, index: TreeMap[str, str], parent_id: str,
                child_id: str, maximum: u256, kind: str) -> None:
        children = json.loads(index.get(parent_id, "[]"))
        if len(children) >= int(maximum):
            self._fail("MO_ERR_BOUNDS", kind)
        children.append(child_id)
        index[parent_id] = self._json(children)

    def _append_unique(self, index: TreeMap[str, str], parent_id: str,
                       child_id: str) -> None:
        children = json.loads(index.get(parent_id, "[]"))
        if child_id not in children:
            children.append(child_id)
            index[parent_id] = self._json(children)

    def _idempotent_replay(self, method: str, request_id: str, payload: dict) -> str:
        self._text(request_id, u256(self.MAX_REQUEST_ID), "request_id")
        key = self._sender() + "|" + method + "|" + request_id
        digest = hashlib.sha256(self._json(payload).encode("utf-8")).hexdigest()
        if key in self.idempotency:
            stored = json.loads(self.idempotency[key])
            if stored["digest"] != digest:
                self._fail("MO_ERR_DUPLICATE", "request_id_reused")
            return stored["record_id"]
        return ""

    def _remember(self, method: str, request_id: str, payload: dict, record_id: str) -> None:
        key = self._sender() + "|" + method + "|" + request_id
        digest = hashlib.sha256(self._json(payload).encode("utf-8")).hexdigest()
        self.idempotency[key] = self._json({"digest": digest, "record_id": record_id})

    def _is_manager(self, property_id: str, address: str) -> bool:
        key = property_id + "|" + address
        return key in self.manager_authority and self.manager_authority[key]

    def _require_manager(self, property_id: str) -> None:
        if not self._is_manager(property_id, self._sender()):
            self._fail("MO_ERR_UNAUTHORIZED", "manager_required")

    def _require_participant(self, tenancy_id: str) -> dict:
        tenancy = self._load(self.tenancies, tenancy_id, "tenancy")
        if (self._sender() != tenancy["tenant"] and
                not self._is_manager(tenancy["property_id"], self._sender())):
            self._fail("MO_ERR_UNAUTHORIZED", "tenancy_participant_required")
        return tenancy

    def _require_open_inspection(self, inspection_id: str) -> dict:
        inspection = self._load(self.inspections, inspection_id, "inspection")
        if inspection["status"] == "FROZEN":
            self._fail("MO_ERR_FROZEN_INSPECTION", inspection_id)
        if inspection["status"] != "OPEN":
            self._fail("MO_ERR_STATE", "inspection_not_open")
        return inspection

    def _append_event(self, property_id: str, event_type: str,
                      record_type: str, record_id: str) -> None:
        event_ids = json.loads(self.events_by_property.get(property_id, "[]"))
        if len(event_ids) >= int(self.MAX_HISTORY_PER_PROPERTY):
            self._fail("MO_ERR_BOUNDS", "property_history")
        event_id = self._new_id("EVT", self.event_seq)
        self.event_seq += u256(1)
        self.events[event_id] = self._json({
            "event_id": event_id,
            "property_id": property_id,
            "event_type": event_type,
            "record_type": record_type,
            "record_id": record_id,
            "actor": self._sender(),
            "protocol_at": self._now(),
        })
        event_ids.append(event_id)
        self.events_by_property[property_id] = self._json(event_ids)

    def _page(self, index: TreeMap[str, str], records: TreeMap[str, str],
              parent_id: str, offset: u256, limit: u256) -> str:
        self._text(parent_id, u256(64), "parent_id")
        if int(limit) == 0 or int(limit) > int(self.MAX_PAGE_SIZE):
            self._fail("MO_ERR_BOUNDS", "page_limit")
        if parent_id not in index:
            return self._json({"items": [], "next_offset": int(offset), "has_more": False})
        ids = json.loads(index[parent_id])
        start = int(offset)
        stop = min(start + int(limit), len(ids))
        result = []
        for position in range(start, stop):
            record_id = ids[position]
            result.append(json.loads(records[record_id]))
        return self._json({"items": result, "next_offset": stop,
                           "has_more": stop < len(ids)})

    def _record_parent_context(self, inspection_id: str, area_item_id: str):
        inspection = self._require_open_inspection(inspection_id)
        area = self._load(self.area_items, area_item_id, "area_item")
        room = self._load(self.rooms, area["room_id"], "room")
        tenancy = self._require_participant(inspection["tenancy_id"])
        if tenancy["status"] in ("ENDED", "CANCELLED"):
            self._fail("MO_ERR_STATE", "tenancy_closed")
        if (inspection["property_id"] != area["property_id"] or
                inspection["unit_id"] != area["unit_id"] or
                tenancy["property_id"] != area["property_id"] or
                tenancy["unit_id"] != area["unit_id"] or
                room["unit_id"] != area["unit_id"]):
            self._fail("MO_ERR_WRONG_SCOPE", "inspection_area_binding")
        return inspection, tenancy, area, room

    def _add_inspection_membership(self, inspection: dict, room_id: str,
                                   area_item_id: str, condition_id: str = "",
                                   evidence_id: str = "") -> None:
        room_ids = inspection["room_ids"]
        if room_id not in room_ids:
            room_ids.append(room_id)
        area_ids = inspection["area_item_ids"]
        if area_item_id not in area_ids:
            area_ids.append(area_item_id)
        if condition_id:
            inspection["condition_record_ids"].append(condition_id)
        if evidence_id:
            inspection["evidence_ids"].append(evidence_id)
        self.inspections[inspection["inspection_id"]] = self._json(inspection)

    @gl.public.write
    def create_property(self, property_label: str, request_id: str) -> str:
        label = self._text(property_label, u256(self.MAX_LABEL), "property_label")
        payload = {"property_label": label}
        replay = self._idempotent_replay("create_property", request_id, payload)
        if replay:
            return replay
        creator = self._sender()
        property_ids = json.loads(self.properties_by_creator.get(creator, "[]"))
        if len(property_ids) >= 64:
            self._fail("MO_ERR_BOUNDS", "properties_per_creator")
        property_id = self._new_id("PROP", self.property_seq)
        self.property_seq += u256(1)
        self.properties[property_id] = self._json({
            "property_id": property_id, "property_label": label,
            "creator": creator, "created_at": self._now(), "status": "ACTIVE",
        })
        self.manager_authority[property_id + "|" + creator] = True
        self.active_manager_count[property_id] = u256(1)
        self.manager_addresses_by_property[property_id] = self._json([creator])
        property_ids.append(property_id)
        self.properties_by_creator[creator] = self._json(property_ids)
        self._append_event(property_id, "PROPERTY_CREATED", "property", property_id)
        self._remember("create_property", request_id, payload, property_id)
        return property_id

    @gl.public.write
    def add_manager(self, property_id: str, manager_address: str) -> None:
        prop = self._load(self.properties, property_id, "property")
        if self._sender() != prop["creator"]:
            self._fail("MO_ERR_UNAUTHORIZED", "property_creator_required")
        try:
            self._text(manager_address, u256(64), "manager_address")
            manager = Address(manager_address).as_hex
        except Exception:
            self._fail("MO_ERR_SCHEMA", "manager_address")
        if manager == self.ZERO_ADDRESS:
            self._fail("MO_ERR_SCHEMA", "manager_address_zero")
        for tenancy_id in json.loads(self.tenancies_by_property.get(property_id, "[]")):
            tenancy = json.loads(self.tenancies[tenancy_id])
            if (tenancy["tenant"] == manager and
                    tenancy["status"] not in ("ENDED", "CANCELLED")):
                self._fail("MO_ERR_STATE", "open_tenant_cannot_become_manager")
        key = property_id + "|" + manager
        if key in self.manager_authority and self.manager_authority[key]:
            self._fail("MO_ERR_DUPLICATE", "manager")
        if int(self.active_manager_count[property_id]) >= int(self.MAX_MANAGERS_PER_PROPERTY):
            self._fail("MO_ERR_BOUNDS", "managers_per_property")
        self.manager_authority[key] = True
        self.active_manager_count[property_id] += u256(1)
        if property_id not in self.manager_addresses_by_property:
            self.manager_addresses_by_property[property_id] = self._json([prop["creator"]])
        addresses = json.loads(self.manager_addresses_by_property[property_id])
        if manager not in addresses:
            if len(addresses) >= int(self.MAX_MANAGER_HISTORY_PER_PROPERTY):
                self._fail("MO_ERR_BOUNDS", "manager_history_per_property")
            addresses.append(manager)
            self.manager_addresses_by_property[property_id] = self._json(addresses)
        self._append_event(property_id, "MANAGER_AUTHORIZED", "property", property_id)

    @gl.public.write
    def remove_manager(self, property_id: str, manager_address: str) -> None:
        prop = self._load(self.properties, property_id, "property")
        if self._sender() != prop["creator"]:
            self._fail("MO_ERR_UNAUTHORIZED", "property_creator_required")
        try:
            self._text(manager_address, u256(64), "manager_address")
            manager = Address(manager_address).as_hex
        except Exception:
            self._fail("MO_ERR_SCHEMA", "manager_address")
        if manager == prop["creator"]:
            self._fail("MO_ERR_STATE", "creator_authority_permanent")
        key = property_id + "|" + manager
        if key not in self.manager_authority or not self.manager_authority[key]:
            self._fail("MO_ERR_NOT_FOUND", "manager")
        self.manager_authority[key] = False
        self.active_manager_count[property_id] -= u256(1)
        self._append_event(property_id, "MANAGER_REVOKED", "property", property_id)

    @gl.public.write
    def create_unit(self, property_id: str, unit_label: str, request_id: str) -> str:
        prop = self._load(self.properties, property_id, "property")
        self._require_manager(property_id)
        label = self._text(unit_label, u256(self.MAX_LABEL), "unit_label")
        payload = {"property_id": property_id, "unit_label": label}
        replay = self._idempotent_replay("create_unit", request_id, payload)
        if replay:
            return replay
        for existing_id in json.loads(self.units_by_property.get(property_id, "[]")):
            if json.loads(self.units[existing_id])["unit_label"] == label:
                self._fail("MO_ERR_DUPLICATE", "unit_label")
        unit_id = self._new_id("UNIT", self.unit_seq)
        self.unit_seq += u256(1)
        self.units[unit_id] = self._json({
            "unit_id": unit_id, "property_id": prop["property_id"],
            "unit_label": label, "created_by": self._sender(),
            "created_at": self._now(), "status": "ACTIVE",
        })
        self._append(self.units_by_property, property_id, unit_id,
                     u256(self.MAX_UNITS_PER_PROPERTY), "units_per_property")
        self._append_event(property_id, "UNIT_CREATED", "unit", unit_id)
        self._remember("create_unit", request_id, payload, unit_id)
        return unit_id

    @gl.public.write
    def create_tenancy(self, property_id: str, unit_id: str, tenant_address: str,
                       start_metadata: str, request_id: str) -> str:
        prop = self._load(self.properties, property_id, "property")
        self._require_manager(property_id)
        unit = self._load(self.units, unit_id, "unit")
        if unit["property_id"] != property_id:
            self._fail("MO_ERR_PARENT", "unit_property")
        try:
            self._text(tenant_address, u256(64), "tenant_address")
            tenant = Address(tenant_address).as_hex
        except Exception:
            self._fail("MO_ERR_SCHEMA", "tenant_address")
        if tenant == self.ZERO_ADDRESS:
            self._fail("MO_ERR_SCHEMA", "tenant_address_zero")
        if self._is_manager(property_id, tenant):
            self._fail("MO_ERR_SCHEMA", "tenant_is_manager")
        start_note = self._text(start_metadata, u256(self.MAX_TEXT),
                                "start_metadata", allow_empty=True)
        payload = {"property_id": property_id, "unit_id": unit_id,
                   "tenant": tenant, "start_metadata": start_note}
        replay = self._idempotent_replay("create_tenancy", request_id, payload)
        if replay:
            return replay
        pair_key = unit_id + "|" + tenant
        if pair_key in self.open_tenancy_by_unit_tenant:
            self._fail("MO_ERR_DUPLICATE", "open_unit_tenant_tenancy")
        tenancy_id = self._new_id("TEN", self.tenancy_seq)
        self.tenancy_seq += u256(1)
        self.tenancies[tenancy_id] = self._json({
            "tenancy_id": tenancy_id, "property_id": prop["property_id"],
            "unit_id": unit["unit_id"], "manager_creator": self._sender(),
            "tenant": tenant, "start_metadata": start_note,
            "created_at": self._now(), "activated_at": "",
            "move_out_requested_by": "", "move_out_requested_at": "",
            "end_metadata": "", "ended_at": "", "ended_by": "",
            "status": "DRAFT",
        })
        self.open_tenancy_by_unit_tenant[pair_key] = tenancy_id
        self._append(self.tenancies_by_property, property_id, tenancy_id,
                     u256(self.MAX_TENANCIES_PER_PROPERTY), "tenancies_per_property")
        self._append_event(property_id, "TENANCY_CREATED", "tenancy", tenancy_id)
        self._remember("create_tenancy", request_id, payload, tenancy_id)
        return tenancy_id

    @gl.public.write
    def activate_tenancy(self, tenancy_id: str) -> None:
        tenancy = self._load(self.tenancies, tenancy_id, "tenancy")
        if self._sender() != tenancy["tenant"]:
            self._fail("MO_ERR_UNAUTHORIZED", "designated_tenant_required")
        if tenancy["status"] != "DRAFT":
            self._fail("MO_ERR_STATE", "tenancy_not_draft")
        unit_id = tenancy["unit_id"]
        if unit_id in self.current_tenancy_by_unit:
            self._fail("MO_ERR_STATE", "unit_already_active")
        tenancy["status"] = "ACTIVE"
        tenancy["activated_at"] = self._now()
        self.tenancies[tenancy_id] = self._json(tenancy)
        self.current_tenancy_by_unit[unit_id] = tenancy_id
        self._append_event(tenancy["property_id"], "TENANCY_ACTIVATED", "tenancy", tenancy_id)

    @gl.public.write
    def cancel_draft_tenancy(self, tenancy_id: str) -> None:
        tenancy = self._load(self.tenancies, tenancy_id, "tenancy")
        self._require_manager(tenancy["property_id"])
        if tenancy["status"] == "CANCELLED" and tenancy.get("cancelled_by") == self._sender():
            return
        if tenancy["status"] != "DRAFT":
            self._fail("MO_ERR_STATE", "only_draft_tenancy_can_cancel")
        tenancy["status"] = "CANCELLED"
        tenancy["cancelled_by"] = self._sender()
        tenancy["cancelled_at"] = self._now()
        self.tenancies[tenancy_id] = self._json(tenancy)
        pair_key = tenancy["unit_id"] + "|" + tenancy["tenant"]
        del self.open_tenancy_by_unit_tenant[pair_key]
        self._append_event(tenancy["property_id"], "TENANCY_CANCELLED", "tenancy", tenancy_id)

    @gl.public.write
    def request_move_out(self, tenancy_id: str) -> None:
        tenancy = self._require_participant(tenancy_id)
        if tenancy["status"] == "MOVE_OUT_PENDING" and tenancy["move_out_requested_by"] == self._sender():
            return
        if tenancy["status"] != "ACTIVE":
            self._fail("MO_ERR_STATE", "tenancy_not_active")
        tenancy["status"] = "MOVE_OUT_PENDING"
        tenancy["move_out_requested_by"] = self._sender()
        tenancy["move_out_requested_at"] = self._now()
        self.tenancies[tenancy_id] = self._json(tenancy)
        self._append_event(tenancy["property_id"], "MOVE_OUT_REQUESTED", "tenancy", tenancy_id)

    @gl.public.write
    def confirm_tenancy_end(self, tenancy_id: str, end_metadata: str) -> None:
        tenancy = self._require_participant(tenancy_id)
        note = self._text(end_metadata, u256(self.MAX_TEXT), "end_metadata", allow_empty=True)
        if tenancy["status"] == "ENDED" and tenancy.get("ended_by") == self._sender():
            if tenancy.get("end_metadata") == note:
                return
            self._fail("MO_ERR_DUPLICATE", "tenancy_end_replay_payload")
        if tenancy["status"] != "MOVE_OUT_PENDING":
            self._fail("MO_ERR_STATE", "move_out_not_pending")
        if tenancy["move_out_requested_by"] == self._sender():
            self._fail("MO_ERR_UNAUTHORIZED", "counterparty_confirmation_required")
        if tenancy["move_out_requested_by"] == tenancy["tenant"]:
            if not self._is_manager(tenancy["property_id"], self._sender()):
                self._fail("MO_ERR_UNAUTHORIZED", "manager_counterparty_required")
        elif self._sender() != tenancy["tenant"]:
            self._fail("MO_ERR_UNAUTHORIZED", "designated_tenant_counterparty_required")
        tenancy["status"] = "ENDED"
        tenancy["end_metadata"] = note
        tenancy["ended_at"] = self._now()
        tenancy["ended_by"] = self._sender()
        self.tenancies[tenancy_id] = self._json(tenancy)
        if tenancy["unit_id"] in self.current_tenancy_by_unit:
            del self.current_tenancy_by_unit[tenancy["unit_id"]]
        pair_key = tenancy["unit_id"] + "|" + tenancy["tenant"]
        if pair_key in self.open_tenancy_by_unit_tenant:
            del self.open_tenancy_by_unit_tenant[pair_key]
        self._append_event(tenancy["property_id"], "TENANCY_ENDED", "tenancy", tenancy_id)

    @gl.public.write
    def create_inspection(self, tenancy_id: str, inspection_type: str,
                          request_id: str) -> str:
        tenancy = self._require_participant(tenancy_id)
        kind = self._enum(inspection_type, self.INSPECTION_TYPES, "inspection_type")
        state = tenancy["status"]
        if state in ("ENDED", "CANCELLED"):
            self._fail("MO_ERR_STATE", "tenancy_closed")
        if kind == "MOVE_OUT" and state != "MOVE_OUT_PENDING":
            self._fail("MO_ERR_STATE", "move_out_inspection_requires_pending")
        if kind in ("PERIODIC", "MAINTENANCE") and state != "ACTIVE":
            self._fail("MO_ERR_STATE", "inspection_requires_active_tenancy")
        payload = {"tenancy_id": tenancy_id, "inspection_type": kind}
        replay = self._idempotent_replay("create_inspection", request_id, payload)
        if replay:
            return replay
        inspection_id = self._new_id("INSP", self.inspection_seq)
        self.inspection_seq += u256(1)
        self.inspections[inspection_id] = self._json({
            "inspection_id": inspection_id, "property_id": tenancy["property_id"],
            "unit_id": tenancy["unit_id"], "tenancy_id": tenancy_id,
            "inspection_type": kind, "created_by": self._sender(),
            "created_at": self._now(), "frozen_at": "", "status": "OPEN",
            "room_ids": [], "area_item_ids": [], "condition_record_ids": [],
            "evidence_ids": [],
        })
        self._append(self.inspections_by_tenancy, tenancy_id, inspection_id,
                     u256(self.MAX_INSPECTIONS_PER_TENANCY), "inspections_per_tenancy")
        self._append_event(tenancy["property_id"], "INSPECTION_CREATED", "inspection", inspection_id)
        self._remember("create_inspection", request_id, payload, inspection_id)
        return inspection_id

    @gl.public.write
    def cancel_empty_inspection(self, inspection_id: str) -> None:
        inspection = self._load(self.inspections, inspection_id, "inspection")
        tenancy = self._require_participant(inspection["tenancy_id"])
        if inspection["status"] == "CANCELLED" and inspection.get("cancelled_by") == self._sender():
            return
        if inspection["status"] != "OPEN":
            self._fail("MO_ERR_STATE", "inspection_not_open")
        if (inspection["evidence_ids"] or inspection["condition_record_ids"]):
            self._fail("MO_ERR_STATE", "inspection_not_empty")
        inspection["status"] = "CANCELLED"
        inspection["cancelled_by"] = self._sender()
        inspection["cancelled_at"] = self._now()
        self.inspections[inspection_id] = self._json(inspection)
        self._append_event(tenancy["property_id"], "INSPECTION_CANCELLED", "inspection", inspection_id)

    @gl.public.write
    def create_room(self, unit_id: str, room_label: str, request_id: str) -> str:
        unit = self._load(self.units, unit_id, "unit")
        self._require_manager(unit["property_id"])
        label = self._text(room_label, u256(self.MAX_LABEL), "room_label")
        payload = {"unit_id": unit_id, "room_label": label}
        replay = self._idempotent_replay("create_room", request_id, payload)
        if replay:
            return replay
        for existing_id in json.loads(self.rooms_by_unit.get(unit_id, "[]")):
            if json.loads(self.rooms[existing_id])["room_label"] == label:
                self._fail("MO_ERR_DUPLICATE", "room_label")
        room_id = self._new_id("ROOM", self.room_seq)
        self.room_seq += u256(1)
        self.rooms[room_id] = self._json({
            "room_id": room_id, "property_id": unit["property_id"],
            "unit_id": unit_id, "room_label": label,
            "created_by": self._sender(), "created_at": self._now(),
        })
        self._append(self.rooms_by_unit, unit_id, room_id,
                     u256(self.MAX_ROOMS_PER_UNIT), "rooms_per_unit")
        self._append_event(unit["property_id"], "ROOM_CREATED", "room", room_id)
        self._remember("create_room", request_id, payload, room_id)
        return room_id

    @gl.public.write
    def create_area_item(self, room_id: str, subject_type: str, label: str,
                         description_ref: str, request_id: str) -> str:
        room = self._load(self.rooms, room_id, "room")
        self._require_manager(room["property_id"])
        kind = self._text(subject_type, u256(32), "subject_type")
        area_label = self._text(label, u256(self.MAX_LABEL), "area_item_label")
        description = self._text(description_ref, u256(self.MAX_TEXT),
                                  "description_ref", allow_empty=True)
        payload = {"room_id": room_id, "subject_type": kind,
                   "label": area_label, "description_ref": description}
        replay = self._idempotent_replay("create_area_item", request_id, payload)
        if replay:
            return replay
        for existing_id in json.loads(self.areas_by_room.get(room_id, "[]")):
            existing = json.loads(self.area_items[existing_id])
            if existing["subject_type"] == kind and existing["label"] == area_label:
                self._fail("MO_ERR_DUPLICATE", "area_item_identity_label")
        area_id = self._new_id("AREA", self.area_seq)
        self.area_seq += u256(1)
        self.area_items[area_id] = self._json({
            "area_item_id": area_id, "property_id": room["property_id"],
            "unit_id": room["unit_id"], "room_id": room_id,
            "subject_type": kind, "label": area_label,
            "description_ref": description, "created_by": self._sender(),
            "created_at": self._now(),
        })
        self._append(self.areas_by_room, room_id, area_id,
                     u256(self.MAX_AREAS_PER_ROOM), "areas_per_room")
        self._append_event(room["property_id"], "AREA_ITEM_CREATED", "area_item", area_id)
        self._remember("create_area_item", request_id, payload, area_id)
        return area_id

    @gl.public.write
    def create_condition_record(self, inspection_id: str, area_item_id: str,
                                condition_type: str, description: str,
                                claim_ref: str, request_id: str) -> str:
        self._text(inspection_id, u256(64), "inspection_id")
        self._text(area_item_id, u256(64), "area_item_id")
        kind = self._enum(condition_type, self.CONDITION_TYPES, "condition_type")
        detail = self._text(description, u256(self.MAX_TEXT), "description", allow_empty=True)
        claim = self._text(claim_ref, u256(self.MAX_SOURCE_REF), "claim_ref", allow_empty=True)
        payload = {"inspection_id": inspection_id, "area_item_id": area_item_id,
                   "condition_type": kind, "description": detail, "claim_ref": claim}
        replay = self._idempotent_replay("create_condition_record", request_id, payload)
        if replay:
            return replay
        inspection, tenancy, area, room = self._record_parent_context(inspection_id, area_item_id)
        condition_ids = json.loads(self.conditions_by_inspection.get(inspection_id, "[]"))
        if len(condition_ids) >= int(self.MAX_CONDITIONS_PER_INSPECTION):
            self._fail("MO_ERR_BOUNDS", "conditions_per_inspection")
        condition_id = self._new_id("COND", self.condition_seq)
        self.condition_seq += u256(1)
        self.condition_records[condition_id] = self._json({
            "condition_record_id": condition_id,
            "property_id": inspection["property_id"], "unit_id": inspection["unit_id"],
            "tenancy_id": inspection["tenancy_id"], "inspection_id": inspection_id,
            "room_id": room["room_id"], "area_item_id": area["area_item_id"],
            "submitter": self._sender(), "condition_type": kind,
            "description": detail, "claim_ref": claim,
            "created_at": self._now(), "status": "PARTICIPANT_RECORDED",
        })
        self._append(self.conditions_by_inspection, inspection_id, condition_id,
                     u256(self.MAX_CONDITIONS_PER_INSPECTION), "conditions_per_inspection")
        self._add_inspection_membership(inspection, room["room_id"], area["area_item_id"],
                                        condition_id=condition_id)
        self._append_event(tenancy["property_id"], "CONDITION_RECORD_CREATED",
                           "condition_record", condition_id)
        self._remember("create_condition_record", request_id, payload, condition_id)
        return condition_id

    @gl.public.write
    def submit_evidence(self, inspection_id: str, area_item_id: str,
                        condition_record_id: str, evidence_type: str,
                        source_ref: str, expected_sha256: str,
                        supersedes_evidence_id: str, request_id: str) -> str:
        self._text(inspection_id, u256(64), "inspection_id")
        self._text(area_item_id, u256(64), "area_item_id")
        kind = self._enum(evidence_type, self.EVIDENCE_TYPES, "evidence_type")
        source = self._text(source_ref, u256(self.MAX_SOURCE_REF), "source_ref")
        digest = self._text(expected_sha256, u256(64), "expected_sha256")
        digest = digest.lower()
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            self._fail("MO_ERR_SHA256", "expected_64_hex_characters")
        condition_id = self._text(condition_record_id, u256(64),
                                  "condition_record_id", allow_empty=True)
        supersedes_id = self._text(supersedes_evidence_id, u256(64),
                                   "supersedes_evidence_id", allow_empty=True)
        payload = {"inspection_id": inspection_id, "area_item_id": area_item_id,
                   "condition_record_id": condition_id, "evidence_type": kind,
                   "source_ref": source, "expected_sha256": digest,
                   "supersedes_evidence_id": supersedes_id}
        replay = self._idempotent_replay("submit_evidence", request_id, payload)
        if replay:
            return replay
        inspection, tenancy, area, room = self._record_parent_context(inspection_id, area_item_id)
        if condition_id:
            condition = self._load(self.condition_records, condition_id, "condition_record")
            if (condition["inspection_id"] != inspection_id or
                    condition["area_item_id"] != area_item_id):
                self._fail("MO_ERR_WRONG_SCOPE", "condition_evidence_binding")
        old_evidence = {}
        if supersedes_id:
            old_evidence = self._load(self.evidence_records, supersedes_id, "evidence")
            if (old_evidence["status"] != "FROZEN" or
                    old_evidence["submitter"] != self._sender() or
                    old_evidence["property_id"] != inspection["property_id"] or
                    old_evidence["unit_id"] != inspection["unit_id"] or
                    old_evidence["tenancy_id"] != inspection["tenancy_id"] or
                    old_evidence["inspection_id"] == inspection_id or
                    old_evidence["room_id"] != room["room_id"] or
                    old_evidence["area_item_id"] != area_item_id or
                    old_evidence["evidence_type"] != kind or
                    supersedes_id in self.superseded_by):
                self._fail("MO_ERR_WRONG_SCOPE", "supersession_binding")
        evidence_ids = json.loads(self.evidence_by_inspection.get(inspection_id, "[]"))
        if len(evidence_ids) >= int(self.MAX_EVIDENCE_PER_INSPECTION):
            self._fail("MO_ERR_BOUNDS", "evidence_per_inspection")
        # Exact duplicate payloads in the same inspection are not useful evidence.
        for existing_id in evidence_ids:
            existing = json.loads(self.evidence_records[existing_id])
            if (existing["area_item_id"] == area_item_id and
                    existing["submitter"] == self._sender() and
                    existing["expected_sha256"] == digest and
                    existing["evidence_type"] == kind):
                self._fail("MO_ERR_DUPLICATE", "evidence_payload")
        evidence_id = self._new_id("EVID", self.evidence_seq)
        self.evidence_seq += u256(1)
        self.evidence_records[evidence_id] = self._json({
            "evidence_id": evidence_id, "property_id": inspection["property_id"],
            "unit_id": inspection["unit_id"], "tenancy_id": inspection["tenancy_id"],
            "inspection_id": inspection_id, "room_id": room["room_id"],
            "area_item_id": area["area_item_id"],
            "condition_record_id": condition_id, "submitter": self._sender(),
            "evidence_type": kind, "source_ref": source,
            "expected_sha256": digest, "submitted_at": self._now(),
            "frozen_at": "", "status": "SUBMITTED",
            "supersedes_evidence_id": supersedes_id,
        })
        self._append(self.evidence_by_inspection, inspection_id, evidence_id,
                     u256(self.MAX_EVIDENCE_PER_INSPECTION), "evidence_per_inspection")
        self._add_inspection_membership(inspection, room["room_id"], area["area_item_id"],
                                        evidence_id=evidence_id)
        self._append_event(tenancy["property_id"], "EVIDENCE_SUBMITTED", "evidence", evidence_id)
        self._remember("submit_evidence", request_id, payload, evidence_id)
        return evidence_id

    @gl.public.write
    def freeze_evidence(self, evidence_id: str) -> None:
        evidence = self._load(self.evidence_records, evidence_id, "evidence")
        if self._sender() != evidence["submitter"]:
            self._fail("MO_ERR_UNAUTHORIZED", "original_submitter_required")
        if evidence["status"] == "FROZEN":
            return
        inspection = self._require_open_inspection(evidence["inspection_id"])
        evidence["status"] = "FROZEN"
        evidence["frozen_at"] = self._now()
        old_id = evidence["supersedes_evidence_id"]
        if old_id:
            old = self._load(self.evidence_records, old_id, "evidence")
            if old_id in self.superseded_by:
                self._fail("MO_ERR_DUPLICATE", "evidence_already_superseded")
            if (old["status"] != "FROZEN" or old["submitter"] != self._sender() or
                    old["property_id"] != evidence["property_id"] or
                    old["unit_id"] != evidence["unit_id"] or
                    old["tenancy_id"] != evidence["tenancy_id"] or
                    old["inspection_id"] == evidence["inspection_id"] or
                    old["room_id"] != evidence["room_id"] or
                    old["area_item_id"] != evidence["area_item_id"] or
                    old["evidence_type"] != evidence["evidence_type"]):
                self._fail("MO_ERR_WRONG_SCOPE", "supersession_binding")
            self.superseded_by[old_id] = evidence_id
        self.evidence_records[evidence_id] = self._json(evidence)
        self._append_event(inspection["property_id"], "EVIDENCE_FROZEN", "evidence", evidence_id)
        if old_id:
            self._append_event(inspection["property_id"], "EVIDENCE_SUPERSEDED",
                               "evidence", old_id)

    @gl.public.write
    def freeze_inspection(self, inspection_id: str) -> None:
        inspection = self._load(self.inspections, inspection_id, "inspection")
        if inspection["status"] == "FROZEN":
            if self._sender() == inspection["created_by"]:
                return
            self._fail("MO_ERR_UNAUTHORIZED", "inspection_creator_required")
        if inspection["status"] != "OPEN":
            self._fail("MO_ERR_STATE", "inspection_not_open")
        if self._sender() != inspection["created_by"]:
            self._fail("MO_ERR_UNAUTHORIZED", "inspection_creator_required")
        for evidence_id in inspection["evidence_ids"]:
            evidence = self._load(self.evidence_records, evidence_id, "evidence")
            if evidence["status"] != "FROZEN":
                self._fail("MO_ERR_STATE", "all_evidence_must_be_frozen")
        # Frozen membership is an exact bounded snapshot; child records cannot join later.
        inspection["status"] = "FROZEN"
        inspection["frozen_at"] = self._now()
        inspection["contents_committed"] = {
            "room_ids": inspection["room_ids"],
            "area_item_ids": inspection["area_item_ids"],
            "condition_record_ids": inspection["condition_record_ids"],
            "evidence_ids": inspection["evidence_ids"],
        }
        self.inspections[inspection_id] = self._json(inspection)
        self._append_event(inspection["property_id"], "INSPECTION_FROZEN", "inspection", inspection_id)

    @gl.public.view
    def get_property(self, property_id: str) -> str:
        return self._json(self._load(self.properties, property_id, "property"))

    @gl.public.view
    def get_unit(self, unit_id: str) -> str:
        return self._json(self._load(self.units, unit_id, "unit"))

    @gl.public.view
    def get_tenancy(self, tenancy_id: str) -> str:
        return self._json(self._load(self.tenancies, tenancy_id, "tenancy"))

    @gl.public.view
    def get_inspection(self, inspection_id: str) -> str:
        return self._json(self._load(self.inspections, inspection_id, "inspection"))

    @gl.public.view
    def get_room(self, room_id: str) -> str:
        return self._json(self._load(self.rooms, room_id, "room"))

    @gl.public.view
    def get_area_item(self, area_item_id: str) -> str:
        return self._json(self._load(self.area_items, area_item_id, "area_item"))

    @gl.public.view
    def get_condition_record(self, condition_record_id: str) -> str:
        return self._json(self._load(self.condition_records, condition_record_id, "condition_record"))

    @gl.public.view
    def get_evidence(self, evidence_id: str) -> str:
        evidence = self._load(self.evidence_records, evidence_id, "evidence")
        evidence["superseded_by_evidence_id"] = self.superseded_by.get(evidence_id, "")
        return self._json(evidence)

    @gl.public.view
    def get_visual_observation_record(self, observation_id: str) -> str:
        return self._json(self._load(self.visual_observations, observation_id,
                                     "visual_observation"))

    @gl.public.view
    def get_established_condition_record(self, finding_id: str) -> str:
        return self._json(self._load(self.established_conditions, finding_id,
                                     "established_condition"))

    @gl.public.view
    def get_event(self, event_id: str) -> str:
        return self._json(self._load(self.events, event_id, "event"))

    @gl.public.view
    def list_properties(self, creator: str, offset: u256, limit: u256) -> str:
        try:
            self._text(creator, u256(64), "creator_address")
            creator_key = Address(creator).as_hex
        except Exception:
            self._fail("MO_ERR_SCHEMA", "creator_address")
        return self._page(self.properties_by_creator, self.properties, creator_key, offset, limit)

    @gl.public.view
    def list_managers(self, property_id: str) -> str:
        self._load(self.properties, property_id, "property")
        addresses = json.loads(self.manager_addresses_by_property[property_id])
        result = []
        for manager in addresses:
            result.append({
                "address": manager,
                "active": self.manager_authority.get(property_id + "|" + manager, False),
            })
        return self._json({"items": result})

    @gl.public.view
    def list_units(self, property_id: str, offset: u256, limit: u256) -> str:
        return self._page(self.units_by_property, self.units, property_id, offset, limit)

    @gl.public.view
    def list_tenancies(self, property_id: str, offset: u256, limit: u256) -> str:
        return self._page(self.tenancies_by_property, self.tenancies, property_id, offset, limit)

    @gl.public.view
    def list_inspections(self, tenancy_id: str, offset: u256, limit: u256) -> str:
        return self._page(self.inspections_by_tenancy, self.inspections, tenancy_id, offset, limit)

    @gl.public.view
    def list_rooms(self, unit_id: str, offset: u256, limit: u256) -> str:
        return self._page(self.rooms_by_unit, self.rooms, unit_id, offset, limit)

    @gl.public.view
    def list_area_items(self, room_id: str, offset: u256, limit: u256) -> str:
        return self._page(self.areas_by_room, self.area_items, room_id, offset, limit)

    @gl.public.view
    def list_condition_records(self, inspection_id: str, offset: u256, limit: u256) -> str:
        return self._page(self.conditions_by_inspection, self.condition_records,
                          inspection_id, offset, limit)

    @gl.public.view
    def list_evidence(self, inspection_id: str, offset: u256, limit: u256) -> str:
        return self._page(self.evidence_by_inspection, self.evidence_records,
                          inspection_id, offset, limit)

    @gl.public.view
    def list_property_history(self, property_id: str, offset: u256, limit: u256) -> str:
        return self._page(self.events_by_property, self.events, property_id, offset, limit)

    @gl.public.view
    def list_visual_observations(self, inspection_id: str, offset: u256, limit: u256) -> str:
        return self._page(self.observations_by_inspection, self.visual_observations,
                          inspection_id, offset, limit)

    @gl.public.view
    def list_established_conditions(self, inspection_id: str,
                                    offset: u256, limit: u256) -> str:
        return self._page(self.findings_by_inspection, self.established_conditions,
                          inspection_id, offset, limit)
