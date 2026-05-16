from pptx import Presentation

from core.generator import generate_pptx
from core.models import SlideItem, SlideType


def test_generate_pptx_defaults_to_square(tmp_path):
    output = tmp_path / "square.pptx"

    generate_pptx([SlideItem(type=SlideType.COVER, content="TATA IBADAH")], str(output))

    presentation = Presentation(str(output))
    assert presentation.slide_width == presentation.slide_height


def test_generate_pptx_supports_landscape_16_9(tmp_path):
    output = tmp_path / "wide.pptx"

    generate_pptx(
        [SlideItem(type=SlideType.COVER, content="TATA IBADAH")],
        str(output),
        aspect_ratio="landscape_16_9",
    )

    presentation = Presentation(str(output))
    assert presentation.slide_width > presentation.slide_height
