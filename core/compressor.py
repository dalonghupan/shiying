"""图片压缩模块"""
from pathlib import Path
from typing import Callable
from PIL import Image
from utils.logger import get_logger

logger = get_logger(__name__)


def compress_images(
    source_paths: list[str],
    dest_dir: str,
    quality: int = 80,
    max_size_kb: int = 0,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict:
    """批量压缩图片到目标目录。

    Args:
        source_paths: 源图片路径列表
        dest_dir: 目标目录
        quality: 压缩质量 (10-95)
        max_size_kb: 目标文件大小 (KB)，0 表示仅按质量压缩
        on_progress: 进度回调 (current, total)

    Returns:
        {"success": int, "failed": int, "skipped": int}
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    result = {"success": 0, "failed": 0, "skipped": 0}
    total = len(source_paths)

    for i, src_path in enumerate(source_paths):
        try:
            src = Path(src_path)
            out_name = f"small_{src.name}"
            out_path = dest / out_name

            if out_path.exists():
                result["skipped"] += 1
                continue

            _compress_single(src, out_path, quality, max_size_kb)
            result["success"] += 1
        except Exception as e:
            logger.warning("压缩失败: %s — %s", src_path, e)
            result["failed"] += 1
        finally:
            if on_progress:
                on_progress(i + 1, total)

    return result


def _compress_single(src: Path, out: Path, quality: int, max_size_kb: int):
    """压缩单张图片。"""
    img = Image.open(src)

    # RGBA/P/LA 模式转 RGB（JPEG 不支持透明通道）
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")

    # 保存为 JPEG（统一输出格式，压缩效果最好）
    if max_size_kb > 0:
        _save_with_size_limit(img, out, max_size_kb)
    else:
        img.save(out, "JPEG", quality=quality, optimize=True)

    img.close()


def _save_with_size_limit(img: Image.Image, out: Path, max_size_kb: int):
    """按目标大小压缩，循环降低 quality 直到满足要求。"""
    q = 80
    min_q = 10

    while q >= min_q:
        img.save(out, "JPEG", quality=q, optimize=True)
        if out.stat().st_size <= max_size_kb * 1024:
            return
        q -= 10

    # 最后用最低质量保存一次
    img.save(out, "JPEG", quality=min_q, optimize=True)
