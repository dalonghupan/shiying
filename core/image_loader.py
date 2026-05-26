"""图片异步加载模块"""
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from utils.image_utils import get_image_files
from utils.cache import create_thumbnail
from utils.thread_manager import ThreadPoolManager
from config import THUMBNAIL_SIZE, THUMBNAIL_LOAD_BATCH


class ImageLoader(QObject):
    """异步图片加载器"""

    thumbnail_ready = pyqtSignal(str, QPixmap)  # (文件路径, 缩略图)
    batch_loaded = pyqtSignal(int)               # 已加载数量
    all_loaded = pyqtSignal()                    # 全部加载完成
    error_occurred = pyqtSignal(str, str)        # (文件路径, 错误信息)

    def __init__(self):
        super().__init__()
        self.thread_pool = ThreadPoolManager()
        self._image_paths: list[Path] = []
        self._loaded_count = 0

    def load_directory(self, directory: str):
        """加载目录下的所有图片"""
        self._image_paths = get_image_files(directory)
        self._loaded_count = 0
        self._load_next_batch()

    def _load_next_batch(self):
        """加载下一批图片"""
        start = self._loaded_count
        end = min(start + THUMBNAIL_LOAD_BATCH, len(self._image_paths))

        if start >= len(self._image_paths):
            self.all_loaded.emit()
            return

        batch = self._image_paths[start:end]
        for path in batch:
            worker = self.thread_pool.submit(self._load_single_image, str(path))
            worker.signals.result.connect(self._on_image_loaded)
            worker.signals.error.connect(lambda err, p=str(path): self.error_occurred.emit(p, err))

    def _load_single_image(self, image_path: str) -> tuple[str, QPixmap]:
        """在后台线程加载单张图片缩略图"""
        pil_img = create_thumbnail(image_path, THUMBNAIL_SIZE)
        pil_img = pil_img.convert("RGB")
        data = pil_img.tobytes("raw", "RGB")
        qimg = QImage(data, pil_img.width, pil_img.height, pil_img.width * 3, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        del pil_img, data, qimg  # 显式释放
        return image_path, pixmap

    def _on_image_loaded(self, result: tuple[str, QPixmap]):
        """单张图片加载完成回调"""
        path, pixmap = result
        self._loaded_count += 1
        self.thumbnail_ready.emit(path, pixmap)
        self.batch_loaded.emit(self._loaded_count)

        # 当前批次全部完成时，加载下一批
        if self._loaded_count % THUMBNAIL_LOAD_BATCH == 0:
            self._load_next_batch()
        elif self._loaded_count >= len(self._image_paths):
            self.all_loaded.emit()

    @property
    def total_count(self) -> int:
        return len(self._image_paths)
