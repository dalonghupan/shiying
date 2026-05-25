"""拾影·朋友圈智能美图筛选系统"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("拾影")
    app.setStyle("Fusion")
    qss_path = Path(__file__).parent / "assets" / "styles.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
