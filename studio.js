import { createClient } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';
import { TransactionStatus } from 'genlayer-js/types';
import { connectWallet, normalizeChainId, switchToStudioNet, STUDIONET_CHAIN_ID } from './studio-wallet.js';
import { WRITES, E2E_WRITES, VIEWS, submitOnlyWhenConfirmed } from './studio-policy.js';
import { E2E_ORDER, stepUnlocked, classifyReceipt, matchesRecord, restoreE2EState, isRecheckCandidate, canRecoverFailedTenancy, canRecoverFailedArea, findMatchingDraftTenancy, findMatchingAreaItem, confirmed as confirmE2E } from './studio-e2e-policy.js';

const RPC = 'https://studio.genlayer.com/api';
const CONTRACT = '0x4F96B354b19541F7087b73c548Dc2db380e09b77';
const root = document.querySelector('#studio-app');
const demoRoot = document.querySelector('#app');
const modeDemo = document.querySelector('#mode-demo');
const modeStudio = document.querySelector('#mode-studio');
const topNew = document.querySelector('#top-new');
const topConnect = document.querySelector('#top-connect');
const footerMode = document.querySelector('footer span:last-child');

let reader;
let writer;
let schema;
let account = null;
let correctChain = false;
let busy = false;
const E2E_KEY = 'moveout-studionet-e2e-v1';
const PUBLIC_SAMPLE_URL = 'https://raw.githubusercontent.com/Chinny070/moveout/8fa5bcbcc4918b28b5ba95ef431542a8d40fb128/benchmarks/stage3-fixtures/sample-photo.jpg';
const PUBLIC_SAMPLE_SHA256 = 'c9fcb81c83df208461db666064921602aef4a89fd118879528ea34c46b53d12a';
const E2E_NAMES = {
  connect:'Connect wallet', network:'Verify wallet network', property:'Create test property', unit:'Register test unit',
  tenancy:'Create test tenancy', inspection:'Create MOVE_IN inspection', room:'Add test room', area:'Add inspection area',
  inclusion:'Include area in inspection', condition:'Record manual condition note', evidence:'Register public test photograph',
  freezeEvidence:'Freeze photograph evidence', freezeInspection:'Freeze inspection record',
  verifyEvidence:'Verify photograph bytes on StudioNet', readback:'Verify inspection records on-chain',
};
function newE2E() {
  const suffix=crypto.randomUUID().slice(0,8).toUpperCase();
  return { version:2, runId:suffix, propertyLabel:`MoveOut StudioNet Test Property ${suffix}`, unitLabel:`Test Apartment ${suffix}`,
    roomLabel:`Living Room ${suffix}`, areaLabel:`Living Room Wall ${suffix}`,
    conditionText:'Small mark on living room wall, recorded for workflow testing only.',
    evidenceUrl:PUBLIC_SAMPLE_URL,evidenceSha256:PUBLIC_SAMPLE_SHA256,
    tenantAddress:'', managerAddress:'', ids:{}, steps:Object.fromEntries(E2E_ORDER.map((key)=>[key,{status:'LOCKED'}])) };
}
function loadE2E() {
  try {
    const saved=JSON.parse(localStorage.getItem(E2E_KEY)??sessionStorage.getItem(E2E_KEY)??'null');
    const state=restoreE2EState(saved,newE2E());
    state.evidenceUrl=PUBLIC_SAMPLE_URL;
    state.evidenceSha256=PUBLIC_SAMPLE_SHA256;
    return state;
  }
  catch { return newE2E(); }
}
let e2e=loadE2E();
function saveE2E() { localStorage.setItem(E2E_KEY,JSON.stringify(e2e)); }

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}
function rid() { return crypto.randomUUID(); }
function parse(value) {
  if (typeof value !== 'string') return value;
  try { return JSON.parse(value); } catch { return value; }
}
function method(name) {
  const value = schema?.methods?.[name];
  if (!value) throw new Error(`The deployed contract schema does not expose ${name}.`);
  return value;
}
function fields(name) {
  return (method(name).params ?? []).map(([name,type]) => ({name,type}));
}
function callArgs(name, values) {
  return fields(name).map((f) => {
    const key = f.name ?? f.identifier;
    if (!(key in values)) throw new Error(`Missing parameter ${key} for ${name}.`);
    return values[key];
  });
}
function read(name, values = {}) {
  if (!VIEWS.has(name)) throw new Error('This view is not enabled in the frontend.');
  const args = callArgs(name, values);
  return reader.readContract({ address: CONTRACT, functionName: name, args, transactionHashVariant: 'latest-final' }).then(parse);
}
function createWalletClient(address) {
  return createClient({ chain: studionet, account: address, provider: window.ethereum });
}
function button(label, action, attrs = '') {
  return `<button class="button button-outline button-small" data-action="${esc(action)}" ${attrs}>${esc(label)}</button>`;
}
function renderFrame(content) {
  root.innerHTML = `<section class="studio-page">
    <div class="studio-heading"><div><p class="eyebrow">LIVE CONTRACT RECORDS</p><h1>StudioNet workspace</h1><p class="muted">Read-only by default. StudioNet records are separate from this browser's Demo Mode data.</p></div><div class="studio-buttons">${account && !correctChain ? button('Switch to StudioNet','switch-chain') : ''}<button class="button button-dark button-small" data-action="connect">${account ? 'Wallet connected' : 'Connect wallet'}</button>${account ? button('Disconnect','disconnect') : ''}</div></div>
    <div class="studio-network"><strong>GenLayer StudioNet</strong><span>Chain 61999</span><code>${CONTRACT}</code><span>${correctChain ? 'Wallet chain verified' : account ? 'Wrong wallet network — writes disabled' : 'Public read mode'}</span></div>
    <div id="studio-alert" class="studio-alert hidden" role="status"></div>
    <div class="studio-content">${content}</div>
  </section>`;
}
function alert(message, bad = false) {
  const box = document.querySelector('#studio-alert');
  if (!box) return;
  box.classList.remove('hidden', 'error');
  if (bad) box.classList.add('error');
  box.textContent = message;
}
function errorText(error) {
  if (error?.code === 4001) return 'Wallet request was rejected. No transaction was submitted.';
  return error?.shortMessage || error?.message || String(error);
}
function receiptSummary(receipt) {
  const leaders=receipt?.consensus_data?.leader_receipt??receipt?.consensus_data?.leaderReceipt??[];
  const leader=Array.isArray(leaders)?leaders.find((entry)=>entry?.mode==='leader')??leaders[0]:leaders;
  return {
    status:receipt?.statusName??receipt?.status_name??'unknown',
    execution:receipt?.txExecutionResultName??receipt?.tx_execution_result_name??receipt?.execution_result??leader?.execution_result??'unknown',
    consensus:receipt?.resultName??receipt?.result_name??'consensus result unavailable',
  };
}
function panel(title, rows, actions = '') {
  return `<section class="studio-card"><div class="studio-card-head"><h2>${esc(title)}</h2>${actions}</div>${rows}</section>`;
}
function objectRows(value) {
  if (value == null || typeof value !== 'object') return `<p>${esc(value ?? 'No record returned.')}</p>`;
  return `<dl class="studio-dl">${Object.entries(value).map(([k,v]) => `<div><dt>${esc(k.replaceAll('_',' '))}</dt><dd>${esc(typeof v === 'object' ? JSON.stringify(v) : v)}</dd></div>`).join('')}</dl>`;
}
function itemRows(items, detailAction, type) {
  if (!Array.isArray(items) || items.length === 0) return '<p class="studio-empty">No records returned by the contract.</p>';
  return `<div class="studio-records">${items.map((item) => {
    const id = item.property_id ?? item.unit_id ?? item.tenancy_id ?? item.inspection_id ?? item.room_id ?? item.area_item_id ?? item.condition_record_id ?? item.evidence_id;
    const label = item.property_label ?? item.unit_label ?? item.inspection_type ?? item.room_label ?? item.label ?? item.condition_type ?? item.evidence_type ?? type;
    return `<button class="studio-record" data-action="${esc(detailAction)}" data-id="${esc(id)}"><strong>${esc(label)}</strong><code>${esc(id)}</code></button>`;
  }).join('')}</div>`;
}
function paged(payload) { return payload?.items ?? payload?.records ?? (Array.isArray(payload) ? payload : []); }
function stepState(key) {
  const saved=e2e.steps[key]?.status ?? 'LOCKED';
  return saved==='LOCKED' && stepUnlocked(e2e,key) ? 'READY' : saved;
}
function e2eCard(key, methodNames, params, expected) {
  const status=stepState(key);
  const canAct=status==='READY';
  const actionLabel=key==='connect'?'Connect wallet':key==='network'?'Verify wallet network':'Prepare & Approve in Wallet';
  const guidance={
    connect:'Connect a browser wallet to identify the account that will own the fictional test records.',
    network:'Verify the connected wallet is on GenLayer StudioNet before any test step can continue.',
    property:'Create a clearly labelled fictional property record owned by the connected account.',
    unit:'Add a test unit to the property created in the previous step.',
    tenancy:'Prepare a draft tenancy for a different test address. The manager cannot also be the tenant.',
    inspection:'Create a move-in inspection linked to the test tenancy.',
    room:'Add a test room to the property unit.',
    area:'Add an inspection area to the test room.',
    inclusion:'Link the inspection area to the test inspection.',
    condition:'Record a manual participant note. This is not an AI finding or a liability decision.',
    evidence:'Register the existing public sample JPEG URL and frozen SHA-256. No private photo is uploaded.',
    freezeEvidence:'Freeze the submitted evidence record so its source and digest cannot be changed.',
    freezeInspection:'Freeze the inspection manifest after its room, target area, note, and photograph are present.',
    verifyEvidence:'Ask StudioNet validators to independently fetch the public JPEG and check its SHA-256.',
    readback:'Read the finalized property, inspection, note, evidence, and provenance records again from StudioNet.'
  }[key];
  const buttonHtml=canAct?`<button class="button ${key==='connect'?'button-outline':'button-dark'} button-small" data-action="e2e-${esc(key)}">${actionLabel}</button>`:'';
  const statusClass=status==='PASS'?'pass':status==='FAILED'||status==='REJECTED'||status==='UNRESOLVED'?'fail':'';
  const step=e2e.steps[key]??{};
  const hashes=step.hash?(step.status==='REJECTED'?`<p class="e2e-hash">Prior transaction retained for read-only reconciliation (the rejected wallet request submitted nothing): <code>${esc(step.hash)}</code></p>`:`<p class="e2e-hash">Transaction: <code>${esc(step.hash)}</code><br>Status: ${esc(step.receiptStatus??status)}</p>`):'';
  const recoveredHash=step.recoveredFromHash?`<p class="e2e-hash">Failed attempt (not the recovered record): <code>${esc(step.recoveredFromHash)}</code></p>`:'';
  return `<article class="e2e-step ${statusClass}"><div class="e2e-step-head"><span class="e2e-step-number">${E2E_ORDER.indexOf(key)+1}</span><div class="e2e-step-title"><h3>${esc(E2E_NAMES[key])}</h3><p>${esc(guidance)}</p></div><span class="e2e-status ${statusClass}" data-e2e-status="${key}">${esc(status)}</span></div><details class="e2e-result"><summary>What this step verifies</summary><p>${esc(expected)}</p></details>${hashes}${recoveredHash}${step.message?`<p class="e2e-message">${esc(step.message)}</p>`:''}${buttonHtml}</article>`;
}
function e2ePanel() {
  const prefix=`Run ${e2e.runId}; fictional test records are permanent contract records. The sample photograph is already public; private photographs and AI assessment methods are not used.`;
  return `<section class="e2e-panel"><div class="studio-card-head"><div><p class="eyebrow">OWNER-APPROVED TRANSACTION TEST</p><h2>MoveOut — Live StudioNet Test</h2></div><span class="e2e-tag">Live contract · No mock responses</span></div><p class="studio-caution">${esc(prefix)} Each write opens a separate app confirmation and wallet approval. Canceling does not submit. Never approve unless the wallet shows StudioNet and you have reviewed the transaction.</p><div class="e2e-records"><label class="write-field">Test property label<input class="field-input" readonly value="${esc(e2e.propertyLabel)}"></label><label class="write-field">Test unit label<input class="field-input" readonly value="${esc(e2e.unitLabel)}"></label><label class="write-field">Test room label<input class="field-input" readonly value="${esc(e2e.roomLabel)}"></label><label class="write-field">Test inspection area<input class="field-input" readonly value="${esc(e2e.areaLabel)}"></label><label class="write-field">Designated tenant test address<input class="field-input" data-e2e-tenant value="${esc(e2e.tenantAddress)}" placeholder="Enter a second test account address (not the manager)"></label></div><div class="e2e-steps">
  ${e2eCard('connect','EIP-1193 eth_requestAccounts','Explicit browser-wallet account request','A public wallet address is returned; no key material is requested.')}
  ${e2eCard('network','eth_chainId','Expected chain ID 61999','Connected wallet is on StudioNet 61999.')}
  ${e2eCard('property','create_property',JSON.stringify({property_label:e2e.propertyLabel,request_id:'unique per test action'}),'A finalized transaction and matching property record created by the connected manager.')}
  ${e2eCard('unit','create_unit',JSON.stringify({property_id:e2e.ids.property_id??'from step 3',unit_label:e2e.unitLabel,request_id:'unique per test action'}),'A finalized unit record linked to the new property.')}
  ${e2eCard('tenancy','create_tenancy',JSON.stringify({property_id:e2e.ids.property_id??'from step 3',unit_id:e2e.ids.unit_id??'from step 4',tenant_address:e2e.tenantAddress||'owner supplies a different test address',start_metadata:'MoveOut E2E fictional test',request_id:'unique per test action'}),'A DRAFT tenancy linked to the property and unit; tenant address differs from manager. The contract forbids manager-as-tenant.')}
  ${e2eCard('inspection','create_inspection',JSON.stringify({tenancy_id:e2e.ids.tenancy_id??'from step 5',inspection_type:'MOVE_IN',request_id:'unique per test action'}),'A MOVE_IN inspection linked to the DRAFT tenancy. Manager is a participant per deployed contract rules.')}
  ${e2eCard('room','create_room',JSON.stringify({unit_id:e2e.ids.unit_id??'from step 4',room_label:e2e.roomLabel,request_id:'unique per test action'}),'A room record linked to the test unit.')}
  ${e2eCard('area','create_area_item',JSON.stringify({room_id:e2e.ids.room_id??'from step 6',subject_type:'SURFACE',label:e2e.areaLabel,description_ref:'Fictional E2E inspection target',request_id:'unique per test action'}),'An inspection area item linked to the test room.')}
  ${e2eCard('inclusion','include_area_in_inspection',JSON.stringify({inspection_id:e2e.ids.inspection_id??'from step 5',area_item_id:e2e.ids.area_item_id??'from step 6',request_id:'unique per test action'}),'The new area is listed in the test inspection.')}
  ${e2eCard('condition','create_condition_record',JSON.stringify({inspection_id:e2e.ids.inspection_id??'from step 5',area_item_id:e2e.ids.area_item_id??'from step 6',condition_type:'MAINTENANCE_NOTE',description:e2e.conditionText,claim_ref:'',request_id:'unique per test action'}),'A participant-recorded workflow note appears in the inspection; not an AI finding or liability assessment.')}
  <div class="e2e-sample"><p class="eyebrow">PUBLIC TEST PHOTOGRAPH</p><p><a href="${PUBLIC_SAMPLE_URL}" target="_blank" rel="noopener noreferrer">View the existing sample bedroom JPEG (8,858 bytes)</a></p><code>SHA-256 ${PUBLIC_SAMPLE_SHA256}</code><p>This commit-pinned project fixture was already publicly hosted for provenance testing. The contract stores this URL and digest, not the image bytes.</p></div>
  ${e2eCard('evidence','submit_evidence',JSON.stringify({inspection_id:e2e.ids.inspection_id??'from step 5',area_item_id:e2e.ids.area_item_id??'from step 6',condition_record_id:e2e.ids.condition_record_id??'from step 10',evidence_type:'PHOTO',source_ref:PUBLIC_SAMPLE_URL,expected_sha256:PUBLIC_SAMPLE_SHA256,supersedes_evidence_id:'',request_id:'unique per test action'}),'The contract stores the public URL, digest, and parent IDs as SUBMITTED photo evidence.')}
  ${e2eCard('freezeEvidence','freeze_evidence',JSON.stringify({evidence_id:e2e.ids.evidence_id??'from photograph registration'}),'The exact photo metadata record is FROZEN.')}
  ${e2eCard('freezeInspection','freeze_inspection',JSON.stringify({inspection_id:e2e.ids.inspection_id??'from step 5'}),'The inspection manifest is FROZEN with all evidence and area links committed.')}
  ${e2eCard('verifyEvidence','verify_evidence_provenance',JSON.stringify({tenancy_id:e2e.ids.tenancy_id??'from step 5',evidence_id:e2e.ids.evidence_id??'from photograph registration',request_id:'unique per test action'}),'A finalized validator-side retrieval record reports VERIFIED with the expected SHA-256.')}
  ${e2eCard('readback','get_property, get_unit, get_tenancy, get_inspection, get_room, get_area_item, get_condition_record, get_evidence, get_evidence_verification_status','Read finalized state for each created record','Every returned record, parent link, frozen status, source URL, digest, and provenance result matches the prepared test data.')}
  <button class="button button-outline button-small" data-action="e2e-recheck" type="button">Recheck saved on-chain progress</button>
  </div></section>`;
}

