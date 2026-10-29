from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QFileDialog, QGroupBox,
    QFrame, QSizePolicy, QSpacerItem
)
from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QTextCursor, QPixmap
from PyQt6.QtCore import Qt, QTimer
from compare_logic import compare_excels
from compare_material_logic import compare_material_excels
from PyQt6.QtWidgets import QComboBox
from PyQt6.QtGui import QIcon
import sys




class ExcelCompareGUI(QWidget):
    def __init__(self, on_back_callback=None):
        super().__init__()
        self.setWindowTitle("Compare Excel Connections")
        self.setWindowIcon(QIcon("icon.ico"))
        self.setMinimumSize(1100, 700)
        self.on_back_callback = on_back_callback
        self.init_ui()
        self.setup_theme()

    def setup_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #F0F8FF;
                color: #003366;
                font-family: Segoe UI;
            }
            QGroupBox {
                border: 1px solid #B0E0E6;
                border-radius: 10px;
                margin-top: 15px;
                padding: 15px;
                background-color: rgba(255, 255, 255, 0.9);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                font-weight: bold;
                color: #0066CC;
            }
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #66B2FF, stop:1 #3399FF);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5CA3E8, stop:1 #2D89D8);
            }
            QPushButton:pressed {
                background-color: #0078D7;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #B0E0E6;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QTextEdit {
                background-color: #122340;
                border: 1px solid #66B2FF;
                border-radius: 6px;
                color: #A9D1FF;
                font-family: Consolas;
                font-size: 12px;
            }
        """)

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # Sidebar with logo
        sidebar = QVBoxLayout()
        sidebar_frame = QWidget()
        sidebar_frame.setStyleSheet("background-color: #D6ECFF; border-radius: 0px;")
        sidebar_frame.setMinimumWidth(260)
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(20, 40, 20, 40)

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap("logo.png")
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaled(220, 300, Qt.AspectRatioMode.KeepAspectRatio,
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

        # Right content area
        content_layout = QVBoxLayout()

        # Title
        title_label = QLabel("Excel Connection Comparator")
        title_label.setFont(QFont('Segoe UI', 24, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #0066CC;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title_label)

        # File selection area
        file_group = QGroupBox("Select Excel Files")
        file_layout = QVBoxLayout()

        self.file1_input = QLineEdit()
        btn1 = QPushButton("Browse File 1")
        btn1.clicked.connect(lambda: self.browse_file(self.file1_input))
        row1 = QHBoxLayout()
        row1.addWidget(self.file1_input)
        row1.addWidget(btn1)

        self.file2_input = QLineEdit()
        btn2 = QPushButton("Browse File 2")
        btn2.clicked.connect(lambda: self.browse_file(self.file2_input))
        row2 = QHBoxLayout()
        row2.addWidget(self.file2_input)
        row2.addWidget(btn2)

        file_layout.addLayout(row1)
        file_layout.addLayout(row2)
        file_group.setLayout(file_layout)
        content_layout.addWidget(file_group)

        # Compare Mode Selection
        self.compare_mode = QComboBox()
        self.compare_mode.addItems(["Compare Connection", "Compare Material"])
        self.compare_mode.setStyleSheet("padding: 6px; font-size: 14px;")
        content_layout.addWidget(self.compare_mode)

        # Compare button
        compare_button = QPushButton("🔍 Compare")
        compare_button.clicked.connect(self.compare)
        content_layout.addWidget(compare_button, alignment=Qt.AlignmentFlag.AlignCenter)


        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        content_layout.addWidget(self.log_output)

        # Back button
        back_button = QPushButton("← Back")
        back_button.clicked.connect(self.go_back)
        content_layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignLeft)

        main_layout.addLayout(content_layout, stretch=1)

    def browse_file(self, target):
        path, _ = QFileDialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx *.xls)")
        if path:
            target.setText(path)

    def append_log(self, text):
        cursor = self.log_output.textCursor()
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#A9D1FF"))
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text + "\n", fmt)
        self.log_output.setTextCursor(cursor)
        self.log_output.ensureCursorVisible()

    def compare(self):
        file1 = self.file1_input.text().strip()
        file2 = self.file2_input.text().strip()
        if not file1 or not file2:
            self.append_log("❌ Please select both Excel files.")
            return

        self.append_log("⏳ Comparing files...")
        QTimer.singleShot(200, lambda: self._compare_files(file1, file2))

    def _compare_files(self, file1, file2):
        mode = self.compare_mode.currentText()
        if mode == "Compare Material":
            result = compare_material_excels(file1, file2)
        else:
            result = compare_excels(file1, file2)

        
        self.append_log("\n" + result)

    def go_back(self):
        if self.on_back_callback:
            self.close()
            self.on_back_callback()


def run_compare_gui(on_back_callback=None):
    return ExcelCompareGUI(on_back_callback=on_back_callback)
