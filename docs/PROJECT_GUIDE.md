# Project guide: understanding, restoring and running everything

This guide is for coming back to the project after a long time, possibly on a new computer with nothing installed. It explains what the project is, where every piece lives, how it works, and how to get it running again from scratch.

## 1. What this project is

It recognises faces from a camera and records who was present.

- **You give it photos** of the people it should know (one name per person).
- **It watches a camera.** For each face it sees, it decides: "this is JANE" or "unknown".
- **It writes attendance**: each recognised person is logged once per day with the date and time.

There are two versions of it, because they run in different places:

| | Desktop app (Python) | Browser app (JavaScript) |
|---|---|---|
| Where | `src/facial_attendance/` | `web/` |
| Runs on | Your computer, with `face-attendance run` | Anyone's browser, on Vercel |
| Face engine | `face_recognition` (dlib) | `face-api` (same kind of model) |
| Attendance saved in | A CSV file on disk | The visitor's browser, plus CSV download |
| Extras | 14 OpenCV image filters, screenshots, `report`/`compare` commands | Nothing leaves the visitor's device |
| Why separate | Needs a local camera window and dlib | Vercel can't run dlib, so recognition happens in the browser |

## 2. Where everything lives

| What | Where |
|---|---|
| Source code, docs, tests (public) | https://github.com/ANJULS09/Facial-Recognition-Attendance-System |
| Live website | https://facial-recognition-attendance-syste-mocha.vercel.app |
| Face photos, old attendance file, screenshot, IDE settings (**private**) | https://github.com/ANJULS09/Facial-Recognition-Attendance-System-private-data |
| Hosting | Vercel project `facial-recognition-attendance-system`, account `anjuls09` |

The private repo exists because the public one must never contain photos of real people. Keep it private.

**Not stored anywhere on GitHub, by design:**

- **Logins**: your GitHub and Vercel logins are on your computer only. Log in again on a new machine (`gh auth login`, `npx vercel login`).
- **`web/.env.local`**: contains a Vercel access token. Never commit it. `vercel link` recreates it.
- **`.venv/`**: a Python environment. It is rebuilt with `pip install`, so it isn't backed up.

## 3. The repository map

```
.
├── src/facial_attendance/     Python app (the "desktop" version)
│   ├── config.py              default folders and thresholds
│   ├── attendance.py          the CSV attendance log
│   ├── faces.py               reads photos and turns faces into numbers
│   ├── recognizer.py          finds faces in a frame and matches them
│   ├── filters.py             the 14 image filters
│   ├── app.py                 the live camera window
│   ├── tools.py               check-camera and compare helpers
│   └── cli.py                 the `face-attendance` command
├── tests/                     Python tests (pytest)
├── web/                       Browser app
│   ├── public/                the website itself (this is what Vercel serves)
│   │   ├── index.html         page structure
│   │   ├── css/style.css      look and layout
│   │   ├── js/                matching, attendance, storage, faces, app
│   │   ├── vendor/face-api.js the face library (third party, MIT)
│   │   └── models/            the trained face models (third party, MIT)
│   ├── tests/                 JavaScript tests (node:test)
│   └── vercel.json            hosting settings and security headers
├── legacy/                    the original scripts, unchanged, for reference
├── docs/                      this guide and ARCHITECTURE.md
├── .github/workflows/ci.yml   automatic tests on every push
├── ImagesAttendance/          where enrolment photos go (empty in git)
├── pyproject.toml             Python packaging, test and lint settings
├── requirements*.txt          Python dependencies
├── CHANGELOG.md               what changed from the original scripts
└── README.md                  the public front page
```

## 4. How face recognition works (plain language)

1. **Detect**: find where faces are in the image (a box around each).
2. **Encode**: turn each face into 128 numbers, a "fingerprint" made by a neural network. Photos of the same person give similar numbers; different people give different numbers.
3. **Compare**: measure the straight-line distance between two fingerprints. Small distance means the same person.
4. **Decide**: if the closest enrolled fingerprint is within the **tolerance** (default `0.6`), it's a match; otherwise the face is "unknown". Lower tolerance is stricter (fewer false matches, more misses).

That is all the "AI" there is. The rest of the project is plumbing: reading photos, drawing boxes, saving attendance.

## 5. Reading the Python code

Read in this order; each file is short and builds on the previous.

1. **`config.py`**: the defaults (folder names, tolerance `0.6`, scale `0.25`).
2. **`attendance.py`**: `AttendanceLog.mark(name)` writes one row per person per day and returns whether it was new. Look at how it remembers `(name, date)` pairs.
3. **`faces.py`**: `load_known_faces()` reads `ImagesAttendance/`. A file `Jane Doe.jpg` enrols "JANE DOE"; a folder `Jane Doe/` with several photos enrols one person from many photos. Names and fingerprints are stored side by side so they never fall out of step (a bug in the original).
4. **`recognizer.py`**: `best_match()` is the distance-and-tolerance rule from section 4. `FaceRecognizer.recognize()` shrinks the frame (faster), finds faces, and scales the boxes back up.
5. **`filters.py`**: a table of key → filter, such as `g` = grayscale. Adding a filter means adding one function and one table entry.
6. **`app.py`**: the loop: read a camera frame, recognise, log attendance, apply the chosen filter, draw boxes, show the window, handle key presses.
7. **`cli.py`**: turns `face-attendance run --tolerance 0.5` into calls to the above.

Then read `tests/`: each test file is a small, runnable explanation of one module.

## 6. Reading the browser code