function saveStep(key,status,details={}) { e2e.steps[key]={...(e2e.steps[key]??{}),status,...details}; saveE2E(); }
function sameAddress(a,b) { return typeof a==='string'&&typeof b==='string'&&a.toLowerCase()===b.toLowerCase(); }
function lookup(list, predicate) { return paged(list).find(predicate) ?? null; }
function fieldLabel(name) {
  const labels={property_label:'Test property',unit_label:'Test unit',tenant_address:'Test tenant wallet',
    inspection_type:'Inspection type',room_label:'Test room',label:'Inspection area',description:'Manual condition note',
    evidence_type:'Evidence type',source_ref:'Public photograph source',expected_sha256:'Expected SHA-256',
    evidence_id:'Evidence record',inspection_id:'Inspection record',tenancy_id:'Tenancy record',
    area_item_id:'Inspection area record',condition_record_id:'Condition note record',supersedes_evidence_id:'Superseded evidence'};
  return labels[name]??name.replaceAll('_',' ').replace(/\b\w/g,(letter)=>letter.toUpperCase());
}
function stepPrerequisite(key) {
  if(!stepUnlocked(e2e,key)) throw new Error(`Complete and verify the previous step before ${E2E_NAMES[key]}.`);
  if(key!=='connect'&&key!=='network'&&(!account||!correctChain)) throw new Error('Connect a wallet on StudioNet 61999 first.');
  if(e2e.managerAddress&&account&&!sameAddress(e2e.managerAddress,account)) throw new Error('This E2E run is bound to the manager wallet that created its test property. Reconnect that wallet; do not submit a duplicate write.');
}
function confirmationDialog(key,methodName,args) {
  return new Promise((resolve)=>{
    const dialog=document.createElement('dialog'); dialog.className='dialog e2e-confirm';
    const summary=Object.entries(args).filter(([name])=>name!=='request_id').map(([name,value])=>`<div><dt>${esc(fieldLabel(name))}</dt><dd>${esc(value===''?'None':value)}</dd></div>`).join('');
    dialog.innerHTML=`<form method="dialog"><div class="dialog-top"><div><p class="eyebrow">LIVE STUDIONET TRANSACTION</p><h2>Review before wallet approval</h2></div><button class="icon-button" value="cancel" aria-label="Close">×</button></div><p><b>Action:</b> ${esc(E2E_NAMES[key])}<br><b>Network:</b> StudioNet · 61999<br><b>Wallet:</b> ${esc(account)}<br><b>Contract:</b> ${CONTRACT}<br><b>Value:</b> 0 GEN</p><dl class="e2e-transaction-fields">${summary}</dl><details class="e2e-technical"><summary>Advanced transaction details</summary><p>Contract method: <code>${esc(methodName)}</code></p><pre class="e2e-args">${esc(JSON.stringify(args,null,2))}</pre></details><p class="privacy-hint">This creates permanent test data. The next step stays locked until the transaction is FINALIZED, execution returned successfully, and an actual contract view confirms the expected record. Never re-submit an uncertain transaction.</p><div class="dialog-actions"><button class="button button-quiet" value="cancel">Cancel</button><button class="button button-dark" value="confirm">Continue to wallet approval</button></div></form>`;
    document.body.append(dialog);
    dialog.addEventListener('close',()=>{const action=dialog.returnValue;dialog.remove();resolve(action);},{once:true});
    dialog.showModal();
  });
}
async function e2eWrite(key,methodName,values,verify) {
  try {
    stepPrerequisite(key);
    if(!E2E_WRITES.has(methodName)) throw new Error(`${methodName} is not an enabled guided test method.`);
    if(!writer) throw new Error('Wallet-backed GenLayer client is not connected.');
    const currentChain=normalizeChainId(await window.ethereum.request({method:'eth_chainId'}));
    if(currentChain!==STUDIONET_CHAIN_ID) throw new Error(`Wallet changed network to ${currentChain}; transaction was not prepared.`);
    if(key==='tenancy'&&!/^0x[\da-f]{40}$/i.test(e2e.tenantAddress)) throw new Error('Enter a valid public address for a different test tenant account.');
    if(key==='tenancy'&&sameAddress(e2e.tenantAddress,account)) throw new Error('The test tenant must be different from the property manager wallet.');
    const args=callArgs(methodName,values);
    const params=Object.fromEntries(fields(methodName).map((p,i)=>[p.name,args[i]]));
    saveStep(key,'READY',{message:'Awaiting explicit in-app confirmation.'});
    const decision=await confirmationDialog(key,methodName,params);
    const allowed=await confirmE2E(decision,async()=>true);
    if(!allowed){saveStep(key,'READY',{message:'Canceled in app. No wallet request or transaction was made.'});await loadHome();return;}
    saveStep(key,'IN_PROGRESS',{message:'Wallet request in progress. No automatic retry.'});
    await loadHome();
    let hash;
    try { hash=await writer.writeContract({address:CONTRACT,functionName:methodName,args,value:0n}); }
    catch(error) { const rejected=error?.code===4001;saveStep(key,rejected?'REJECTED':'UNRESOLVED',{message:`${errorText(error)}. No automatic retry; inspect wallet/network before another test run.`});await loadHome();return; }
    saveStep(key,'SUBMITTED',{hash,message:'Submitted; waiting for FINALIZED receipt. Do not resubmit.'});
    await loadHome();
    let receipt;
    try { receipt=await writer.waitForTransactionReceipt({hash,status:TransactionStatus.FINALIZED,retries:60,interval:5000}); }
    catch(error) { saveStep(key,'UNRESOLVED',{hash,message:`Receipt/finality could not be confirmed: ${errorText(error)}. Use this hash to check the chain; do not submit again.`});await loadHome();return; }
    const outcome=classifyReceipt(receipt);
    const summary=receiptSummary(receipt);
    if(outcome.status!=='FINALIZED') { saveStep(key,outcome.status,{hash,receiptStatus:`${summary.status} / ${summary.execution} / ${summary.consensus}`,message:outcome.reason});await loadHome();return; }
    const result=await verify();
    if(!result?.ok){saveStep(key,'FAILED',{hash,receiptStatus:`${summary.status} / ${summary.execution} / ${summary.consensus}`,message:`Transaction finalized but expected application state was not verified: ${result?.reason??'no matching record returned'}.`});await loadHome();return;}
    Object.assign(e2e.ids,result.ids??{});
    if(key==='property')e2e.managerAddress=account;
    saveStep(key,'PASS',{hash,receiptStatus:`${summary.status} / ${summary.execution} / ${summary.consensus}`,message:result.message??'Finalized and matched to a contract view.'});
    await loadHome();
  } catch(error) { saveStep(key,'FAILED',{message:errorText(error)});await loadHome(); }
}

