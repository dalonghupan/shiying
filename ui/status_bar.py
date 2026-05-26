"""底部状态栏"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QProgressBar, QLabel
from PyQt6.QtCore import Qt


class StatusBar(QWidget):
    """底部状态栏"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)

        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(300)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        layout.addStretch()

    def set_status(self, text: str):
        self.status_label.setText(text)

    def show_progress(self, current: int, total: int):
        self.progress_bar.show()
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        if current >= total:
            self.progress_bar.hide()

    def hide_progress(self):
        self.progress_bar.hide()
