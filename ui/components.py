from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPainter, QPixmap
from PyQt5.QtWidgets import QFileDialog, QCheckBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from core.models import SlideType
from core.template_engine import TemplateResolver


def _qcolor(value: str) -> QColor:
    return QColor(value or "#FFFFFF")


class VisualSlidePreviewWidget(QWidget):
    """Template-based square preview for a single slide."""

    DEFAULT_SIZE = 280

    def __init__(
        self,
        slide_item,
        template_name="gmim_default",
        aspect_ratio="square",
        font_family=None,
        font_sizes=None,
        size=280,
        parent=None,
    ):
        super().__init__(parent)
        self.slide_item = slide_item
        self.template_name = template_name
        self.aspect_ratio = aspect_ratio
        self.font_family = font_family
        self.font_sizes = font_sizes or {}
        self.resolver = TemplateResolver(template_name)
        self.setFixedSize(*self.preview_dimensions(size, aspect_ratio))

    @staticmethod
    def preview_dimensions(size: int, aspect_ratio: str) -> tuple[int, int]:
        if aspect_ratio == "landscape_16_9":
            return size, int(size * 9 / 16)
        if aspect_ratio == "standard_4_3":
            return size, int(size * 3 / 4)
        return size, size

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        rect = self.rect()
        style = self.resolver.resolve(self.slide_item)
        style = self._with_ui_font_overrides(style)
        background = style.get("background", {})
        bg_color = background.get("color", "#1F4D3A")
        if self.slide_item.background and self.slide_item.background.color:
            bg_color = self.slide_item.background.color
        painter.fillRect(rect, _qcolor(bg_color))

        image_path = self.slide_item.bg_image or background.get("image")
        if image_path:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(rect.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                x_offset = max(0, (pixmap.width() - rect.width()) // 2)
                y_offset = max(0, (pixmap.height() - rect.height()) // 2)
                painter.drawPixmap(rect, pixmap, pixmap.rect().adjusted(x_offset, y_offset, -x_offset, -y_offset))

        overlay_opacity = float(background.get("overlay_opacity", 0) or 0)
        if self.slide_item.background:
            overlay_opacity = self.slide_item.background.overlay_opacity
        if overlay_opacity > 0:
            overlay = QColor(background.get("overlay_color", "#000000"))
            overlay.setAlpha(int(max(0, min(overlay_opacity, 1)) * 255))
            painter.fillRect(rect, overlay)

        self._draw_text(painter, rect.adjusted(20, 20, -20, -20), style)

    def _with_ui_font_overrides(self, style: dict) -> dict:
        updated = dict(style)
        if self.font_family:
            updated["font_family"] = self.font_family
        font_size = self._font_size_for_slide()
        if font_size:
            updated["font_size"] = font_size
        return updated

    def _font_size_for_slide(self):
        if not self.font_sizes:
            return None
        if self.slide_item.type in {
            SlideType.COVER,
            SlideType.SECTION,
            SlideType.SONG_TITLE,
            SlideType.BLESSING,
            SlideType.CLOSING,
        }:
            return self.font_sizes.get("title")
        if self.slide_item.type == SlideType.SONG_LYRICS:
            return self.font_sizes.get("lyric")
        return self.font_sizes.get("liturgi")

    def _draw_text(self, painter: QPainter, rect, style: dict) -> None:
        text_color = _qcolor(style.get("color", "#FFFFFF"))
        font_size = max(10, int(style.get("font_size", 42) * 0.26))
        font = QFont(style.get("font_family", "Segoe UI"), font_size)
        font.setBold(bool(style.get("bold", False)))
        painter.setFont(font)
        painter.setPen(text_color)

        if self.slide_item.speaker_lines:
            self._draw_speaker_lines(painter, rect, style, font)
            return
        else:
            text = self.slide_item.content

        align = {
            "left": Qt.AlignLeft,
            "right": Qt.AlignRight,
            "center": Qt.AlignCenter,
        }.get(style.get("align", "center"), Qt.AlignCenter)
        painter.drawText(rect, align | Qt.AlignVCenter | Qt.TextWordWrap, text)

    def _draw_speaker_lines(self, painter: QPainter, rect, style: dict, font: QFont) -> None:
        line_height = painter.fontMetrics().height() + 4
        total_height = line_height * len(self.slide_item.speaker_lines)
        y = rect.y() + max(0, (rect.height() - total_height) // 2)
        last_speaker = ""
        for speaker_line in self.slide_item.speaker_lines:
            speaker = (speaker_line.speaker or "").strip()
            if speaker:
                last_speaker = speaker
            effective_speaker = speaker or last_speaker
            painter.setFont(font)
            painter.setPen(_qcolor(self.speaker_color(effective_speaker, style)))
            text = f"{speaker} : {speaker_line.text}" if speaker else speaker_line.text
            line_rect = rect.__class__(rect.x(), y, rect.width(), line_height)
            align = Qt.AlignLeft
            if effective_speaker == "J":
                align = Qt.AlignRight
            elif "+" in effective_speaker:
                align = Qt.AlignCenter
            painter.drawText(line_rect, align | Qt.AlignVCenter | Qt.TextWordWrap, text)
            y += line_height

    @staticmethod
    def speaker_color(speaker: str, style: dict) -> str:
        speaker_colors = style.get("speaker_colors", {})
        return speaker_colors.get(speaker, style.get("color", "#FFFFFF"))


class PreviewSlideItemWidget(QWidget):
    selected = pyqtSignal(object)

    def __init__(self, slide_item, template_name="gmim_default", parent=None):
        super().__init__(parent)
        self.slide_item = slide_item
        self.template_name = template_name
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        self.setStyleSheet(
            "PreviewSlideItemWidget { background:#FFFFFF; border:1px solid #D9DED8; border-radius:8px; }"
        )

        top = QHBoxLayout()
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.slide_item.include)
        self.checkbox.stateChanged.connect(self._on_check_changed)
        self.lbl_num = QLabel(f"[{self.slide_item.slide_number}]")
        self.lbl_num.setStyleSheet("color:#8A928A; font-weight:bold; border:none;")
        self.lbl_badge = QLabel(self.slide_item.type.label)
        self.lbl_badge.setStyleSheet("background:#1F4D3A; color:#FFFFFF; padding:3px 8px; border-radius:4px; font-size:11px;")
        top.addWidget(self.checkbox)
        top.addWidget(self.lbl_num)
        top.addWidget(self.lbl_badge)
        top.addStretch()

        if self.slide_item.type == SlideType.SECTION:
            self.btn_bg = QPushButton("Ubah Background")
            self.btn_bg.setStyleSheet("QPushButton { background:#2A5C44; color:#FFF; border-radius:4px; padding:4px 8px; font-size:11px; }")
            self.btn_bg.clicked.connect(self._pick_background)
            top.addWidget(self.btn_bg)

        preview = QLabel(self.slide_item.content[:120])
        preview.setWordWrap(True)
        preview.setStyleSheet("color:#1E1E1E; border:none;")
        section = QLabel(self.slide_item.section or "Tanpa section")
        section.setWordWrap(True)
        section.setStyleSheet("color:#5F665F; border:none; font-size:11px;")
        layout.addLayout(top)
        layout.addWidget(section)
        layout.addWidget(preview)

    def mousePressEvent(self, event):
        self.selected.emit(self.slide_item)
        super().mousePressEvent(event)

    def _on_check_changed(self, state):
        self.slide_item.include = state == Qt.Checked

    def _pick_background(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih Gambar Latar Belakang",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if path:
            self.slide_item.bg_image = path
            self.selected.emit(self.slide_item)
