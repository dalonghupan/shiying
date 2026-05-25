# core/scorer.py
"""统一评分接口"""
from dataclasses import dataclass
import numpy as np
from core.algorithm_filter import calculate_sharpness, calculate_composition
from config import SHARPNESS_WEIGHT, COMPOSITION_WEIGHT


@dataclass
class ScoreResult:
    """评分结果"""
    score: float          # 0-100 综合分
    source: str           # "algorithm" 或 "ai"
    details: dict         # 各维度分数明细


def score_image_algorithm(gray_image: np.ndarray) -> ScoreResult:
    """使用基础算法评分

    Args:
        gray_image: 灰度图 numpy 数组

    Returns:
        ScoreResult 评分结果
    """
    sharpness_raw = calculate_sharpness(gray_image)
    composition_raw = calculate_composition(gray_image)

    # 清晰度归一化到 0-100（经验值：500 以上算非常清晰）
    sharpness_score = min(100.0, sharpness_raw / 5.0)
    composition_score = composition_raw  # 已经是 0-100

    total = sharpness_score * SHARPNESS_WEIGHT + composition_score * COMPOSITION_WEIGHT
    total = max(0.0, min(100.0, total))

    return ScoreResult(
        score=round(total, 1),
        source="algorithm",
        details={
            "sharpness": round(sharpness_score, 1),
            "composition": round(composition_score, 1),
        }
    )


def score_image_ai(image_base64: str, api_url: str, api_key: str = "") -> ScoreResult:
    """使用 AI 模型评分（占位，后续实现）"""
    raise NotImplementedError("AI scoring not yet implemented")
