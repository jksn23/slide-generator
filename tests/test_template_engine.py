from core.models import SlideItem, SlideType
from core.template_engine import TemplateResolver


def test_template_resolver_loads_gmim_default_and_square_ratio():
    resolver = TemplateResolver("gmim_default")

    ratio = resolver.aspect_ratio()

    assert ratio == {"width": 10, "height": 10}


def test_template_resolver_applies_slide_type_style():
    resolver = TemplateResolver("gmim_default")
    style = resolver.resolve(SlideItem(type=SlideType.SONG_LYRICS, content="Haleluya"))

    assert style["background"]["color"] == "#202322"
    assert style["align"] == "center"
    assert style["font_size"] == 46


def test_template_resolver_applies_section_override():
    resolver = TemplateResolver("gmim_default")
    style = resolver.resolve(
        SlideItem(type=SlideType.BIBLE_READING, section="Pembacaan Alkitab", content="Mazmur 1")
    )

    assert style["background"]["color"] == "#FFFFFF"
    assert style["color"] == "#1E1E1E"