1. **`web/public/js/matching.js`**: the same distance-and-tolerance rule, in JavaScript.
2. **`attendance.js`**: the same once-per-day log, plus safe CSV export (quotes commas, defuses `=` formulas).
3. **`storage.js`**: saves people and attendance in the browser's local storage, and ignores corrupted data.
4. **`faces.js`**: a thin wrapper around the face library: load models, detect faces, make thumbnails.
5. **`app.js`**: the page logic: enrolment form, camera loop, drawing boxes on a canvas, attendance table.
6. **`index.html` and `css/style.css`**: structure and look.

## 7. Getting everything back on a new computer

You need: **git**, **Python 3.10+**, **CMake** and a C++ compiler (for dlib), and **Node 20+** (only for the web app). See the README for install commands per OS.

```bash
# 1. Get the code
git clone https://github.com/ANJULS09/Facial-Recognition-Attendance-System.git
cd Facial-Recognition-Attendance-System

# 2. Python environment and the app
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e . -r requirements-dev.txt

# 3. Check it works
pytest
ruff check .
(cd web && npm test)
```

**Restore the private data (photos etc.)** — needs `gh auth login` as `ANJULS09` first:

```bash
gh repo clone ANJULS09/Facial-Recognition-Attendance-System-private-data ../fras-private
cp -R ../fras-private/ImagesAttendance/. ImagesAttendance/   # enrolment photos
cp -R ../fras-private/ImagesBasic .                          # test photos for the Basics script
cp ../fras-private/screenshot_0.png .                        # an old demo screenshot
```

The backup's `Attendance.csv` is in the **old format** (`Name,Time`, no date). It is only useful for the scripts in `legacy/`; the new app writes `data/attendance.csv` and refuses old-format files rather than corrupting them.

**Run the desktop app:**

```bash
face-attendance run                  # press q to quit
face-attendance report --all
```

**Run the website locally:**

```bash
cd web && npm start                  # http://localhost:3000
```

## 8. Command cheat-sheet

| Task | Command |
|---|---|
| Run live recognition | `face-attendance run` |
| Stricter matching | `face-attendance run --tolerance 0.5` |
| Detect smaller/farther faces | `face-attendance run --scale 0.5` |
| Use a lighter CPU load | `face-attendance run --process-every 3` |
| Show today's attendance | `face-attendance report` |
| Compare two photos | `face-attendance compare a.jpg b.jpg` |
| Check the camera | `face-attendance check-camera` |
| Python tests / lint | `pytest` · `ruff check .` |
| Website tests | `cd web && npm test` |

Live-window keys: `q` quit, `p` screenshot, `o g e s m b c l x y d r z h w` for filters (full table in the README).

## 9. Deploying the website (Vercel)

It is already deployed and **redeploys automatically on every push to `main`**. Vercel is configured with *Root Directory = `web`* and *Output Directory = `public`*; there is no build step.

To set it up again from nothing (new Vercel account or project), either:

- **Dashboard:** Add New → Project → import the GitHub repo → set **Root Directory** to `web` → Deploy.
- **Terminal, from the repo root:** `npx vercel link` then `npx vercel --prod`. Once Root Directory is `web`, run the CLI from the repo root, not from `web/`.

Vercel's own generated URLs (with a hash, or ending in `-projects.vercel.app`) sit behind a Vercel login. The public link is the project's short `.vercel.app` alias; add a custom name under *Settings → Domains*.

## 10. How the project got here

- **Original**: three scripts (`legacy/`). The main one did everything in a single loop, including 14 image filters computed on every frame.
- **Restructured** into an installable package with a command-line tool, tests and CI. Notable fixes: names could shift onto the wrong person, a missing CSV crashed the app, commas corrupted the CSV, Sobel/Laplacian wrapped negative values. Full list in [CHANGELOG.md](../CHANGELOG.md); design reasoning in [ARCHITECTURE.md](ARCHITECTURE.md).
- **Browser version** added so it can be hosted for free on Vercel without any server.

Git history holds every step: `git log --oneline`. To see the very first version of any file, `git show afe9584:<file>`.

## 11. Things to remember

- **Privacy**: faces are biometric data. Keep photos out of the public repo, get people's consent, and don't share the private repo.
- **Not spoof-proof**: a printed photo or a phone screen can be recognised as a person. Don't use it to guard anything important.
- **Tests never need a camera or photos.** They fake the face library, so they run anywhere, including GitHub's CI.
- **Dependencies to keep in mind**: `numpy` is pinned below 2 for compatibility with `dlib`; the web app bundles its own copy of `face-api` and the models, so it doesn't depend on a CDN.

## 12. Troubleshooting

| Symptom | Fix |
|---|---|
| `pip install` fails building `dlib` | Install CMake and a C++ compiler first (README, Installation). |
| Camera won't open on macOS | System Settings → Privacy & Security → Camera → allow your terminal or IDE. |
| "No usable faces found" | Put clear, front-facing photos in `ImagesAttendance/`, named after each person. |
| Someone isn't recognised | Add more photos in a folder named after them, or raise `--tolerance` slightly (for example `0.65`). |
| Wrong person recognised | Lower `--tolerance` (for example `0.5`) and add better photos. |
| `error: ... has header ['Name', 'Time']` | You pointed `--attendance-file` at an old-format CSV. Use a new path. |
| Website camera doesn't start | The browser needs camera permission and HTTPS (Vercel provides it; `localhost` also works). |
| Website says data is gone | Local storage is per browser and per device; clearing site data or using another browser starts fresh. Download the CSV to keep records. |
