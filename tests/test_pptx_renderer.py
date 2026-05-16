from pptx import Presentation

from core.generator import generate_pptx
from core.models import SlideItem, SlideType, SpeakerLine


def _shape_texts(presentation):
    return "\n".join(shape.text for slide in presentation.slides for shape in slide.shapes if hasattr(shape, "text"))


def test_pptx_renderer_uses_template_and_creates_square_slide(tmp_path):
    output = tmp_path / "rendered.pptx"

    generate_pptx(
        [
            SlideItem(type=SlideType.COVER, content="TATA IBADAH"),
            SlideItem(type=SlideType.SONG_LYRICS, content="Haleluya\nAmin"),
        ],
        str(output),
    )

    presentation = Presentation(str(output))
    assert len(presentation.slides) == 2
    assert presentation.slide_width == presentation.slide_height
    assert "Haleluya" in _shape_texts(presentation)


def test_pptx_renderer_outputs_rich_speaker_text(tmp_path):
    output = tmp_path / "speaker.pptx"

    generate_pptx(
        [
            SlideItem(
                type=SlideType.LITURGY_DIALOG,
                content="Tuhan menyertai saudara.",
                speaker="P",
                speaker_lines=[SpeakerLine("P", "Tuhan menyertai saudara.")],
            )
        ],
        str(output),
    )

    presentation = Presentation(str(output))
    text = _shape_texts(presentation)
    assert "P :" in text
    assert "Tuhan menyertai saudara." in text


def test_generate_pptx_applies_ui_font_overrides(tmp_path):
    output = tmp_path / "font_override.pptx"

    generate_pptx(
        [SlideItem(type=SlideType.COVER, content="TATA IBADAH")],
        str(output),
        font_family="Arial",
        font_sizes={"title": 72, "lyric": 44, "liturgi": 36},
    )

    presentation = Presentation(str(output))
    text_shape = next(shape for shape in presentation.slides[0].shapes if hasattr(shape, "text") and shape.text)
    run = text_shape.text_frame.paragraphs[0].runs[0]
    assert run.font.name == "Arial"
    assert run.font.size.pt == 72


def test_export_text_box_is_centered_on_landscape_slide(tmp_path):
    output = tmp_path / "centered_wide.pptx"

    generate_pptx(
        [SlideItem(type=SlideType.SONG_TITLE, content="Menyanyi KJ No. 4\nHai Mari Sembah")],
        str(output),
        aspect_ratio="landscape_16_9",
    )

    presentation = Presentation(str(output))
    text_shape = next(shape for shape in presentation.slides[0].shapes if hasattr(shape, "text") and shape.text)
    shape_center_x = text_shape.left + text_shape.width // 2
    shape_center_y = text_shape.top + text_shape.height // 2
    slide_center_x = presentation.slide_width // 2
    slide_center_y = presentation.slide_height // 2
    tolerance = presentation.slide_width * 0.01

    assert abs(shape_center_x - slide_center_x) <= tolerance
    assert abs(shape_center_y - slide_center_y) <= tolerance
