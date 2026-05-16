from core.models import SlideType
from core.parser import RawBlock, parse_blocks


def test_liturgy_detects_p_j_and_joint_speaker():
    deck = parse_blocks(
        [
            RawBlock("PERSIAPAN", "Heading 1", 0),
            RawBlock("P: Kasih karunia menyertai kamu.", "Normal", 1),
            RawBlock("J: Dan menyertai saudara juga.", "Normal", 2),
            RawBlock("P+J: Amin.", "Normal", 3),
        ]
    )

    speakers = [slide.speaker for slide in deck.slides if slide.type == SlideType.LITURGY_DIALOG]

    assert speakers == ["P", "J", "P+J"]


def test_liturgy_slide_has_no_empty_content():
    deck = parse_blocks(
        [
            RawBlock("PERSIAPAN", "Heading 1", 0),
            RawBlock("P: Marilah kita beribadah.", "Normal", 1),
        ]
    )

    assert all(slide.content.strip() for slide in deck.slides)
