from pathlib import Path
import pytest
from PIL import Image
from core.compressor import compress_images


def _create_test_image(path: Path, size=(100, 100), mode="RGB"):
    """创建测试图片"""
    img = Image.new(mode, size, color="red")
    img.save(path, "PNG")


def test_compress_images_basic(tmp_path):
    """测试基本压缩功能"""
    src_dir = tmp_path / "source"
    src_dir.mkdir()
    dst_dir = tmp_path / "dest"

    for i in range(3):
        _create_test_image(src_dir / f"photo{i}.png")

    sources = [str(src_dir / f"photo{i}.png") for i in range(3)]
    result = compress_images(sources, str(dst_dir), quality=50)

    assert result["success"] == 3
    assert result["failed"] == 0
    assert result["skipped"] == 0

    for i in range(3):
        out = dst_dir / f"small_photo{i}.png"
        assert out.exists()
        assert out.stat().st_size > 0


def test_compress_images_prefix(tmp_path):
    """压缩后文件名应有 small_ 前缀"""
    src_dir = tmp_path / "source"
    src_dir.mkdir()
    dst_dir = tmp_path / "dest"

    _create_test_image(src_dir / "vacation.jpg")

    result = compress_images([str(src_dir / "vacation.jpg")], str(dst_dir))
    assert result["success"] == 1
    assert (dst_dir / "small_vacation.jpg").exists()


def test_compress_images_skip_existing(tmp_path):
    """已存在的压缩文件应跳过"""
    src_dir = tmp_path / "source"
    src_dir.mkdir()
    dst_dir = tmp_path / "dest"
    dst_dir.mkdir()

    _create_test_image(src_dir / "photo.png")
    (dst_dir / "small_photo.png").write_bytes(b"existing")

    result = compress_images([str(src_dir / "photo.png")], str(dst_dir))
    assert result["skipped"] == 1
    assert (dst_dir / "small_photo.png").read_bytes() == b"existing"


def test_compress_images_quality(tmp_path):
    """低质量压缩应产生更小的文件"""
    src_dir = tmp_path / "source"
    src_dir.mkdir()

    _create_test_image(src_dir / "photo.png", size=(200, 200))

    dst_high = tmp_path / "high"
    dst_low = tmp_path / "low"

    compress_images([str(src_dir / "photo.png")], str(dst_high), quality=95)
    compress_images([str(src_dir / "photo.png")], str(dst_low), quality=10)

    size_high = (dst_high / "small_photo.png").stat().st_size
    size_low = (dst_low / "small_photo.png").stat().st_size
    assert size_low < size_high


def test_compress_images_size_limit(tmp_path):
    """按大小压缩应满足目标大小"""
    src_dir = tmp_path / "source"
    src_dir.mkdir()
    dst_dir = tmp_path / "dest"

    _create_test_image(src_dir / "photo.png", size=(300, 300))

    result = compress_images(
        [str(src_dir / "photo.png")], str(dst_dir),
        max_size_kb=10
    )
    assert result["success"] == 1
    out = dst_dir / "small_photo.png"
    assert out.exists()
    assert out.stat().st_size <= 10 * 1024


def test_compress_images_rgba(tmp_path):
    """RGBA 图片应自动转为 RGB"""
    src_dir = tmp_path / "source"
    src_dir.mkdir()
    dst_dir = tmp_path / "dest"

    _create_test_image(src_dir / "photo.png", mode="RGBA")

    result = compress_images([str(src_dir / "photo.png")], str(dst_dir))
    assert result["success"] == 1
    assert (dst_dir / "small_photo.png").exists()


def test_compress_images_progress_callback(tmp_path):
    """测试进度回调"""
    src_dir = tmp_path / "source"
    src_dir.mkdir()
    dst_dir = tmp_path / "dest"

    for i in range(5):
        _create_test_image(src_dir / f"p{i}.png")

    progress_log = []
    sources = [str(src_dir / f"p{i}.png") for i in range(5)]
    compress_images(sources, str(dst_dir), on_progress=lambda c, t: progress_log.append((c, t)))

    assert len(progress_log) == 5
    assert progress_log[-1] == (5, 5)


def test_compress_images_invalid_file(tmp_path):
    """无效文件应计入 failed"""
    dst_dir = tmp_path / "dest"
    result = compress_images(["/nonexistent/photo.jpg"], str(dst_dir))
    assert result["failed"] == 1
    assert result["success"] == 0
