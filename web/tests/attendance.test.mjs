import assert from "node:assert/strict";
import test from "node:test";

import { AttendanceLog, csvField, formatDate, formatTime } from "../public/js/attendance.js";

const at = (y, mo, d, h = 9, mi = 0, s = 0) => new Date(y, mo - 1, d, h, mi, s);

test("formats local date and time with zero padding", () => {
  assert.equal(formatDate(at(2025, 3, 1)), "2025-03-01");
  assert.equal(formatTime(at(2025, 3, 1, 9, 2, 5)), "09:02:05");
});

test("marks a person once per day", () => {
  const log = new AttendanceLog();
  assert.deepEqual(log.mark("JANE DOE", at(2025, 3, 1, 9)), {
    name: "JANE DOE",
    date: "2025-03-01",
    time: "09:00:00",
  });
  assert.equal(log.mark("JANE DOE", at(2025, 3, 1, 15)), null);
  assert.equal(log.records.length, 1);
});

test("the same person is logged again on a new day", () => {
  const log = new AttendanceLog();
  assert.ok(log.mark("JANE DOE", at(2025, 3, 1)));
  assert.ok(log.mark("JANE DOE", at(2025, 3, 2)));
  assert.equal(log.records.length, 2);
});

test("restoring saved records keeps the once-per-day rule", () => {
  const log = new AttendanceLog([{ name: "A", date: "2025-03-01", time: "09:00:00" }]);
  assert.equal(log.mark("A", at(2025, 3, 1, 12)), null);
});

test("on() returns only that day's records", () => {
  const log = new AttendanceLog();
  log.mark("A", at(2025, 3, 1));
  log.mark("B", at(2025, 3, 1));
  log.mark("A", at(2025, 3, 2));
  assert.deepEqual(log.on(at(2025, 3, 1)).map((r) => r.name), ["A", "B"]);
});

test("clear() resets records and the seen set", () => {
  const log = new AttendanceLog();
  log.mark("A", at(2025, 3, 1));
  log.clear();
  assert.equal(log.records.length, 0);
  assert.ok(log.mark("A", at(2025, 3, 1)));
});

test("csvField quotes commas, quotes and newlines", () => {
  assert.equal(csvField("DOE, JANE"), '"DOE, JANE"');
  assert.equal(csvField('say "hi"'), '"say ""hi"""');
  assert.equal(csvField("plain"), "plain");
});

test("csvField defuses spreadsheet formulas", () => {
  assert.equal(csvField("=SUM(A1)"), "'=SUM(A1)");
  assert.equal(csvField("@cmd"), "'@cmd");
});

test("toCSV writes a header and one row per record", () => {
  const log = new AttendanceLog();
  log.mark("JANE DOE", at(2025, 3, 1, 9, 2, 41));
  log.mark("DOE, JOHN", at(2025, 3, 1, 9, 5, 13));
  assert.equal(
    log.toCSV(),
    'Name,Date,Time\r\nJANE DOE,2025-03-01,09:02:41\r\n"DOE, JOHN",2025-03-01,09:05:13\r\n',
  );
});
