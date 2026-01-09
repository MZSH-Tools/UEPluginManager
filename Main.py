# UE Plugin Manager 启动文件
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QFont
from Source.UI.MainWindow import MainWindow


def CheckProject() -> bool:
    """检查当前目录是否为 UE 项目"""
    CurDir = Path.cwd()
    UProjectFiles = list(CurDir.glob("*.uproject"))
    return len(UProjectFiles) > 0


def Main():
    App = QApplication(sys.argv)
    App.setFont(QFont("Microsoft YaHei", 9))

    if not CheckProject():
        QMessageBox.critical(None, "错误", "当前目录未找到 .uproject 文件\n请在 UE 项目根目录下运行本程序")
        sys.exit(1)

    Window = MainWindow()
    Window.show()
    sys.exit(App.exec())


if __name__ == "__main__":
    Main()
