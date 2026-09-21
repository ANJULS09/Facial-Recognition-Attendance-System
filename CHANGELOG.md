# Changelog

## 1.0.0

Restructured the original scripts into an installable package with a CLI, tests and CI.

### Added
- `face-attendance` command with `run`, `report`, `check-camera` and `compare` subcommands
- Options for camera index, match tolerance, detection scale, frame skipping, and file locations
- Red `UNKNOWN` box for faces that match nobody
- Multiple enrolment photos per person (put them in a folder named after the person)
- Date-stamped attendance, logged once per person per day
- Pytest suite, Ruff configuration, GitHub Actions CI
- Architecture and contributing docs

### Fixed
- Names could shift onto the wrong person when an enrolment photo contained no detectable face
- The app crashed if `Attendance.csv` didn't exist; the log is now created automatically
- Names containing commas corrupted the CSV
- Laplacian and Sobel filters wrapped negative values instead of taking the absolute value
- Screenshots overwrote each other between runs; they now have timestamped names
- Long names no longer overflow the label bar
- `Basics.py` no longer depends on hard-coded Windows paths (now `face-attendance compare`)

### Changed
- All 14 filters were computed on every frame; only the selected one is now
- Recognition overlay is drawn on every filter, not just the original view
- Attendance is written to `data/attendance.csv` with columns `Name,Date,Time`
- Enrolment photos, attendance logs and screenshots are git-ignored

### Removed
- `AttendanceProject.py`, `Basics.py`, `camera.py` (replaced by the package; still in git history)
