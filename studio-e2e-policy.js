export const E2E_ORDER = ['connect', 'network', 'property', 'unit', 'tenancy', 'inspection', 'room', 'area', 'inclusion', 'condition', 'readback'];
export const E2E_FINAL_STATES = new Set(['PASS', 'FAILED', 'REJECTED', 'UNRESOLVED']);

export function stepUnlocked(state, step) {
  const index=E2E_ORDER.indexOf(step);
  if(index<0) return false;
  if(index===0) return true;
  for(const key of E2E_ORDER.slice(0,index)) if(state.steps?.[key]?.status!=='PASS') return false;
  return true;
}

export function classifyReceipt(receipt) {
  if(receipt?.statusName!=='FINALIZED') return {status:'UNRESOLVED',reason:`Not finalized (${receipt?.statusName ?? 'unknown status'})`};
  if(receipt?.txExecutionResultName!=='FINISHED_WITH_RETURN') return {status:'FAILED',reason:`Finalized without successful contract return (${receipt?.txExecutionResultName ?? 'execution result unknown'})`};
  return {status:'FINALIZED',reason:'Finalized with contract return; verify application state separately.'};
}

export function matchesRecord(actual, expected) {
  return Boolean(actual && Object.entries(expected).every(([key,value]) => actual[key] === value));
}

export function confirmed(action, submit) {
  if(action!=='confirm') return false;
  return Promise.resolve(submit()).then(()=>true);
}
