from datetime import date, datetime

import pytest

from facial_attendance.attendance import FIELDNAMES, AttendanceLog


def test_creates_file_with_header(tmp_path):
    path = tmp_path / "nested" / "attendance.csv"
    AttendanceLog(path)
    assert path.read_text().strip() == ",".join(FIELDNAMES)


def test_marks_once_per_day(tmp_path):
    log = AttendanceLog(tmp_path / "a.csv")
    morning = datetime(2025, 3, 1, 9, 0, 0)
    assert log.mark("JANE DOE", morning) is True
    assert log.mark("JANE DOE", morning.replace(hour=15)) is False
    assert [r.time for r in log.records()] == ["09:00:00"]


def test_same_person_is_logged_again_on_a_new_day(tmp_path):
    log = AttendanceLog(tmp_path / "a.csv")
    assert log.mark("JANE DOE", datetime(2025, 3, 1, 9, 0)) is True
    assert log.mark("JANE DOE", datetime(2025, 3, 2, 9, 0)) is True
    assert len(log.records()) == 2


def test_state_survives_a_restart(tmp_path):
    path = tmp_path / "a.csv"
    when = datetime(2025, 3, 1, 9, 0)
    AttendanceLog(path).mark("JANE DOE", when)
    assert AttendanceLog(path).mark("JANE DOE", when) is False


def test_names_with_commas_are_quoted(tmp_path):
    log = AttendanceLog(tmp_path / "a.csv")
    log.mark("DOE, JANE", datetime(2025, 3, 1, 9, 0))
    assert [r.name for r in AttendanceLog(tmp_path / "a.csv").records()] == ["DOE, JANE"]


def test_records_and_count_for_a_day(tmp_path):
    log = AttendanceLog(tmp_path / "a.csv")
    log.mark("A", datetime(2025, 3, 1, 9, 0))
    log.mark("B", datetime(2025, 3, 1, 9, 5))
    log.mark("A", datetime(2025, 3, 2, 9, 0))
    assert [r.name for r in log.records_on(date(2025, 3, 1))] == ["A", "B"]
    assert log.count_on(date(2025, 3, 2)) == 1
    assert log.count_on(date(2025, 3, 3)) == 0


def test_rejects_file_with_a_different_header(tmp_path):
    path = tmp_path / "old.csv"
    path.write_text("Name,Time\nJANE,09:00:00")
    with pytest.raises(ValueError, match="header"):
        AttendanceLog(path)
