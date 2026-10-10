export const E2E_ORDER = [
  'connect', 'network', 'property', 'unit', 'tenancy', 'inspection', 'room', 'area',
  'inclusion', 'condition', 'evidence', 'freezeEvidence', 'freezeInspection',
  'verifyEvidence', 'readback',
];
export const E2E_FINAL_STATES = new Set(['PASS', 'FAILED', 'REJECTED', 'UNRESOLVED']);

export function restoreE2EState(saved, fresh) {
  if (!saved || typeof saved !== 'object' || !saved.steps || !saved.runId) return fresh;
  const state = {
    ...fresh,
    ...saved,
    version: 2,
    ids: { ...fresh.ids, ...(saved.ids ?? {}) },
    steps: { ...fresh.steps, ...saved.steps },
  };
  if ((saved.version ?? 1) < 2 && state.steps.readback?.status === 'PASS') {
    state.steps.readback = {
      status: 'READY',
      message: 'Run the expanded readback after registering and verifying the public sample photo.',
    };
  }
  for (const key of E2E_ORDER.slice(2)) {
    if (state.steps[key]?.status === 'PASS') state.steps[key] = { ...state.steps[key], status: 'RECHECKING' };
  }
  for (const key of ['connect', 'network']) {
    if (state.steps[key]?.status === 'PASS') {
      state.steps[key] = {
        status: 'READY',
        message: 'Reconnect and verify the wallet again after refreshing the page.',
      };
    }
  }
  return state;
}

export function stepUnlocked(state, step) {
  const index=E2E_ORDER.indexOf(step);
  if(index<0) return false;
  if(index===0) return true;
  if(index===1) return state.steps?.connect?.status==='PASS';
  if(state.steps?.network?.status!=='PASS') return false;
  for(const key of E2E_ORDER.slice(2,index)) if(state.steps?.[key]?.status!=='PASS') return false;
  return true;
}

export function isRecheckCandidate(step) {
  return Boolean((step?.hash || step?.recoveredFromHash) && ['PASS', 'RECHECKING', 'UNRESOLVED'].includes(step.status));
}

export function canRecoverFailedTenancy(step) {
  return Boolean(step?.hash && step.status === 'FAILED');
}

export function canRecoverFailedArea(step) {
  return Boolean(step?.hash && step.status === 'FAILED');
}

export function findMatchingDraftTenancy(records, expected) {
  if (!Array.isArray(records)) return null;
  const matches = records.filter((record) =>
    record?.property_id === expected.property_id &&
    record?.unit_id === expected.unit_id &&
    record?.status === 'DRAFT' &&
    record?.start_metadata === expected.start_metadata &&
    typeof record?.tenant === 'string' && typeof expected.tenant === 'string' &&
    record.tenant.toLowerCase() === expected.tenant.toLowerCase() &&
    typeof record?.manager_creator === 'string' && typeof expected.manager === 'string' &&
    record.manager_creator.toLowerCase() === expected.manager.toLowerCase()
  );
  return matches.length === 1 ? matches[0] : null;
}

export function findMatchingAreaItem(records, expected) {
  if (!Array.isArray(records)) return null;
  const matches = records.filter((record) =>
    record?.room_id === expected.room_id &&
    record?.property_id === expected.property_id &&
    record?.unit_id === expected.unit_id &&
    record?.subject_type === expected.subject_type &&
    record?.label === expected.label &&
    record?.description_ref === expected.description_ref &&
    typeof record?.created_by === 'string' && typeof expected.creator === 'string' &&
    record.created_by.toLowerCase() === expected.creator.toLowerCase()
  );
  return matches.length === 1 ? matches[0] : null;
}

export function classifyReceipt(receipt) {
  const status=receipt?.statusName??receipt?.status_name;
  const result=receipt?.resultName??receipt?.result_name;
  const leaderReceipts=receipt?.consensus_data?.leader_receipt??receipt?.consensus_data?.leaderReceipt??[];
  const leaderReceipt=Array.isArray(leaderReceipts)?leaderReceipts.find((entry)=>entry?.mode==='leader')??leaderReceipts[0]:leaderReceipts;
  const execution=receipt?.txExecutionResultName??receipt?.tx_execution_result_name??receipt?.execution_result??leaderReceipt?.execution_result;
  if(status!=='FINALIZED') return {status:'UNRESOLVED',reason:`Not finalized (${status ?? 'unknown status'})`};
  if(result&& !['MAJORITY_AGREE','AGREE'].includes(result)) return {status:'FAILED',reason:`Finalized without accepted equivalence consensus (${result})`};
  if(!['FINISHED_WITH_RETURN','SUCCESS'].includes(execution)) {
    const status=execution==='FINISHED_WITH_ERROR'||execution==='ERROR'||execution==='FAILURE'?'FAILED':'UNRESOLVED';
    return {status,reason:`Finalized without a confirmed successful contract return (${execution ?? 'execution result unavailable'})`};
  }
  return {status:'FINALIZED',reason:'Finalized with contract return; verify application state separately.'};
}

export function matchesRecord(actual, expected) {
  return Boolean(actual && Object.entries(expected).every(([key,value]) => actual[key] === value));
}

export function confirmed(action, submit) {
  if(action!=='confirm') return false;
  return Promise.resolve(submit()).then(()=>true);
}
