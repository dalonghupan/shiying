"""图片网格预览面板"""
from PyQt6.QtWidgets import (
    QWidget, QLabel, QCheckBox, QVBoxLayout, QScrollArea, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QPixmap, QMouseEvent, QResizeEvent
from config import COLOR_SCORE_HIGH


class ImageCard(QWidget):
    """单张图片卡片"""
    toggled = pyqtSignal(str, bool)
    double_clicked = pyqtSignal(str)

    def __init__(self, image_path: str, pixmap: QPixmap, index: int = 0, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self._score = 0.0
        self._source = ""
        self._setup_ui(pixmap, index)

    def _setup_ui(self, pixmap: QPixmap, index: int = 0):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        self.image_label = QLabel()
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(256, 256)
        layout.addWidget(self.image_label)

        self.index_label = QLabel(str(index), self.image_label)
        self.index_label.setStyleSheet(
            "background: rgba(0,0,0,120); color: white; font-size: 11px; "
            "padding: 1px 4px; border-radius: 3px;"
        )
        self.index_label.move(4, 4)
        self.index_label.adjustSize()

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
        self.grid_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        self.scroll_area.setWidget(self.grid_widget)
        layout.addWidget(self.scroll_area)

    def add_image(self, image_path: str, pixmap: QPixmap):
        index = len(self.cards) + 1
        card = ImageCard(image_path, pixmap, index=index, parent=self.grid_widget)
        card.toggled.connect(self._on_card_toggled)
        card.double_clicked.connect(self.image_double_clicked.emit)
        self.cards[image_path] = card
        # 只定位新卡片（O(1)），不做全量重排
        self._place_card(card, index - 1)

    # 卡片固定尺寸（256 图片 + 4px*2 边距 = 264 宽；256 图片 + score + checkbox + spacing + margins ≈ 300 高）
    CARD_W = 264
    CARD_H = 300
    SPACING = 8

    def _place_card(self, card: QWidget, index: int):
        """定位单张卡片到网格位置，同时更新布局"""
        card.show()
        self._relayout_grid()

    def _relayout_grid(self):
        """重新排列可见卡片到网格（手动定位）"""
        visible_cards = [card for card in self.cards.values() if card.isVisible()]
        if not visible_cards:
            return

        spacing = self.SPACING
        card_w = self.CARD_W
        card_h = self.CARD_H
        viewport_w = self.scroll_area.viewport().width()
        cols = max(1, (viewport_w + spacing) // (card_w + spacing))

        for i, card in enumerate(visible_cards):
            row = i // cols
            col = i % cols
            x = spacing + col * (card_w + spacing)
            y = spacing + row * (card_h + spacing)
            card.setGeometry(x, y, card_w, card_h)

        # 计算 grid_widget 所需高度
        rows = (len(visible_cards) + cols - 1) // cols
        total_h = spacing + rows * (card_h + spacing) + spacing
        self.grid_widget.setFixedHeight(total_h)
        self.grid_widget.setMinimumWidth(spacing + cols * (card_w + spacing))

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
        # 立即隐藏并标记删除所有子 widget
        for child in self.grid_widget.findChildren(QWidget):
            child.hide()
            child.deleteLater()
        self.grid_widget.setFixedHeight(0)

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
