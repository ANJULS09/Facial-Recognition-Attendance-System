"""Small utilities: camera check and two-image face comparison."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from . import faces
from .config import DEFAULT_TOLERANCE, WINDOW_NAME
from .recognizer import best_match


def check_camera(index: int = 0) -> tuple[bool, str]:
    capture = cv2.VideoCapture(index)
    try:
        if not capture.isOpened():
            return False, f"Camera {index} not found or failed to open."
        ok, frame = capture.read()
        if not ok:
            return False, f"Camera {index} opened but returned no frame."
        height, width = frame.shape[:2]
        return True, f"Camera {index} is working ({width}x{height})."
    finally:
        capture.release()


@dataclass(frozen=True)
class ComparisonResult:
    match: bool
    distance: float


def _first_face(path: Path):
    """Return ``(rgb_image, location, encoding)`` for the first face in ``path``."""
    fr = faces.get_backend()
    image = fr.load_image_file(str(path))
    locations = fr.face_locations(image)
    if not locations:
        raise ValueError(f"No face found in {path}")
    encoding = fr.face_encodings(image, locations)[0]
    return image, locations[0], encoding


def compare_images(
    first: str | Path,
    second: str | Path,
    tolerance: float = DEFAULT_TOLERANCE,
    show: bool = False,
) -> ComparisonResult:
    image_a, loc_a, enc_a = _first_face(Path(first))
    image_b, loc_b, enc_b = _first_face(Path(second))

    index, distance = best_match([enc_a], enc_b, tolerance)
    result = ComparisonResult(match=index is not None, distance=distance)

    if show:
        for title, image, (top, right, bottom, left) in (
            ("First", image_a, loc_a),
            ("Second", image_b, loc_b),
        ):
            view = cv2.cvtColor(np.ascontiguousarray(image), cv2.COLOR_RGB2BGR)
            cv2.rectangle(view, (left, top), (right, bottom), (255, 0, 255), 2)
            if title == "Second":
                text = f"{result.match} {result.distance:.2f}"
                cv2.putText(view, text, (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow(f"{WINDOW_NAME} - {title}", view)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return result
