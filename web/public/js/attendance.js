// Attendance log: one entry per person per day, exportable as CSV.

export const HEADER = ["Name", "Date", "Time"];

const pad = (n) => String(n).padStart(2, "0");

export const formatDate = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
export const formatTime = (d) => `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;

const keyOf = (name, date) => `${name}\u0000${date}`;

/** Quote a CSV field, and defuse spreadsheet formulas (=, +, -, @) in names. */
export function csvField(value) {
  let text = String(value);
  if (/^[=+\-@\t\r]/.test(text)) text = `'${text}`;
  if (/[",\n\r]/.test(text)) text = `"${text.replace(/"/g, '""')}"`;
  return text;
}

export class AttendanceLog {
  /** @param {{name: string, date: string, time: string}[]} records */
  constructor(records = []) {
    this.records = records.map((r) => ({ name: r.name, date: r.date, time: r.time }));
    this.seen = new Set(this.records.map((r) => keyOf(r.name, r.date)));
  }

  /** Log `name` as present. Returns the new record, or null if already logged that day. */
  mark(name, when = new Date()) {
    const date = formatDate(when);
    if (this.seen.has(keyOf(name, date))) return null;
    const record = { name, date, time: formatTime(when) };
    this.records.push(record);
    this.seen.add(keyOf(name, date));
    return record;
  }

  on(when = new Date()) {
    const date = formatDate(when);
    return this.records.filter((r) => r.date === date);
  }

  clear() {
    this.records = [];
    this.seen.clear();
  }

  toCSV() {
    const rows = [HEADER, ...this.records.map((r) => [r.name, r.date, r.time])];
    return rows.map((row) => row.map(csvField).join(",")).join("\r\n") + "\r\n";
  }
}
