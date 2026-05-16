from copy import deepcopy

from core.models import SlideType
from core.renderers import PPTXRenderer


def _font_size_for_slide(slide_type: SlideType, font_sizes: dict | None) -> int | None:
    if not font_sizes:
        return None
    if slide_type in {
        SlideType.COVER,
        SlideType.SECTION,
        SlideType.SONG_TITLE,
        SlideType.BLESSING,
        SlideType.CLOSING,
    }:
        return font_sizes.get("title")
    if slide_type == SlideType.SONG_LYRICS:
        return font_sizes.get("lyric")
    return font_sizes.get("liturgi")


def _apply_font_overrides(slides: list, font_family: str, font_sizes: dict | None) -> list:
    rendered_slides = []
    for slide in slides:
        copied = deepcopy(slide)
        style = copied.metadata.setdefault("style", {})
        if font_family:
            style["font_family"] = font_family
        font_size = _font_size_for_slide(copied.type, font_sizes)
        if font_size:
            style["font_size"] = font_size
        rendered_slides.append(copied)
    return rendered_slides


def generate_pptx(
    slides: list,
    output_path: str,
    font_family: str = "Segoe UI",
    font_sizes: dict = None,
    transition: str = None,
    template_name: str = "gmim_default",
    aspect_ratio: str = "square",
):
    renderer = PPTXRenderer(template_name=template_name)
    rendered_slides = _apply_font_overrides(slides, font_family, font_sizes)
    renderer.render(rendered_slides, output_path=output_path, aspect_ratio=aspect_ratio, transition=transition)
