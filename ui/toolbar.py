"""顶部工具栏"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QFileDialog
from PyQt6.QtCore import pyqtSignal


class Toolbar(QWidget):
    """顶部工具栏"""

    directory_selected = pyqtSignal(str)
    filter_clicked = pyqtSignal()
    export_clicked = pyqtSignal()
    mode_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_dir = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self.dir_btn = QPushButton("选择目录")
        self.dir_btn.clicked.connect(self._select_directory)
        layout.addWidget(self.dir_btn)

        self.dir_label = QLabel("未选择目录")
        self.dir_label.setStyleSheet("color: #888; padding: 0 8px;")
        layout.addWidget(self.dir_label)

        layout.addStretch()

        self.filter_btn = QPushButton("开始筛选")
        self.filter_btn.setEnabled(False)
        self.filter_btn.clicked.connect(self.filter_clicked.emit)
        layout.addWidget(self.filter_btn)

        self.export_btn = QPushButton("导出已选")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_clicked.emit)
        layout.addWidget(self.export_btn)

    def _select_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择图片目录")
        if dir_path:
            self._current_dir = dir_path
            self.dir_label.setText(dir_path)
            self.filter_btn.setEnabled(True)
            self.directory_selected.emit(dir_path)

    def enable_export(self, enabled: bool):
        self.export_btn.setEnabled(enabled)

    @property
    def current_directory(self) -> str:
        return self._current_dir
