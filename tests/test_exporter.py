import shutil
from pathlib import Path
import pytest
from core.exporter import export_images


def test_export_images(tmp_path):
    """测试批量导出图片"""
    src_dir = tmp_path / "source"
    src_dir.mkdir()
    dst_dir = tmp_path / "dest"

    for i in range(3):
        (src_dir / f"photo{i}.jpg").write_bytes(b"fake image data")

    sources = [str(src_dir / f"photo{i}.jpg") for i in range(3)]
    result = export_images(sources, str(dst_dir))

    assert result["success"] == 3
    assert result["failed"] == 0
    assert (dst_dir / "photo0.jpg").exists()
    assert (dst_dir / "photo1.jpg").exists()
    assert (dst_dir / "photo2.jpg").exists()


def test_export_images_skip_existing(tmp_path):
    """已存在的文件应跳过"""
    src_dir = tmp_path / "source"
    dst_dir = tmp_path / "dest"
    src_dir.mkdir()
    dst_dir.mkdir()

    (src_dir / "photo.jpg").write_bytes(b"new data")
    (dst_dir / "photo.jpg").write_bytes(b"old data")

    result = export_images([str(src_dir / "photo.jpg")], str(dst_dir))
    assert result["skipped"] == 1
    assert (dst_dir / "photo.jpg").read_bytes() == b"old data"


def test_export_images_progress_callback(tmp_path):
    """测试进度回调"""
    src_dir = tmp_path / "source"
    src_dir.mkdir()
    dst_dir = tmp_path / "dest"

    for i in range(5):
        (src_dir / f"p{i}.jpg").write_bytes(b"data")

    progress_log = []
    sources = [str(src_dir / f"p{i}.jpg") for i in range(5)]
    export_images(sources, str(dst_dir), on_progress=lambda c, t: progress_log.append((c, t)))

    assert len(progress_log) == 5
    assert progress_log[-1][0] == 5
