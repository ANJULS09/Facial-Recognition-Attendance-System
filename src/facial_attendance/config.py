"""Default settings shared by the CLI and the live app."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_KNOWN_DIR = Path("ImagesAttendance")
DEFAULT_ATTENDANCE_FILE = Path("data/attendance.csv")
DEFAULT_SCREENSHOT_DIR = Path("screenshots")

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")

# 0.6 is the face_recognition library's default; lower is stricter.
DEFAULT_TOLERANCE = 0.6
# Frames are shrunk before detection so recognition keeps up with the camera.
DEFAULT_SCALE = 0.25

WINDOW_NAME = "Facial Recognition & Attendance"


@dataclass
class Config:
    known_dir: Path = DEFAULT_KNOWN_DIR
    attendance_file: Path = DEFAULT_ATTENDANCE_FILE
    screenshot_dir: Path = DEFAULT_SCREENSHOT_DIR
    camera_index: int = 0
    tolerance: float = DEFAULT_TOLERANCE
    scale: float = DEFAULT_SCALE
    process_every: int = 1  # run recognition on every Nth frame
