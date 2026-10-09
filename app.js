(() => {
  'use strict';

  const DB_NAME = 'moveout-demo-v1';
  const STORE = 'inspections';
  const app = document;
  const $ = (id) => app.getElementById(id);
  const homeView = $('home-view');
  const inspectionView = $('inspection-view');
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
    emptyState.classList.toggle('hidden', records.length > 0);
    list.innerHTML = records.map((record) => {
      const property = record.propertyName || 'Property inspection';
      const unit = record.unitName ? ` · ${record.unitName}` : '';
      const areas = record.areas.length;
      const photos = record.areas.reduce((n, area) => n + area.photos.length, 0);
      return `<article class="inspection-card"><div><h3>${escapeText(property)}</h3><p>${escapeText(record.dateLabel)}${escapeText(unit)} · ${areas} ${areas === 1 ? 'area' : 'areas'} · ${photos} ${photos === 1 ? 'photo' : 'photos'}</p></div><div class="card-side"><span class="status-badge ${record.status === 'COMPLETE' ? 'complete' : ''}">${record.status === 'COMPLETE' ? 'REVIEW COMPLETE' : 'IN PROGRESS'}</span><button class="open-card" type="button" data-open="${escapeText(record.id)}" aria-label="Open ${escapeText(property)}">→</button></div></article>`;
    }).join('');
  }

  function switchView(view) {
    homeView.classList.toggle('hidden', view !== 'home');
    inspectionView.classList.toggle('hidden', view !== 'inspection');
    window.scrollTo({ top: 0, behavior: 'smooth' });
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
    $('area-list').innerHTML = record.areas.map((entry) => `<button class="area-item ${entry.id === activeAreaId ? 'active' : ''}" data-area="${escapeText(entry.id)}" type="button"><span class="area-dot"></span><span>${escapeText(entry.name)}</span><span class="area-count">${entry.conditions.length + entry.photos.length || ''}</span></button>`).join('');
    $('area-detail').innerHTML = area ? areaMarkup(area) : `<div class="area-placeholder"><div class="empty-icon">＋</div><h3>Add an area to begin</h3><p>Start with a room, hallway, or outdoor area.</p><button class="button button-outline" id="first-area" type="button">Add first area</button></div>`;
    if (area) renderPhotoPreviews(area);
  }

  function areaMarkup(area) {
    const conditions = area.conditions.map((condition) => `<article class="condition-item"><div class="condition-meta"><strong>${escapeText(condition.category)}</strong><span>${dateText(condition.createdAt, true)} <button class="remove-button" data-remove-condition="${escapeText(condition.id)}" type="button">Remove</button></span></div><p>${escapeText(condition.note)}</p></article>`).join('');
    const photos = area.photos.length ? `<div class="photo-list">${area.photos.map((photo) => `<article class="photo-card"><img data-photo="${escapeText(photo.id)}" alt="${escapeText(photo.name)}"><div class="photo-caption"><strong title="${escapeText(photo.name)}">${escapeText(photo.name)}</strong><span>${dateText(photo.createdAt, true)}</span><button class="remove-button" data-remove-photo="${escapeText(photo.id)}" type="button">Remove</button></div></article>`).join('')}</div>` : '<p class="photo-empty">No photographs attached to this area yet.</p>';
    return `<div class="area-top"><div><p class="eyebrow">INSPECTION AREA</p><h2>${escapeText(area.name)}</h2><p>${area.conditions.length} condition notes · ${area.photos.length} photographs</p></div><button class="area-delete" data-delete-area="${escapeText(area.id)}" type="button">Remove area</button></div>
      <section class="content-section"><h3>Record a visible condition</h3><p class="section-help">Write what you can see. These are your notes, not an AI or legal assessment.</p><form id="condition-form" class="condition-form"><select class="field-select" id="condition-category" aria-label="Condition category"><option>General condition</option><option>Walls</option><option>Floor</option><option>Ceiling</option><option>Windows & doors</option><option>Fixtures</option><option>Other</option></select><input class="field-input" id="condition-note" maxlength="500" placeholder="Describe the visible condition…" required><button class="button button-dark button-small" type="submit">Add note</button></form><div class="condition-list">${conditions}</div></section>
      <section class="content-section"><h3>Photographic evidence</h3><p class="section-help">Photos remain in this browser profile. Do not add sensitive images to a shared device.</p><div class="photo-drop"><p>Attach JPG, PNG, WebP, or HEIC photographs to this area.</p><label class="button button-outline button-small" for="photo-input">＋ Add photographs</label><input id="photo-input" type="file" accept="image/jpeg,image/png,image/webp,image/heic,image/heif" multiple></div>${photos}</section>`;
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
      await showInspection(record.id);
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
    if (files.some((file) => !file.type.startsWith('image/'))) { notify('Please select image files only.'); input.value = ''; return; }
    if (files.some((file) => file.size > 15 * 1024 * 1024)) { notify('Each photograph must be 15 MB or smaller.'); input.value = ''; return; }
    const record = await getInspection(currentId);
    const area = record.areas.find((entry) => entry.id === activeAreaId);
    if (!area) return;
    for (const file of files) area.photos.push({ id: uid(), name: file.name, type: file.type || 'application/octet-stream', size: file.size, blob: file, createdAt: Date.now() });
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
    $('empty-new').addEventListener('click', openDialog);
    $('close-dialog').addEventListener('click', closeDialog);
    $('cancel-dialog').addEventListener('click', closeDialog);
    form.addEventListener('submit', createInspection);
    $('back-home').addEventListener('click', async () => { currentId = null; switchView('home'); await renderHome(); });
    $('add-area').addEventListener('click', () => setAreaForm(true));
    $('first-area').addEventListener('click', () => setAreaForm(true));
    $('cancel-area').addEventListener('click', () => setAreaForm(false));
    $('area-form').addEventListener('submit', createArea);
    $('complete-inspection').addEventListener('click', toggleComplete);
    list.addEventListener('click', async (event) => {
      const button = event.target.closest('[data-open]');
      if (button) await showInspection(button.dataset.open);
    });
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
    });
    window.addEventListener('hashchange', async () => {
      if (location.hash === '#home') { currentId = null; switchView('home'); await renderHome(); }
    });
  }

  async function init() {
    if (!('indexedDB' in window)) {
      $('app').innerHTML = '<div class="empty-state"><h3>Local browser storage is unavailable</h3><p>Open MoveOut in a current browser with IndexedDB enabled to use this demo.</p></div>';
      return;
    }
    try { await openDb(); wire(); await renderHome(); }
    catch { $('app').innerHTML = '<div class="empty-state"><h3>Could not open local browser storage</h3><p>Check that site data is enabled for this browser, then reload MoveOut.</p></div>'; }
  }

  init();
})();
