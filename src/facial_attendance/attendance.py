"""CSV attendance log: one entry per person per day."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

FIELDNAMES = ["Name", "Date", "Time"]
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"


@dataclass(frozen=True)
class AttendanceRecord:
    name: str
    date: str
    time: str


class AttendanceLog:
    """Append-only attendance file with a header row of ``Name,Date,Time``."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._ensure_file()
        self._seen = {(r.name, r.date) for r in self.records()}

    def _ensure_file(self) -> None:
        if not self.path.exists() or self.path.stat().st_size == 0:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(FIELDNAMES)
            return

        with self.path.open(newline="", encoding="utf-8") as f:
            header = next(csv.reader(f), [])
        if header != FIELDNAMES:
            raise ValueError(
                f"{self.path} has header {header}, expected {FIELDNAMES}. "
                "It looks like a file from another version; move it aside "
                "or choose a different --attendance-file."
            )

    def records(self) -> list[AttendanceRecord]:
        with self.path.open(newline="", encoding="utf-8") as f:
            return [
                AttendanceRecord(row["Name"], row["Date"], row["Time"])
                for row in csv.DictReader(f)
                if row.get("Name")
            ]

    def records_on(self, day: date | None = None) -> list[AttendanceRecord]:
        wanted = (day or date.today()).strftime(DATE_FORMAT)
        return [r for r in self.records() if r.date == wanted]

    def count_on(self, day: date | None = None) -> int:
        wanted = (day or date.today()).strftime(DATE_FORMAT)
        return sum(1 for _, d in self._seen if d == wanted)

    def mark(self, name: str, when: datetime | None = None) -> bool:
        """Log ``name`` as present. Returns False if already logged that day."""
        when = when or datetime.now()
        day = when.strftime(DATE_FORMAT)
        if (name, day) in self._seen:
            return False
        with self.path.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([name, day, when.strftime(TIME_FORMAT)])
        self._seen.add((name, day))
        return True
