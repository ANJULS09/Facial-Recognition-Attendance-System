// Thin wrapper around face-api (exposed as the global `faceapi` by vendor/face-api.js).
// Uses the tiny face detector plus the 68-point landmark and 128-d recognition nets.

const MODEL_URL = new URL("../models", import.meta.url).href;

const liveOptions = () => new faceapi.TinyFaceDetectorOptions({ inputSize: 416, scoreThreshold: 0.5 });
const stillOptions = () => new faceapi.TinyFaceDetectorOptions({ inputSize: 608, scoreThreshold: 0.4 });

export async function loadModels() {
  await faceapi.tf.ready();
  await Promise.all([
    faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
    faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
    faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
  ]);
}

async function detect(input, options) {
  const results = await faceapi
    .detectAllFaces(input, options)
    .withFaceLandmarks()
    .withFaceDescriptors();
  return results.map((r) => {
    const { x, y, width, height } = r.detection.box;
    return { box: { x, y, width, height }, descriptor: Array.from(r.descriptor) };
  });
}

/** Detect every face in the current video frame. */
export const detectLive = (video) => detect(video, liveOptions());

/**
 * Find the most prominent face in a still image or canvas.
 * @returns {Promise<{face: {box, descriptor: number[]}, count: number} | null>}
 */
export async function describeStill(input) {
  const found = await detect(input, stillOptions());
  if (found.length === 0) return null;
  const area = (f) => f.box.width * f.box.height;
  const face = found.reduce((a, b) => (area(b) > area(a) ? b : a));
  // Rounded so stored descriptors stay small; 1e-6 is far below matching precision.
  face.descriptor = face.descriptor.map((v) => Math.round(v * 1e6) / 1e6);
  return { face, count: found.length };
}

export const loadImage = (file) => faceapi.bufferToImage(file);

/** Square JPEG data-URL crop around a face box, for the enrolled-people list. */
export function cropThumbnail(source, box, size = 96) {
  const width = source.naturalWidth || source.videoWidth || source.width;
  const height = source.naturalHeight || source.videoHeight || source.height;
  const side = Math.min(Math.max(box.width, box.height) * 1.5, width, height);
  const cx = box.x + box.width / 2;
  const cy = box.y + box.height / 2;
  const sx = Math.min(Math.max(cx - side / 2, 0), width - side);
  const sy = Math.min(Math.max(cy - side / 2, 0), height - side);

  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = size;
  canvas.getContext("2d").drawImage(source, sx, sy, side, side, 0, 0, size, size);
  return canvas.toDataURL("image/jpeg", 0.7);
}
