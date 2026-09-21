// Browser-only persistence. Nothing here leaves the device.

const PEOPLE_KEY = "fras.people.v1";
const ATTENDANCE_KEY = "fras.attendance.v1";

function read(key) {
  try {
    const parsed = JSON.parse(localStorage.getItem(key) ?? "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function write(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false; // storage full or unavailable (e.g. private browsing)
  }
}

const isDescriptor = (d) => Array.isArray(d) && d.length === 128 && d.every(Number.isFinite);
const isThumb = (t) => typeof t === "string" && t.startsWith("data:image/jpeg;base64,");
const isText = (s) => typeof s === "string" && s.length > 0;

/** Drop anything that doesn't look like data we wrote, so bad storage can't break the page. */
export function loadPeople() {
  return read(PEOPLE_KEY)
    .filter((p) => p && isText(p.name) && Array.isArray(p.samples))
    .map((p) => ({
      name: p.name,
      samples: p.samples
        .filter((s) => s && isDescriptor(s.descriptor))
        .map((s) => ({ descriptor: s.descriptor, thumb: isThumb(s.thumb) ? s.thumb : "" })),
    }))
    .filter((p) => p.samples.length > 0);
}

export function loadAttendance() {
  return read(ATTENDANCE_KEY).filter(
    (r) => r && isText(r.name) && isText(r.date) && isText(r.time),
  );
}

export const savePeople = (people) => write(PEOPLE_KEY, people);
export const saveAttendance = (records) => write(ATTENDANCE_KEY, records);

export function clearAll() {
  try {
    localStorage.removeItem(PEOPLE_KEY);
    localStorage.removeItem(ATTENDANCE_KEY);
  } catch {
    // nothing to clear
  }
}
