import numpy as np
import pytest

from facial_attendance.filters import FILTERS, ORIGINAL_KEY, apply_filter


@pytest.fixture
def frame():
    rng = np.random.default_rng(0)
    return rng.integers(0, 256, size=(48, 64, 3), dtype=np.uint8)


def test_keys_do_not_clash_with_reserved_app_keys():
    assert "q" not in FILTERS
    assert "p" not in FILTERS
    assert ORIGINAL_KEY in FILTERS


@pytest.mark.parametrize("key", sorted(FILTERS))
def test_every_filter_returns_a_bgr_uint8_frame_of_the_same_size(key, frame):
    result = apply_filter(key, frame)
    assert result.dtype == np.uint8
    assert result.shape == frame.shape


def test_original_filter_returns_an_untouched_copy(frame):
    result = apply_filter(ORIGINAL_KEY, frame)
    assert np.array_equal(result, frame)
    assert result is not frame


def test_filters_do_not_modify_the_input(frame):
    before = frame.copy()
    for key in FILTERS:
        apply_filter(key, frame)
    assert np.array_equal(frame, before)
