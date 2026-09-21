# Contributing

Thanks for helping improve this project.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e . -r requirements-dev.txt     # needs CMake for dlib; see README
```

## Before opening a pull request

```bash
ruff check .
pytest
```

Both run in CI on Python 3.10–3.12. The tests replace `face_recognition` with a fake backend, so they don't need dlib, a camera, or any photos.

## Guidelines

- Keep changes focused, and add or update tests for new behaviour.
- New code that touches faces should go through `faces.get_backend()` so it stays testable.
- **Never commit face photos, screenshots, or attendance files.** They are git-ignored on purpose; check `git status` before committing.
- Update `CHANGELOG.md` for user-visible changes.

## Reporting bugs

Open an issue with your OS, Python version, the command you ran, and the full error output. Please don't attach photos of other people.