function verifiedEvidenceStatus(status) {
  const latest=status?.latest;
  return Boolean(status?.historically_verified && latest?.outcome==='VERIFIED' &&
    latest?.expected_sha256===PUBLIC_SAMPLE_SHA256 && latest?.retrieved_sha256===PUBLIC_SAMPLE_SHA256);
}
async function readbackRecords() {
  const [property,unit,tenancy,inspection,room,area,condition,evidence,verification,completeness]=await Promise.all([
    read('get_property',{property_id:e2e.ids.property_id}),read('get_unit',{unit_id:e2e.ids.unit_id}),
    read('get_tenancy',{tenancy_id:e2e.ids.tenancy_id}),read('get_inspection',{inspection_id:e2e.ids.inspection_id}),
    read('get_room',{room_id:e2e.ids.room_id}),read('get_area_item',{area_item_id:e2e.ids.area_item_id}),
    read('get_condition_record',{condition_record_id:e2e.ids.condition_record_id}),read('get_evidence',{evidence_id:e2e.ids.evidence_id}),
    read('get_evidence_verification_status',{evidence_id:e2e.ids.evidence_id}),
    read('get_inspection_completeness',{inspection_id:e2e.ids.inspection_id}),
  ]);
  const checks=[
    matchesRecord(property,{property_id:e2e.ids.property_id,property_label:e2e.propertyLabel})&&sameAddress(property.creator,e2e.managerAddress),
    matchesRecord(unit,{unit_id:e2e.ids.unit_id,property_id:e2e.ids.property_id,unit_label:e2e.unitLabel}),
    matchesRecord(tenancy,{tenancy_id:e2e.ids.tenancy_id,property_id:e2e.ids.property_id,unit_id:e2e.ids.unit_id,status:'DRAFT'})&&sameAddress(tenancy.tenant,e2e.tenantAddress),
    matchesRecord(inspection,{inspection_id:e2e.ids.inspection_id,tenancy_id:e2e.ids.tenancy_id,inspection_type:'MOVE_IN',status:'FROZEN'}),
    matchesRecord(room,{room_id:e2e.ids.room_id,unit_id:e2e.ids.unit_id,room_label:e2e.roomLabel}),
    matchesRecord(area,{area_item_id:e2e.ids.area_item_id,room_id:e2e.ids.room_id,label:e2e.areaLabel}),
    matchesRecord(condition,{condition_record_id:e2e.ids.condition_record_id,inspection_id:e2e.ids.inspection_id,area_item_id:e2e.ids.area_item_id,condition_type:'MAINTENANCE_NOTE',description:e2e.conditionText}),
    matchesRecord(evidence,{evidence_id:e2e.ids.evidence_id,inspection_id:e2e.ids.inspection_id,area_item_id:e2e.ids.area_item_id,condition_record_id:e2e.ids.condition_record_id,evidence_type:'PHOTO',source_ref:PUBLIC_SAMPLE_URL,expected_sha256:PUBLIC_SAMPLE_SHA256,status:'FROZEN'}),
    verifiedEvidenceStatus(verification),
    completeness?.complete===true&&completeness?.frozen===true,
  ];
  return {ok:checks.every(Boolean),checks,property,unit,tenancy,inspection,room,area,condition,evidence,verification,completeness};
}
async function verifySavedStep(key,cache=new Map()) {
  const id=e2e.ids;
  const get=(name,args)=>{const key=`${name}:${JSON.stringify(args)}`;if(!cache.has(key))cache.set(key,read(name,args));return cache.get(key);};
  if(key==='property') {
    if(!id.property_id) {
      const list=await get('list_properties',{creator:e2e.managerAddress,offset:0,limit:50});
      const matches=paged(list).filter((r)=>r.property_label===e2e.propertyLabel&&sameAddress(r.creator,e2e.managerAddress));
      if(matches.length!==1)return false;
      id.property_id=matches[0].property_id;
      saveE2E();
    }
    const r=await get('get_property',{property_id:id.property_id});return matchesRecord(r,{property_id:id.property_id,property_label:e2e.propertyLabel})&&sameAddress(r.creator,e2e.managerAddress);
  }
  if(key==='unit') return matchesRecord(await get('get_unit',{unit_id:id.unit_id}),{unit_id:id.unit_id,property_id:id.property_id,unit_label:e2e.unitLabel});
  if(key==='tenancy') { const r=await get('get_tenancy',{tenancy_id:id.tenancy_id});return matchesRecord(r,{tenancy_id:id.tenancy_id,property_id:id.property_id,unit_id:id.unit_id,status:'DRAFT'})&&sameAddress(r.tenant,e2e.tenantAddress); }
  if(key==='inspection') return matchesRecord(await get('get_inspection',{inspection_id:id.inspection_id}),{inspection_id:id.inspection_id,tenancy_id:id.tenancy_id,inspection_type:'MOVE_IN'});
  if(key==='room') return matchesRecord(await get('get_room',{room_id:id.room_id}),{room_id:id.room_id,unit_id:id.unit_id,room_label:e2e.roomLabel});
  if(key==='area') return matchesRecord(await get('get_area_item',{area_item_id:id.area_item_id}),{area_item_id:id.area_item_id,room_id:id.room_id,label:e2e.areaLabel});
  if(key==='inclusion') { const r=await get('get_inspection',{inspection_id:id.inspection_id});return Array.isArray(r.area_item_ids)&&r.area_item_ids.includes(id.area_item_id); }
  if(key==='condition') return matchesRecord(await get('get_condition_record',{condition_record_id:id.condition_record_id}),{condition_record_id:id.condition_record_id,inspection_id:id.inspection_id,area_item_id:id.area_item_id,condition_type:'MAINTENANCE_NOTE',description:e2e.conditionText});
  if(key==='evidence'||key==='freezeEvidence') {
    const r=await get('get_evidence',{evidence_id:id.evidence_id});
    return matchesRecord(r,{evidence_id:id.evidence_id,inspection_id:id.inspection_id,area_item_id:id.area_item_id,source_ref:PUBLIC_SAMPLE_URL,expected_sha256:PUBLIC_SAMPLE_SHA256})&&(key!=='freezeEvidence'||r.status==='FROZEN');
  }
  if(key==='freezeInspection') { const [r,c]=await Promise.all([get('get_inspection',{inspection_id:id.inspection_id}),get('get_inspection_completeness',{inspection_id:id.inspection_id})]);return r.status==='FROZEN'&&c?.complete===true; }
  if(key==='verifyEvidence') return verifiedEvidenceStatus(await get('get_evidence_verification_status',{evidence_id:id.evidence_id}));
  return false;
}
async function recheckSavedProgress({automatic=false}={}) {
  const keys=E2E_ORDER.slice(2).filter(key=>key!=='readback'&&(isRecheckCandidate(e2e.steps[key])||(key==='tenancy'&&canRecoverFailedTenancy(e2e.steps[key]))||(key==='area'&&canRecoverFailedArea(e2e.steps[key]))));
  if(!keys.length){if(!automatic)alert('No finalized StudioNet test steps are saved to recheck. No transaction was sent.');return;}
  if(!automatic)alert('Re-reading saved records from finalized StudioNet state. No transaction will be sent.');
  let chainVerified=true;
  const cache=new Map();
  for(const key of keys){
    let ok=false;
    let receiptStatus;
    try {
      const step=e2e.steps[key];
      if(key==='area'&&canRecoverFailedArea(step)) {
        try {
          const receipt=await reader.waitForTransactionReceipt({hash:step.hash,status:TransactionStatus.FINALIZED,retries:60,interval:5000});
          const outcome=classifyReceipt(receipt);
          const summary=receiptSummary(receipt);
          const receiptStatus=`${summary.status} / ${summary.execution} / ${summary.consensus}`;
          if(outcome.status!=='FINALIZED') {
            saveStep(key,outcome.status,{receiptStatus,message:`Saved transaction did not finalize with a successful contract return: ${outcome.reason}. No transaction was sent.`});
            chainVerified=false;
            continue;
          }
          const records=paged(await read('list_area_items',{room_id:e2e.ids.room_id,offset:0,limit:50}));
          const record=findMatchingAreaItem(records,{
            room_id:e2e.ids.room_id,
            property_id:e2e.ids.property_id,
            unit_id:e2e.ids.unit_id,
            subject_type:'SURFACE',
            label:e2e.areaLabel,
            description_ref:'Fictional E2E inspection target',
            creator:e2e.managerAddress,
          });
          if(record) {
            e2e.ids.area_item_id=record.area_item_id;
            saveStep(key,'PASS',{receiptStatus,message:`Verified finalized area ${record.area_item_id} from the on-chain room record. No transaction was sent.`});
          } else {
            saveStep(key,'FAILED',{receiptStatus,message:'The transaction succeeded, but no unique area record matched this run’s room, label, type, description, and creator. No transaction was sent.'});
            chainVerified=false;
          }
        } catch(error) {
          saveStep(key,'FAILED',{message:`Read-only area recovery could not complete: ${errorText(error)}. Retry the recheck later; no transaction was sent.`});
          chainVerified=false;
        }
        continue;
      }
      if(key==='tenancy'&&canRecoverFailedTenancy(step)) {
        try {
          const records=paged(await read('list_tenancies',{property_id:e2e.ids.property_id,offset:0,limit:50}));
          const record=findMatchingDraftTenancy(records,{
            property_id:e2e.ids.property_id,
            unit_id:e2e.ids.unit_id,
            tenant:e2e.tenantAddress,
            manager:e2e.managerAddress,
            start_metadata:`Fictional MoveOut E2E ${e2e.runId}`,
          });
          if(record) {
            e2e.ids.tenancy_id=record.tenancy_id;
            saveStep(key,'PASS',{hash:undefined,recoveredFromHash:step.hash,receiptStatus:'READ-ONLY RECORD RECOVERY',message:`Verified existing DRAFT tenancy ${record.tenancy_id} from the finalized contract view. No transaction was sent.`});
          } else {
            saveStep(key,'FAILED',{message:'No unique DRAFT tenancy matched this run’s property, unit, tenant, manager, and run metadata. No transaction was sent; check inputs and retry this read-only recheck.'});
            chainVerified=false;
          }
        } catch(error) {
          saveStep(key,'FAILED',{message:`Read-only tenancy recovery could not complete: ${errorText(error)}. Retry the recheck later; no transaction was sent.`});
          chainVerified=false;
        }
        continue;
      }
      let finalized=Boolean(step?.hash||(key==='tenancy'&&step?.recoveredFromHash));
      if(finalized&&step.status==='UNRESOLVED') {
        const receipt=await reader.waitForTransactionReceipt({hash:step.hash,status:TransactionStatus.FINALIZED,retries:60,interval:5000});
        const outcome=classifyReceipt(receipt);
        const summary=receiptSummary(receipt);
        finalized=outcome.status==='FINALIZED';
        receiptStatus=`${summary.status} / ${summary.execution} / ${summary.consensus}`;
      }
      ok=chainVerified&&finalized&&await verifySavedStep(key,cache);
    } catch { ok=false; }
    if(!ok){chainVerified=false;saveStep(key,'UNRESOLVED',{message:'Could not independently confirm this saved step from the current finalized contract view. Check its transaction hash; do not resubmit.'});}
    else saveStep(key,'PASS',{...(receiptStatus?{receiptStatus}:{}),message:'Re-read and matched the finalized contract record after page refresh.'});
  }
  if(['PASS','RECHECKING'].includes(e2e.steps.readback?.status)){
    const allExpected=E2E_ORDER.slice(2,E2E_ORDER.indexOf('readback')).every(key=>e2e.steps[key]?.status==='PASS');
    saveStep('readback',chainVerified&&allExpected?'PASS':'UNRESOLVED',{message:chainVerified&&allExpected?'All finalized records and validator provenance were re-read and matched after refresh.':'One or more records failed re-verification. Inspect the recorded hashes; do not resubmit a write.'});
  }
  await loadHome();
}

