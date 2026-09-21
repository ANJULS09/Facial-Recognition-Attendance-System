"""Command-line interface: ``face-attendance <command>``."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, datetime
from pathlib import Path

from . import __version__
from .config import (
    DEFAULT_ATTENDANCE_FILE,
    DEFAULT_KNOWN_DIR,
    DEFAULT_SCALE,
    DEFAULT_SCREENSHOT_DIR,
    DEFAULT_TOLERANCE,
    Config,
)


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be 1 or greater")
    return number


def _iso_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("use the format YYYY-MM-DD") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="face-attendance",
        description="Real-time facial recognition and attendance logging.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="show debug logging")
    commands = parser.add_subparsers(dest="command", metavar="<command>")

    run = commands.add_parser("run", help="start live recognition and attendance logging")
    run.add_argument("--known-dir", type=Path, default=DEFAULT_KNOWN_DIR,
                     help="folder of enrolment photos (default: %(default)s)")
    run.add_argument("--attendance-file", type=Path, default=DEFAULT_ATTENDANCE_FILE,
                     help="CSV attendance log (default: %(default)s)")
    run.add_argument("--screenshot-dir", type=Path, default=DEFAULT_SCREENSHOT_DIR,
                     help="where 'p' saves screenshots (default: %(default)s)")
    run.add_argument("--camera", type=int, default=0, help="camera index (default: %(default)s)")
    run.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE,
                     help="max face distance for a match; lower is stricter (default: %(default)s)")
    run.add_argument("--scale", type=float, default=DEFAULT_SCALE,
                     help="frame scale used for detection, 0-1 (default: %(default)s)")
    run.add_argument("--process-every", type=_positive_int, default=1, metavar="N",
                     help="run recognition on every Nth frame to save CPU (default: %(default)s)")

    camera = commands.add_parser("check-camera", help="check that the webcam opens")
    camera.add_argument("--camera", type=int, default=0, help="camera index (default: %(default)s)")

    compare = commands.add_parser("compare", help="compare the first face in two images")
    compare.add_argument("first", type=Path)
    compare.add_argument("second", type=Path)
    compare.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    compare.add_argument("--show", action="store_true", help="display both images with the result")

    report = commands.add_parser("report", help="print attendance records")
    report.add_argument("--file", type=Path, default=DEFAULT_ATTENDANCE_FILE,
                        help="CSV attendance log (default: %(default)s)")
    report.add_argument("--date", type=_iso_date, help="day to show, YYYY-MM-DD (default: today)")
    report.add_argument("--all", action="store_true", help="show every day")

    return parser


def _cmd_run(args: argparse.Namespace) -> int:
    from .app import run  # imported lazily: pulls in the GUI stack

    config = Config(
        known_dir=args.known_dir,
        attendance_file=args.attendance_file,
        screenshot_dir=args.screenshot_dir,
        camera_index=args.camera,
        tolerance=args.tolerance,
        scale=args.scale,
        process_every=args.process_every,
    )
    return run(config)


def _cmd_check_camera(args: argparse.Namespace) -> int:
    from .tools import check_camera

    ok, message = check_camera(args.camera)
    print(message)
    return 0 if ok else 1


def _cmd_compare(args: argparse.Namespace) -> int:
    from .tools import compare_images

    result = compare_images(args.first, args.second, args.tolerance, args.show)
    print(f"Match: {result.match} | distance: {result.distance:.3f} "
          f"(tolerance {args.tolerance})")
    return 0 if result.match else 1


def _cmd_report(args: argparse.Namespace) -> int:
    from .attendance import AttendanceLog

    if not args.file.exists():
        print(f"No attendance file at {args.file}", file=sys.stderr)
        return 1

    log = AttendanceLog(args.file)
    records = log.records() if args.all else log.records_on(args.date)
    if not records:
        print("No attendance records.")
        return 0

    width = max(len(r.name) for r in records)
    for record in records:
        print(f"{record.name:<{width}}  {record.date}  {record.time}")
    print(f"\n{len(records)} record(s)")
    return 0


_COMMANDS = {
    "run": _cmd_run,
    "check-camera": _cmd_check_camera,
    "compare": _cmd_compare,
    "report": _cmd_report,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 2

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    try:
        return _COMMANDS[args.command](args)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
