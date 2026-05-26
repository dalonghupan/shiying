"""顶部工具栏"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QFileDialog
from PyQt6.QtCore import pyqtSignal


class Toolbar(QWidget):
    """顶部工具栏"""

    directory_selected = pyqtSignal(str)
    filter_clicked = pyqtSignal()
    export_clicked = pyqtSignal()
    select_all_clicked = pyqtSignal()
    sort_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_dir = ""
        self._all_selected = False
        self._sort_desc = True
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self.dir_btn = QPushButton("选择目录")
        self.dir_btn.clicked.connect(self._select_directory)
        layout.addWidget(self.dir_btn)

        self.dir_label = QLabel("未选择目录")
        self.dir_label.setStyleSheet("color: #8E8EA0; padding: 0 8px;")
        layout.addWidget(self.dir_label)

        layout.addStretch()

        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setEnabled(False)
        self.select_all_btn.clicked.connect(self._on_select_all)
        layout.addWidget(self.select_all_btn)

        self.sort_btn = QPushButton("排序 ↓")
        self.sort_btn.setEnabled(False)
        self.sort_btn.setToolTip("点击切换升序/降序")
        self.sort_btn.clicked.connect(self._on_sort)
        layout.addWidget(self.sort_btn)

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
            self.select_all_btn.setEnabled(True)
            self.sort_btn.setEnabled(True)
            self.directory_selected.emit(dir_path)

    def _on_select_all(self):
        self._all_selected = not self._all_selected
        self.select_all_btn.setText("取消全选" if self._all_selected else "全选")
        self.select_all_clicked.emit()

    def _on_sort(self):
        self._sort_desc = not self._sort_desc
        self.sort_btn.setText("排序 ↓" if self._sort_desc else "排序 ↑")
        self.sort_clicked.emit()

    @property
    def sort_descending(self) -> bool:
        return self._sort_desc

    def enable_export(self, enabled: bool):
        self.export_btn.setEnabled(enabled)

    def reset_select_all(self):
        self._all_selected = False
        self.select_all_btn.setText("全选")

    @property
    def current_directory(self) -> str:
        return self._current_dir
