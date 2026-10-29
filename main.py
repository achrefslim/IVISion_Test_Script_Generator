from PyQt6.QtWidgets import QApplication
from welcome import WelcomeWindow
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = WelcomeWindow()
    window.show()
    sys.exit(app.exec())
