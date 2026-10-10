export const MAX_DEMO_PHOTO_BYTES = 15 * 1024 * 1024;
export const DEMO_PHOTO_MIME_TYPES = new Set([
  'image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif',
]);

export function validateDemoPhoto(file) {
  if (!file || !DEMO_PHOTO_MIME_TYPES.has(String(file.type ?? '').toLowerCase())) {
    return 'UNSUPPORTED_TYPE';
  }
  if (!Number.isFinite(file.size) || file.size <= 0) return 'INVALID_SIZE';
  if (file.size > MAX_DEMO_PHOTO_BYTES) return 'TOO_LARGE';
  return null;
}

export function createDemoPhotoRecord(file, { id = crypto.randomUUID(), createdAt = Date.now() } = {}) {
  return {
    id,
    name: file.name,
    type: file.type,
    size: file.size,
    blob: file,
    createdAt,
  };
}
