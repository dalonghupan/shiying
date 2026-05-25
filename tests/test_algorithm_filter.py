import numpy as np
import cv2
import pytest
from core.algorithm_filter import calculate_sharpness


def test_sharpness_blur_image():
    """模糊图片应得低分"""
    img = np.ones((100, 100), dtype=np.uint8) * 128
    score = calculate_sharpness(img)
    assert score < 10


def test_sharpness_clear_image():
    """清晰图片应得高分"""
    np.random.seed(42)
    img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
    score = calculate_sharpness(img)
    assert score > 100


def test_sharpness_returns_float():
    img = np.ones((100, 100), dtype=np.uint8) * 128
    score = calculate_sharpness(img)
    assert isinstance(score, float)
