"""图片导出模块"""
import shutil
from pathlib import Path
from typing import Callable


def export_images(
    source_paths: list[str],
    destination_dir: str,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict:
    """批量导出图片到目标目录

    Args:
        source_paths: 源图片路径列表
        destination_dir: 目标目录路径
        on_progress: 进度回调 (当前完成数, 总数)

    Returns:
        {"success": int, "failed": int, "skipped": int}
    """
    dst = Path(destination_dir)
    dst.mkdir(parents=True, exist_ok=True)

    success = 0
    failed = 0
    skipped = 0
    total = len(source_paths)

    for i, src_path in enumerate(source_paths):
        src = Path(src_path)
        dst_file = dst / src.name

        if dst_file.exists():
            skipped += 1
        else:
            try:
                shutil.copy2(str(src), str(dst_file))
                success += 1
            except Exception:
                failed += 1

        if on_progress:
            on_progress(i + 1, total)

    return {"success": success, "failed": failed, "skipped": skipped}
