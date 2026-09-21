// Nearest-face matching. Mirrors best_match() in the Python package:
// Euclidean distance over 128-d descriptors, match if within tolerance.

export const DEFAULT_TOLERANCE = 0.6;

export function euclidean(a, b) {
  let sum = 0;
  for (let i = 0; i < a.length; i++) {
    const d = a[i] - b[i];
    sum += d * d;
  }
  return Math.sqrt(sum);
}

/**
 * @param {{name: string, descriptor: ArrayLike<number>}[]} samples enrolled faces
 * @param {ArrayLike<number>} descriptor face to identify
 * @returns {{name: string|null, distance: number|null}} name is null when nobody is
 *   within tolerance; distance is null only when there are no samples.
 */
export function bestMatch(samples, descriptor, tolerance = DEFAULT_TOLERANCE) {
  if (samples.length === 0) return { name: null, distance: null };

  let bestIndex = 0;
  let bestDistance = Infinity;
  for (let i = 0; i < samples.length; i++) {
    const distance = euclidean(samples[i].descriptor, descriptor);
    if (distance < bestDistance) {
      bestDistance = distance;
      bestIndex = i;
    }
  }
  return {
    name: bestDistance <= tolerance ? samples[bestIndex].name : null,
    distance: bestDistance,
  };
}

/** Uppercase and collapse whitespace so "jane  doe" and "Jane Doe" are one person. */
export function normalizeName(name) {
  return name.trim().replace(/\s+/g, " ").toUpperCase();
}
