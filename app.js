import { createDemoPhotoRecord, validateDemoPhoto } from './demo-photo-policy.js';

(() => {
  'use strict';

  const DB_NAME = 'moveout-demo-v1';
  const STORE = 'inspections';
  const app = document;
  const $ = (id) => app.getElementById(id);
  const modeStudio = $('mode-studio');
  const homeView = $('home-view');
  const inspectionView = $('inspection-view');
  const workspaceView = $('workspace-view');
  const list = $('inspection-list');
  const emptyState = $('empty-state');
  const dialog = $('new-inspection-dialog');
  const form = $('inspection-form');
  const toast = $('toast');
  let db;
  let currentId = null;
  let activeAreaId = null;
  let toastTimer;
  const previewUrls = new Set();

  function openDb() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, 1);
      request.onupgradeneeded = () => request.result.createObjectStore(STORE, { keyPath: 'id' });
      request.onsuccess = () => { db = request.result; resolve(db); };
      request.onerror = () => reject(request.error || new Error('Could not open local browser storage.'));
    });
  }

  function allInspections() {
    return new Promise((resolve, reject) => {
      const request = db.transaction(STORE, 'readonly').objectStore(STORE).getAll();
      request.onsuccess = () => resolve(request.result.sort((a, b) => b.updatedAt - a.updatedAt));
      request.onerror = () => reject(request.error);
    });
  }

  function getInspection(id) {
    return new Promise((resolve, reject) => {
      const request = db.transaction(STORE, 'readonly').objectStore(STORE).get(id);
      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(request.error);
    });
  }

  function saveInspection(record) {
    record.updatedAt = Date.now();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).put(record);
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error || new Error('Could not save this record.'));
      tx.onabort = () => reject(tx.error || new Error('The browser storage transaction was aborted.'));
    });
  }

  function deleteInspection(id) {
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).delete(id);
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error);
    });
  }

  function uid() { return crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`; }
  function dateText(value, includeTime = false) {
    const options = includeTime ? { dateStyle: 'medium', timeStyle: 'short' } : { dateStyle: 'medium' };
    return new Intl.DateTimeFormat(undefined, options).format(new Date(value));
  }
  function escapeText(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
  }
  function notify(message) {
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 2800);
  }
  function releasePreviews() { for (const url of previewUrls) URL.revokeObjectURL(url); previewUrls.clear(); }

  async function renderHome() {
    releasePreviews();
    const records = await allInspections();
    $('inspection-count').textContent = `${records.length} ${records.length === 1 ? 'inspection' : 'inspections'}`;
    const properties = new Set(records.map((record) => record.propertyName?.trim()).filter(Boolean));
    $('stat-properties').textContent = properties.size;
    $('stat-inspections').textContent = records.length;
    $('stat-progress').textContent = records.filter((record) => record.status !== 'COMPLETE').length;
    $('stat-complete').textContent = records.filter((record) => record.status === 'COMPLETE').length;
    emptyState.classList.toggle('hidden', records.length > 0);
    const propertyGroups = groupProperties(records);
    $('property-empty').classList.toggle('hidden', propertyGroups.length > 0);
    $('property-list').innerHTML = propertyGroups.slice(0, 3).map(propertyCard).join('');
    for (const group of propertyGroups.slice(0,3)) {
      const photo = group.records.flatMap((record) => record.areas.flatMap((area) => area.photos)).find((entry) => entry.blob instanceof Blob);
      if (photo) { const url = URL.createObjectURL(photo.blob); previewUrls.add(url); const image = $('property-list').querySelector(`[data-property-photo="${CSS.escape(photo.id)}"]`); if (image) image.src = url; }
    }
    list.innerHTML = records.map((record) => {
      const property = record.propertyName || 'Property inspection';
      const unit = record.unitName ? ` · ${record.unitName}` : '';
      const areas = record.areas.length;
      const photos = record.areas.reduce((n, area) => n + area.photos.length, 0);
      return `<article class="inspection-card"><div><h3>${escapeText(property)}</h3><p>${escapeText(record.dateLabel)}${escapeText(unit)} · ${areas} ${areas === 1 ? 'area' : 'areas'} · ${photos} ${photos === 1 ? 'photo' : 'photos'}</p></div><div class="card-side"><span class="status-badge ${record.status === 'COMPLETE' ? 'complete' : ''}">${record.status === 'COMPLETE' ? 'REVIEW COMPLETE' : 'IN PROGRESS'}</span><button class="open-card" type="button" data-open="${escapeText(record.id)}" aria-label="Open ${escapeText(property)}">→</button></div></article>`;
    }).join('');
  }

  function groupProperties(records) {
    const groups = new Map();
    for (const record of records) {
      const name = record.propertyName?.trim();
      if (!name) continue;
      if (!groups.has(name)) groups.set(name, { name, records: [] });
      groups.get(name).records.push(record);
    }
    return [...groups.values()];
  }
  function propertyCard(group) {
    const units = new Set(group.records.map((record) => record.unitName?.trim()).filter(Boolean));
    const photo = group.records.flatMap((record) => record.areas.flatMap((area) => area.photos)).find((entry) => entry.blob instanceof Blob);
    const cover = photo ? `<img data-property-photo="${escapeText(photo.id)}" alt="Photo from ${escapeText(group.name)} inspection">` : `<div class="property-art"><span>⌂</span><small>No property photo</small></div>`;
    return `<button class="property-card" type="button" data-property-name="${escapeText(group.name)}"><span class="property-image">${cover}</span><span class="property-card-body"><strong>${escapeText(group.name)}</strong><small>${units.size} ${units.size===1?'unit':'units'} · ${group.records.length} ${group.records.length===1?'inspection':'inspections'}</small><span class="property-active">Local demo record</span></span></button>`;
  }
  function compactEmpty(title, description, action='Create an inspection') {
    return `<div class="large-empty"><span class="large-empty-mark">⌂</span><h2>${escapeText(title)}</h2><p>${escapeText(description)}</p><button class="button button-dark button-small" data-new-inspection>${escapeText(action)}</button></div>`;
  }
  function workspaceInspectionCard(record) {
    const photos=record.areas.reduce((n,area)=>n+area.photos.length,0), notes=record.areas.reduce((n,area)=>n+area.conditions.length,0);
    return `<button class="workspace-inspection" type="button" data-open="${escapeText(record.id)}"><span class="workspace-inspection-icon">▤</span><span class="workspace-inspection-main"><strong>${escapeText(record.propertyName||'Property inspection')}</strong><small>${escapeText(record.unitName||'Unit not specified')} · ${escapeText(record.dateLabel)} · ${record.areas.length} areas · ${photos} photos · ${notes} notes</small></span><span class="status-badge ${record.status==='COMPLETE'?'complete':''}">${record.status==='COMPLETE'?'REVIEW COMPLETE':'IN PROGRESS'}</span><span class="open-card">›</span></button>`;
  }
  async function renderWorkspace(page, propertyName='') {
    releasePreviews();
    const records = await allInspections();
    const properties = groupProperties(records);
    const title = {properties:'Properties',inspections:'Inspections',evidence:'Evidence',activity:'Activity',settings:'Settings'}[page] || 'Overview';
    let content = '';
    if (page === 'properties') {
      const property = properties.find((entry)=>entry.name===propertyName);
      if (property) {
        const units=new Map();
        for (const record of property.records) { const label=record.unitName?.trim()||'Unit not specified'; if(!units.has(label)) units.set(label,[]); units.get(label).push(record); }
        const propertyPhoto=property.records.flatMap((record)=>record.areas.flatMap((area)=>area.photos)).find((photo)=>photo.blob instanceof Blob);
        const cover=propertyPhoto?`<img data-property-photo="${escapeText(propertyPhoto.id)}" alt="Photograph from ${escapeText(property.name)} inspection">`:`<span>⌂</span><small>No property photograph has been added to an inspection.</small>`;
        content=`<button class="back-link" data-workspace="properties">← All properties</button><section class="property-detail-hero"><div class="property-art property-detail-art">${cover}</div><div><p class="eyebrow">LOCAL DEMO PROPERTY</p><h2>${escapeText(property.name)}</h2><p class="muted">${units.size} ${units.size===1?'unit':'units'} · ${property.records.length} ${property.records.length===1?'inspection':'inspections'}</p><button class="button button-dark button-small" data-add-inspection-for="${escapeText(property.name)}">＋ Add inspection</button></div></section><section class="workspace-section"><div class="section-heading"><h2>Units & inspection history</h2></div><div class="unit-grid">${[...units.entries()].map(([unit,items])=>`<article class="unit-card"><div class="unit-card-top"><span class="unit-icon">▣</span><span class="status-badge ${items[0].status==='COMPLETE'?'complete':''}">${items[0].status==='COMPLETE'?'REVIEW COMPLETE':'IN PROGRESS'}</span></div><h3>${escapeText(unit)}</h3><p>${items.length} ${items.length===1?'inspection':'inspections'}</p>${items.map((record)=>`<button class="history-row" data-open="${escapeText(record.id)}"><span>${escapeText(record.dateLabel)} · ${record.areas.length} areas · ${record.areas.reduce((n,a)=>n+a.photos.length,0)} photos</span><b>Open →</b></button>`).join('')}</article>`).join('')}</div></section>`;
      } else content=properties.length?`<div class="property-grid property-grid-page">${properties.map(propertyCard).join('')}</div>`:compactEmpty('No properties yet','Create an inspection with a property label. Properties are grouped from your own local inspection records.');
    } else if (page === 'inspections') {
      content=records.length?`<div class="workspace-list">${records.map(workspaceInspectionCard).join('')}</div>`:compactEmpty('No inspections yet','Start an inspection to document a property and its rooms.');
    } else if (page === 'evidence') {
      const evidence=records.flatMap((record)=>record.areas.flatMap((area)=>[
        ...area.photos.map((photo)=>({type:'Photograph',title:photo.name,where:`${record.propertyName||'Property inspection'} · ${record.unitName||'Unit not specified'} · ${area.name}`,at:photo.createdAt,record,photo})),
        ...area.conditions.map((note)=>({type:'Condition note',title:note.category,where:`${record.propertyName||'Property inspection'} · ${record.unitName||'Unit not specified'} · ${area.name}`,at:note.createdAt,record,note}))
      ])).sort((a,b)=>b.at-a.at);
      content=evidence.length?`<div class="evidence-grid">${evidence.map((entry)=>`<article class="evidence-card">${entry.photo?`<img data-evidence-photo="${escapeText(entry.photo.id)}" alt="${escapeText(entry.photo.name)}">`:'<span class="evidence-note-icon">✎</span>'}<div><span class="evidence-kind">${entry.type}</span><h3>${escapeText(entry.title)}</h3><p>${escapeText(entry.where)}</p>${entry.note?`<blockquote>${escapeText(entry.note.note)}</blockquote>`:''}<button class="text-button" data-open="${escapeText(entry.record.id)}">Open inspection →</button></div></article>`).join('')}</div>`:compactEmpty('No evidence yet','Photographs and condition notes added in Demo Mode will be collected here.');
    } else if (page === 'settings') {
      content=`<div class="settings-grid"><article class="settings-card"><span class="settings-icon">⌂</span><div><h2>Demo data</h2><p>Inspection labels, notes, and photographs created in Demo Mode are stored in this browser profile. They are not uploaded or synchronized with StudioNet.</p><span class="settings-tag">Local browser storage · IndexedDB</span></div></article><article class="settings-card"><span class="settings-icon">◉</span><div><h2>StudioNet connection</h2><p>Live contract records are a separate workspace on GenLayer StudioNet. A wallet is only requested when you choose to connect.</p><button class="button button-outline button-small" data-mode-studio>Open StudioNet Tests</button></div></article><article class="settings-card"><span class="settings-icon">✓</span><div><h2>Inspection safety</h2><p>Demo notes and images are records you enter yourself. MoveOut Demo Mode does not perform AI assessments or determine responsibility.</p></div></article></div>`;
    } else {
      const entries=records.flatMap((record)=>[
        {at:record.createdAt,title:'Inspection created',detail:`${record.propertyName||'Property inspection'} · ${record.unitName||'Unit not specified'}`,record},
        ...record.areas.flatMap((area)=>[...area.conditions.map((note)=>({at:note.createdAt,title:'Condition note added',detail:`${area.name} · ${note.category}`,record})),...area.photos.map((photo)=>({at:photo.createdAt,title:'Photograph attached',detail:`${area.name} · ${photo.name}`,record}))]),
        ...(record.status==='COMPLETE'?[{at:record.updatedAt,title:'Review marked complete',detail:record.propertyName||'Property inspection',record}]:[])
      ]).sort((a,b)=>b.at-a.at);
      content=entries.length?`<div class="activity-list">${entries.map((entry)=>`<article class="activity-row"><span class="activity-marker"></span><div><strong>${escapeText(entry.title)}</strong><p>${escapeText(entry.detail)}</p><small>${dateText(entry.at,true)}</small></div><button class="text-button" data-open="${escapeText(entry.record.id)}">View →</button></article>`).join('')}</div>`:compactEmpty('No activity yet','Inspection updates made in this browser will appear here.');
    }
    workspaceView.innerHTML=`<section class="workspace-page"><div class="workspace-heading"><div><p class="eyebrow">DEMO MODE · THIS BROWSER</p><h1>${title}</h1><p class="muted">${page==='properties'?'Property and unit details are derived from your local inspection labels.':page==='evidence'?'Private photos remain in this browser and are not uploaded.':page==='activity'?'A local history of inspection changes.':page==='settings'?'Local storage and privacy information for this demo.':'All local demo inspections.'}</p></div>${page==='properties'||page==='inspections'?'<button class="button button-dark button-small" data-new-inspection>＋ New inspection</button>':''}</div>${content}</section>`;
    homeView.classList.add('hidden'); inspectionView.classList.add('hidden'); workspaceView.classList.remove('hidden');
    for (const image of workspaceView.querySelectorAll('[data-property-photo],[data-evidence-photo]')) { const id=image.dataset.propertyPhoto||image.dataset.evidencePhoto; const photo=records.flatMap((r)=>r.areas.flatMap((a)=>a.photos)).find((p)=>p.id===id); if(photo?.blob instanceof Blob){const url=URL.createObjectURL(photo.blob);previewUrls.add(url);image.src=url;} }
  }

  function switchView(view) {
    homeView.classList.toggle('hidden', view !== 'home');
    inspectionView.classList.toggle('hidden', view !== 'inspection');
    workspaceView.classList.add('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  async function renderHashRoute() {
    const path = location.hash.slice(1);
    const [rawRoute, ...rawParts] = (path || (new URLSearchParams(location.search).get('mode') === 'studionet' ? 'studio' : 'home')).split('/');
    const route = decodeURIComponent(rawRoute);
    const parts = rawParts.map(decodeURIComponent);
    if (route === 'studio') {
      if (!modeStudio.classList.contains('active')) modeStudio.click();
      return;
    }
    if (modeStudio.classList.contains('active')) $('mode-demo').click();
    document.querySelectorAll('.side-link.active,.mobile-navigation .active').forEach((item) => item.classList.remove('active'));
    const nav = document.querySelector(`[data-local-nav="${CSS.escape(route === 'home' ? 'overview' : route)}"]`);
    nav?.classList.add('active');
    if (route === 'inspection' && parts.length) {
      await showInspection(parts.join('/'));
    } else if (route === 'properties' && parts.length) {
      await renderWorkspace('properties', parts.join('/'));
    } else if (['properties', 'inspections', 'evidence', 'activity', 'settings'].includes(route)) {
      await renderWorkspace(route);
    } else {
      currentId = null;
      switchView('home');
      await renderHome();
    }
  }

  function navigateHash(route) {
    const next = `#${route}`;
    if (location.hash === next) renderHashRoute();
    else location.hash = route;
  }

  async function showInspection(id) {
    const record = await getInspection(id);
    if (!record) { notify('That inspection could not be found.'); return renderHome(); }
    currentId = id;
    activeAreaId = record.areas[0]?.id || null;
    switchView('inspection');
    await renderInspection();
  }

  async function renderInspection() {
    releasePreviews();
    const record = await getInspection(currentId);
    if (!record) return renderHome();
    const area = record.areas.find((entry) => entry.id === activeAreaId) || null;
    activeAreaId = area?.id || null;
    const conditionCount = record.areas.reduce((count, entry) => count + entry.conditions.length, 0);
    const photoCount = record.areas.reduce((count, entry) => count + entry.photos.length, 0);
    $('inspection-title').textContent = record.propertyName || 'Property inspection';
    $('inspection-subtitle').textContent = `${record.unitName ? `${record.unitName} · ` : ''}Started ${dateText(record.createdAt, true)}`;
    $('status-badge').textContent = record.status === 'COMPLETE' ? 'REVIEW COMPLETE' : 'IN PROGRESS';
    $('status-badge').classList.toggle('complete', record.status === 'COMPLETE');
    $('complete-inspection').textContent = record.status === 'COMPLETE' ? 'Reopen inspection' : 'Mark review complete';
    $('area-total').textContent = record.areas.length;
    $('condition-total').textContent = conditionCount;
    $('photo-total').textContent = photoCount;
    const reviewIndex = record.status === 'COMPLETE' ? 4 : area ? 2 : 1;
    $('inspection-progress').innerHTML = `<div class="flow-step done"><span>✓</span><small>Property & Unit</small></div><i class="flow-line done"></i><div class="flow-step done"><span>✓</span><small>Inspection Details</small></div><i class="flow-line ${reviewIndex>2?'done':''}"></i><div class="flow-step ${reviewIndex===2?'current':reviewIndex>2?'done':''}"><span>${reviewIndex>2?'✓':'3'}</span><small>Rooms & Areas</small></div><i class="flow-line ${reviewIndex>3?'done':''}"></i><div class="flow-step ${reviewIndex===3?'current':reviewIndex>3?'done':''}"><span>${reviewIndex>3?'✓':'4'}</span><small>Review</small></div><i class="flow-line ${reviewIndex>4?'done':''}"></i><div class="flow-step ${reviewIndex===4?'current':''}"><span>${reviewIndex===4?'✓':'5'}</span><small>Complete</small></div>`;
    $('area-list').innerHTML = record.areas.map((entry) => `<button class="area-item ${entry.id === activeAreaId ? 'active' : ''}" data-area="${escapeText(entry.id)}" type="button"><span class="area-dot"></span><span>${escapeText(entry.name)}</span><span class="area-count">${entry.conditions.length + entry.photos.length || ''}</span></button>`).join('');
    $('area-detail').innerHTML = area ? areaMarkup(area) : `<div class="area-placeholder"><div class="empty-icon">＋</div><h3>Add an area to begin</h3><p>Start with a room, hallway, or outdoor area.</p><button class="button button-outline" id="first-area" type="button">Add first area</button></div>`;
    if (area) renderPhotoPreviews(area);
  }

  function areaMarkup(area) {
    const conditions = area.conditions.map((condition) => `<article class="condition-item"><div class="condition-meta"><strong>${escapeText(condition.category)}</strong><span>${dateText(condition.createdAt, true)} <button class="remove-button" data-remove-condition="${escapeText(condition.id)}" type="button">Remove</button></span></div><p>${escapeText(condition.note)}</p></article>`).join('');
    const photos = area.photos.length ? `<div class="photo-list">${area.photos.map((photo) => `<article class="photo-card"><img data-photo="${escapeText(photo.id)}" alt="${escapeText(photo.name)}"><div class="photo-caption"><strong title="${escapeText(photo.name)}">${escapeText(photo.name)}</strong><span>${dateText(photo.createdAt, true)}</span><button class="remove-button" data-remove-photo="${escapeText(photo.id)}" type="button">Remove</button></div></article>`).join('')}</div>` : '<p class="photo-empty">No photographs attached to this area yet.</p>';
    return `<div class="area-top"><div><p class="eyebrow">INSPECTION AREA</p><h2>${escapeText(area.name)}</h2><p>${area.conditions.length} condition notes · ${area.photos.length} photographs</p></div><button class="area-delete" data-delete-area="${escapeText(area.id)}" type="button">Remove area</button></div>
      <section class="content-section"><h3>Record a visible condition</h3><p class="section-help">Write what you can see. These are your notes, not an AI or legal assessment.</p><form id="condition-form" class="condition-form"><select class="field-select" id="condition-category" aria-label="Condition category"><option>General condition</option><option>Walls</option><option>Floor</option><option>Ceiling</option><option>Windows & doors</option><option>Fixtures</option><option>Other</option></select><input class="field-input" id="condition-note" maxlength="500" placeholder="Describe the visible condition…" required><button class="button button-dark button-small" type="submit">Add note</button></form><div class="condition-list">${conditions}</div></section>
      <section class="content-section"><h3>Photographic evidence</h3><p class="section-help">Photos remain in this browser profile. Do not add sensitive images to a shared device.</p><div class="photo-drop"><p>Attach JPG, PNG, WebP, or HEIC photographs to this area.</p><button class="button button-outline button-small" id="photo-select-button" type="button">＋ Add photographs</button><input id="photo-input" type="file" accept="image/jpeg,image/png,image/webp,image/heic,image/heif" multiple hidden></div>${photos}</section>`;
  }

  function renderPhotoPreviews(area) {
    for (const photo of area.photos) {
      if (!(photo.blob instanceof Blob)) continue;
      const url = URL.createObjectURL(photo.blob);
      previewUrls.add(url);
      const image = document.querySelector(`[data-photo="${CSS.escape(photo.id)}"]`);
      if (image) image.src = url;
    }
  }

  function openDialog() { form.reset(); dialog.showModal(); $('property-name').focus(); }
  function closeDialog() { dialog.close(); }

  async function createInspection(event) {
    event.preventDefault();
    const propertyName = $('property-name').value.trim();
    const unitName = $('unit-name').value.trim();
    const now = Date.now();
    const record = { id: uid(), propertyName, unitName, createdAt: now, updatedAt: now, dateLabel: dateText(now), status: 'IN_PROGRESS', areas: [] };
    try {
      await saveInspection(record);
      closeDialog();
      navigateHash(`inspection/${encodeURIComponent(record.id)}`);
      notify('Inspection created and saved in this browser.');
    } catch { notify('Could not save the inspection. Check browser storage and try again.'); }
  }

  function setAreaForm(open) {
    const areaForm = $('area-form');
    areaForm.classList.toggle('hidden', !open);
    if (open) $('area-name').focus();
    else areaForm.reset();
  }

  async function createArea(event) {
    event.preventDefault();
    const name = $('area-name').value.trim();
    if (!name) return;
    const record = await getInspection(currentId);
    if (record.areas.some((area) => area.name.toLocaleLowerCase() === name.toLocaleLowerCase())) {
      notify('An area with that name already exists.'); return;
    }
    const area = { id: uid(), name, createdAt: Date.now(), conditions: [], photos: [] };
    record.areas.push(area);
    try {
      await saveInspection(record);
      activeAreaId = area.id;
      setAreaForm(false);
      await renderInspection();
      notify(`${name} added.`);
    } catch { notify('Could not save this area. Check browser storage and try again.'); }
  }

  async function addCondition(event) {
    event.preventDefault();
    const note = $('condition-note').value.trim();
    if (!note) return;
    const record = await getInspection(currentId);
    const area = record.areas.find((entry) => entry.id === activeAreaId);
    if (!area) return;
    area.conditions.push({ id: uid(), category: $('condition-category').value, note, createdAt: Date.now() });
    try { await saveInspection(record); await renderInspection(); notify('Condition note saved.'); }
    catch { notify('Could not save the note. Check browser storage and try again.'); }
  }

  async function addPhotos(input) {
    const files = Array.from(input.files || []);
    if (!files.length) return;
    if (files.some((file) => validateDemoPhoto(file) === 'UNSUPPORTED_TYPE')) { notify('Please select a JPEG, PNG, WebP, HEIC, or HEIF photograph.'); input.value = ''; return; }
    if (files.some((file) => validateDemoPhoto(file) === 'INVALID_SIZE')) { notify('The selected photograph is empty or has an invalid size.'); input.value = ''; return; }
    if (files.some((file) => validateDemoPhoto(file) === 'TOO_LARGE')) { notify('Each photograph must be 15 MB or smaller.'); input.value = ''; return; }
    const record = await getInspection(currentId);
    const area = record.areas.find((entry) => entry.id === activeAreaId);
    if (!area) return;
    for (const file of files) area.photos.push(createDemoPhotoRecord(file, { id: uid(), createdAt: Date.now() }));
    try { await saveInspection(record); await renderInspection(); notify(`${files.length} ${files.length === 1 ? 'photograph' : 'photographs'} attached.`); }
    catch { notify('The browser could not store these photographs. Try fewer or smaller files.'); }
    input.value = '';
  }

  async function removeCondition(conditionId) {
    if (!window.confirm('Remove this condition note?')) return;
    const record = await getInspection(currentId);
    const area = record.areas.find((entry) => entry.id === activeAreaId);
    area.conditions = area.conditions.filter((condition) => condition.id !== conditionId);
    await saveInspection(record); await renderInspection(); notify('Condition note removed.');
  }

  async function removePhoto(photoId) {
    if (!window.confirm('Remove this photograph from the local inspection?')) return;
    const record = await getInspection(currentId);
    const area = record.areas.find((entry) => entry.id === activeAreaId);
    area.photos = area.photos.filter((photo) => photo.id !== photoId);
    await saveInspection(record); await renderInspection(); notify('Photograph removed.');
  }

  async function removeArea(areaId) {
    const record = await getInspection(currentId);
    const area = record.areas.find((entry) => entry.id === areaId);
    if (!area || !window.confirm(`Remove ${area.name} and its notes and photographs?`)) return;
    record.areas = record.areas.filter((entry) => entry.id !== areaId);
    activeAreaId = record.areas[0]?.id || null;
    await saveInspection(record); await renderInspection(); notify('Area removed.');
  }

  async function toggleComplete() {
    const record = await getInspection(currentId);
    record.status = record.status === 'COMPLETE' ? 'IN_PROGRESS' : 'COMPLETE';
    await saveInspection(record); await renderInspection();
    notify(record.status === 'COMPLETE' ? 'Review marked complete.' : 'Inspection reopened.');
  }

  async function removeInspection(id) {
    const record = await getInspection(id);
    if (!record || !window.confirm(`Delete local demo inspection “${record.propertyName || 'Property inspection'}” and its evidence?`)) return;
    await deleteInspection(id); await renderHome(); notify('Local inspection deleted.');
  }

  function wire() {
    $('start-inspection').addEventListener('click', openDialog);
    $('top-new').addEventListener('click', openDialog);
    $('global-search').addEventListener('input', (event) => {
      const query = event.target.value.trim().toLocaleLowerCase();
      for (const card of document.querySelectorAll('.inspection-card,.property-card,.workspace-inspection,.evidence-card,.activity-row')) card.classList.toggle('search-hidden', query && !card.textContent.toLocaleLowerCase().includes(query));
    });
    $('sidebar-studio').addEventListener('click', (event) => { event.preventDefault(); $('mode-studio').click(); });
    document.querySelectorAll('[data-local-nav]').forEach((link) => link.addEventListener('click', (event) => {
      event.preventDefault();
      const page=link.dataset.localNav;
      navigateHash(page === 'overview' ? 'home' : page);
    }));
    document.addEventListener('click',(event)=>{
      if(event.target.closest('[data-mode-studio]')){navigateHash('studio');return;}
      const card=event.target.closest('[data-property-name]');
      if(card && !card.closest('#property-list')){navigateHash(`properties/${encodeURIComponent(card.dataset.propertyName)}`);return;}
      const open=event.target.closest('[data-open]');
      if(open){navigateHash(`inspection/${encodeURIComponent(open.dataset.open)}`);return;}
      const workspace=event.target.closest('[data-workspace]');
      if(workspace){navigateHash(workspace.dataset.workspace);return;}
      if(event.target.closest('[data-new-inspection]')){openDialog();return;}
      const add=event.target.closest('[data-add-inspection-for]');
      if(add){openDialog();$('property-name').value=add.dataset.addInspectionFor;return;}
    });
    $('empty-new').addEventListener('click', openDialog);
    $('close-dialog').addEventListener('click', closeDialog);
    $('cancel-dialog').addEventListener('click', closeDialog);
    form.addEventListener('submit', createInspection);
    $('back-home').addEventListener('click', () => navigateHash('home'));
    $('add-area').addEventListener('click', () => setAreaForm(true));
    $('first-area').addEventListener('click', () => setAreaForm(true));
    $('cancel-area').addEventListener('click', () => setAreaForm(false));
    $('area-form').addEventListener('submit', createArea);
    $('complete-inspection').addEventListener('click', toggleComplete);
    $('area-list').addEventListener('click', async (event) => {
      const button = event.target.closest('[data-area]');
      if (!button) return;
      activeAreaId = button.dataset.area;
      await renderInspection();
    });
    $('area-detail').addEventListener('submit', async (event) => {
      if (event.target.id === 'condition-form') await addCondition(event);
    });
    $('area-detail').addEventListener('change', async (event) => {
      if (event.target.id === 'photo-input') await addPhotos(event.target);
    });
    $('area-detail').addEventListener('click', async (event) => {
      const condition = event.target.closest('[data-remove-condition]');
      const photo = event.target.closest('[data-remove-photo]');
      const area = event.target.closest('[data-delete-area]');
      if (condition) await removeCondition(condition.dataset.removeCondition);
      else if (photo) await removePhoto(photo.dataset.removePhoto);
      else if (area) await removeArea(area.dataset.deleteArea);
      else if (event.target.id === 'first-area') setAreaForm(true);
      else if (event.target.closest('#photo-select-button')) $('photo-input').click();
    });
    window.addEventListener('hashchange', renderHashRoute);
  }

  async function init() {
    if (!('indexedDB' in window)) {
      $('app').innerHTML = '<div class="empty-state"><h3>Local browser storage is unavailable</h3><p>Open MoveOut in a current browser with IndexedDB enabled to use this demo.</p></div>';
      return;
    }
    try { await openDb(); wire(); await renderHashRoute(); }
    catch { $('app').innerHTML = '<div class="empty-state"><h3>Could not open local browser storage</h3><p>Check that site data is enabled for this browser, then reload MoveOut.</p></div>'; }
  }

  init();
})();
