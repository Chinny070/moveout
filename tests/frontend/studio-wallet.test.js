import test from 'node:test';
import assert from 'node:assert/strict';
import { connectWallet, normalizeChainId, STUDIONET_CHAIN_ID, switchToStudioNet } from '../../studio-wallet.js';
import { WRITES, E2E_WRITES, VIEWS, submitOnlyWhenConfirmed } from '../../studio-policy.js';
import { E2E_ORDER, stepUnlocked, classifyReceipt, matchesRecord, restoreE2EState, isRecheckCandidate, confirmed } from '../../studio-e2e-policy.js';

test('normalizes hex and decimal chain IDs', () => {
  assert.equal(normalizeChainId('0xf22f'), STUDIONET_CHAIN_ID);
  assert.equal(normalizeChainId('61999'), STUDIONET_CHAIN_ID);
  assert.ok(Number.isNaN(normalizeChainId(undefined)));
});

test('connect requests public accounts and reports wrong chain without switching', async () => {
  const calls=[];
  const provider={request:async ({method})=>{calls.push(method);return method==='eth_requestAccounts'?['0xaffe15eec45b68835cc9e5b4ab85dd5deae8e70b']:'0x1';}};
  const state=await connectWallet(provider);
  assert.equal(state.correctChain,false);
  assert.deepEqual(calls,['eth_requestAccounts','eth_chainId']);
  assert.equal(calls.some((x)=>x.includes('privateKey')||x.includes('seed')),false);
});

test('missing provider fails explicitly', async () => {
  await assert.rejects(connectWallet(undefined),/No EIP-1193 wallet/);
});

test('switching handles an unknown network then verifies chain', async () => {
  const calls=[];
  const provider={request:async ({method,params})=>{
    calls.push({method,params});
    if(method==='wallet_switchEthereumChain'&&calls.filter(x=>x.method===method).length===1){const error=new Error('unknown chain');error.code=4902;throw error;}
    if(method==='eth_chainId')return '0xf22f';
    return null;
  }};
  assert.equal(await switchToStudioNet(provider),STUDIONET_CHAIN_ID);
  assert.deepEqual(calls.map(x=>x.method),['wallet_switchEthereumChain','wallet_addEthereumChain','eth_chainId']);
});

test('switching rejects if wallet remains on wrong chain', async () => {
  const provider={request:async ({method})=>method==='eth_chainId'?'0x1':null};
  await assert.rejects(switchToStudioNet(provider),/remains on chain 1/);
});

test('write allowlist excludes every disabled AI method', () => {
  for (const name of ['observe_nominated_target','observe_evidence','observe_evidence_pair','assess_supplemental_continuity']) {
    assert.equal(WRITES.has(name),false);
    assert.equal(VIEWS.has(name),false);
  }
  for (const name of ['observe_nominated_target','observe_evidence','observe_evidence_pair','assess_supplemental_continuity']) {
    assert.equal(E2E_WRITES.has(name),false);
  }
  assert.deepEqual([...E2E_WRITES].filter((name)=>!WRITES.has(name)).sort(),['freeze_evidence','freeze_inspection','verify_evidence_provenance']);
  assert.equal(VIEWS.has('get_evidence_verification_status'),true);
});

test('canceling confirmation never invokes the write callback', async () => {
  let calls=0;
  const submitted=await submitOnlyWhenConfirmed('cancel',async()=>{calls+=1;});
  assert.equal(submitted,false);
  assert.equal(calls,0);
});

test('confirmed dialog invokes its write callback exactly once', async () => {
  let calls=0;
  const submitted=await submitOnlyWhenConfirmed('confirm',async()=>{calls+=1;});
  assert.equal(submitted,true);
  assert.equal(calls,1);
});

test('E2E dependent steps stay locked until every earlier step is verified', () => {
  const state={steps:Object.fromEntries(E2E_ORDER.map((key)=>[key,{status:'PASS'}]))};
  assert.equal(stepUnlocked({steps:{connect:{status:'PASS'},network:{status:'LOCKED'}}},'network'),true);
  assert.equal(stepUnlocked(state,'property'),true);
  state.steps.unit.status='LOCKED';
  assert.equal(stepUnlocked(state,'tenancy'),false);
  assert.equal(stepUnlocked(state,'unit'),true);
  state.steps.unit.status='PASS';
  assert.equal(stepUnlocked(state,'evidence'),true);
  state.steps.freezeEvidence.status='LOCKED';
  assert.equal(stepUnlocked(state,'freezeInspection'),false);
});

