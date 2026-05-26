"""主窗口 — 集成所有 UI 组件和核心逻辑"""
import cv2
import numpy as np
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from ui.toolbar import Toolbar
from ui.sidebar import Sidebar
from ui.preview_panel import PreviewPanel
from ui.status_bar import StatusBar
from core.image_loader import ImageLoader
from core.scorer import score_image_algorithm
from core.exporter import export_images
from utils.thread_manager import ThreadPoolManager
from config import COLOR_PRIMARY, COLOR_BACKGROUND, COLOR_BORDER


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("拾影·朋友圈智能美图筛选系统")
        self.setMinimumSize(1200, 800)

        self._image_paths: list[str] = []
        self._scores: dict[str, float] = {}
        self._current_mode = "algorithm"

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

        self.loader.thumbnail_ready.connect(self._on_thumbnail_ready)
        self.loader.batch_loaded.connect(self._on_batch_loaded)
        self.loader.all_loaded.connect(self._on_all_loaded)

        self.sidebar.threshold_changed.connect(self._on_threshold_changed)
        self.sidebar.mode_changed.connect(self._on_mode_changed)
        self.sidebar.test_connection_clicked.connect(self._test_ai_connection)

        self.preview_panel.selection_changed.connect(self._update_stats)

    def _on_directory_selected(self, dir_path: str):
        self.preview_panel.clear()
        self._image_paths.clear()
        self._scores.clear()
        self.status_bar.set_status(f"正在加载: {dir_path}")
        self.loader.load_directory(dir_path)

    def _on_thumbnail_ready(self, path: str, pixmap: QPixmap):
        self._image_paths.append(path)
        self.preview_panel.add_image(path, pixmap)

    def _on_batch_loaded(self, count: int):
        self.status_bar.show_progress(count, self.loader.total_count)

    def _on_all_loaded(self):
        self.status_bar.set_status(f"加载完成，共 {len(self._image_paths)} 张图片")
        self.status_bar.hide_progress()
        self.toolbar.enable_export(False)
        self._update_stats()

    def _on_filter_clicked(self):
        if not self._image_paths:
            return
        self.status_bar.set_status("正在筛选...")
        if self._current_mode == "algorithm":
            self._filter_algorithm()
        else:
            self._filter_ai()

    def _filter_algorithm(self):
        total = len(self._image_paths)

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

        if not api_url:
            QMessageBox.warning(self, "配置错误", "请先配置 AI 模型接口地址")
            return

        config = AIConfig(api_url=api_url, api_key=api_key)
        agent = AIAgent(config)
        total = len(self._image_paths)
        self._ai_completed = 0

        async def run_ai_scoring():
            for path in self._image_paths:
                try:
                    result = await agent.score_image(path)
                    self._scores[path] = result["score"]
                    self.preview_panel.update_score(path, result["score"], "ai")
                except Exception as e:
                    self._scores[path] = 0.0
                    self.preview_panel.update_score(path, 0.0, "ai(error)")
                finally:
                    self._ai_completed += 1
                    self.status_bar.show_progress(self._ai_completed, total)
            await agent.close()
            self._update_stats()
            self.status_bar.set_status(f"AI 筛选完成，共 {total} 张图片")

        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_ai_scoring())

        worker = self.thread_pool.submit(run_async)
        worker.signals.error.connect(lambda err: self.status_bar.set_status(f"AI 筛选出错: {err}"))

    def _on_score_result(self, result: tuple[str, float]):
        path, score = result
        self._scores[path] = score
        source = "algorithm" if self._current_mode == "algorithm" else "ai"
        self.preview_panel.update_score(path, score, source)
        self._update_stats()

    def _on_threshold_changed(self, threshold: int):
        self.preview_panel.select_above_score(threshold)
        self._update_stats()

    def _on_mode_changed(self, mode: str):
        self._current_mode = mode
        self.status_bar.set_status(f"已切换到{'基础算法' if mode == 'algorithm' else 'AI 大模型'}模式")

    def _on_export_clicked(self):
        selected = self.preview_panel.get_selected_paths()
        if not selected:
            QMessageBox.information(self, "提示", "请先选择要导出的图片")
            return

        from PyQt6.QtWidgets import QFileDialog
        dst_dir = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if not dst_dir:
            return

        self.status_bar.set_status("正在导出...")
        result = export_images(selected, dst_dir, lambda c, t: self.status_bar.show_progress(c, t))
        self.status_bar.set_status(f"导出完成: 成功 {result['success']}, 跳过 {result['skipped']}, 失败 {result['failed']}")

    def _test_ai_connection(self):
        """测试 AI 模型连接"""
        import asyncio
        from core.ai_agent import AIAgent, AIConfig

        api_url = self.sidebar.get_api_url()
        api_key = self.sidebar.get_api_key()

        if not api_url:
            QMessageBox.warning(self, "配置错误", "请先填写接口地址")
            return

        config = AIConfig(api_url=api_url, api_key=api_key)
        agent = AIAgent(config)

        def test():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(agent.test_connection())

        worker = self.thread_pool.submit(test)
        worker.signals.result.connect(
            lambda ok: QMessageBox.information(self, "连接测试", "连接成功!" if ok else "连接失败，请检查配置")
        )

    def _update_stats(self):
        total = len(self._image_paths)
        selected = len(self.preview_panel.get_selected_paths())
        scored = [s for s in self._scores.values() if s > 0]
        avg_score = sum(scored) / len(scored) if scored else 0.0
        max_score = max(scored) if scored else 0.0
        self.sidebar.update_stats(total, selected, avg_score, max_score)

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLOR_BACKGROUND};
            }}
            QPushButton {{
                background-color: {COLOR_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #E8D5E3;
            }}
            QPushButton:disabled {{
                background-color: #F0F0F0;
                color: #AAA;
            }}
            QGroupBox {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 16px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }}
        """)
