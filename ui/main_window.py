import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import (
    QComboBox,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.generator import font_category_for_slide, generate_pptx
from core.deck_editor import DeckEditor
from core.models import SlideType
from core.parser import parse_file_to_deck
from core.presets import PresetRegistry
from core.readers import PDFTextExtractionError
from core.template_engine import TemplateResolver
from core.text_splitter import max_chars_for_style, wrap_text_to_visual_lines
from ui.components import PreviewSlideItemWidget, VisualSlidePreviewWidget
from ui.fullscreen_preview import FullscreenPreviewDialog
from ui.styles import get_stylesheet
from ui.template_manager_dialog import TemplateManagerDialog


TRANSITION_LABELS = {
    "Tanpa Transisi": None,
    "Fade": "fade",
    "Wipe (Kiri ke Kanan)": "wipe",
    "Push (Kiri ke Kanan)": "push",
    "Zoom": "zoom",
    "Morph": "morph",
}


def transition_value_from_label(label: str):
    return TRANSITION_LABELS.get(label)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LiturgiSlide")
        self.resize(1280, 780)
        self.setStyleSheet(get_stylesheet())
        self.deck = None
        self.slides = []
        self.selected_slide = None
        self.file_path = None
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(80)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(24, 16, 24, 16)
        title_label = QLabel("LiturgiSlide")
        title_label.setObjectName("AppTitle")
        subtitle_label = QLabel("Generator Slide Ibadah Semi-Otomatis - GMIM Syaloem")
        subtitle_label.setObjectName("AppSubtitle")
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        main_layout.addWidget(header)

        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(24, 24, 24, 24)
        body_layout.setSpacing(24)

        left_scroll = QScrollArea()
        left_scroll.setObjectName("LeftPanelScroll")
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setMinimumWidth(340)
        left_scroll.setMaximumWidth(360)

        left_panel = QWidget()
        left_panel.setObjectName("LeftPanelContent")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(16)
        left_layout.addWidget(self._build_document_card())
        left_layout.addWidget(self._build_settings_card())
        left_layout.addStretch()
        left_scroll.setWidget(left_panel)

        right_panel = QFrame()
        right_panel.setProperty("class", "Card")
        right_layout = QHBoxLayout(right_panel)
        right_layout.setSpacing(16)
        right_layout.addWidget(self._build_slide_list_panel(), stretch=1)
        right_layout.addWidget(self._build_focus_preview_panel(), stretch=2)
        right_layout.addWidget(self._build_editor_panel(), stretch=1)

        body_layout.addWidget(left_scroll)
        body_layout.addWidget(right_panel)
        main_layout.addWidget(body_widget, stretch=1)
        main_layout.addWidget(self._build_footer())
        self.statusBar().showMessage("Siap")

    def _build_document_card(self):
        card = QFrame()
        card.setProperty("class", "Card")
        layout = QVBoxLayout(card)
        layout.setSpacing(12)
        title = QLabel("Dokumen Tata Ibadah")
        title.setProperty("class", "SectionTitle")
        self.btn_browse = QPushButton("Pilih File Word/PDF")
        self.btn_browse.setProperty("class", "SecondaryButton")
        self.btn_browse.clicked.connect(self.browse_file)
        self.lbl_file_name = QLabel("Belum ada file dipilih")
        self.lbl_file_name.setProperty("class", "BodyText")
        self.lbl_file_name.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(self.btn_browse)
        layout.addWidget(self.lbl_file_name)
        return card

    def _build_settings_card(self):
        card = QFrame()
        card.setObjectName("SettingsCard")
        card.setProperty("class", "Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(9)
        title = QLabel("Pengaturan Slide")
        title.setProperty("class", "SectionTitle")
        layout.addWidget(title)

        self.spin_lines = self._spin(layout, "Max baris per slide:", 1, 15, 6)

        families = QFontDatabase().families()
        self.combo_font_heading = self._font_combo(families)
        self.combo_font_song_title = self._font_combo(families)
        self.combo_font_lyric = self._font_combo(families)
        self.combo_font_liturgi = self._font_combo(families)
        self._labeled_widget(layout, "Font heading/section:", self.combo_font_heading)
        self._labeled_widget(layout, "Font judul lagu:", self.combo_font_song_title)
        self._labeled_widget(layout, "Font lirik lagu:", self.combo_font_lyric)
        self._labeled_widget(layout, "Font liturgi/bacaan:", self.combo_font_liturgi)

        self.spin_font_title = self._spin(layout, "Ukuran font judul:", 10, 150, 60)
        self.spin_font_lyric = self._spin(layout, "Ukuran font lirik:", 10, 150, 48)
        self.spin_font_liturgi = self._spin(layout, "Ukuran font liturgi:", 10, 150, 40)
        self.spin_font_title.valueChanged.connect(self.refresh_selected_preview)
        self.spin_font_lyric.valueChanged.connect(self.refresh_selected_preview)
        self.spin_font_liturgi.valueChanged.connect(self.refresh_selected_preview)

        self.combo_transition = QComboBox()
        self.combo_transition.addItems(list(TRANSITION_LABELS.keys()))
        self._labeled_widget(layout, "Efek Transisi Slide:", self.combo_transition)

        self.combo_template = QComboBox()
        self.combo_template.addItems(["gmim_default", "gmim_dark"])
        self._labeled_widget(layout, "Template:", self.combo_template)
        self.btn_template_manager = QPushButton("Kelola Template")
        self.btn_template_manager.clicked.connect(self.open_template_manager)
        layout.addWidget(self.btn_template_manager)

        self.check_ocr = QCheckBox("Gunakan OCR jika PDF scan")
        self.check_ocr.setProperty("class", "BodyText")
        layout.addWidget(self.check_ocr)

        self.combo_ratio = QComboBox()
        self.combo_ratio.addItems(["1:1 Square", "16:9 Landscape", "4:3 Standard"])
        self.combo_ratio.currentTextChanged.connect(self.on_ratio_changed)
        self._labeled_widget(layout, "Ukuran slide:", self.combo_ratio)

        self.combo_preset = QComboBox()
        self.combo_preset.addItems(PresetRegistry().names())
        self.combo_preset.currentTextChanged.connect(self.apply_preset_defaults)
        self._labeled_widget(layout, "Preset GMIM:", self.combo_preset)
        return card

    def apply_preset_defaults(self, preset_name):
        preset = PresetRegistry()
        template_name = preset.default_template(preset_name)
        aspect_ratio = preset.default_aspect_ratio(preset_name)
        self.combo_template.setCurrentText(template_name)
        ratio_label = {
            "square": "1:1 Square",
            "landscape_16_9": "16:9 Landscape",
            "standard_4_3": "4:3 Standard",
        }.get(aspect_ratio, "1:1 Square")
        self.combo_ratio.setCurrentText(ratio_label)
        self.on_ratio_changed()

    def _build_slide_list_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel("List Slide")
        title.setProperty("class", "SectionTitle")
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.preview_container = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_container)
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_layout.setSpacing(12)
        self.preview_layout.addStretch()
        self.scroll_area.setWidget(self.preview_container)
        layout.addWidget(title)
        layout.addWidget(self.scroll_area)
        return panel

    def _build_focus_preview_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Preview Utama")
        title.setProperty("class", "SectionTitle")
        self.focus_preview_container = QWidget()
        self.focus_preview_layout = QVBoxLayout(self.focus_preview_container)
        self.focus_preview_layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(self.focus_preview_container, stretch=1)
        return panel

    def _build_editor_panel(self):
        panel = QFrame()
        panel.setProperty("class", "Card")
        layout = QVBoxLayout(panel)
        title = QLabel("Panel Edit")
        title.setProperty("class", "SectionTitle")
        self.edit_title = QLineEdit()
        self.edit_content = QTextEdit()
        self.edit_type = QComboBox()
        self.edit_type.addItems([slide_type.value for slide_type in SlideType])
        self.edit_template = QComboBox()
        self.edit_template.addItems(["", "gmim_default", "gmim_dark"])
        self.edit_section = QLineEdit()
        self.edit_align = QComboBox()
        self.edit_align.addItems(["center", "left", "right"])
        self.btn_apply_edit = QPushButton("Terapkan Edit")
        self.btn_duplicate = QPushButton("Duplicate")
        self.btn_delete = QPushButton("Delete")
        self.btn_split = QPushButton("Split Slide")
        self.btn_merge = QPushButton("Merge Next")
        self.btn_move_up = QPushButton("Move Up")
        self.btn_move_down = QPushButton("Move Down")
        self.lbl_overflow_warning = QLabel("")
        self.lbl_overflow_warning.setStyleSheet("color:#C62828;")
        self.lbl_overflow_warning.setWordWrap(True)
        self.btn_apply_edit.clicked.connect(self.apply_editor_changes)
        self.btn_duplicate.clicked.connect(self.duplicate_selected_slide)
        self.btn_delete.clicked.connect(self.delete_selected_slide)
        self.btn_split.clicked.connect(self.split_selected_slide)
        self.btn_merge.clicked.connect(self.merge_selected_slide)
        self.btn_move_up.clicked.connect(lambda: self.move_selected_slide(-1))
        self.btn_move_down.clicked.connect(lambda: self.move_selected_slide(1))
        layout.addWidget(title)
        self._labeled_widget(layout, "Judul:", self.edit_title)
        self._labeled_widget(layout, "Tipe:", self.edit_type)
        self._labeled_widget(layout, "Template slide:", self.edit_template)
        self._labeled_widget(layout, "Section:", self.edit_section)
        self._labeled_widget(layout, "Alignment:", self.edit_align)
        content_label = QLabel("Isi:")
        content_label.setProperty("class", "BodyText")
        layout.addWidget(content_label)
        layout.addWidget(self.edit_content, stretch=1)
        layout.addWidget(self.btn_apply_edit)
        layout.addWidget(self.btn_duplicate)
        layout.addWidget(self.btn_delete)
        layout.addWidget(self.btn_split)
        layout.addWidget(self.btn_merge)
        layout.addWidget(self.btn_move_up)
        layout.addWidget(self.btn_move_down)
        layout.addWidget(self.lbl_overflow_warning)
        return panel

    def _build_footer(self):
        footer = QWidget()
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(24, 0, 24, 16)
        self.btn_preview = QPushButton("Buat Preview")
        self.btn_preview.setProperty("class", "SecondaryButton")
        self.btn_preview.clicked.connect(self.generate_preview)
        self.btn_fullscreen_preview = QPushButton("Preview Full Screen")
        self.btn_fullscreen_preview.setProperty("class", "SecondaryButton")
        self.btn_fullscreen_preview.clicked.connect(self.show_fullscreen_preview)
        self.btn_generate = QPushButton("Generate PowerPoint")
        self.btn_generate.setProperty("class", "PrimaryButton")
        self.btn_generate.clicked.connect(self.generate_ppt)
        layout.addWidget(self.btn_preview)
        layout.addWidget(self.btn_fullscreen_preview)
        layout.addWidget(self.btn_generate)
        layout.addStretch()
        return footer

    def _labeled_widget(self, layout, label_text, widget):
        label = QLabel(label_text)
        label.setProperty("class", "BodyText")
        label.setWordWrap(True)
        self._prepare_form_control(widget)
        layout.addWidget(label)
        layout.addWidget(widget)

    def _spin(self, layout, label_text, minimum, maximum, value):
        spin = QSpinBox()
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        self._labeled_widget(layout, label_text, spin)
        return spin

    def _font_combo(self, families):
        combo = QComboBox()
        combo.addItems(families)
        if "Segoe UI" in families:
            combo.setCurrentText("Segoe UI")
        elif "Arial" in families:
            combo.setCurrentText("Arial")
        combo.currentTextChanged.connect(self.refresh_selected_preview)
        return combo

    def _prepare_form_control(self, widget):
        if isinstance(widget, (QComboBox, QLineEdit, QSpinBox)):
            widget.setMinimumHeight(36)
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def _get_font_sizes(self):
        return {
            "title": self.spin_font_title.value(),
            "lyric": self.spin_font_lyric.value(),
            "liturgi": self.spin_font_liturgi.value(),
        }

    def _get_font_families(self):
        return {
            "heading": self.combo_font_heading.currentText(),
            "song_title": self.combo_font_song_title.currentText(),
            "lyric": self.combo_font_lyric.currentText(),
            "liturgi": self.combo_font_liturgi.currentText(),
        }

    def _font_size_for_slide(self, slide):
        font_sizes = self._get_font_sizes()
        if slide.type in {
            SlideType.COVER,
            SlideType.SECTION,
            SlideType.SONG_TITLE,
            SlideType.BLESSING,
            SlideType.CLOSING,
        }:
            return font_sizes["title"]
        if slide.type == SlideType.SONG_LYRICS:
            return font_sizes["lyric"]
        return font_sizes["liturgi"]

    def apply_ui_style_to_slide(self, slide):
        style = slide.metadata.setdefault("style", {})
        style["font_family"] = self._get_font_families()[font_category_for_slide(slide.type)]
        style["font_size"] = self._font_size_for_slide(slide)

    def apply_ui_style_to_slides(self):
        for slide in self.slides:
            self.apply_ui_style_to_slide(slide)

    def _get_aspect_ratio(self):
        return {
            "1:1 Square": "square",
            "16:9 Landscape": "landscape_16_9",
            "4:3 Standard": "standard_4_3",
        }.get(self.combo_ratio.currentText(), "square")

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih File Word/PDF",
            "",
            "Dokumen Ibadah (*.docx *.pdf);;Word Documents (*.docx);;PDF Documents (*.pdf)",
        )
        if file_path:
            self.file_path = file_path
            self.lbl_file_name.setText(os.path.basename(file_path))
            self.statusBar().showMessage(f"File dipilih: {os.path.basename(file_path)}")

    def generate_preview(self):
        if not self.file_path:
            QMessageBox.warning(self, "Peringatan", "Pilih file Word atau PDF terlebih dahulu.")
            return

        self.statusBar().showMessage("Sedang memproses dokumen...")
        try:
            self.deck = parse_file_to_deck(
                self.file_path,
                self.spin_lines.value(),
                preset_name=self.combo_preset.currentText(),
                use_ocr=self.check_ocr.isChecked(),
            )
        except PDFTextExtractionError as exc:
            self.statusBar().showMessage("PDF tidak menghasilkan teks.")
            QMessageBox.warning(self, "PDF Scan", str(exc))
            return
        except Exception as exc:
            self.statusBar().showMessage(f"Gagal memproses dokumen: {exc}")
            QMessageBox.critical(self, "Import Error", f"Dokumen tidak dapat diproses:\n{exc}")
            return
        if self._deck_used_ocr():
            QMessageBox.warning(self, "Hasil OCR", "Hasil OCR mungkin tidak 100% akurat. Mohon periksa kembali teks sebelum export.")
        self.deck.template_name = self.combo_template.currentText()
        self.deck.aspect_ratio = self._get_aspect_ratio()
        self.slides = self.deck.slides
        self.apply_ui_style_to_slides()
        self._clear_layout(self.preview_layout)
        self._clear_layout(self.focus_preview_layout)
        self.refresh_preview_list()

        if self.slides:
            self.show_slide_preview(self.slides[0])
        self.statusBar().showMessage(f"Preview berhasil dibuat - {len(self.slides)} slide.")

    def refresh_preview_list(self):
        self._clear_layout(self.preview_layout)
        for slide in self.slides:
            item = PreviewSlideItemWidget(slide, template_name=self.combo_template.currentText())
            item.selected.connect(self.show_slide_preview)
            self.preview_layout.addWidget(item)
        self.preview_layout.addStretch()

    def show_slide_preview(self, slide):
        self.selected_slide = slide
        self.apply_ui_style_to_slide(slide)
        self._clear_layout(self.focus_preview_layout)
        preview = VisualSlidePreviewWidget(
            slide,
            template_name=self.combo_template.currentText(),
            aspect_ratio=self._get_aspect_ratio(),
            size=360,
        )
        self.focus_preview_layout.addStretch()
        self.focus_preview_layout.addWidget(preview, alignment=Qt.AlignCenter)
        self.focus_preview_layout.addStretch()
        self.edit_title.setText(slide.title or "")
        self.edit_content.setPlainText(slide.content)
        self.edit_type.setCurrentText(slide.type.value)
        self.edit_template.setCurrentText(slide.template or "")
        self.edit_section.setText(slide.section)
        self.edit_align.setCurrentText(slide.metadata.get("style", {}).get("align", "center"))
        self.lbl_overflow_warning.setText(self._overflow_warning(slide))

    def refresh_selected_preview(self, *args):
        self.apply_ui_style_to_slides()
        if self.selected_slide:
            self.show_slide_preview(self.selected_slide)

    def on_ratio_changed(self, *args):
        if self.deck:
            self.deck.aspect_ratio = self._get_aspect_ratio()
        self.refresh_selected_preview()

    def apply_editor_changes(self):
        if not self.deck or not self.selected_slide:
            return
        editor = DeckEditor(self.deck)
        slide = editor.update_slide(
            self.selected_slide.id,
            title=self.edit_title.text(),
            content=self.edit_content.toPlainText(),
            slide_type=self.edit_type.currentText(),
            section=self.edit_section.text(),
            template=self.edit_template.currentText() or None,
            alignment=self.edit_align.currentText(),
        )
        self.slides = self.deck.slides
        self.apply_ui_style_to_slide(slide)
        self.refresh_preview_list()
        self.show_slide_preview(slide)
        self.statusBar().showMessage("Slide berhasil diperbarui.")

    def duplicate_selected_slide(self):
        if not self.deck or not self.selected_slide:
            return
        slide = DeckEditor(self.deck).duplicate(self.selected_slide.id)
        self.slides = self.deck.slides
        self.refresh_preview_list()
        self.show_slide_preview(slide)

    def delete_selected_slide(self):
        if not self.deck or not self.selected_slide:
            return
        DeckEditor(self.deck).delete(self.selected_slide.id)
        self.slides = self.deck.slides
        self.selected_slide = self.slides[0] if self.slides else None
        self.refresh_preview_list()
        if self.selected_slide:
            self.show_slide_preview(self.selected_slide)
        else:
            self._clear_layout(self.focus_preview_layout)

    def split_selected_slide(self):
        if not self.deck or not self.selected_slide:
            return
        try:
            slide = DeckEditor(self.deck).split(self.selected_slide.id)
        except ValueError as exc:
            QMessageBox.warning(self, "Split Slide", str(exc))
            return
        self.slides = self.deck.slides
        self.refresh_preview_list()
        self.show_slide_preview(slide)

    def merge_selected_slide(self):
        if not self.deck or not self.selected_slide:
            return
        try:
            slide = DeckEditor(self.deck).merge(self.selected_slide.id)
        except ValueError as exc:
            QMessageBox.warning(self, "Merge Slide", str(exc))
            return
        self.slides = self.deck.slides
        self.refresh_preview_list()
        self.show_slide_preview(slide)

    def move_selected_slide(self, direction):
        if not self.deck or not self.selected_slide:
            return
        DeckEditor(self.deck).move(self.selected_slide.id, direction)
        self.slides = self.deck.slides
        self.apply_ui_style_to_slides()
        self.refresh_preview_list()
        self.show_slide_preview(self.selected_slide)

    def show_fullscreen_preview(self):
        if not self.slides:
            QMessageBox.warning(self, "Peringatan", "Buat preview terlebih dahulu sebelum preview full screen.")
            return
        self.apply_ui_style_to_slides()
        index = self.slides.index(self.selected_slide) if self.selected_slide in self.slides else 0
        dialog = FullscreenPreviewDialog(
            self.slides,
            start_index=index,
            template_name=self.combo_template.currentText(),
            aspect_ratio=self._get_aspect_ratio(),
            parent=self,
        )
        dialog.exec_()

    def generate_ppt(self):
        if not self.slides:
            QMessageBox.warning(self, "Peringatan", "Buat preview terlebih dahulu sebelum generate PowerPoint.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Simpan File PowerPoint", "Ibadah.pptx", "PowerPoint Files (*.pptx)")
        if not save_path:
            return

        transition = transition_value_from_label(self.combo_transition.currentText())

        self.statusBar().showMessage("Sedang membuat file PowerPoint...")
        try:
            self.apply_ui_style_to_slides()
            generate_pptx(
                slides=self.slides,
                output_path=save_path,
                font_families=self._get_font_families(),
                font_sizes=self._get_font_sizes(),
                transition=transition,
                template_name=self.combo_template.currentText(),
                aspect_ratio=self._get_aspect_ratio(),
            )
            self.statusBar().showMessage("PowerPoint berhasil dibuat.")
            QMessageBox.information(self, "Sukses", "PowerPoint berhasil dibuat dan siap digunakan.")
        except Exception as exc:
            self.statusBar().showMessage(f"Gagal: {exc}")
            QMessageBox.critical(self, "Error", f"Terjadi kesalahan saat membuat PowerPoint:\n{exc}")

    def _clear_layout(self, layout):
        for index in reversed(range(layout.count())):
            item = layout.itemAt(index)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
            else:
                layout.removeItem(item)

    def open_template_manager(self):
        dialog = TemplateManagerDialog(parent=self)
        dialog.exec_()
        current = self.combo_template.currentText()
        self.combo_template.clear()
        self.combo_template.addItems(dialog.manager.list_templates())
        self.combo_template.setCurrentText(current if current in dialog.manager.list_templates() else "gmim_default")

    def _deck_used_ocr(self):
        if not self.deck:
            return False
        service_document = self.deck.metadata.get("service_document", {})
        for section in service_document.get("sections", []):
            for item in section.get("items", []):
                if item.get("metadata", {}).get("ocr_used"):
                    return True
        return False

    def _overflow_warning(self, slide):
        try:
            style = TemplateResolver(self.combo_template.currentText()).resolve(slide)
        except Exception:
            style = {}
        max_chars = max_chars_for_style(
            font_size=style.get("font_size", self._font_size_for_slide(slide)),
            aspect_ratio=self._get_aspect_ratio(),
        )
        visual_lines = wrap_text_to_visual_lines(slide.content, max_chars)
        if len(visual_lines) > self.spin_lines.value():
            return "Peringatan: teks berpotensi terlalu panjang. Gunakan Split Slide sebelum export."
        return ""
