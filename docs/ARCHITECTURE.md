# Architecture

## Data flow

```
ImagesAttendance/ ──► faces.load_known_faces ──► KnownFaces(names, encodings)
                                                        │
camera ─► app.run ─► recognizer.FaceRecognizer.recognize ┘
              │              │
              │              └─► [Detection(name | None, box, distance)]
              │
              ├─► attendance.AttendanceLog.mark ──► data/attendance.csv
              └─► filters.apply_filter + draw_detection ──► window
```

## Modules

| Module | Responsibility |
|---|---|
| `cli.py` | Argument parsing and the `run`, `report`, `check-camera` and `compare` commands. Heavy imports happen inside each command so `--help` and `report` are instant. |
| `app.py` | The webcam loop: read frame → recognise → log → filter → draw → handle keys. |
| `faces.py` | Finds enrolment photos and encodes them into `KnownFaces`. Also owns `get_backend()`, the single place `face_recognition` is imported. |
| `recognizer.py` | `FaceRecognizer` detects and encodes faces in a frame; `best_match` picks the nearest known face. |
| `attendance.py` | `AttendanceLog`, a CSV file with one row per person per day. |
| `filters.py` | The filter registry (`FILTERS`) and `apply_filter`. |
| `tools.py` | `check_camera` and `compare_images`. |
| `config.py` | Default paths and thresholds, and the `Config` dataclass. |

## Design decisions

- **`face_recognition` is imported lazily** through `faces.get_backend()`. Everything else (matching, logging, filters, CLI) works without dlib, and the tests replace the backend with a small fake. That keeps CI fast, because dlib takes minutes to compile.
- **`KnownFaces.names[i]` always belongs to `encodings[i]`.** Names and encodings are appended together, so a photo with no detectable face can't shift later names onto the wrong person.
- **Matching is plain NumPy.** `best_match` computes Euclidean distances and takes the minimum, which is what `face_recognition.compare_faces` does, and it can be unit-tested without images.
- **Detection runs on a downscaled frame** (`--scale`, default 0.25) and boxes are scaled back to full-frame coordinates. `--process-every N` further reduces CPU load.
- **Only the selected filter is computed** each frame, and the recognition overlay is drawn on the filtered image, so every filter shows boxes.
- **Attendance is keyed by `(name, date)`**, held in memory and loaded from the file at start-up. `mark()` returns whether a new row was written. The CSV is written with the `csv` module so names containing commas are quoted correctly.
- **Files from another format are rejected**, not appended to. `AttendanceLog` checks the header and raises a clear error instead of mixing column layouts.

## Extending

- **New filter:** write `def my_filter(frame) -> ndarray` in `filters.py` and add a `Filter("k", "Label", my_filter)` entry to `FILTERS`. Avoid `p` and `q`, which the app reserves.
- **Different storage:** `AttendanceLog` exposes `mark`, `records`, `records_on` and `count_on`; a database-backed class with the same methods can replace it in `app.run`.
- **Different recognition backend:** replace `faces.get_backend()` and the calls made on it (`load_image_file`, `face_locations`, `face_encodings`).
