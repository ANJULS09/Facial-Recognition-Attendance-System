# Original scripts

These three files are the project exactly as it was first written, kept unchanged so you can see where it started. They are **not** used by the current project, which lives in [`src/facial_attendance/`](../src/facial_attendance). See [docs/PROJECT_GUIDE.md](../docs/PROJECT_GUIDE.md) for what changed and why.

| File | What it did |
|---|---|
| `camera.py` | Opens the webcam and prints whether it worked. Replaced by `face-attendance check-camera`. |
| `Basics.py` | Compares two photos of the same person and prints the match and distance. Has hard-coded Windows paths (`E:\...`), so edit them to run it. Replaced by `face-attendance compare`. |
| `AttendanceProject.py` | The full app: live recognition, attendance CSV and 14 image filters in one long script. Replaced by the `facial_attendance` package. |

## Running them

They were written to run from the folder that contains `ImagesAttendance/`, with dependencies from `requirements.txt` installed:

```bash
python legacy/camera.py
python legacy/AttendanceProject.py   # needs ImagesAttendance/ and an Attendance.csv whose first line is: Name,Time
```

Known issues (fixed in the new package): names can shift onto the wrong person if a photo has no detectable face, the app crashes if `Attendance.csv` is missing, and names with commas corrupt the CSV.

The same files are also in git history: `git show afe9584:AttendanceProject.py`.