async function runE2EStep(key) {
  try {
    if(key==='connect') { await connect();return; }
    if(key==='network') {
      stepPrerequisite(key);
      const chain=normalizeChainId(await window.ethereum.request({method:'eth_chainId'}));
      correctChain=chain===STUDIONET_CHAIN_ID;
      if(correctChain)writer=createWalletClient(account);else writer=null;
      if(!correctChain) { saveStep('network','READY',{message:`Wallet is on chain ${chain}; use “Switch to StudioNet” then verify again.`});await loadHome();return; }
      e2e.managerAddress=account;saveStep('network','PASS',{message:`Verified chain 61999 for ${account}.`});await loadHome();return;
    }
    if(key==='property') return e2eWrite(key,'create_property',{property_label:e2e.propertyLabel,request_id:rid()},async()=>{
      const found=lookup(await read('list_properties',{creator:account,offset:0,limit:50}),r=>r.property_label===e2e.propertyLabel&&sameAddress(r.creator,account));
      if(!found)return {ok:false,reason:'list_properties did not return the new property'};
      return {ok:true,ids:{property_id:found.property_id},message:`Verified property ${found.property_id} via list_properties.`};
    });
    if(key==='unit') return e2eWrite(key,'create_unit',{property_id:e2e.ids.property_id,unit_label:e2e.unitLabel,request_id:rid()},async()=>{
      const found=lookup(await read('list_units',{property_id:e2e.ids.property_id,offset:0,limit:50}),r=>r.unit_label===e2e.unitLabel&&r.property_id===e2e.ids.property_id);
      if(!found)return {ok:false,reason:'list_units did not return the expected child unit'};
      return {ok:true,ids:{unit_id:found.unit_id},message:`Verified unit ${found.unit_id} via list_units.`};
    });
    if(key==='tenancy') return e2eWrite(key,'create_tenancy',{property_id:e2e.ids.property_id,unit_id:e2e.ids.unit_id,tenant_address:e2e.tenantAddress,start_metadata:`Fictional MoveOut E2E ${e2e.runId}`,request_id:rid()},async()=>{
      const found=lookup(await read('list_tenancies',{property_id:e2e.ids.property_id,offset:0,limit:50}),r=>r.unit_id===e2e.ids.unit_id&&sameAddress(r.tenant,e2e.tenantAddress)&&r.status==='DRAFT');
      if(!found)return {ok:false,reason:'list_tenancies did not return matching DRAFT tenancy'};
      return {ok:true,ids:{tenancy_id:found.tenancy_id},message:`Verified DRAFT tenancy ${found.tenancy_id}.`};
    });
    if(key==='inspection') return e2eWrite(key,'create_inspection',{tenancy_id:e2e.ids.tenancy_id,inspection_type:'MOVE_IN',request_id:rid()},async()=>{
      const found=lookup(await read('list_inspections',{tenancy_id:e2e.ids.tenancy_id,offset:0,limit:50}),r=>r.tenancy_id===e2e.ids.tenancy_id&&r.inspection_type==='MOVE_IN');
      if(!found)return {ok:false,reason:'list_inspections did not return a MOVE_IN inspection for the test tenancy'};
      return {ok:true,ids:{inspection_id:found.inspection_id},message:`Verified MOVE_IN inspection ${found.inspection_id}.`};
    });
    if(key==='room') return e2eWrite(key,'create_room',{unit_id:e2e.ids.unit_id,room_label:e2e.roomLabel,request_id:rid()},async()=>{
      const found=lookup(await read('list_rooms',{unit_id:e2e.ids.unit_id,offset:0,limit:50}),r=>r.unit_id===e2e.ids.unit_id&&r.room_label===e2e.roomLabel);
      if(!found)return {ok:false,reason:'list_rooms did not return the expected test room'};
      return {ok:true,ids:{room_id:found.room_id},message:`Verified room ${found.room_id}.`};
    });
    if(key==='area') return e2eWrite(key,'create_area_item',{room_id:e2e.ids.room_id,subject_type:'SURFACE',label:e2e.areaLabel,description_ref:'Fictional E2E inspection target',request_id:rid()},async()=>{
      const found=lookup(await read('list_area_items',{room_id:e2e.ids.room_id,offset:0,limit:50}),r=>r.room_id===e2e.ids.room_id&&r.label===e2e.areaLabel);
      if(!found)return {ok:false,reason:'list_area_items did not return the expected test area'};
      return {ok:true,ids:{area_item_id:found.area_item_id},message:`Verified area item ${found.area_item_id}.`};
    });
    if(key==='inclusion') return e2eWrite(key,'include_area_in_inspection',{inspection_id:e2e.ids.inspection_id,area_item_id:e2e.ids.area_item_id,request_id:rid()},async()=>{
      const found=lookup(await read('list_inspection_area_items',{inspection_id:e2e.ids.inspection_id,offset:0,limit:50}),r=>r.area_item_id===e2e.ids.area_item_id);
      if(!found)return {ok:false,reason:'list_inspection_area_items did not return the included target area'};
      return {ok:true,message:`Verified target area ${e2e.ids.area_item_id} is included.`};
    });
    if(key==='condition') return e2eWrite(key,'create_condition_record',{inspection_id:e2e.ids.inspection_id,area_item_id:e2e.ids.area_item_id,condition_type:'MAINTENANCE_NOTE',description:e2e.conditionText,claim_ref:'',request_id:rid()},async()=>{
      const found=lookup(await read('list_condition_records',{inspection_id:e2e.ids.inspection_id,offset:0,limit:50}),r=>r.area_item_id===e2e.ids.area_item_id&&r.condition_type==='MAINTENANCE_NOTE'&&r.description===e2e.conditionText);
      if(!found)return {ok:false,reason:'list_condition_records did not return the expected manual note'};
      return {ok:true,ids:{condition_record_id:found.condition_record_id},message:`Verified participant note ${found.condition_record_id}.`};
    });
    if(key==='evidence') return e2eWrite(key,'submit_evidence',{inspection_id:e2e.ids.inspection_id,area_item_id:e2e.ids.area_item_id,condition_record_id:e2e.ids.condition_record_id,evidence_type:'PHOTO',source_ref:PUBLIC_SAMPLE_URL,expected_sha256:PUBLIC_SAMPLE_SHA256,supersedes_evidence_id:'',request_id:rid()},async()=>{
      const found=lookup(await read('list_evidence',{inspection_id:e2e.ids.inspection_id,offset:0,limit:50}),r=>r.area_item_id===e2e.ids.area_item_id&&r.condition_record_id===e2e.ids.condition_record_id&&r.evidence_type==='PHOTO'&&r.source_ref===PUBLIC_SAMPLE_URL&&r.expected_sha256===PUBLIC_SAMPLE_SHA256);
      if(!found)return {ok:false,reason:'list_evidence did not return the expected public sample metadata'};
      return {ok:true,ids:{evidence_id:found.evidence_id},message:`Verified submitted evidence ${found.evidence_id}; no image bytes were placed on-chain.`};
    });
    if(key==='freezeEvidence') return e2eWrite(key,'freeze_evidence',{evidence_id:e2e.ids.evidence_id},async()=>{
      const found=await read('get_evidence',{evidence_id:e2e.ids.evidence_id});
      if(!matchesRecord(found,{evidence_id:e2e.ids.evidence_id,source_ref:PUBLIC_SAMPLE_URL,expected_sha256:PUBLIC_SAMPLE_SHA256,status:'FROZEN'}))return {ok:false,reason:'get_evidence did not return the frozen sample record'};
      return {ok:true,message:`Evidence ${e2e.ids.evidence_id} is frozen.`};
    });
    if(key==='freezeInspection') return e2eWrite(key,'freeze_inspection',{inspection_id:e2e.ids.inspection_id},async()=>{
      const [inspection,completeness]=await Promise.all([read('get_inspection',{inspection_id:e2e.ids.inspection_id}),read('get_inspection_completeness',{inspection_id:e2e.ids.inspection_id})]);
      if(inspection.status!=='FROZEN'||completeness?.complete!==true)return {ok:false,reason:'The frozen inspection or completeness view did not confirm the complete evidence manifest'};
      return {ok:true,message:'The finalized inspection and evidence manifest are frozen and complete.'};
    });
    if(key==='verifyEvidence') return e2eWrite(key,'verify_evidence_provenance',{tenancy_id:e2e.ids.tenancy_id,evidence_id:e2e.ids.evidence_id,request_id:rid()},async()=>{
      const status=await read('get_evidence_verification_status',{evidence_id:e2e.ids.evidence_id});
      if(!verifiedEvidenceStatus(status))return {ok:false,reason:`The validator-side retrieval record is not VERIFIED for the expected digest (${status?.latest?.outcome??'no result'}).`};
      return {ok:true,ids:{verification_id:status.latest.verification_id},message:`Validators verified retrieved SHA-256 ${status.latest.retrieved_sha256}.`};
    });
    if(key==='readback') {
      stepPrerequisite(key);saveStep(key,'IN_PROGRESS',{message:'Reading finalized records from StudioNet.'});await loadHome();
      const result=await readbackRecords();
      if(!result.ok){saveStep(key,'UNRESOLVED',{message:`Finalized state did not match all prepared records: ${result.checks.map((ok,i)=>`${i+1}:${ok?'ok':'mismatch'}`).join(', ')}. No write was retried.`});await loadHome();return;}
      saveStep(key,'PASS',{message:'All property, unit, tenancy, inspection, room, area, note, evidence, and validator provenance records matched finalized state.'});await loadHome();return;
    }
  } catch(error) { saveStep(key,key==='readback'?'UNRESOLVED':'FAILED',{message:errorText(error)});await loadHome(); }
}

