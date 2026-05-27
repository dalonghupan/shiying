"""主窗口 — 集成所有 UI 组件和核心逻辑"""
import cv2
import numpy as np
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QMessageBox, QDialog, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from ui.toolbar import Toolbar
from ui.sidebar import Sidebar
from ui.preview_panel import PreviewPanel
from ui.status_bar import StatusBar
from core.image_loader import ImageLoader
from core.scorer import score_image_algorithm
from core.exporter import export_images
from core.compressor import compress_images
from utils.thread_manager import ThreadPoolManager
from utils.logger import get_logger
from config import COLOR_PRIMARY, COLOR_BACKGROUND, COLOR_BORDER

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("拾影·朋友圈智能美图筛选系统")
        self.setMinimumSize(1200, 800)

        self._image_paths: list[str] = []
        self._scores: dict[str, float] = {}           # path -> score
        self._score_sources: dict[str, str] = {}      # path -> "algorithm" / "ai"
        self._current_mode = "algorithm"
        self._filter_total = 0
        self._filter_completed = 0

        self._setup_ui()
        self._connect_signals()
        self._apply_styles()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.toolbar = Toolbar()
        main_layout.addWidget(self.toolbar)

        mid_layout = QHBoxLayout()
        mid_layout.setContentsMargins(0, 0, 0, 0)

        self.sidebar = Sidebar()
        mid_layout.addWidget(self.sidebar)

        self.preview_panel = PreviewPanel()
        mid_layout.addWidget(self.preview_panel, 1)

        main_layout.addLayout(mid_layout, 1)

        self.status_bar = StatusBar()
        main_layout.addWidget(self.status_bar)

        self.loader = ImageLoader()
        self.thread_pool = ThreadPoolManager()

    def _connect_signals(self):
        self.toolbar.directory_selected.connect(self._on_directory_selected)
        self.toolbar.filter_clicked.connect(self._on_filter_clicked)
        self.toolbar.export_clicked.connect(self._on_export_clicked)
        self.toolbar.compress_clicked.connect(self._on_compress_clicked)
        self.toolbar.select_all_clicked.connect(self._on_select_all)
        self.toolbar.sort_clicked.connect(self._on_sort)

        self.loader.thumbnail_ready.connect(self._on_thumbnail_ready)
        self.loader.batch_loaded.connect(self._on_batch_loaded)
        self.loader.all_loaded.connect(self._on_all_loaded)

        self.sidebar.threshold_changed.connect(self._on_threshold_changed)
        self.sidebar.mode_changed.connect(self._on_mode_changed)
        self.sidebar.test_connection_clicked.connect(self._test_ai_connection)

        self.preview_panel.selection_changed.connect(self._update_stats)
        self.preview_panel.image_double_clicked.connect(self._show_preview)
        self.sidebar.stat_clicked.connect(self._on_stat_clicked)

    def _on_directory_selected(self, dir_path: str):
        self.preview_panel.clear()
        self._image_paths.clear()
        self._scores.clear()
        self._score_sources.clear()
        self.toolbar.enable_export(False)
        self.status_bar.set_status(f"正在加载: {dir_path}")
        self.loader.load_directory(dir_path)

    def _on_thumbnail_ready(self, path: str, pixmap: QPixmap):
        self._image_paths.append(path)
        self.preview_panel.add_image(path, pixmap)

    def _on_batch_loaded(self, count: int):
        self.status_bar.show_progress(count, self.loader.total_count)

    def _on_all_loaded(self):
        self.preview_panel.finalize_layout()
        self.status_bar.set_status(f"加载完成，共 {len(self._image_paths)} 张图片")
        self.status_bar.hide_progress()
        self.toolbar.enable_export(False)
        self.toolbar.enable_compress(False)
        self._update_stats()

    def _on_filter_clicked(self):
        if not self._image_paths:
            return
        self.toolbar.set_filter_running(True)
        self.toolbar.enable_export(False)
        self.status_bar.set_status("正在筛选...")
        if self._current_mode == "algorithm":
            self._filter_algorithm()
        else:
            self._filter_ai()

    def _filter_algorithm(self):
        self._filter_total = len(self._image_paths)
        self._filter_completed = 0

        def process_image(path: str) -> tuple[str, float]:
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                return path, 0.0
            result = score_image_algorithm(img)
            return path, result.score

        for i, path in enumerate(self._image_paths):
            worker = self.thread_pool.submit(process_image, path)
            worker.signals.result.connect(self._on_score_result)

    def _filter_ai(self):
        """AI 模型筛选"""
        import asyncio
        from core.ai_agent import AIAgent, AIConfig

        api_url = self.sidebar.get_api_url()
        api_key = self.sidebar.get_api_key()
        model_name = self.sidebar.get_model_name()

        if not api_url or not api_url.startswith(("http://", "https://")):
            QMessageBox.warning(self, "配置错误", "请先配置有效的 AI 模型接口地址（以 http:// 或 https:// 开头）")
            return

        if "/chat/completions" not in api_url and "/v1/" not in api_url:
            QMessageBox.warning(self, "配置错误", "接口地址格式不正确，应包含 /v1/chat/completions\n\n示例：https://api.deepseek.com/v1/chat/completions")
            return

        if not model_name:
            QMessageBox.warning(self, "配置错误", "请填写模型名称（如 deepseek-chat）")
            return

        config = AIConfig(api_url=api_url, api_key=api_key, model_name=model_name)
        agent = AIAgent(config)
        total = len(self._image_paths)
        self._ai_completed = 0
        consecutive_errors = 0

        async def run_ai_scoring():
            nonlocal consecutive_errors
            for path in self._image_paths:
                try:
                    result = await agent.score_image(path)
                    self._scores[path] = result["score"]
                    self._score_sources[path] = "ai"
                    threshold = self.sidebar.threshold_slider.value()
                    self.preview_panel.update_score(path, result["score"], "ai", threshold)
                    consecutive_errors = 0
                except Exception as e:
                    self._scores[path] = 0.0
                    self._score_sources[path] = "ai"
                    threshold = self.sidebar.threshold_slider.value()
                    self.preview_panel.update_score(path, 0.0, "ai(error)", threshold)
                    consecutive_errors += 1
                    logger.error("AI 评分失败: %s — %s", path, e, exc_info=True)
                    # 连续失败 3 次，停止筛选
                    if consecutive_errors >= 3:
                        logger.warning("连续 %d 次评分失败，停止筛选", consecutive_errors)
                        raise RuntimeError(f"连续 {consecutive_errors} 次评分失败，可能是模型配置错误: {e}")
                finally:
                    self._ai_completed += 1
                    self.status_bar.show_progress(self._ai_completed, total)
            await agent.close()
            self._update_stats()
            self.toolbar.set_filter_running(False)
            self.toolbar.enable_export(True)
            self.toolbar.enable_compress(True)
            self.status_bar.set_status(f"AI 筛选完成，共 {total} 张图片")

        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(run_ai_scoring())
            except Exception as e:
                loop.run_until_complete(agent.close())
                raise e

        worker = self.thread_pool.submit(run_async)
        worker.signals.error.connect(lambda err: (
            logger.error("AI 筛选线程异常: %s", err),
            QMessageBox.critical(self, "AI 筛选出错", f"筛选中断：{err}\n\n请检查模型配置是否正确。"),
            self.status_bar.set_status("AI 筛选出错"),
            self.toolbar.set_filter_running(False),
        ))

    def _on_score_result(self, result: tuple[str, float]):
        path, score = result
        self._scores[path] = score
        self._score_sources[path] = "algorithm"
        threshold = self.sidebar.threshold_slider.value()
        self.preview_panel.update_score(path, score, "algorithm", threshold)
        self._filter_completed += 1
        self.status_bar.show_progress(self._filter_completed, self._filter_total)
        self._update_stats()
        if self._filter_completed >= self._filter_total:
            self.toolbar.set_filter_running(False)
            self.toolbar.enable_export(True)
            self.toolbar.enable_compress(True)
            self.status_bar.set_status(f"筛选完成，共 {self._filter_total} 张图片")
            self.status_bar.hide_progress()

    def _on_threshold_changed(self, threshold: int):
        self.preview_panel.refresh_borders(threshold)
        self._update_stats()

    def _on_mode_changed(self, mode: str):
        self._current_mode = mode
        self.status_bar.set_status(f"已切换到{'基础算法' if mode == 'algorithm' else 'AI 大模型'}模式")

    def _on_select_all(self):
        self.preview_panel.toggle_select_all()
        self._update_stats()

    def _on_sort(self):
        self.preview_panel.sort_by_score(self.toolbar.sort_descending)

    def _on_compress_clicked(self):
        selected = self.preview_panel.get_selected_paths()
        if not selected:
            QMessageBox.information(self, "提示", "请先选择要压缩的图片")
            return

        from PyQt6.QtWidgets import QFileDialog
        dst_dir = QFileDialog.getExistingDirectory(self, "选择压缩输出目录")
        if not dst_dir:
            return

        quality = self.sidebar.get_compress_quality()
        max_size_kb = self.sidebar.get_compress_max_size_kb()

        self.toolbar.enable_compress(False)
        self.toolbar.enable_export(False)
        self.status_bar.set_status("正在压缩...")

        result = compress_images(selected, dst_dir, quality, max_size_kb,
                                 lambda c, t: self.status_bar.show_progress(c, t))
        logger.info("压缩完成: 成功 %d, 跳过 %d, 失败 %d",
                     result['success'], result['skipped'], result['failed'])
        self.toolbar.enable_compress(True)
        self.toolbar.enable_export(True)
        self.status_bar.set_status(f"压缩完成: 成功 {result['success']}, 跳过 {result['skipped']}, 失败 {result['failed']}")
        self.status_bar.hide_progress()

    def _on_export_clicked(self):
        selected = self.preview_panel.get_selected_paths()
        if not selected:
            QMessageBox.information(self, "提示", "请先选择要导出的图片")
            return

        from PyQt6.QtWidgets import QFileDialog
        dst_dir = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if not dst_dir:
            return

        self.toolbar.enable_export(False)
        self.status_bar.set_status("正在导出...")
        result = export_images(selected, dst_dir, lambda c, t: self.status_bar.show_progress(c, t))
        logger.info("导出完成: 成功 %d, 跳过 %d, 失败 %d", result['success'], result['skipped'], result['failed'])
        self.toolbar.enable_export(True)
        self.status_bar.set_status(f"导出完成: 成功 {result['success']}, 跳过 {result['skipped']}, 失败 {result['failed']}")

    def _test_ai_connection(self):
        """测试 AI 模型连接"""
        import asyncio
        from core.ai_agent import AIAgent, AIConfig

        api_url = self.sidebar.get_api_url()
        api_key = self.sidebar.get_api_key()

        if not api_url or not api_url.startswith(("http://", "https://")):
            QMessageBox.warning(self, "配置错误", "请填写有效的接口地址（以 http:// 或 https:// 开头）")
            return

        if "/chat/completions" not in api_url and "/v1/" not in api_url:
            QMessageBox.warning(self, "配置错误", "接口地址格式不正确，应包含 /v1/chat/completions\n\n示例：https://api.deepseek.com/v1/chat/completions")
            return

        model_name = self.sidebar.get_model_name()
        self.status_bar.set_status("正在测试连接...")

        config = AIConfig(api_url=api_url, api_key=api_key, model_name=model_name or "deepseek-chat")
        agent = AIAgent(config)

        def test():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(agent.test_connection())
            except Exception:
                return False
            finally:
                loop.run_until_complete(agent.close())

        worker = self.thread_pool.submit(test)
        worker.signals.result.connect(
            lambda ok: (
                QMessageBox.information(self, "连接测试", "连接成功!" if ok else "连接失败，请检查配置"),
                self.status_bar.set_status("就绪"),
            )
        )
        worker.signals.error.connect(lambda err: (
            logger.error("AI 连接测试异常: %s", err),
            QMessageBox.warning(self, "连接测试", f"连接异常: {err}"),
            self.status_bar.set_status("就绪"),
        ))

    def _show_preview(self, image_path: str):
        """双击图片弹出大图预览"""
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(image_path.split("/")[-1])
        dialog.setMinimumSize(800, 600)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scaled = pixmap.scaled(
            dialog.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        label.setPixmap(scaled)
        layout.addWidget(label)

        dialog.exec()

    def _on_stat_clicked(self, stat_type: str):
        """点击统计信息筛选显示对应图片"""
        if stat_type == "total":
            self.preview_panel.show_all()
            self.status_bar.set_status("显示全部图片")
        elif stat_type == "selected":
            self.preview_panel.show_only_selected()
            count = len(self.preview_panel.get_selected_paths())
            self.status_bar.set_status(f"筛选已选择: {count} 张")
        elif stat_type == "above_threshold":
            threshold = self.sidebar.threshold_slider.value()
            self.preview_panel.show_only_above_threshold(threshold)
            count = sum(1 for s in self._scores.values() if s >= threshold)
            self.status_bar.set_status(f"筛选高于阈值({threshold}): {count} 张")

    def _update_stats(self):
        total = len(self._image_paths)
        selected = len(self.preview_panel.get_selected_paths())
        scored = [s for s in self._scores.values() if s > 0]
        avg_score = sum(scored) / len(scored) if scored else 0.0
        max_score = max(scored) if scored else 0.0
        threshold = self.sidebar.threshold_slider.value()
        above_threshold = sum(1 for s in self._scores.values() if s >= threshold)
        self.sidebar.update_stats(total, selected, avg_score, max_score, above_threshold)

    def _apply_styles(self):
        pass
