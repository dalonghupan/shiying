"""图片网格预览面板"""
from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QCheckBox, QVBoxLayout, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from config import COLOR_SCORE_HIGH


class ImageCard(QWidget):
    """单张图片卡片"""
    toggled = pyqtSignal(str, bool)

    def __init__(self, image_path: str, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self._score = 0.0
        self._source = ""
        self._setup_ui(pixmap)

    def _setup_ui(self, pixmap: QPixmap):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        self.image_label = QLabel()
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(256, 256)
        layout.addWidget(self.image_label)

        self.score_label = QLabel("--")
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.score_label.setStyleSheet("font-size: 12px; color: #8E8EA0;")
        layout.addWidget(self.score_label)

        self.checkbox = QCheckBox("选择")
        self.checkbox.stateChanged.connect(self._on_toggled)
        layout.addWidget(self.checkbox)

    def set_score(self, score: float, source: str = ""):
        self._score = score
        self._source = source
        source_text = f"[{source}] " if source else ""
        self.score_label.setText(f"{source_text}{score:.1f} 分")
        if score >= 80:
            self.image_label.setStyleSheet(f"border: 2px solid {COLOR_SCORE_HIGH}; border-radius: 4px;")
        else:
            self.image_label.setStyleSheet("")

    def _on_toggled(self, state):
        self.toggled.emit(self.image_path, state == 2)

    @property
    def is_selected(self) -> bool:
        return self.checkbox.isChecked()


class PreviewPanel(QWidget):
    """图片预览面板"""
    selection_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards: dict[str, ImageCard] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(8)

        self.scroll_area.setWidget(self.grid_widget)
        layout.addWidget(self.scroll_area)

    def add_image(self, image_path: str, pixmap: QPixmap):
        card = ImageCard(image_path, pixmap)
        card.toggled.connect(self._on_card_toggled)
        self.cards[image_path] = card

        count = len(self.cards) - 1
        cols = max(1, self.scroll_area.width() // 280)
        row = count // cols
        col = count % cols
        self.grid_layout.addWidget(card, row, col)

    def update_score(self, image_path: str, score: float, source: str = ""):
        if image_path in self.cards:
            self.cards[image_path].set_score(score, source)

    def get_selected_paths(self) -> list[str]:
        return [path for path, card in self.cards.items() if card.is_selected]

    def select_above_score(self, threshold: float):
        for path, card in self.cards.items():
            card.checkbox.setChecked(card._score >= threshold)

    def select_all(self, selected: bool = True):
        for card in self.cards.values():
            card.checkbox.setChecked(selected)

    def deselect_all(self):
        self.select_all(False)

    def toggle_select_all(self):
        all_checked = all(card.is_selected for card in self.cards.values())
        self.select_all(not all_checked)

    def sort_by_score(self, descending: bool = True):
        sorted_items = sorted(
            self.cards.items(),
            key=lambda x: x[1]._score,
            reverse=descending
        )
        # 重新排列到网格
        cols = max(1, self.scroll_area.width() // 280)
        for i, (path, card) in enumerate(sorted_items):
            row = i // cols
            col = i % cols
            self.grid_layout.removeWidget(card)
            self.grid_layout.addWidget(card, row, col)

    def clear(self):
        self.cards.clear()
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_card_toggled(self, path: str, checked: bool):
        self.selection_changed.emit()
