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


def calculate_composition(gray_image: np.ndarray) -> float:
    """计算图片构图分数（三分线 + 对称度）

    Args:
        gray_image: 灰度图 numpy 数组

    Returns:
        构图分数 0-100
    """
    h, w = gray_image.shape[:2]

    # 三分线交叉点
    third_h = [h // 3, 2 * h // 3]
    third_w = [w // 3, 2 * w // 3]

    # 使用边缘检测找主体区域
    edges = cv2.Canny(gray_image, 50, 150)

    # 计算主体重心
    moments = cv2.moments(edges)
    if moments["m00"] == 0:
        return 50.0  # 无明显主体，给中间分

    cx = int(moments["m10"] / moments["m00"])
    cy = int(moments["m01"] / moments["m00"])

    # 计算重心到最近三分线交叉点的距离
    min_dist = float("inf")
    for th in third_h:
        for tw in third_w:
            dist = ((cx - tw) ** 2 + (cy - th) ** 2) ** 0.5
            min_dist = min(min_dist, dist)

    # 归一化距离到 0-1（对角线长度为最大距离）
    max_dist = (w ** 2 + h ** 2) ** 0.5
    dist_score = max(0, 100 * (1 - min_dist / (max_dist * 0.5)))

    # 对称度评分
    left = edges[:, : w // 2]
    right = np.flip(edges[:, w // 2 : 2 * (w // 2)], axis=1)
    if left.shape == right.shape:
        symmetry = 100 * (1 - np.mean(np.abs(left.astype(float) - right.astype(float))) / 255)
    else:
        symmetry = 50.0

    # 综合：三分线 70% + 对称度 30%
    return dist_score * 0.7 + symmetry * 0.3
