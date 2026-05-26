"""侧边栏 — 阈值调节、模型配置、统计信息"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QLineEdit,
    QSlider, QLabel, QPushButton, QRadioButton, QComboBox
)
from PyQt6.QtCore import pyqtSignal, Qt


# 内置 AI 模型提供商配置
AI_PROVIDERS = {
    "OpenAI": {
        "url": "https://api.openai.com/v1/chat/completions",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "tip": "推荐 gpt-4o，支持图片分析"
    },
    "Anthropic": {
        "url": "https://api.anthropic.com/v1/messages",
        "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        "tip": "推荐 claude-3-opus，支持图片分析"
    },
    "Google": {
        "url": "https://generativelanguage.googleapis.com/v1beta/chat/completions",
        "models": ["gemini-pro-vision", "gemini-1.5-pro"],
        "tip": "推荐 gemini-pro-vision，支持图片分析"
    },
    "自定义": {
        "url": "",
        "models": [],
        "tip": "手动输入接口地址和模型名称"
    }
}


class Sidebar(QWidget):
    """侧边栏"""

    threshold_changed = pyqtSignal(int)
    mode_changed = pyqtSignal(str)
    test_connection_clicked = pyqtSignal()
    config_saved = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(280)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # 模式选择
        mode_group = QGroupBox("筛选模式")
        mode_layout = QVBoxLayout()
        self.mode_algorithm = QRadioButton("基础算法")
        self.mode_ai = QRadioButton("AI 大模型")
        self.mode_algorithm.setChecked(True)
        self.mode_algorithm.toggled.connect(self._on_mode_toggled)
        self.mode_ai.toggled.connect(self._on_mode_toggled)
        mode_layout.addWidget(self.mode_algorithm)
        mode_layout.addWidget(self.mode_ai)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # 阈值调节
        threshold_group = QGroupBox("筛选阈值")
        threshold_layout = QVBoxLayout()
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(0, 100)
        self.threshold_slider.setValue(60)
        self.threshold_label = QLabel("阈值: 60")
        self.threshold_slider.valueChanged.connect(self._on_threshold_changed)
        threshold_layout.addWidget(self.threshold_label)
        threshold_layout.addWidget(self.threshold_slider)
        threshold_group.setLayout(threshold_layout)
        layout.addWidget(threshold_group)

        # 模型配置
        model_group = QGroupBox("AI 模型配置")
        model_layout = QFormLayout()

        # 提供商下拉框
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(AI_PROVIDERS.keys())
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)

        # 模型下拉框
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)

        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("https://api.openai.com/v1/chat/completions")

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("sk-...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.model_tip_label = QLabel()
        self.model_tip_label.setWordWrap(True)
        self.model_tip_label.setStyleSheet("color: #8E8EA0; font-size: 11px;")

        self.test_btn = QPushButton("测试连接")
        self.test_btn.clicked.connect(self.test_connection_clicked.emit)
        self.save_btn = QPushButton("保存配置")
        self.save_btn.clicked.connect(self._save_config)

        model_layout.addRow("提供商:", self.provider_combo)
        model_layout.addRow("模型:", self.model_combo)
        model_layout.addRow("接口地址:", self.api_url_input)
        model_layout.addRow("API Key:", self.api_key_input)
        model_layout.addRow(self.model_tip_label)
        model_layout.addRow(self.test_btn)
        model_layout.addRow(self.save_btn)
        model_group.setLayout(model_layout)
        self.model_group = model_group
        layout.addWidget(model_group)
        model_group.hide()

        # 初始化默认提供商
        self._on_provider_changed("OpenAI")

        # 统计信息
        stats_group = QGroupBox("统计信息")
        stats_layout = QVBoxLayout()
        self.total_label = QLabel("总图片: 0")
        self.selected_label = QLabel("已选择: 0")
        self.above_threshold_label = QLabel("高于阈值: 0")
        self.avg_score_label = QLabel("平均分: --")
        self.max_score_label = QLabel("最高分: --")
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.selected_label)
        stats_layout.addWidget(self.above_threshold_label)
        stats_layout.addWidget(self.avg_score_label)
        stats_layout.addWidget(self.max_score_label)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        layout.addStretch()

    def _on_provider_changed(self, provider: str):
        if provider not in AI_PROVIDERS:
            return
        config = AI_PROVIDERS[provider]
        self.api_url_input.setText(config["url"])
        self.model_tip_label.setText(config["tip"])

        # 更新模型下拉框
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        self.model_combo.addItems(config["models"])
        if config["models"]:
            self.model_combo.setCurrentIndex(0)
        self.model_combo.blockSignals(False)

        # 自定义模式下允许编辑地址
        is_custom = (provider == "自定义")
        self.api_url_input.setReadOnly(False)
        self.api_url_input.setPlaceholderText(
            "手动输入接口地址" if is_custom else config["url"]
        )

    def _on_model_changed(self, model: str):
        pass

    def _on_threshold_changed(self, value):
        self.threshold_label.setText(f"阈值: {value}")
        self.threshold_changed.emit(value)

    def _on_mode_toggled(self):
        is_ai = self.mode_ai.isChecked()
        self.model_group.setVisible(is_ai)
        self.mode_changed.emit("ai" if is_ai else "algorithm")

    def _save_config(self):
        config = {
            "api_url": self.api_url_input.text().strip(),
            "api_key": self.api_key_input.text().strip(),
            "model_name": self.model_combo.currentText().strip(),
        }
        self.config_saved.emit(config)

    def get_model_name(self) -> str:
        return self.model_combo.currentText().strip()

    def update_stats(self, total: int, selected: int, avg_score: float, max_score: float, above_threshold: int = 0):
        self.total_label.setText(f"总图片: {total}")
        self.selected_label.setText(f"已选择: {selected}")
        self.above_threshold_label.setText(f"高于阈值: {above_threshold}")
        self.avg_score_label.setText(f"平均分: {avg_score:.1f}")
        self.max_score_label.setText(f"最高分: {max_score:.1f}")

    def get_api_url(self) -> str:
        return self.api_url_input.text().strip()

    def get_api_key(self) -> str:
        return self.api_key_input.text().strip()
