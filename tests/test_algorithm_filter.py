import numpy as np
import cv2
import pytest
from core.algorithm_filter import calculate_sharpness, calculate_composition


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


def test_composition_center_subject():
    """主体在中心的图片应有中等构图分"""
    img = np.zeros((300, 300), dtype=np.uint8)
    img[100:200, 100:200] = 255  # 中心白色方块
    score = calculate_composition(img)
    assert 0 <= score <= 100


def test_composition_rule_of_thirds():
    """主体在三分线交叉点应得较高分"""
    img = np.zeros((300, 300), dtype=np.uint8)
    img[80:120, 80:120] = 255  # 放在三分线交叉点 (100, 100)
    score = calculate_composition(img)
    assert score > 30


def test_composition_returns_float():
    img = np.zeros((300, 300), dtype=np.uint8)
    score = calculate_composition(img)
    assert isinstance(score, float)
