# UE Plugin Manager 启动文件
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from Source.UI.MainWindow import MainWindow


def Main():
    App = QApplication(sys.argv)
    Window = MainWindow()
    Window.show()
    sys.exit(App.exec())


if __name__ == "__main__":
    Main()
