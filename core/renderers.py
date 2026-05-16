import os
import tempfile
from typing import Iterable

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Inches, Pt

from core.models import SlideDeck, SlideItem, SlideBackground, SlideType
from core.template_engine import TemplateResolver


PPTX_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
PPTX_P14_NS = "http://schemas.microsoft.com/office/powerpoint/2010/main"
_PPTX_SUPPORTED = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tiff", ".tif", ".wmf"}


def _rgb(value: str) -> RGBColor:
    value = (value or "#FFFFFF").lstrip("#")
    return RGBColor(int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def _alignment(value: str) -> PP_ALIGN:
    return {
        "left": PP_ALIGN.LEFT,
        "right": PP_ALIGN.RIGHT,
        "center": PP_ALIGN.CENTER,
        "justify": PP_ALIGN.JUSTIFY,
    }.get(value, PP_ALIGN.CENTER)


def _ensure_supported_image(image_path: str) -> tuple[str, str | None]:
    ext = os.path.splitext(image_path)[1].lower()
    if ext in _PPTX_SUPPORTED:
        return image_path, None

    try:
        from PIL import Image

        image = Image.open(image_path).convert("RGBA")
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        image.save(tmp.name, format="PNG")
        tmp.close()
        return tmp.name, tmp.name
    except Exception as exc:
        raise RuntimeError(f"Tidak dapat mengonversi gambar '{image_path}': {exc}") from exc


class BackgroundRenderer:
    def render(self, slide, prs: Presentation, slide_item: SlideItem, style: dict) -> None:
        background = self._resolve_background(slide_item, style)
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = _rgb(background.color or "#000000")

        if background.image and os.path.exists(background.image):
            self._add_image(slide, prs, background.image)

        if background.overlay_opacity > 0:
            overlay = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Emu(0),
                Emu(0),
                prs.slide_width,
                prs.slide_height,
            )
            overlay.fill.solid()
            overlay.fill.fore_color.rgb = _rgb(background.overlay_color)
            overlay.fill.transparency = int(max(0.0, min(background.overlay_opacity, 1.0)) * 100)
            overlay.line.fill.background()

    def _resolve_background(self, slide_item: SlideItem, style: dict) -> SlideBackground:
        style_bg = style.get("background", {})
        background = SlideBackground.from_any(style_bg) or SlideBackground()
        if slide_item.background:
            if slide_item.background.color:
                background.color = slide_item.background.color
            if slide_item.background.image:
                background.image = slide_item.background.image
            background.overlay_color = slide_item.background.overlay_color or background.overlay_color
            background.overlay_opacity = slide_item.background.overlay_opacity
        return background

    def _add_image(self, slide, prs: Presentation, image_path: str) -> None:
        use_path, tmp_path = _ensure_supported_image(image_path)
        try:
            picture = slide.shapes.add_picture(use_path, Emu(0), Emu(0), prs.slide_width, prs.slide_height)
            sp_tree = slide.shapes._spTree
            sp_tree.remove(picture._element)
            sp_tree.insert(2, picture._element)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)


