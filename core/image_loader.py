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
    batch_loaded = pyqtSignal(int)               # 已处理数量
    all_loaded = pyqtSignal()                    # 全部加载完成
    error_occurred = pyqtSignal(str, str)        # (文件路径, 错误信息)

    def __init__(self):
        super().__init__()
        self.thread_pool = ThreadPoolManager()
        self._image_paths: list[Path] = []
        self._processed_count = 0  # 已处理数（成功 + 失败）

    def load_directory(self, directory: str):
        """加载目录下的所有图片"""
        self._image_paths = get_image_files(directory)
        self._processed_count = 0
        if not self._image_paths:
            self.all_loaded.emit()
            return
        self._load_next_batch()

    def _load_next_batch(self):
        """加载下一批图片"""
        start = self._processed_count
        end = min(start + THUMBNAIL_LOAD_BATCH, len(self._image_paths))

        if start >= len(self._image_paths):
            self.all_loaded.emit()
            return

        batch = self._image_paths[start:end]
        for path in batch:
            worker = self.thread_pool.submit(self._load_single_image, str(path))
            worker.signals.result.connect(self._on_image_loaded)
            worker.signals.error.connect(self._on_image_error)

    def _load_single_image(self, image_path: str) -> tuple[str, QPixmap]:
        """在后台线程加载单张图片缩略图"""
        pil_img = create_thumbnail(image_path, THUMBNAIL_SIZE)
        pil_img = pil_img.convert("RGB")
        data = pil_img.tobytes("raw", "RGB")
        qimg = QImage(data, pil_img.width, pil_img.height, pil_img.width * 3, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        del pil_img, data, qimg
        return image_path, pixmap

    def _on_image_loaded(self, result: tuple[str, QPixmap]):
        """单张图片加载成功回调"""
        path, pixmap = result
        self._processed_count += 1
        self.thumbnail_ready.emit(path, pixmap)
        self.batch_loaded.emit(self._processed_count)
        self._check_batch_complete()

    def _on_image_error(self, error_msg: str):
        """单张图片加载失败回调"""
        self._processed_count += 1
        self.error_occurred.emit("", error_msg)
        self.batch_loaded.emit(self._processed_count)
        self._check_batch_complete()

    def _check_batch_complete(self):
        """检查当前批次是否完成，触发下一批"""
        if self._processed_count >= len(self._image_paths):
            self.all_loaded.emit()
        elif self._processed_count % THUMBNAIL_LOAD_BATCH == 0:
            self._load_next_batch()

    @property
    def total_count(self) -> int:
        return len(self._image_paths)
