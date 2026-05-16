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


def test_section_detector_marks_bold_keyword_headings():
    blocks = [
        RawBlock("NAS PEMBIMBING", "Normal", 0, has_bold=True),
        RawBlock("Mazmur 9:8-9", "Normal", 1),
        RawBlock("TAHBISAN DAN SALAM", "Normal", 2, has_bold=True),
    ]

    detected = SectionDetector().detect(blocks)

    assert detected[0].kind == "section"
    assert detected[0].slide_type == SlideType.BIBLE_READING
    assert detected[1].section == "NAS PEMBIMBING"
    assert detected[2].kind == "section"
    assert detected[2].slide_type == SlideType.LITURGY_DIALOG


def test_required_bold_heading_keywords_are_detected():
    expected = {
        "NAS PEMBIMBING": SlideType.BIBLE_READING,
        "TAHBISAN DAN SALAM": SlideType.LITURGY_DIALOG,
        "DOA PENYEMBAHAN": SlideType.PRAYER,
        "PENGAKUAN DOSA": SlideType.PRAYER,
        "JANJI ANUGERAH ALLAH": SlideType.BIBLE_READING,
        "PUJI-PUJIAN": SlideType.SONG_TITLE,
        "FIRMAN TUHAN": SlideType.SERMON,
        "PERSEMBAHAN": SlideType.OFFERING,
        "BERKAT": SlideType.BLESSING,
        "SAAT TEDUH": SlideType.PRAYER,
        "WARTA JEMAAT": SlideType.ANNOUNCEMENT,
        "KHOTBAH": SlideType.SERMON,
    }

    detected = SectionDetector().detect(
        [RawBlock(text, "Normal", index, has_bold=True) for index, text in enumerate(expected)]
    )

    assert [block.slide_type for block in detected] == list(expected.values())