test('refresh restoration preserves chain records and requires wallet reconnect and network recheck', () => {
  const fresh={version:2,runId:'FRESH',ids:{},steps:Object.fromEntries(E2E_ORDER.map((key)=>[key,{status:'LOCKED'}]))};
  const saved={version:2,runId:'SAVED',ids:{property_id:'PROP-1'},steps:Object.fromEntries(E2E_ORDER.map((key)=>[key,{status:'PASS',hash:`0x${key}`}]))};
  const restored=restoreE2EState(saved,fresh);
  assert.equal(restored.runId,'SAVED');
  assert.equal(restored.ids.property_id,'PROP-1');
  assert.equal(restored.steps.property.hash,'0xproperty');
  assert.equal(restored.steps.property.status,'RECHECKING');
  assert.equal(restored.steps.connect.status,'READY');
  assert.equal(restored.steps.network.status,'READY');
  assert.equal(stepUnlocked(restored,'network'),false);
  assert.equal(stepUnlocked(restored,'property'),false);
  restored.steps.connect.status='PASS';
  assert.equal(stepUnlocked(restored,'network'),true);
  restored.steps.network.status='PASS';
  restored.steps.property.status='PASS';
  assert.equal(stepUnlocked(restored,'property'),true);
});

test('unresolved submitted steps with a transaction hash remain eligible for read-only reconciliation', () => {
  assert.equal(isRecheckCandidate({status:'UNRESOLVED',hash:'0xsubmitted'}),true);
  assert.equal(isRecheckCandidate({status:'PASS',hash:'0xfinalized'}),true);
  assert.equal(isRecheckCandidate({status:'UNRESOLVED'}),false);
  assert.equal(isRecheckCandidate({status:'IN_PROGRESS',hash:'0xmaybe'}),false);
});

test('legacy E2E progress preserves identifiers but requires the new photo verification before final readback', () => {
  const fresh={version:2,runId:'FRESH',ids:{},steps:Object.fromEntries(E2E_ORDER.map((key)=>[key,{status:'LOCKED'}]))};
  const saved={runId:'OLD',ids:{property_id:'PROP-OLD'},steps:Object.fromEntries(['connect','network','property','unit','tenancy','inspection','room','area','inclusion','condition','readback'].map((key)=>[key,{status:'PASS',hash:`0x${key}`}]))};
  const restored=restoreE2EState(saved,fresh);
  assert.equal(restored.ids.property_id,'PROP-OLD');
  assert.equal(restored.steps.evidence.status,'LOCKED');
  assert.equal(restored.steps.readback.status,'READY');
  assert.equal(restored.steps.connect.status,'READY');
});

test('E2E requires finality and successful execution before state verification', () => {
  assert.equal(classifyReceipt({statusName:'ACCEPTED',txExecutionResultName:'FINISHED_WITH_RETURN'}).status,'UNRESOLVED');
  assert.equal(classifyReceipt({statusName:'FINALIZED',txExecutionResultName:'FINISHED_WITH_ERROR'}).status,'FAILED');
  assert.equal(classifyReceipt({statusName:'FINALIZED',txExecutionResultName:'FINISHED_WITH_RETURN'}).status,'FINALIZED');
  assert.equal(classifyReceipt({status_name:'FINALIZED',result_name:'MAJORITY_AGREE',consensus_data:{leader_receipt:[{mode:'leader',execution_result:'SUCCESS'}]}}).status,'FINALIZED');
  assert.equal(classifyReceipt({status_name:'FINALIZED',result_name:'MAJORITY_AGREE',consensus_data:{leader_receipt:[{mode:'leader',execution_result:'ERROR'}]}}).status,'FAILED');
  assert.equal(classifyReceipt({status_name:'FINALIZED',result_name:'MAJORITY_DISAGREE',consensus_data:{leader_receipt:[{mode:'leader',execution_result:'SUCCESS'}]}}).status,'FAILED');
  assert.equal(classifyReceipt({status_name:'FINALIZED',result_name:'MAJORITY_AGREE'}).status,'UNRESOLVED');
});

test('on-chain state verification compares required record fields exactly', () => {
  const expected={property_id:'PROP-1',property_label:'Test'};
  assert.equal(matchesRecord({property_id:'PROP-1',property_label:'Test',extra:'ok'},expected),true);
  assert.equal(matchesRecord({property_id:'PROP-2',property_label:'Test'},expected),false);
  assert.equal(matchesRecord(null,expected),false);
});

test('E2E transaction preparation remains behind explicit confirmation', async () => {
  let calls=0;
  assert.equal(await confirmed('cancel',async()=>{calls++;}),false);
  assert.equal(calls,0);
  assert.equal(await confirmed('confirm',async()=>{calls++;}),true);
  assert.equal(calls,1);
});
