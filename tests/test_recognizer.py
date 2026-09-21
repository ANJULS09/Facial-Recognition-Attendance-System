import numpy as np
import pytest

from facial_attendance.faces import KnownFaces
from facial_attendance.recognizer import FaceRecognizer, best_match


def enc(*values):
    return np.array(values, dtype=float)


def test_best_match_picks_the_closest_face():
    known = [enc(0, 0), enc(1, 0), enc(5, 5)]
    index, distance = best_match(known, enc(0.9, 0), tolerance=0.6)
    assert index == 1
    assert distance == pytest.approx(0.1)


def test_best_match_returns_none_outside_tolerance():
    index, distance = best_match([enc(0, 0)], enc(3, 4), tolerance=0.6)
    assert index is None
    assert distance == pytest.approx(5.0)


def test_best_match_tolerance_is_inclusive():
    index, _ = best_match([enc(0, 0)], enc(0.6, 0), tolerance=0.6)
    assert index == 0


def test_best_match_with_no_known_faces():
    assert best_match([], enc(1, 1)) == (None, None)


def test_recognizer_rejects_bad_scale():
    with pytest.raises(ValueError):
        FaceRecognizer(KnownFaces(), scale=0)
    with pytest.raises(ValueError):
        FaceRecognizer(KnownFaces(), scale=1.5)


def test_recognize_scales_boxes_back_to_full_frame(monkeypatch):
    from facial_attendance import faces

    class FakeBackend:
        def face_locations(self, image):
            assert image.shape[:2] == (25, 50)  # frame was shrunk to 25%
            return [(5, 20, 15, 10)]

        def face_encodings(self, image, locations):
            return [enc(1, 0)]

    monkeypatch.setattr(faces, "get_backend", lambda: FakeBackend())
    known = KnownFaces(names=["A", "B"], encodings=[enc(0, 0), enc(1, 0)])

    frame = np.zeros((100, 200, 3), dtype=np.uint8)
    [detection] = FaceRecognizer(known, scale=0.25).recognize(frame)

    assert detection.name == "B"
    assert detection.box == (20, 80, 60, 40)


def test_recognize_reports_unknown_faces(monkeypatch):
    from facial_attendance import faces

    class FakeBackend:
        def face_locations(self, image):
            return [(0, 5, 5, 0)]

        def face_encodings(self, image, locations):
            return [enc(9, 9)]

    monkeypatch.setattr(faces, "get_backend", lambda: FakeBackend())
    known = KnownFaces(names=["A"], encodings=[enc(0, 0)])

    [detection] = FaceRecognizer(known).recognize(np.zeros((40, 40, 3), dtype=np.uint8))
    assert detection.name is None
    assert not detection.known
