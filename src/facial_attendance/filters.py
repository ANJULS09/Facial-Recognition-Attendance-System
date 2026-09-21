"""OpenCV image filters that can be switched on live with a key press."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import cv2
import numpy as np

_KERNEL = np.ones((5, 5), np.uint8)
_SHARPEN_KERNEL = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])


def _gray(frame: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


def original(frame):
    return frame.copy()


def grayscale(frame):
    return _gray(frame)


def equalized(frame):
    return cv2.equalizeHist(_gray(frame))


def gaussian_blur(frame):
    return cv2.GaussianBlur(frame, (5, 5), 0)


def median_blur(frame):
    return cv2.medianBlur(frame, 5)


def bilateral(frame):
    return cv2.bilateralFilter(frame, 9, 75, 75)


def canny(frame):
    return cv2.Canny(_gray(frame), 100, 200)


def laplacian(frame):
    return cv2.convertScaleAbs(cv2.Laplacian(_gray(frame), cv2.CV_64F))


def sobel_x(frame):
    return cv2.convertScaleAbs(cv2.Sobel(_gray(frame), cv2.CV_64F, 1, 0, ksize=5))


def sobel_y(frame):
    return cv2.convertScaleAbs(cv2.Sobel(_gray(frame), cv2.CV_64F, 0, 1, ksize=5))


def dilation(frame):
    return cv2.dilate(canny(frame), _KERNEL, iterations=1)


def erosion(frame):
    return cv2.erode(canny(frame), _KERNEL, iterations=1)


def morph_gradient(frame):
    return cv2.morphologyEx(_gray(frame), cv2.MORPH_GRADIENT, _KERNEL)


def adaptive_threshold(frame):
    return cv2.adaptiveThreshold(
        _gray(frame), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )


def sharpen(frame):
    return cv2.filter2D(frame, -1, _SHARPEN_KERNEL)


@dataclass(frozen=True)
class Filter:
    key: str
    label: str
    apply: Callable[[np.ndarray], np.ndarray]


ORIGINAL_KEY = "o"

# Keys "p" (screenshot) and "q" (quit) are reserved by the app.
FILTERS: dict[str, Filter] = {
    f.key: f
    for f in (
        Filter("o", "Original", original),
        Filter("g", "Grayscale", grayscale),
        Filter("e", "Histogram equalization", equalized),
        Filter("s", "Gaussian blur", gaussian_blur),
        Filter("m", "Median blur", median_blur),
        Filter("b", "Bilateral filter", bilateral),
        Filter("c", "Canny edges", canny),
        Filter("l", "Laplacian edges", laplacian),
        Filter("x", "Sobel X", sobel_x),
        Filter("y", "Sobel Y", sobel_y),
        Filter("d", "Dilation", dilation),
        Filter("r", "Erosion", erosion),
        Filter("z", "Morphological gradient", morph_gradient),
        Filter("h", "Adaptive threshold", adaptive_threshold),
        Filter("w", "Sharpening", sharpen),
    )
}


def apply_filter(key: str, frame: np.ndarray) -> np.ndarray:
    """Apply the filter bound to ``key``. The result is always 3-channel BGR so
    recognition boxes can be drawn on top of any filter."""
    result = FILTERS[key].apply(frame)
    if result.ndim == 2:
        result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
    return result
