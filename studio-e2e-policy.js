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
