from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout

from ui.components import VisualSlidePreviewWidget


class FullscreenPreviewDialog(QDialog):
    def __init__(
        self,
        slides,
        start_index: int = 0,
        template_name: str = "gmim_default",
        aspect_ratio: str = "square",
        parent=None,
    ):
        super().__init__(parent)
        self.slides = [slide for slide in slides if getattr(slide, "include", True)]
        self.index = min(max(start_index, 0), max(len(self.slides) - 1, 0))
        self.template_name = template_name
        self.aspect_ratio = aspect_ratio
        self.preview = None
        self.counter = QLabel()
        self.counter.setAlignment(Qt.AlignRight)
        self.counter.setStyleSheet("color:#FFFFFF; font-size:14px; padding:8px;")
        self.setWindowTitle("Preview Full Screen")
        self.setStyleSheet("QDialog { background:#000000; }")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(8)
        self.layout.addWidget(self.counter)
        self._render_current_slide()

    def showEvent(self, event):
        super().showEvent(event)
        self.showFullScreen()
        self._render_current_slide()

    def keyPressEvent(self, event):
        key = event.key()
        if key in {Qt.Key_Right, Qt.Key_Space}:
            self.next_slide()
            return
        if key in {Qt.Key_Left, Qt.Key_Backspace}:
            self.previous_slide()
            return
        if key == Qt.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def next_slide(self):
        if self.slides:
            self.index = min(self.index + 1, len(self.slides) - 1)
            self._render_current_slide()

    def previous_slide(self):
        if self.slides:
            self.index = max(self.index - 1, 0)
            self._render_current_slide()

    def _preview_size(self) -> int:
        screen = self.screen()
        geometry = screen.availableGeometry() if screen else self.geometry()
        width = max(320, geometry.width() - 96)
        height = max(240, geometry.height() - 120)
        if self.aspect_ratio == "landscape_16_9":
            return min(width, int(height * 16 / 9))
        if self.aspect_ratio == "standard_4_3":
            return min(width, int(height * 4 / 3))
        return min(width, height)

    def _render_current_slide(self):
        if self.preview is not None:
            self.layout.removeWidget(self.preview)
            self.preview.setParent(None)
            self.preview.deleteLater()

        if not self.slides:
            self.counter.setText("0 / 0")
            return

        self.counter.setText(f"{self.index + 1} / {len(self.slides)}")
        self.preview = VisualSlidePreviewWidget(
            self.slides[self.index],
            template_name=self.template_name,
            aspect_ratio=self.aspect_ratio,
            size=self._preview_size(),
            parent=self,
        )
        self.layout.addWidget(self.preview, alignment=Qt.AlignCenter)
