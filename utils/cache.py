"""缩略图缓存管理"""
import hashlib
from pathlib import Path
from PIL import Image
from config import CACHE_DIR, THUMBNAIL_SIZE


def get_cache_path(image_path: str, size: tuple[int, int] = THUMBNAIL_SIZE) -> Path:
    """根据图片路径和尺寸生成缓存文件路径"""
    key = hashlib.md5(f"{image_path}{size}".encode()).hexdigest()
    return CACHE_DIR / f"{key}.jpg"


def get_cached_thumbnail(image_path: str, size: tuple[int, int] = THUMBNAIL_SIZE) -> Image.Image | None:
    """获取缓存的缩略图，不存在则返回 None"""
    cache_path = get_cache_path(image_path, size)
    if cache_path.exists():
        return Image.open(cache_path)
    return None


def save_thumbnail(image_path: str, thumbnail: Image.Image, size: tuple[int, int] = THUMBNAIL_SIZE) -> Path:
    """保存缩略图到缓存"""
    cache_path = get_cache_path(image_path, size)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    thumbnail.save(str(cache_path), "JPEG", quality=85)
    return cache_path


def create_thumbnail(image_path: str, size: tuple[int, int] = THUMBNAIL_SIZE) -> Image.Image:
    """创建缩略图（先检查缓存）"""
    cached = get_cached_thumbnail(image_path, size)
    if cached is not None:
        return cached
    img = Image.open(image_path)
    img.thumbnail(size, Image.Resampling.LANCZOS)
    # RGBA/P 模式需转 RGB 才能保存为 JPEG
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    save_thumbnail(image_path, img, size)
    return img


def clear_cache():
    """清空缓存目录"""
    if CACHE_DIR.exists():
        for f in CACHE_DIR.glob("*.jpg"):
            f.unlink()
