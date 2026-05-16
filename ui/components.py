from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                             QCheckBox, QPushButton, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPainter, QColor, QPixmap, QBrush
from core.models import SlideType


# ─── Visual 16:9 Preview Widget ───────────────────────────────────────────────

class VisualSlidePreviewWidget(QWidget):
    """Renders a scaled-down 16:9 representation of a single slide,
    matching the exact colours, alignment, and fonts used in the PPTX export."""

    PREVIEW_W = 336
    PREVIEW_H = 189  # 16:9

    def __init__(self, slide_item, font_family="Segoe UI", font_sizes=None, parent=None):
        super().__init__(parent)
        self.slide_item = slide_item
        self.font_family = font_family
        # Scale factor: PPTX uses ~720pt height → preview ~189px  → scale ≈ 0.26
        self.scale = self.PREVIEW_H / 720.0
        self.font_sizes = font_sizes or {"title": 60, "lyric": 48, "liturgi": 40}
        self.setFixedSize(self.PREVIEW_W, self.PREVIEW_H)

    def _scaled_pt(self, pt: int) -> int:
        return max(6, int(pt * self.scale))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        sl = self.slide_item
        rect = self.rect()
        inner = rect.adjusted(8, 8, -8, -8)

        # ── Background ─────────────────────────────────────
        bg_color = QColor("#FFFFFF")
        text_color = QColor("#1E1E1E")
        align = Qt.AlignCenter
        font_bold = False
        font_pt = self._scaled_pt(self.font_sizes.get("liturgi", 40))

        if sl.slide_type == SlideType.COVER:
            bg_color = QColor("#1F4D3A"); text_color = QColor("#FFFFFF")
            font_pt = self._scaled_pt(self.font_sizes.get("title", 60)); font_bold = True

        elif sl.slide_type == SlideType.INSTRUKSI:
            bg_color = QColor("#2F80ED"); text_color = QColor("#FFFFFF")
            font_pt = self._scaled_pt(36)

        elif sl.slide_type == SlideType.BAGIAN:
            bg_color = QColor("#123326"); text_color = QColor("#FFFFFF")
            font_pt = self._scaled_pt(self.font_sizes.get("title", 60)); font_bold = True

        elif sl.slide_type == SlideType.JUDUL_LAGU:
            bg_color = QColor("#1F4D3A"); text_color = QColor("#F2C94C")
            font_pt = self._scaled_pt(self.font_sizes.get("title", 60)); font_bold = True

        elif sl.slide_type == SlideType.LIRIK_LAGU:
            bg_color = QColor("#202322"); text_color = QColor("#FFFFFF")
            font_pt = self._scaled_pt(self.font_sizes.get("lyric", 48))

        elif sl.slide_type == SlideType.LITURGI:
            bg_color = QColor("#F7F8F6"); text_color = QColor("#1E1E1E")
            font_pt = self._scaled_pt(self.font_sizes.get("liturgi", 40))
            if sl.is_nyanyian:
                align = Qt.AlignCenter
            else:
                # Bacaan: always left; speaker-based for nyanyian
                if sl.speaker == "J":
                    align = Qt.AlignRight | Qt.AlignVCenter
                elif sl.speaker == "P":
                    align = Qt.AlignLeft | Qt.AlignVCenter
                else:
                    align = Qt.AlignLeft | Qt.AlignVCenter

        elif sl.slide_type == SlideType.BACAAN:
            bg_color = QColor("#FFFFFF"); text_color = QColor("#1E1E1E")
            font_pt = self._scaled_pt(self.font_sizes.get("liturgi", 40))
            align = Qt.AlignLeft | Qt.AlignTop

        elif sl.slide_type == SlideType.PENUTUP:
            bg_color = QColor("#1F4D3A"); text_color = QColor("#FFFFFF")
            font_pt = self._scaled_pt(self.font_sizes.get("title", 60)); font_bold = True

        # Fill background colour first
        painter.fillRect(rect, bg_color)

        # Overlay background image if set (BAGIAN slides)
        if sl.bg_image and sl.slide_type == SlideType.BAGIAN:
            pix = QPixmap(sl.bg_image)
            if not pix.isNull():
                pix = pix.scaled(rect.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                # Centre-crop
                x_off = (pix.width() - rect.width()) // 2
                y_off = (pix.height() - rect.height()) // 2
                painter.drawPixmap(rect, pix, pix.rect().adjusted(x_off, y_off, -x_off, -y_off))
                # Semi-transparent dark overlay so text remains readable
                painter.fillRect(rect, QColor(0, 0, 0, 140))
                text_color = QColor("#FFFFFF")

        # ── Speaker label (Liturgi) ─────────────────────────
        if sl.slide_type == SlideType.LITURGI and sl.speaker:
            sp_font = QFont(self.font_family, self._scaled_pt(32), QFont.Bold)
            painter.setFont(sp_font)
            sp_color = QColor("#C89B2A") if "J" in sl.speaker else QColor("#2A6B50")
            painter.setPen(sp_color)
            sp_rect = rect.adjusted(8, 4, -8, -(rect.height() - 28))
            sp_align = Qt.AlignRight if sl.speaker == "J" else (
                Qt.AlignCenter if "+" in sl.speaker else Qt.AlignLeft
            )
            painter.drawText(sp_rect, sp_align, f"{sl.speaker} :")
            inner = inner.adjusted(0, 22, 0, 0)

        # ── Main text ──────────────────────────────────────
        font = QFont(self.font_family, font_pt)
        font.setBold(font_bold)
        painter.setFont(font)
        painter.setPen(text_color)
        painter.drawText(inner, align | Qt.TextWordWrap, sl.content)


# ─── Preview List Item Widget ──────────────────────────────────────────────────

class PreviewSlideItemWidget(QWidget):
    """Card widget shown in the preview scroll area for each slide."""

    def __init__(self, slide_item, font_family="Segoe UI", font_sizes=None, parent=None):
        super().__init__(parent)
        self.slide_item = slide_item
        self.font_family = font_family
        self.font_sizes = font_sizes or {}
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        self.setStyleSheet("""
            PreviewSlideItemWidget {
                background-color: #FFFFFF;
                border: 1px solid #D9DED8;
                border-radius: 8px;
            }
        """)

        # ── Top bar ────────────────────────────────────────
        top_layout = QHBoxLayout()

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.slide_item.included)
        self.checkbox.stateChanged.connect(self._on_check_changed)

        self.lbl_num = QLabel(f"[{self.slide_item.slide_number}]")
        self.lbl_num.setStyleSheet("color:#8A928A; font-weight:bold; border:none;")

        badge_colors = {
            "Cover": "#1F4D3A", "Instruksi": "#2F80ED", "Judul Bagian": "#123326",
            "Judul Lagu": "#B8962E", "Lirik Lagu": "#5F665F",
            "Liturgi": "#8A6D1D", "Bacaan": "#6A4BBC", "Penutup": "#202322",
        }
        color = badge_colors.get(self.slide_item.slide_type.value, "#5F665F")
        self.lbl_badge = QLabel(self.slide_item.slide_type.value)
        self.lbl_badge.setStyleSheet(
            f"background-color:{color}; color:#FFFFFF; padding:3px 8px; "
            f"border-radius:4px; font-size:11px; font-weight:bold;"
        )

        # Nyanyian tag for liturgi
        if self.slide_item.slide_type.value == "Liturgi":
            tag = "🎵 Nyanyian" if self.slide_item.is_nyanyian else "📖 Bacaan"
            self.lbl_tag = QLabel(tag)
            self.lbl_tag.setStyleSheet("color:#555; font-size:10px; border:none;")
        else:
            self.lbl_tag = None

        top_layout.addWidget(self.checkbox)
        top_layout.addWidget(self.lbl_num)
        top_layout.addWidget(self.lbl_badge)
        if self.lbl_tag:
            top_layout.addWidget(self.lbl_tag)
        top_layout.addStretch()

        # Background image button — only for BAGIAN slides
        if self.slide_item.slide_type == SlideType.BAGIAN:
            self.btn_bg = QPushButton("🖼 Ubah Background")
            self.btn_bg.setStyleSheet(
                "QPushButton { background:#2A5C44; color:#FFF; border-radius:4px; "
                "padding:4px 10px; font-size:11px; } "
                "QPushButton:hover { background:#1F4D3A; }"
            )
            self.btn_bg.clicked.connect(self._pick_background)
            top_layout.addWidget(self.btn_bg)

        main_layout.addLayout(top_layout)

        # ── 16:9 Visual Preview ────────────────────────────
        self.visual = VisualSlidePreviewWidget(
            self.slide_item,
            font_family=self.font_family,
            font_sizes=self.font_sizes,
        )
        main_layout.addWidget(self.visual, alignment=Qt.AlignCenter)

    def _on_check_changed(self, state):
        self.slide_item.included = (state == Qt.Checked)

    def _pick_background(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Pilih Gambar Latar Belakang", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if path:
            self.slide_item.bg_image = path
            self.visual.update()  # trigger repaint
