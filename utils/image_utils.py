"""图像处理工具函数"""
from pathlib import Path
from config import SUPPORTED_FORMATS


def is_supported_image(file_path: str) -> bool:
    """判断文件是否为支持的图片格式"""
    return Path(file_path).suffix.lower() in SUPPORTED_FORMATS


def get_image_files(directory: str) -> list[Path]:
    """递归获取目录下所有支持的图片文件，按文件名排序"""
    root = Path(directory)
    if not root.is_dir():
        return []
    files = [p for p in root.rglob("*") if p.is_file() and is_supported_image(str(p))]
    files.sort(key=lambda p: p.name)
    return files
