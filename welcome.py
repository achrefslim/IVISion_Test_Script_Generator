from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt
from gui import run_gui
from compare_gui import run_compare_gui
from PyQt6.QtGui import QIcon
import sys



class WelcomeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Welcome - IVISion Tools")
        self.setWindowIcon(QIcon("icon.ico"))
        self.setMinimumSize(1000, 650)
        self.setStyleSheet("""
            QWidget {
                background-color: #F0F8FF;
                font-family: Segoe UI;
                color: #003366;
            }
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #66B2FF, stop:1 #3399FF);
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 16px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5CA3E8, stop:1 #2D89D8);
            }
            QPushButton:pressed {
                background-color: #0078D7;
            }
        """)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(0)

        # Sidebar with blue background and logo
        sidebar_frame = QWidget()
        sidebar_frame.setMinimumWidth(300)
        sidebar_frame.setStyleSheet("background-color: #D6ECFF; border-radius: 10px;")

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(20, 40, 20, 40)

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap("logo.png")
        if not pix.isNull():
            logo_label.setPixmap(pix.scaled(260, 360, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation))
        else:
            logo_label.setText("LOGO\n(Missing)")
            logo_label.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sidebar_layout.addStretch()
        sidebar_layout.addWidget(logo_label)
        sidebar_layout.addStretch()
        sidebar_frame.setLayout(sidebar_layout)
        main_layout.addWidget(sidebar_frame)

        # Right side buttons section
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(60, 40, 40, 40)

        welcome_label = QLabel("Welcome to IVISion Tools")
        welcome_label.setFont(QFont('Segoe UI', 26, QFont.Weight.Bold))
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(welcome_label)
        content_layout.addSpacing(40)

        self.muster_button = QPushButton("Muster")
        self.muster_button.clicked.connect(self.open_gui)
        content_layout.addWidget(self.muster_button, alignment=Qt.AlignmentFlag.AlignCenter)

        content_layout.addSpacing(20)

        self.compare_button = QPushButton("Compare Excel Files")
        self.compare_button.clicked.connect(self.open_compare)
        content_layout.addWidget(self.compare_button, alignment=Qt.AlignmentFlag.AlignCenter)

        content_layout.addStretch()
        main_layout.addLayout(content_layout, 2)

        self.setLayout(main_layout)

    def open_gui(self):
        self.hide()
        self.gui_window = run_gui(on_back_callback=self.show)
        self.gui_window.show()


    def open_compare(self):
        self.hide()
        self.gui_window = run_compare_gui(on_back_callback=self.show)
        self.gui_window.show()
