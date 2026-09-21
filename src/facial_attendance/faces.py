"""Loading enrolment photos and turning them into face encodings."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .config import IMAGE_EXTENSIONS

logger = logging.getLogger(__name__)


def get_backend():
    """Import ``face_recognition`` lazily so the rest of the package (and its
    tests) work without dlib installed."""
    try:
        import face_recognition
    except ImportError as exc:
        raise RuntimeError(
            "The 'face_recognition' package is required. "
            "Install it with: pip install -r requirements.txt"
        ) from exc
    return face_recognition


@dataclass
class KnownFaces:
    """Enrolled encodings. ``names[i]`` always belongs to ``encodings[i]``."""

    names: list[str] = field(default_factory=list)
    encodings: list[np.ndarray] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.encodings)

    @property
    def people(self) -> list[str]:
        return sorted(set(self.names))


def _image_files(directory: Path):
    """Yield ``(person_name, image_path)`` pairs.

    ``Jane Doe.jpg`` enrols "JANE DOE"; a folder ``Jane Doe/`` enrols every
    image inside it as the same person.
    """
    for entry in sorted(directory.iterdir()):
        if entry.name.startswith("."):
            continue
        if entry.is_dir():
            for image in sorted(entry.iterdir()):
                if image.suffix.lower() in IMAGE_EXTENSIONS:
                    yield entry.name.strip().upper(), image
        elif entry.suffix.lower() in IMAGE_EXTENSIONS:
            yield entry.stem.strip().upper(), entry


def load_known_faces(directory: str | Path) -> KnownFaces:
    directory = Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"Enrolment folder not found: {directory}")

    fr = get_backend()
    known = KnownFaces()
    for name, path in _image_files(directory):
        try:
            image = fr.load_image_file(str(path))
        except Exception as exc:  # unreadable or corrupt image
            logger.warning("Skipping %s: %s", path.name, exc)
            continue

        encodings = fr.face_encodings(image)
        if not encodings:
            logger.warning("Skipping %s: no face found", path.name)
            continue
        if len(encodings) > 1:
            logger.warning("%s has %d faces; using the first", path.name, len(encodings))

        known.names.append(name)
        known.encodings.append(encodings[0])

    return known
