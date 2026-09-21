import pytest

from facial_attendance import __version__
from facial_attendance.attendance import AttendanceLog
from facial_attendance.cli import build_parser, main


def test_run_defaults():
    args = build_parser().parse_args(["run"])
    assert args.camera == 0
    assert args.tolerance == 0.6
    assert args.scale == 0.25
    assert args.process_every == 1


def test_run_options():
    args = build_parser().parse_args(
        ["run", "--camera", "2", "--tolerance", "0.45", "--process-every", "3"]
    )
    assert (args.camera, args.tolerance, args.process_every) == (2, 0.45, 3)


def test_rejects_zero_process_every():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["run", "--process-every", "0"])


def test_no_command_prints_help(capsys):
    assert main([]) == 2
    assert "usage: face-attendance" in capsys.readouterr().out


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_report_lists_records_for_a_date(tmp_path, capsys):
    from datetime import datetime

    path = tmp_path / "a.csv"
    log = AttendanceLog(path)
    log.mark("JANE DOE", datetime(2025, 3, 1, 9, 2, 41))
    log.mark("JOHN SMITH", datetime(2025, 3, 2, 9, 5, 13))

    assert main(["report", "--file", str(path), "--date", "2025-03-01"]) == 0
    out = capsys.readouterr().out
    assert "JANE DOE" in out and "09:02:41" in out
    assert "JOHN SMITH" not in out

    assert main(["report", "--file", str(path), "--all"]) == 0
    assert "2 record(s)" in capsys.readouterr().out


def test_report_with_missing_file_fails(tmp_path, capsys):
    assert main(["report", "--file", str(tmp_path / "missing.csv")]) == 1
    assert "No attendance file" in capsys.readouterr().err


def test_run_with_missing_photo_folder_reports_a_clean_error(tmp_path, monkeypatch, capsys):
    from facial_attendance import faces

    monkeypatch.setattr(faces, "get_backend", lambda: object())
    assert main(["run", "--known-dir", str(tmp_path / "nope")]) == 1
    assert "Enrolment folder not found" in capsys.readouterr().err
