import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFileDialog, QFrame,
                             QSpinBox, QComboBox, QScrollArea, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontDatabase

from core.parser import parse_docx
from core.generator import generate_pptx
from ui.styles import get_stylesheet
from ui.components import PreviewSlideItemWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LiturgiSlide")
        self.resize(1100, 760)
        self.setStyleSheet(get_stylesheet())
        self.slides = []
        self.file_path = None

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Header ─────────────────────────────────────────
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(80)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(24, 16, 24, 16)
        title_label = QLabel("LiturgiSlide")
        title_label.setObjectName("AppTitle")
        subtitle_label = QLabel("Generator Slide Ibadah Semi-Otomatis – GMIM Syaloem")
        subtitle_label.setObjectName("AppSubtitle")
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        main_layout.addWidget(header)

        # ── Body ────────────────────────────────────────────
        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(24, 24, 24, 24)
        body_layout.setSpacing(24)

        # ── Left Panel (Settings & Input) ───────────────────
        left_panel = QWidget()
        left_panel.setFixedWidth(320)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(16)

        # Card: Document
        doc_card = QFrame()
        doc_card.setProperty("class", "Card")
        doc_layout = QVBoxLayout(doc_card)
        doc_layout.setSpacing(12)
        doc_title = QLabel("Dokumen Tata Ibadah")
        doc_title.setProperty("class", "SectionTitle")
        self.btn_browse = QPushButton("Pilih File Word")
        self.btn_browse.setProperty("class", "SecondaryButton")
        self.btn_browse.clicked.connect(self.browse_file)
        self.lbl_file_name = QLabel("Belum ada file dipilih")
        self.lbl_file_name.setProperty("class", "BodyText")
        self.lbl_file_name.setWordWrap(True)
        doc_layout.addWidget(doc_title)
        doc_layout.addWidget(self.btn_browse)
        doc_layout.addWidget(self.lbl_file_name)

        # Card: Settings
        set_card = QFrame()
        set_card.setProperty("class", "Card")
        set_layout = QVBoxLayout(set_card)
        set_layout.setSpacing(10)

        set_title = QLabel("Pengaturan Slide")
        set_title.setProperty("class", "SectionTitle")
        set_layout.addWidget(set_title)

        # Max lines
        lbl_lines = QLabel("Max baris per slide:")
        lbl_lines.setProperty("class", "BodyText")
        self.spin_lines = QSpinBox()
        self.spin_lines.setRange(1, 15)
        self.spin_lines.setValue(6)
        set_layout.addWidget(lbl_lines)
        set_layout.addWidget(self.spin_lines)

        # Font Family
        lbl_font = QLabel("Font:")
        lbl_font.setProperty("class", "BodyText")
        self.combo_font = QComboBox()
        db = QFontDatabase()
        families = db.families()
        self.combo_font.addItems(families)
        if "Segoe UI" in families:
            self.combo_font.setCurrentText("Segoe UI")
        elif "Arial" in families:
            self.combo_font.setCurrentText("Arial")
        set_layout.addWidget(lbl_font)
        set_layout.addWidget(self.combo_font)

        # --- Font Size Controls ---
        lbl_fs_title = QLabel("Ukuran font judul (Bagian/Cover):")
        lbl_fs_title.setProperty("class", "BodyText")
        self.spin_font_title = QSpinBox()
        self.spin_font_title.setRange(10, 150)
        self.spin_font_title.setValue(60)
        set_layout.addWidget(lbl_fs_title)
        set_layout.addWidget(self.spin_font_title)

        lbl_fs_lyric = QLabel("Ukuran font lirik lagu:")
        lbl_fs_lyric.setProperty("class", "BodyText")
        self.spin_font_lyric = QSpinBox()
        self.spin_font_lyric.setRange(10, 150)
        self.spin_font_lyric.setValue(48)
        set_layout.addWidget(lbl_fs_lyric)
        set_layout.addWidget(self.spin_font_lyric)

        lbl_fs_liturgi = QLabel("Ukuran font liturgi/bacaan:")
        lbl_fs_liturgi.setProperty("class", "BodyText")
        self.spin_font_liturgi = QSpinBox()
        self.spin_font_liturgi.setRange(10, 150)
        self.spin_font_liturgi.setValue(40)
        set_layout.addWidget(lbl_fs_liturgi)
        set_layout.addWidget(self.spin_font_liturgi)

        # --- Transition ---
        lbl_trans = QLabel("Efek Transisi Slide:")
        lbl_trans.setProperty("class", "BodyText")
        self.combo_transition = QComboBox()
        self.combo_transition.addItems([
            "Tanpa Transisi",
            "Fade",
            "Wipe (Kiri ke Kanan)",
            "Push (Kiri ke Kanan)",
            "Zoom",
        ])
        set_layout.addWidget(lbl_trans)
        set_layout.addWidget(self.combo_transition)

        left_layout.addWidget(doc_card)
        left_layout.addWidget(set_card)
        left_layout.addStretch()

        # ── Right Panel (Preview) ───────────────────────────
        right_panel = QFrame()
        right_panel.setProperty("class", "Card")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(16)
        preview_title = QLabel("Preview Slide")
        preview_title.setProperty("class", "SectionTitle")
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.preview_container = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_container)
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_layout.setSpacing(12)
        self.preview_layout.addStretch()
        self.scroll_area.setWidget(self.preview_container)
        right_layout.addWidget(preview_title)
        right_layout.addWidget(self.scroll_area)

        body_layout.addWidget(left_panel)
        body_layout.addWidget(right_panel)
        main_layout.addWidget(body_widget, stretch=1)

        # ── Footer / Actions ────────────────────────────────
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 0, 24, 16)
        self.btn_preview = QPushButton("Buat Preview")
        self.btn_preview.setProperty("class", "SecondaryButton")
        self.btn_preview.clicked.connect(self.generate_preview)
        self.btn_generate = QPushButton("Generate PowerPoint")
        self.btn_generate.setProperty("class", "PrimaryButton")
        self.btn_generate.clicked.connect(self.generate_ppt)
        footer_layout.addWidget(self.btn_preview)
        footer_layout.addWidget(self.btn_generate)
        footer_layout.addStretch()
        main_layout.addWidget(footer)

        self.statusBar().showMessage("Siap")

    def _get_font_sizes(self):
        """Return a dict of font sizes from the spin boxes."""
        return {
            "title": self.spin_font_title.value(),
            "lyric": self.spin_font_lyric.value(),
            "liturgi": self.spin_font_liturgi.value(),
        }

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Pilih File Word", "", "Word Documents (*.docx)"
        )
        if file_path:
            self.file_path = file_path
            self.lbl_file_name.setText(os.path.basename(file_path))
            self.statusBar().showMessage(f"File dipilih: {os.path.basename(file_path)}")

    def generate_preview(self):
        if not self.file_path:
            QMessageBox.warning(self, "Peringatan", "Pilih file Word terlebih dahulu.")
            return

        self.statusBar().showMessage("Sedang memproses dokumen...")
        max_lines = self.spin_lines.value()
        self.slides = parse_docx(self.file_path, max_lines)

        # Clear existing preview
        for i in reversed(range(self.preview_layout.count())):
            widget = self.preview_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # Add new widgets
        font_family = self.combo_font.currentText()
        font_sizes = self._get_font_sizes()
        for slide in self.slides:
            w = PreviewSlideItemWidget(slide, font_family=font_family, font_sizes=font_sizes)
            self.preview_layout.addWidget(w)

        self.preview_layout.addStretch()
        self.statusBar().showMessage(f"Preview berhasil dibuat — {len(self.slides)} slide.")

    def generate_ppt(self):
        if not self.slides:
            QMessageBox.warning(
                self, "Peringatan", "Buat preview terlebih dahulu sebelum generate PowerPoint."
            )
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Simpan File PowerPoint", "Ibadah.pptx", "PowerPoint Files (*.pptx)"
        )
        if not save_path:
            return

        transition_map = {
            "Tanpa Transisi": None,
            "Fade": "fade",
            "Wipe (Kiri ke Kanan)": "wipe",
            "Push (Kiri ke Kanan)": "push",
            "Zoom": "zoom",
        }
        transition = transition_map.get(self.combo_transition.currentText())

        self.statusBar().showMessage("Sedang membuat file PowerPoint...")
        try:
            generate_pptx(
                slides=self.slides,
                output_path=save_path,
                font_family=self.combo_font.currentText(),
                font_sizes=self._get_font_sizes(),
                transition=transition,
            )
            self.statusBar().showMessage("PowerPoint berhasil dibuat.")
            QMessageBox.information(self, "Sukses", "PowerPoint berhasil dibuat dan siap digunakan.")
        except Exception as e:
            self.statusBar().showMessage(f"Gagal: {str(e)}")
            QMessageBox.critical(self, "Error", f"Terjadi kesalahan saat membuat PowerPoint:\n{str(e)}")
