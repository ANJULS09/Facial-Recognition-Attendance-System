"""The live webcam loop: recognise, log attendance, show filtered video."""

from __future__ import annotations

import logging
from datetime import datetime

import cv2
import numpy as np

from .attendance import AttendanceLog
from .config import WINDOW_NAME, Config
from .faces import load_known_faces
from .filters import FILTERS, ORIGINAL_KEY, apply_filter
from .recognizer import Detection, FaceRecognizer

logger = logging.getLogger(__name__)

GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
FONT = cv2.FONT_HERSHEY_COMPLEX


def draw_detection(image: np.ndarray, detection: Detection) -> None:
    top, right, bottom, left = detection.box
    color = GREEN if detection.known else RED
    label = detection.name or "UNKNOWN"

    (text_w, _), _ = cv2.getTextSize(label, FONT, 0.8, 2)
    right_bar = max(right, left + text_w + 12)  # keep long names inside the bar

    cv2.rectangle(image, (left, top), (right, bottom), color, 2)
    cv2.rectangle(image, (left, bottom - 35), (right_bar, bottom), color, cv2.FILLED)
    cv2.putText(image, label, (left + 6, bottom - 8), FONT, 0.8, WHITE, 2)


def draw_status(image: np.ndarray, text: str) -> None:
    cv2.putText(image, text, (10, 28), FONT, 0.7, (0, 0, 0), 4)
    cv2.putText(image, text, (10, 28), FONT, 0.7, WHITE, 1)


def save_screenshot(image: np.ndarray, directory) -> str:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"screenshot_{datetime.now():%Y%m%d_%H%M%S}.png"
    cv2.imwrite(str(path), image)
    return str(path)


def run(config: Config) -> int:
    known = load_known_faces(config.known_dir)
    if not len(known):
        logger.error(
            "No usable faces found in %s. Add one clear, front-facing photo per "
            "person, named after them (e.g. 'Jane Doe.jpg').",
            config.known_dir,
        )
        return 1
    logger.info("Enrolled %d photo(s) for: %s", len(known), ", ".join(known.people))

    log = AttendanceLog(config.attendance_file)
    recognizer = FaceRecognizer(known, config.tolerance, config.scale)

    capture = cv2.VideoCapture(config.camera_index)
    if not capture.isOpened():
        logger.error("Could not open camera %d.", config.camera_index)
        return 1

    logger.info("Running. Press 'q' to quit, 'p' for a screenshot, or a filter key.")
    logger.info("Filters: %s", ", ".join(f"{k}={f.label}" for k, f in FILTERS.items()))

    filter_key = ORIGINAL_KEY
    detections: list[Detection] = []
    frame_number = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                logger.error("Lost the camera feed.")
                return 1

            if frame_number % config.process_every == 0:
                detections = recognizer.recognize(frame)
                for detection in detections:
                    if detection.known and log.mark(detection.name):
                        logger.info("Marked present: %s", detection.name)
            frame_number += 1

            view = apply_filter(filter_key, frame)
            for detection in detections:
                draw_detection(view, detection)
            draw_status(
                view, f"{FILTERS[filter_key].label} | Present today: {log.count_on()}"
            )
            cv2.imshow(WINDOW_NAME, view)

            key = chr(cv2.waitKey(1) & 0xFF)
            if key == "q":
                return 0
            if key == "p":
                logger.info("Screenshot saved: %s", save_screenshot(view, config.screenshot_dir))
            elif key in FILTERS:
                filter_key = key
    finally:
        capture.release()
        cv2.destroyAllWindows()
