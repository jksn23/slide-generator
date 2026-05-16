from core.models import SlideType
from core.parser import RawBlock, SectionDetector


def test_section_detector_marks_bible_reading_section():
    blocks = [
        RawBlock("TATA IBADAH", "Heading 1", 0),
        RawBlock("PEMBACAAN ALKITAB", "Heading 1", 1),
    ]

    detected = SectionDetector().detect(blocks)

    assert detected[1].kind == "section"
    assert detected[1].slide_type == SlideType.BIBLE_READING


def test_section_detector_uses_current_section_for_body_blocks():
    blocks = [
        RawBlock("TATA IBADAH", "Heading 1", 0),
        RawBlock("DOA SYAFAAT", "Heading 1", 1),
        RawBlock("Ya Tuhan, dengarkanlah doa kami.", "Normal", 2),
    ]

    detected = SectionDetector().detect(blocks)

    assert detected[2].section == "DOA SYAFAAT"
