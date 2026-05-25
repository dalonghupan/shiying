"""基础算法筛选模块"""
import cv2
import numpy as np


def calculate_sharpness(gray_image: np.ndarray) -> float:
    """计算图片清晰度（拉普拉斯方差法）

    Args:
        gray_image: 灰度图 numpy 数组

    Returns:
        清晰度分数，越高越清晰
    """
    laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
    return float(laplacian.var())
