# tests/test_scorer.py
import numpy as np
import pytest
from core.scorer import ScoreResult, score_image_algorithm


def test_score_result_fields():
    result = ScoreResult(score=85.0, source="algorithm", details={"sharpness": 100.0, "composition": 62.5})
    assert result.score == 85.0
    assert result.source == "algorithm"
    assert "sharpness" in result.details


def test_score_image_algorithm():
    np.random.seed(42)
    img = np.random.randint(0, 255, (300, 300), dtype=np.uint8)
    result = score_image_algorithm(img)
    assert isinstance(result, ScoreResult)
    assert 0 <= result.score <= 100
    assert result.source == "algorithm"
    assert "sharpness" in result.details
    assert "composition" in result.details


def test_score_image_algorithm_range():
    """纯色图应得低分"""
    img = np.ones((100, 100), dtype=np.uint8) * 128
    result = score_image_algorithm(img)
    assert result.score < 50
