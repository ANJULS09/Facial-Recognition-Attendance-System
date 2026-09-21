import cv2
import numpy as np
import pytest

from facial_attendance import faces


class FakeBackend:
    """Pretends the top-left pixel's value is the face encoding; a value of 0
    means the photo contains no face."""

    def load_image_file(self, path):
        image = cv2.imread(path)
        if image is None:
            raise OSError("cannot read image")
        return image

    def face_encodings(self, image):
        value = int(image[0, 0, 0])
        return [np.array([value, 0.0])] if value else []


def write_image(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), np.full((8, 8, 3), value, dtype=np.uint8))


@pytest.fixture(autouse=True)
def fake_backend(monkeypatch):
    monkeypatch.setattr(faces, "get_backend", lambda: FakeBackend())


def test_names_stay_aligned_when_a_photo_has_no_face(tmp_path):
    write_image(tmp_path / "Alice.png", 10)
    write_image(tmp_path / "Bob.png", 0)  # no face: must not shift later names
    write_image(tmp_path / "Carol.png", 30)

    known = faces.load_known_faces(tmp_path)

    assert known.names == ["ALICE", "CAROL"]
    assert [int(e[0]) for e in known.encodings] == [10, 30]


def test_folder_enrols_several_photos_for_one_person(tmp_path):
    write_image(tmp_path / "Dana" / "front.png", 40)
    write_image(tmp_path / "Dana" / "side.png", 41)
    write_image(tmp_path / "Eli.png", 50)

    known = faces.load_known_faces(tmp_path)

    assert known.names == ["DANA", "DANA", "ELI"]
    assert known.people == ["DANA", "ELI"]
    assert len(known) == 3


def test_ignores_non_images_and_hidden_files(tmp_path):
    write_image(tmp_path / "Alice.png", 10)
    (tmp_path / ".gitkeep").write_text("")
    (tmp_path / "notes.txt").write_text("hello")

    assert faces.load_known_faces(tmp_path).names == ["ALICE"]


def test_corrupt_image_is_skipped(tmp_path):
    write_image(tmp_path / "Alice.png", 10)
    (tmp_path / "Broken.jpg").write_bytes(b"not an image")

    assert faces.load_known_faces(tmp_path).names == ["ALICE"]


def test_missing_folder_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        faces.load_known_faces(tmp_path / "nope")