class TextRenderer:
    REFERENCE_WIDTH = 10.0
    REFERENCE_HEIGHT = 10.0

    def render(self, slide, prs: Presentation, slide_item: SlideItem, style: dict) -> None:
        left, top, width, height = self._scaled_margin(prs, style.get("margin", {}))
        font_size = int(style.get("font_size", 42))

        if style.get("text_shadow"):
            self._render_text_box(slide, slide_item, style, left + Inches(0.04), top + Inches(0.04), width, height, font_size, "#000000", True)
        self._render_text_box(slide, slide_item, style, left, top, width, height, font_size, style.get("color", "#FFFFFF"), False)

    def _scaled_margin(self, prs: Presentation, margin: dict):
        slide_width = prs.slide_width / Inches(1)
        slide_height = prs.slide_height / Inches(1)
        scale_x = slide_width / self.REFERENCE_WIDTH
        scale_y = slide_height / self.REFERENCE_HEIGHT
        return (
            Inches(float(margin.get("left", 0.8)) * scale_x),
            Inches(float(margin.get("top", 0.8)) * scale_y),
            Inches(float(margin.get("width", 8.4)) * scale_x),
            Inches(float(margin.get("height", 8.4)) * scale_y),
        )

    def _render_text_box(self, slide, slide_item: SlideItem, style: dict, left, top, width, height, font_size: int, color: str, shadow: bool) -> None:
        box = slide.shapes.add_textbox(left, top, width, height)
        frame = box.text_frame
        frame.clear()
        frame.word_wrap = True
        frame.vertical_anchor = MSO_ANCHOR.MIDDLE if style.get("vertical_align") == "middle" else MSO_ANCHOR.TOP

        if slide_item.speaker_lines:
            self._render_speaker_lines(frame, slide_item, style, font_size, shadow)
        else:
            self._render_plain_text(frame, slide_item.content, style, font_size, color, shadow)

    def _render_plain_text(self, frame, content: str, style: dict, font_size: int, color: str, shadow: bool) -> None:
        lines = (content or "").splitlines() or [""]
        for index, line in enumerate(lines):
            paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
            paragraph.alignment = _alignment(style.get("align", "center"))
            run = paragraph.add_run()
            run.text = line
            self._apply_font(run, style, font_size, color, shadow)

    def _render_speaker_lines(self, frame, slide_item: SlideItem, style: dict, font_size: int, shadow: bool) -> None:
        speaker_colors = style.get("speaker_colors", {})
        last_speaker = ""
        for index, speaker_line in enumerate(slide_item.speaker_lines):
            speaker = (speaker_line.speaker or "").strip()
            if speaker:
                last_speaker = speaker
            effective_speaker = speaker or last_speaker
            line_color = speaker_colors.get(effective_speaker, style.get("color", "#FFFFFF"))
            paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
            paragraph.alignment = self._speaker_alignment(effective_speaker)
            if speaker:
                speaker_run = paragraph.add_run()
                speaker_run.text = f"{speaker} : "
                self._apply_font(
                    speaker_run,
                    {**style, "bold": True},
                    font_size,
                    line_color,
                    shadow,
                )
            text_run = paragraph.add_run()
            text_run.text = speaker_line.text
            self._apply_font(
                text_run,
                style,
                font_size,
                line_color,
                shadow,
            )

    def _apply_font(self, run, style: dict, font_size: int, color: str, shadow: bool) -> None:
        run.font.name = style.get("font_family", "Segoe UI")
        run.font.size = Pt(font_size)
        run.font.bold = bool(style.get("bold", False))
        run.font.color.rgb = _rgb("#000000" if shadow else color)

    def _speaker_alignment(self, speaker: str) -> PP_ALIGN:
        if speaker == "J":
            return PP_ALIGN.RIGHT
        if "+" in speaker:
            return PP_ALIGN.CENTER
        return PP_ALIGN.LEFT


class PPTXRenderer:
    TRANSITION_XML = {
        "fade": '<p:transition xmlns:p="{ns}" spd="med"><p:fade/></p:transition>',
        "wipe": '<p:transition xmlns:p="{ns}" spd="med"><p:wipe dir="l"/></p:transition>',
        "push": '<p:transition xmlns:p="{ns}" spd="med"><p:push dir="l"/></p:transition>',
        "zoom": '<p:transition xmlns:p="{ns}" spd="med"><p:zoom dir="out"/></p:transition>',
        "morph": (
            '<p:transition xmlns:p="{ns}" xmlns:p14="{p14_ns}" spd="med">'
            '<p:extLst>'
            '<p:ext uri="{{B2D3F22D-AB1C-4A42-A4DB-59C51D907E4D}}">'
            '<p14:morph transition="byObject"/>'
            '</p:ext>'
            '</p:extLst>'
            '</p:transition>'
        ),
    }

    def __init__(self, template_name: str = "gmim_default") -> None:
        self.resolver = TemplateResolver(template_name)
        self.background_renderer = BackgroundRenderer()
        self.text_renderer = TextRenderer()

    def render(
        self,
        slides: SlideDeck | Iterable[SlideItem],
        output_path: str,
        aspect_ratio: str = "square",
        transition: str | None = None,
    ) -> None:
        deck_slides = slides.slides if isinstance(slides, SlideDeck) else list(slides)
        ratio = self.resolver.aspect_ratio(aspect_ratio)
        prs = Presentation()
        prs.slide_width = Inches(ratio["width"])
        prs.slide_height = Inches(ratio["height"])
        blank_layout = prs.slide_layouts[6]

        for slide_item in deck_slides:
            if not slide_item.include:
                continue
            slide = prs.slides.add_slide(blank_layout)
            style = self.resolver.resolve(slide_item)
            self.background_renderer.render(slide, prs, slide_item, style)
            if slide_item.type != SlideType.BLANK:
                self.text_renderer.render(slide, prs, slide_item, style)
            self._apply_transition(slide, transition)

        prs.save(output_path)

    def _apply_transition(self, slide, transition: str | None) -> None:
        if not transition:
            return
        slide_xml = slide._element
        tag = f"{{{PPTX_NS}}}transition"
        for existing in slide_xml.findall(tag):
            slide_xml.remove(existing)
        transition_xml = self.TRANSITION_XML.get(transition, self.TRANSITION_XML["fade"])
        slide_xml.append(etree.fromstring(transition_xml.format(ns=PPTX_NS, p14_ns=PPTX_P14_NS)))