async function loadHome() {
  renderFrame(`${e2ePanel()}<div class="studio-toolbar"><label>Public owner address<input id="property-owner" class="field-input" placeholder="0x…" value="${esc(account ?? '')}"></label>${button('Load properties','properties')}</div><div id="studio-result">${panel('Your contract properties','<p>Enter the creator address and load the actual on-chain property list. No local demo data is shown here.</p>')}</div>`);
  root.querySelector('[data-e2e-tenant]')?.addEventListener('input',(event)=>{e2e.tenantAddress=event.target.value.trim();saveE2E();});
  root.querySelectorAll('[data-action^="e2e-"]').forEach((button)=>button.addEventListener('click',()=>{
    const action=button.dataset.action.slice(4);
    if(action==='recheck') recheckSavedProgress(); else runE2EStep(action);
  }));
  root.querySelector('[data-action="properties"]').onclick = () => loadProperties(root.querySelector('#property-owner').value);
  root.querySelector('#property-owner').addEventListener('keydown', (e) => { if (e.key === 'Enter') loadProperties(e.currentTarget.value); });
}
async function loadProperties(owner) {
  if (!/^0x[\da-f]{40}$/i.test(owner.trim())) return alert('Enter a valid public EVM address.', true);
  const slot = root.querySelector('#studio-result');
  slot.innerHTML = '<p>Reading finalized StudioNet state…</p>';
  try {
    const result = await read('list_properties', { creator: owner.trim(), offset: 0, limit: 50 });
    const items = paged(result);
    slot.innerHTML = panel(`Properties for ${owner.trim()}`, itemRows(items, 'property', 'Property'), button('Create property','new-property','data-owner="'+esc(owner.trim())+'"'));
    slot.querySelector('[data-action="new-property"]').onclick = () => showWrite('create_property', { property_label: '', request_id: rid() }, 'Create a property and grant the connected wallet manager authority.');
    slot.querySelectorAll('[data-action="property"]').forEach((b) => b.onclick = () => loadProperty(b.dataset.id));
  } catch (error) { slot.innerHTML = panel('Property query failed', `<p class="error-text">${esc(errorText(error))}</p>`); }
}
async function loadProperty(id) {
  try {
    const [property, units, tenancies, history] = await Promise.all([
      read('get_property', { property_id: id }), read('list_units', { property_id: id, offset: 0, limit: 50 }),
      read('list_tenancies', { property_id: id, offset: 0, limit: 50 }), read('list_property_history', { property_id: id, offset: 0, limit: 50 }),
    ]);
    renderFrame(`<button class="back-link" data-action="home">← Properties</button><h1>Property record</h1>${panel('Property', objectRows(property), button('Register unit','new-unit','data-parent="'+esc(id)+'"'))}${panel('Units',itemRows(paged(units),'unit','Unit'),button('Register unit','new-unit','data-parent="'+esc(id)+'"'))}${panel('Tenancies',itemRows(paged(tenancies),'tenancy','Tenancy'),button('Create tenancy','new-tenancy','data-parent="'+esc(id)+'"'))}${panel('History',`<pre>${esc(JSON.stringify(paged(history),null,2))}</pre>`)}`);
    root.querySelector('[data-action="home"]').onclick = loadHome;
    root.querySelectorAll('[data-action="new-unit"]').forEach((b) => b.onclick = () => showWrite('create_unit', { property_id: id, unit_label: '', request_id: rid() }));
    root.querySelector('[data-action="new-tenancy"]').onclick = async () => {
      const units = paged(await read('list_units',{ property_id:id, offset:0, limit:50 }));
      if (!units.length) return alert('Create a unit before creating a tenancy.', true);
      showWrite('create_tenancy',{ property_id:id, unit_id:'', tenant_address:'', start_metadata:'{}', request_id:rid() },`Tenancy creation stores a draft. Enter one of these existing unit IDs: ${units.map((u)=>u.unit_id).join(', ')}. Only the designated tenant can activate it.`);
    };
    root.querySelectorAll('[data-action="unit"]').forEach((b) => b.onclick = () => loadUnit(b.dataset.id));
    root.querySelectorAll('[data-action="tenancy"]').forEach((b) => b.onclick = () => loadTenancy(b.dataset.id));
  } catch (error) { renderFrame(panel('Property could not be loaded',`<p class="error-text">${esc(errorText(error))}</p>`)); }
}
async function loadUnit(id) {
  try {
    const [unit, rooms] = await Promise.all([read('get_unit',{unit_id:id}),read('list_rooms',{unit_id:id,offset:0,limit:50})]);
    renderFrame(`<button class="back-link" data-action="back">← Property</button><h1>Unit details</h1>${panel('Unit',objectRows(unit),button('Add room','new-room','data-parent="'+esc(id)+'"'))}${panel('Rooms',itemRows(paged(rooms),'room','Room'),button('Add room','new-room','data-parent="'+esc(id)+'"'))}`);
    root.querySelector('[data-action="back"]').onclick=loadHome;
    root.querySelectorAll('[data-action="new-room"]').forEach((b)=>b.onclick=()=>showWrite('create_room',{unit_id:id,room_label:'',request_id:rid()}));
    root.querySelectorAll('[data-action="room"]').forEach((b)=>b.onclick=()=>loadRoom(b.dataset.id));
  } catch(error) { renderFrame(panel('Unit could not be loaded',`<p class="error-text">${esc(errorText(error))}</p>`)); }
}
async function loadRoom(id) {
  try {
    const [room, areas] = await Promise.all([read('get_room',{room_id:id}),read('list_area_items',{room_id:id,offset:0,limit:50})]);
    renderFrame(`<button class="back-link" data-action="back">← Unit</button><h1>Room and areas</h1>${panel('Room',objectRows(room),button('Register inspection area','new-area','data-parent="'+esc(id)+'"'))}${panel('Area items',itemRows(paged(areas),'area','Area item'),button('Register area','new-area','data-parent="'+esc(id)+'"'))}`);
    root.querySelector('[data-action="back"]').onclick=loadHome;
    root.querySelectorAll('[data-action="new-area"]').forEach((b)=>b.onclick=()=>showWrite('create_area_item',{room_id:id,subject_type:'SURFACE',label:'',description_ref:'',request_id:rid()}));
    root.querySelectorAll('[data-action="area"]').forEach((b)=>b.onclick=()=>loadArea(b.dataset.id));
  } catch(error) { renderFrame(panel('Room could not be loaded',`<p class="error-text">${esc(errorText(error))}</p>`)); }
}
async function loadArea(id) {
  try {
    const area = await read('get_area_item',{area_item_id:id});
    renderFrame(`<button class="back-link" data-action="back">← Room</button><h1>Inspection area item</h1>${panel('Area item',objectRows(area))}<p>Area metadata is available. Inspection inclusion requires a real inspection ID; no data has been fabricated.</p>`);
    root.querySelector('[data-action="back"]').onclick=loadHome;
  } catch(error) { renderFrame(panel('Area item could not be loaded',`<p class="error-text">${esc(errorText(error))}</p>`)); }
}
async function loadTenancy(id) {
  try {
    const [tenancy, inspections] = await Promise.all([read('get_tenancy',{tenancy_id:id}),read('list_inspections',{tenancy_id:id,offset:0,limit:50})]);
    const state = tenancy?.status ?? tenancy?.state;
    const type = state === 'MOVE_OUT_PENDING' ? 'MOVE_OUT' : state === 'ACTIVE' ? 'PERIODIC' : 'MOVE_IN';
    const canCreate=['DRAFT','ACTIVE','MOVE_OUT_PENDING'].includes(state);
    const tenant=String(tenancy?.tenant ?? '').toLowerCase();
    const canActivate=state==='DRAFT' && account && tenant===account.toLowerCase() && correctChain;
    const tenActions=`${canActivate?button('Activate tenancy (tenant)','activate-tenancy','data-tenancy="'+esc(id)+'"'):''}${canCreate?button('Create inspection','new-inspection','data-tenancy="'+esc(id)+'" data-type="'+type+'"'):''}${state==='ACTIVE'?button('Request move-out','request-move-out','data-tenancy="'+esc(id)+'"'):''}`;
    renderFrame(`<button class="back-link" data-action="back">← Property</button><h1>Tenancy and inspections</h1>${panel('Tenancy',objectRows(tenancy),tenActions)}${panel('Inspections',itemRows(paged(inspections),'inspection','Inspection'))}`);
    root.querySelector('[data-action="back"]').onclick=loadHome;
    root.querySelector('[data-action="new-inspection"]')?.addEventListener('click',(e)=>showWrite('create_inspection',{tenancy_id:id,inspection_type:e.currentTarget.dataset.type,request_id:rid()}));
    root.querySelector('[data-action="request-move-out"]')?.addEventListener('click',()=>showWrite('request_move_out',{tenancy_id:id}));
    root.querySelector('[data-action="activate-tenancy"]')?.addEventListener('click',()=>showWrite('activate_tenancy',{tenancy_id:id},'Only the connected designated tenant can activate a draft tenancy.'));
    root.querySelectorAll('[data-action="inspection"]').forEach((b)=>b.onclick=()=>loadInspection(b.dataset.id));
  } catch(error) { renderFrame(panel('Tenancy could not be loaded',`<p class="error-text">${esc(errorText(error))}</p>`)); }
}
async function loadInspection(id) {
  try {
    const [inspection, areas, conditions, evidence, completeness] = await Promise.all([
      read('get_inspection',{inspection_id:id}),read('list_inspection_area_items',{inspection_id:id,offset:0,limit:50}),
      read('list_condition_records',{inspection_id:id,offset:0,limit:50}),read('list_evidence',{inspection_id:id,offset:0,limit:50}),
      read('get_inspection_completeness',{inspection_id:id}),
    ]);
    const areaOptions=paged(areas).map((a)=>`<option value="${esc(a.area_item_id)}">${esc(a.label ?? a.area_item_id)} — ${esc(a.area_item_id)}</option>`).join('');
    renderFrame(`<button class="back-link" data-action="back">← Tenancy</button><h1>Inspection details</h1>${panel('Inspection',objectRows(inspection))}${panel('Completeness',objectRows(completeness))}${panel('Included areas',itemRows(paged(areas),'area','Area item'),button('Include existing area','include-area'))}${panel('Manual condition records',`<pre>${esc(JSON.stringify(paged(conditions),null,2))}</pre>`,button('Record participant note','condition'))}${panel('Evidence metadata',`<pre>${esc(JSON.stringify(paged(evidence),null,2))}</pre>`,button('Register evidence metadata','evidence'))}<p class="studio-caution">These are stored participant records and evidence metadata. They are not AI-verified damage, liability, or deposit conclusions. Images must already be hosted at a permitted immutable public source; MoveOut does not upload them.</p>`);
    root.querySelector('[data-action="back"]').onclick=loadHome;
    root.querySelector('[data-action="include-area"]').onclick=()=>showWrite('include_area_in_inspection',{inspection_id:id,area_item_id:'',request_id:rid()},'Use an area item belonging to this inspection’s unit.');
    root.querySelector('[data-action="condition"]').onclick=()=>showWrite('create_condition_record',{inspection_id:id,area_item_id:'',condition_type:'MAINTENANCE_NOTE',description:'',claim_ref:'',request_id:rid()},'This records a participant assertion only; it does not verify a condition or establish responsibility.');
    root.querySelector('[data-action="evidence"]').onclick=()=>showWrite('submit_evidence',{inspection_id:id,area_item_id:'',condition_record_id:'',evidence_type:'PHOTO',source_ref:'',expected_sha256:'',supersedes_evidence_id:'',request_id:rid()},'Metadata only. Use an immutable commit-pinned raw.githubusercontent.com asset URL and its SHA-256. Do not provide private photographs.');
  } catch(error) { renderFrame(panel('Inspection could not be loaded',`<p class="error-text">${esc(errorText(error))}</p>`)); }
}
function formFor(name, initial) {
  const ps = fields(name);
  return ps.map((p) => {
    const key = p.name ?? p.identifier;
    const val = initial[key] ?? '';
    const type = ['offset','limit'].includes(key) ? 'number' : 'text';
    const locked = key === 'request_id' || (key in initial && initial[key] !== '' && !['property_label','unit_label','room_label','label','description_ref','claim_ref','description','source_ref','expected_sha256','tenant_address','start_metadata','area_item_id','condition_type','evidence_type','condition_record_id','supersedes_evidence_id','subject_type'].includes(key));
    return `<label class="write-field">${esc(key.replaceAll('_',' '))}<input name="${esc(key)}" type="${type}" value="${esc(val)}" ${locked?'readonly':''} required></label>`;
  }).join('');
}
function showWrite(name, initial, note = '') {
  if (!account || !correctChain) return alert('Connect a wallet on StudioNet before preparing a write.', true);
  if (!WRITES.has(name)) return alert('This contract method is not available to the UI.', true);
  const dialog = document.createElement('dialog');
  dialog.className='dialog studio-confirm';
  dialog.innerHTML=`<form method="dialog"><div class="dialog-top"><div><p class="eyebrow">REVIEW BEFORE SIGNING</p><h2>${esc(name)}</h2></div><button class="icon-button" value="cancel" aria-label="Close">×</button></div><p><b>Network:</b> StudioNet (61999)<br><b>Contract:</b> ${CONTRACT}<br><b>From:</b> ${esc(account)}</p>${note?`<p class="privacy-hint">${esc(note)}</p>`:''}<div class="write-fields">${formFor(name,initial)}</div><p class="privacy-hint">No fixed maximum-fee cap is available in this UI. SDK estimates and the wallet's transaction screen are authoritative. Review the wallet request before signing.</p><div class="dialog-actions"><button class="button button-quiet" value="cancel">Cancel</button><button class="button button-dark" value="confirm">Review wallet transaction</button></div></form>`;
  document.body.append(dialog);
  dialog.addEventListener('close', async () => {
    await submitOnlyWhenConfirmed(dialog.returnValue, async () => {
      const values = Object.fromEntries(new FormData(dialog.querySelector('form')).entries());
      for (const [key,value] of Object.entries(values)) if (['offset','limit'].includes(key)) values[key]=Number(value);
      await submitWrite(name, values);
    });
    dialog.remove();
  }, { once:true });
  dialog.showModal();
}
async function submitWrite(name, values) {
  if (busy) return alert('A transaction is already in progress.', true);
  if (!WRITES.has(name) || !correctChain) return alert('Write blocked: unsupported method or wrong wallet network.', true);
  busy=true;
  let hash;
  try {
    const args=callArgs(name,values);
    hash=await writer.writeContract({address:CONTRACT,functionName:name,args,value:0n});
    alert(`Transaction submitted: ${hash}. Waiting for finalized status; do not resubmit if this takes time.`);
    const receipt=await writer.waitForTransactionReceipt({hash,status:TransactionStatus.FINALIZED,retries:60,interval:5000});
    alert(`Transaction ${hash}: ${receipt?.statusName ?? receipt?.status ?? 'receipt returned'}${receipt?.txExecutionResultName?` / ${receipt.txExecutionResultName}`:''}. Refresh the relevant contract view to read finalized data.`);
  } catch(error) { alert(hash ? `Transaction ${hash} was submitted, but its final status could not be confirmed: ${errorText(error)}. Do not submit it again until you check the transaction.` : errorText(error),true); }
  finally { busy=false; }
}
async function connect() {
  try {
    const state=await connectWallet(window.ethereum);
    account=state.address; correctChain=state.correctChain;
    if(correctChain) writer=createWalletClient(account);
    saveStep('connect','PASS',{message:`Explicitly connected ${account}; no keys were requested.`});
    await loadHome();
    if(!correctChain) alert(`Wallet connected at ${account}, but chain ${state.chainId} is not StudioNet 61999. Writes are disabled.`,true);
  } catch(error) { alert(errorText(error),true); }
}
function renderNotReady(message) {
  renderFrame(`<div class="studio-warning"><h2>StudioNet connection unavailable</h2><p>${esc(message)}</p><button class="button button-outline" data-action="retry">Retry</button></div>`);
  root.querySelector('[data-action="retry"]').onclick=enterStudio;
}
async function enterStudio() {
  demoRoot.classList.add('hidden'); root.classList.remove('hidden'); modeDemo.classList.remove('active'); modeStudio.classList.add('active');
  document.querySelector('.chain-chip')?.classList.add('visible');
  document.querySelector('.side-link.active')?.classList.remove('active');
  document.querySelector('#sidebar-studio')?.classList.add('active');
  document.querySelectorAll('[data-mode-studio]').forEach((el)=>el.classList.add('active'));
  topNew.classList.add('hidden'); document.querySelector('#top-connect')?.classList.add('hidden'); footerMode.textContent='StudioNet mode · Contract state only · Demo browser records are separate';
  try {
    reader=createClient({chain:studionet,endpoint:RPC});
    schema=await reader.getContractSchema(CONTRACT);
    const names=new Set(Object.keys(schema.methods));
    for(const n of ['list_properties','get_property','get_unit','get_tenancy','get_inspection','get_room','get_area_item','get_condition_record','get_evidence','get_evidence_verification_status','get_inspection_completeness','list_inspection_area_items','list_condition_records','list_evidence']) if(!names.has(n)) throw new Error(`Deployed schema is missing required read method ${n}.`);
    await loadHome();
    await recheckSavedProgress({automatic:true});
  } catch(error) { renderNotReady(errorText(error)); }
}
function enterDemo() { root.classList.add('hidden'); demoRoot.classList.remove('hidden'); modeStudio.classList.remove('active'); modeDemo.classList.add('active'); topNew.classList.remove('hidden'); document.querySelector('#top-connect')?.classList.remove('hidden'); footerMode.textContent='Demo Mode · Local browser data · No blockchain or AI activity'; document.querySelector('.chain-chip')?.classList.remove('visible'); document.querySelectorAll('.side-link.active,.mobile-navigation .active').forEach((el)=>el.classList.remove('active')); document.querySelectorAll('[data-local-nav="overview"]').forEach((el)=>el.classList.add('active')); document.querySelectorAll('[data-mode-studio]').forEach((el)=>el.classList.remove('active')); }
modeDemo.addEventListener('click',enterDemo);
modeStudio.addEventListener('click',enterStudio);
topConnect.addEventListener('click',async()=>{await enterStudio();if(!root.classList.contains('hidden'))await connect();});
root.addEventListener('click',async(e)=>{
  const btn=e.target.closest('[data-action]'); if(!btn)return;
  if(btn.dataset.action==='connect') await connect();
  else if(btn.dataset.action==='disconnect'){account=null;writer=null;correctChain=false;await loadHome();}
  else if(btn.dataset.action.startsWith('e2e-')) await runE2EStep(btn.dataset.action.slice(4));
  else if(btn.dataset.action==='switch-chain'){
    try { await switchToStudioNet(window.ethereum); correctChain=true; writer=createWalletClient(account); await loadHome(); }
    catch(error) { alert(errorText(error),true); }
  }
});
if(window.ethereum?.on){
  window.ethereum.on('accountsChanged',(accounts)=>{account=accounts?.[0]??null;writer=null;correctChain=false;if(account){window.ethereum.request({method:'eth_chainId'}).then((chain)=>{correctChain=normalizeChainId(chain)===STUDIONET_CHAIN_ID;if(correctChain)writer=createWalletClient(account);if(!root.classList.contains('hidden'))loadHome();}).catch(()=>{});}else if(!root.classList.contains('hidden'))loadHome();});
  window.ethereum.on('chainChanged',(chain)=>{correctChain=normalizeChainId(chain)===STUDIONET_CHAIN_ID;if(correctChain&&account)writer=createWalletClient(account);else writer=null;if(!root.classList.contains('hidden'))loadHome();});
}
// A URL opt-in supports read-only demos and owner walkthroughs without attempting wallet access.
if(new URLSearchParams(window.location.search).get('mode')==='studionet') enterStudio();
