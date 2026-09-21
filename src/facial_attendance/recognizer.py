"""Detect faces in a frame and match them against the enrolled faces."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from . import faces
from .config import DEFAULT_SCALE, DEFAULT_TOLERANCE


@dataclass(frozen=True)
class Detection:
    name: str | None  # None means "unknown"
    box: tuple[int, int, int, int]  # top, right, bottom, left, in full-frame pixels
    distance: float | None

    @property
    def known(self) -> bool:
        return self.name is not None


def best_match(
    known_encodings: list[np.ndarray] | np.ndarray,
    encoding: np.ndarray,
    tolerance: float = DEFAULT_TOLERANCE,
) -> tuple[int | None, float | None]:
    """Return ``(index, distance)`` of the closest known face.

    ``index`` is None when nothing is within ``tolerance``. ``distance`` is None
    only when there are no known faces at all.
    """
    if len(known_encodings) == 0:
        return None, None
    distances = np.linalg.norm(np.asarray(known_encodings) - encoding, axis=1)
    index = int(np.argmin(distances))
    distance = float(distances[index])
    return (index if distance <= tolerance else None), distance


class FaceRecognizer:
    def __init__(
        self,
        known: faces.KnownFaces,
        tolerance: float = DEFAULT_TOLERANCE,
        scale: float = DEFAULT_SCALE,
    ):
        if not 0 < scale <= 1:
            raise ValueError("scale must be in the range (0, 1]")
        self.known = known
        self.tolerance = tolerance
        self.scale = scale

    def recognize(self, frame_bgr: np.ndarray) -> list[Detection]:
        fr = faces.get_backend()
        small = cv2.resize(frame_bgr, (0, 0), fx=self.scale, fy=self.scale)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        locations = fr.face_locations(rgb)
        encodings = fr.face_encodings(rgb, locations)

        detections = []
        for location, encoding in zip(locations, encodings, strict=True):
            index, distance = best_match(self.known.encodings, encoding, self.tolerance)
            name = self.known.names[index] if index is not None else None
            box = tuple(int(round(v / self.scale)) for v in location)
            detections.append(Detection(name, box, distance))
        return detections
