import test from 'node:test';
import assert from 'node:assert/strict';
import { createDemoPhotoRecord, DEMO_PHOTO_MIME_TYPES, MAX_DEMO_PHOTO_BYTES, validateDemoPhoto } from '../../demo-photo-policy.js';

test('Demo Mode accepts only the image types exposed by its file picker', () => {
  for (const type of DEMO_PHOTO_MIME_TYPES) {
    assert.equal(validateDemoPhoto({ type, size: 1 }), null, type);
  }
  for (const type of ['', 'text/html', 'image/svg+xml', 'application/octet-stream']) {
    assert.equal(validateDemoPhoto({ type, size: 1 }), 'UNSUPPORTED_TYPE', type);
  }
});

test('Demo Mode rejects empty and over-limit files before IndexedDB writes', () => {
  assert.equal(validateDemoPhoto({ type: 'image/jpeg', size: 0 }), 'INVALID_SIZE');
  assert.equal(validateDemoPhoto({ type: 'image/jpeg', size: Number.NaN }), 'INVALID_SIZE');
  assert.equal(validateDemoPhoto({ type: 'image/jpeg', size: MAX_DEMO_PHOTO_BYTES }), null);
  assert.equal(validateDemoPhoto({ type: 'image/png', size: MAX_DEMO_PHOTO_BYTES + 1 }), 'TOO_LARGE');
});

test('Demo photo record retains the original Blob and display metadata for IndexedDB', () => {
  const file=Object.assign(new Blob(['public sample image bytes'],{type:'image/jpeg'}),{name:'sample.jpg'});
  const record=createDemoPhotoRecord(file,{id:'photo-1',createdAt:123});
  assert.deepEqual(record,{id:'photo-1',name:'sample.jpg',type:'image/jpeg',size:file.size,blob:file,createdAt:123});
  assert.equal(record.blob,file);
});
