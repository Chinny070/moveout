export const WRITES = new Set([
  'create_property', 'create_unit', 'create_tenancy', 'request_move_out', 'activate_tenancy',
  'create_inspection', 'create_room', 'create_area_item', 'include_area_in_inspection',
  'create_condition_record', 'submit_evidence',
]);
export const VIEWS = new Set([
  'list_properties', 'get_property', 'list_units', 'get_unit', 'list_tenancies', 'get_tenancy',
  'list_inspections', 'get_inspection', 'list_rooms', 'get_room', 'list_area_items', 'get_area_item',
  'list_inspection_area_items', 'list_condition_records', 'get_condition_record', 'list_evidence',
  'get_evidence', 'list_property_history', 'get_inspection_completeness',
]);

export function submitOnlyWhenConfirmed(returnValue, submit) {
  if (returnValue !== 'confirm') return false;
  return Promise.resolve(submit()).then(() => true);
}
