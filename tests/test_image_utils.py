import pytest
from utils.image_utils import is_supported_image, get_image_files


def test_is_supported_image_jpg():
    assert is_supported_image("/path/to/photo.jpg") is True


def test_is_supported_image_png():
    assert is_supported_image("/path/to/photo.PNG") is True


def test_is_supported_image_unsupported():
    assert is_supported_image("/path/to/document.pdf") is False


def test_get_image_files(tmp_path):
    (tmp_path / "photo1.jpg").touch()
    (tmp_path / "photo2.png").touch()
    (tmp_path / "doc.txt").touch()
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "photo3.webp").touch()

    result = get_image_files(str(tmp_path))
    assert len(result) == 3
    extensions = {p.suffix.lower() for p in result}
    assert ".jpg" in extensions
    assert ".png" in extensions
    assert ".webp" in extensions
