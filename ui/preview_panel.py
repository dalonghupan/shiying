"""图片网格预览面板"""
from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QCheckBox, QVBoxLayout, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QPixmap, QMouseEvent, QResizeEvent
from config import COLOR_SCORE_HIGH


class ImageCard(QWidget):
    """单张图片卡片"""
    toggled = pyqtSignal(str, bool)
    double_clicked = pyqtSignal(str)

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

    def set_score(self, score: float, source: str = "", threshold: float = 60):
        self._score = score
        self._source = source
        source_text = f"[{source}] " if source else ""
        self.score_label.setText(f"{source_text}{score:.1f} 分")
        self.update_border(threshold)

    def update_border(self, threshold: float = 60):
        if self._score >= threshold:
            self.image_label.setStyleSheet(f"border: 2px solid {COLOR_SCORE_HIGH}; border-radius: 4px;")
        else:
            self.image_label.setStyleSheet("")

    def _on_toggled(self, state):
        self.toggled.emit(self.image_path, state == 2)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.double_clicked.emit(self.image_path)

    @property
    def is_selected(self) -> bool:
        return self.checkbox.isChecked()


class PreviewPanel(QWidget):
    """图片预览面板"""
    selection_changed = pyqtSignal()
    image_double_clicked = pyqtSignal(str)

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
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.grid_widget)
        self.grid_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        layout.addWidget(self.scroll_area)

    def add_image(self, image_path: str, pixmap: QPixmap):
        card = ImageCard(image_path, pixmap)
        card.toggled.connect(self._on_card_toggled)
        card.double_clicked.connect(self.image_double_clicked.emit)
        self.cards[image_path] = card
        # 直接追加到末尾，不触发全量重排
        count = len(self.cards) - 1
        cols = max(1, self.scroll_area.width() // 280)
        row = count // cols
        col = count % cols
        self.grid_layout.addWidget(card, row, col)

    def _relayout_grid(self):
        """重新排列可见卡片到网格"""
        cols = max(1, self.scroll_area.width() // 280)
        visible_cards = [card for card in self.cards.values() if card.isVisible()]
        # 先移除所有卡片
        for card in self.cards.values():
            self.grid_layout.removeWidget(card)
        # 只排列可见卡片
        for i, card in enumerate(visible_cards):
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(card, row, col)
        for c in range(cols):
            self.grid_layout.setColumnStretch(c, 1)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        if self.cards:
            self._relayout_grid()

    def update_score(self, image_path: str, score: float, source: str = "", threshold: float = 60):
        if image_path in self.cards:
            self.cards[image_path].set_score(score, source, threshold)

    def refresh_borders(self, threshold: float):
        for card in self.cards.values():
            card.update_border(threshold)

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
        self.cards = dict(sorted_items)
        self._relayout_grid()

    def finalize_layout(self):
        """所有图片加载完成后调用一次，完成最终布局"""
        self._relayout_grid()

    def clear(self):
        self.cards.clear()
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_card_toggled(self, path: str, checked: bool):
        self.selection_changed.emit()

    def show_all(self):
        for card in self.cards.values():
            card.setVisible(True)
        self._relayout_grid()

    def show_only_selected(self):
        for card in self.cards.values():
            card.setVisible(card.is_selected)
        self._relayout_grid()

    def show_only_above_threshold(self, threshold: float):
        for card in self.cards.values():
            card.setVisible(card._score >= threshold)
        self._relayout_grid()
