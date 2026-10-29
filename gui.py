from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QFileDialog,
    QRadioButton, QGroupBox, QFrame, QDialog, QDialogButtonBox,
    QButtonGroup, QProgressBar, QGridLayout, QSizePolicy
)
from PyQt6.QtGui import QFont, QColor, QPalette, QTextCharFormat, QTextCursor, QPixmap
from PyQt6.QtCore import Qt, QTimer
import os

from ivs_generator import generate_complete_ivs_script
from pdf_generator import generate_ivs_from_pdf
from new_pdf_parser import generate_ivs_from_new_pdf, is_sp_table_pdf
from ivs3_generator import generate_ivs3_from_excel_or_pdf
from PyQt6.QtGui import QIcon
import sys



class IVisionGUI(QWidget):
    def __init__(self, on_back_callback=None):
        super().__init__()
        self.on_back_callback = on_back_callback
        self.setWindowTitle("IVISion Programme Generator")
        self.setWindowIcon(QIcon("icon.ico"))
        
        self.setMinimumSize(1000, 800)
        self.setAcceptDrops(True)
        self.init_ui()
        self.setup_theme()
        self.progress_value = 0

    def setup_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #F0F8FF;
                color: #003366;
                font-family: Segoe UI;
            }
            QGroupBox {
                border: 1px solid #B0E0E6;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 20px;
                background-color: rgba(255, 255, 255, 180);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                font-weight: bold;
                color: #0066CC;
            }
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #66B2FF, stop:1 #3399FF);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                min-width: 100px;
                font-weight: bold;
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
                padding: 6px;
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
            QProgressBar {
                border: 1px solid #66B2FF;
                border-radius: 6px;
                text-align: center;
                background-color: #E6F2FF;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #66B2FF, stop:1 #3399FF);
                border-radius: 5px;
            }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith((".xls", ".xlsx", ".pdf")):
                self.file_input.setText(file_path)
                base = os.path.splitext(os.path.basename(file_path))[0]
                self.output_input.setText(os.path.join(os.path.dirname(file_path), f"{base}_ivs_script.ivs"))
                is_pdf = file_path.lower().endswith(".pdf")
                self.radio_auto.setChecked(True)
                self.radio_auto.setEnabled(not is_pdf)
                self.radio_manual.setEnabled(not is_pdf)
                self.manual_group.setVisible(False)

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar with logo
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet("background-color: #D6ECFF;")
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_pix = QPixmap("logo.png")
        if not logo_pix.isNull():
            self.logo_label.setPixmap(
                logo_pix.scaled(260, 380, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
        else:
            self.logo_label.setText("LOGO\n(Missing)")
            self.logo_label.setFont(QFont('Segoe UI', 18, QFont.Weight.Bold))
            self.logo_label.setStyleSheet("color: #003366;")
            self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sidebar_layout.addWidget(self.logo_label)
        sidebar_layout.addStretch()
        self.sidebar.setLayout(sidebar_layout)
        main_layout.addWidget(self.sidebar)

        # Content layout
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(20, 20, 20, 20)

        header = QHBoxLayout()
        title = QLabel("IVISion Programme Generator")
        

        title.setFont(QFont('Segoe UI', 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #0066CC;")
        header.addWidget(title)
        header.addStretch()
        version = QLabel("v2.5")
        version.setStyleSheet("color: #66B2FF; font-size: 12px;")
        header.addWidget(version)
        content_layout.addLayout(header)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setFrameShadow(QFrame.Shadow.Sunken)
        sep1.setStyleSheet("color: #66B2FF;")
        content_layout.addWidget(sep1)

        # File selection
        file_group = QGroupBox("Input File Selection")
        file_layout = QVBoxLayout()
        input_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Drag and drop or browse an Excel (.xlsx, .xls) or PDF file")
        self.file_input.setReadOnly(True)
        file_btn = QPushButton("Browse")
        file_btn.clicked.connect(self.browse_file)
        input_layout.addWidget(self.file_input)
        input_layout.addWidget(file_btn)
        file_layout.addLayout(input_layout)
        file_group.setLayout(file_layout)
        content_layout.addWidget(file_group)

        # Column detection
        mode_group = QGroupBox("Column Selection Mode (Excel only)")
        mode_layout = QHBoxLayout()
        self.radio_auto = QRadioButton("Auto detect columns")
        self.radio_manual = QRadioButton("Manual columns")
        self.radio_auto.setChecked(True)
        mode_layout.addWidget(self.radio_auto)
        mode_layout.addWidget(self.radio_manual)
        mode_group.setLayout(mode_layout)
        content_layout.addWidget(mode_group)

        # Manual columns
        self.manual_group = QGroupBox("Manual Column Selection")
        manual_layout = QVBoxLayout()
        toggle_layout = QHBoxLayout()
        toggle_layout.addWidget(QLabel("Number of columns:"))
        self.toggle_col_btn = QPushButton("Switch to 4 Columns")
        self.toggle_col_btn.clicked.connect(self.toggle_column_count)
        toggle_layout.addWidget(self.toggle_col_btn)
        toggle_layout.addStretch()
        manual_layout.addLayout(toggle_layout)

        format_info = QLabel("Supported column formats: 'von', 'nach', 'from pin', 'to device name', etc.")
        format_info.setStyleSheet("color: #003366; font-size: 12px;")
        manual_layout.addWidget(format_info)

        self.col_input_grid = QGridLayout()
        self.manual_cols_inputs = []
        for i in range(4):
            le = QLineEdit()
            le.setPlaceholderText(f"Column name {i+1}")
            le.setMinimumWidth(160)
            le.setFont(QFont('Segoe UI', 12))
            self.manual_cols_inputs.append(le)
            self.col_input_grid.addWidget(le, i // 2, i % 2)
        manual_layout.addLayout(self.col_input_grid)
        self.manual_group.setLayout(manual_layout)
        content_layout.addWidget(self.manual_group)

        self.current_col_count = 2
        self.update_manual_columns()
        self.manual_group.setVisible(False)
        self.radio_auto.toggled.connect(self.toggle_manual_inputs)
        self.toggle_manual_inputs(True)

        # Output settings
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout()
        out_path_layout = QHBoxLayout()
        self.output_input = QLineEdit()
        out_btn = QPushButton("Browse")
        out_btn.clicked.connect(self.browse_output)
        out_path_layout.addWidget(QLabel("Output IVS file:"))
        out_path_layout.addWidget(self.output_input)
        out_path_layout.addWidget(out_btn)
        output_layout.addLayout(out_path_layout)
        output_group.setLayout(output_layout)
        content_layout.addWidget(output_group)

        # Buttons
        button_layout = QHBoxLayout()
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_form)
        self.generate_btn = QPushButton("Generate IVISion Script")
        self.generate_btn.clicked.connect(self.on_generate_clicked)
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.generate_btn)
        content_layout.addLayout(button_layout)

        self.back_btn = QPushButton("⬅ Back")
        self.back_btn.clicked.connect(self.handle_back)
        button_layout.insertWidget(0, self.back_btn)  # Add to the left side


        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(True)
        self.progress.setFormat("Ready")
        content_layout.addWidget(self.progress)

        # Logs
        log_group = QGroupBox("Generation Log")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        content_layout.addWidget(log_group)

        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget)
        self.setLayout(main_layout)
    
    def handle_back(self):
        self.close()
        if self.on_back_callback:
            self.on_back_callback()


    def update_manual_columns(self):
        for i, le in enumerate(self.manual_cols_inputs):
            le.setVisible(i < self.current_col_count)

    def toggle_column_count(self):
        self.current_col_count = 4 if self.current_col_count == 2 else 2
        self.toggle_col_btn.setText(f"Switch to {2 if self.current_col_count == 4 else 4} Columns")
        self.update_manual_columns()

    def toggle_manual_inputs(self, checked):
        if self.file_input.text().lower().endswith('.pdf'):
            self.manual_group.setVisible(False)
            return
        self.manual_group.setVisible(not checked)

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Excel or PDF Files (*.xlsx *.xls *.pdf)")
        if path:
            self.file_input.setText(path)
            base = os.path.splitext(os.path.basename(path))[0]
            self.output_input.setText(os.path.join(os.path.dirname(path), f"{base}_ivs_script.ivs"))
            is_pdf = path.lower().endswith(".pdf")
            self.radio_auto.setChecked(True)
            self.radio_auto.setEnabled(not is_pdf)
            self.radio_manual.setEnabled(not is_pdf)
            self.manual_group.setVisible(False)

    def browse_output(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save IVS File", "", "IVS Files (*.ivs)")
        if path:
            self.output_input.setText(path)

    def reset_form(self):
        self.file_input.clear()
        self.output_input.clear()
        self.radio_auto.setChecked(True)
        self.radio_auto.setEnabled(True)
        self.radio_manual.setEnabled(True)
        self.current_col_count = 2
        self.toggle_col_btn.setText("Switch to 4 Columns")
        for le in self.manual_cols_inputs:
            le.clear()
        self.update_manual_columns()
        self.manual_group.setVisible(False)
        self.log_output.clear()
        self.update_progress(0, "Ready")

    def update_progress(self, val, msg=None):
        self.progress.setValue(val)
        if msg:
            self.progress.setFormat(msg)
        QApplication.processEvents()

    def append_log(self, text, level="info"):
        color = {"info": "#89CFF0", "success": "#A0E7A0", "error": "#FF6B6B"}[level]
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor = self.log_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text + "\n", fmt)
        self.log_output.setTextCursor(cursor)
        self.log_output.ensureCursorVisible()

    def on_generate_clicked(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Select IVISion Version")
        dlg.setFixedSize(300, 160)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Select which IVISion code version to generate:"))
        rb2 = QRadioButton("IVISion Studio")
        rb3 = QRadioButton("IVISion 3")
        rb2.setChecked(True)
        group = QButtonGroup(dlg)
        group.addButton(rb2)
        group.addButton(rb3)
        layout.addWidget(rb2)
        layout.addWidget(rb3)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)
        dlg.setLayout(layout)
        if dlg.exec():
            self.generate_script(ivs3=rb3.isChecked())

    def generate_script(self, ivs3=False):
        path = self.file_input.text().strip()
        out = self.output_input.text().strip()
        if not path:
            self.append_log("❌ Please select a file.", "error")
            return
        if not out:
            self.append_log("❌ Please select output file.", "error")
            return
        self.update_progress(10, "Preparing...")

        QTimer.singleShot(100, lambda: self._generate(path, out, ivs3))

    def _generate(self, path, out, ivs3):
        try:
            self.append_log("⏳ Generating IVISion script...")
            self.update_progress(30, "Processing...")

            manual_cols = None
            if not path.lower().endswith(".pdf") and self.radio_manual.isChecked():
                manual_cols = []
                for i in range(self.current_col_count):
                    col = self.manual_cols_inputs[i].text().strip()
                    if not col:
                        self.append_log(f"❌ Column {i+1} is empty", "error")
                        return
                    manual_cols.append(col)

            if ivs3:
                result = generate_ivs3_from_excel_or_pdf(path, out, manual_cols)
            else:
                if path.lower().endswith(".pdf"):
                    if is_sp_table_pdf(path):
                        result = generate_ivs_from_new_pdf(path, out)
                    else:
                        result = generate_ivs_from_pdf(path, out)
                else:
                    result = generate_complete_ivs_script(path, out, manual_cols)

            self.append_log(result, "success" if result.startswith("✅") else "error")
            if result.startswith("✅"):
                self.append_log("🛠 Generated using IVISion " + ("3" if ivs3 else "Studio"), "info")

            self.update_progress(100, "Done")
            QTimer.singleShot(3000, lambda: self.update_progress(0, "Ready"))

        except Exception as e:
            self.append_log(f"❌ Error: {e}", "error")
            self.update_progress(0, "Error")


def run_gui(on_back_callback=None):
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#F0F8FF"))
    gui = IVisionGUI(on_back_callback=on_back_callback)
    gui.show()
    return gui


