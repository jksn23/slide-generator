from core.models import SlideType
from core.parser import DEFAULT_MAX_CHARS_PER_LINE, BlockClassifier, RawBlock, SectionDetector, SlideBuilder, parse_blocks


def test_slide_builder_outputs_ordered_non_empty_slides():
    blocks = [
        RawBlock("TATA IBADAH", "Heading 1", 0),
        RawBlock("PERSIAPAN", "Heading 1", 1),
        RawBlock("P: Marilah kita beribadah.", "Normal", 2),
    ]
    classified = SectionDetector(BlockClassifier()).detect(blocks)

    deck = SlideBuilder().build(classified)

    assert [slide.slide_number for slide in deck.slides] == [1, 2, 3]
    assert all(slide.content for slide in deck.slides)


def test_slide_builder_keeps_bible_reading_from_becoming_song_lyrics():
    blocks = [
        RawBlock("TATA IBADAH", "Heading 1", 0),
        RawBlock("PEMBACAAN ALKITAB", "Heading 1", 1),
        RawBlock("Yohanes 3:16 Karena begitu besar kasih Allah.", "Normal", 2),
    ]
    classified = SectionDetector(BlockClassifier()).detect(blocks)

    deck = SlideBuilder().build(classified)

    assert deck.slides[-1].type == SlideType.BIBLE_READING


def test_slide_builder_keeps_long_creed_within_max_lines_per_slide():
    creed = (
        "Aku percaya kepada satu Allah Bapa, Yang Mahakuasa, Pencipta langit dan bumi, "
        "segala yang kelihatan dan yang tidak kelihatan. Dan kepada satu TUHAN, Yesus Kristus, "
        "Anak Allah yang tunggal, yang lahir dari Sang Bapa sebelum ada segala zaman, "
        "Allah dari Allah, Terang dari terang, Allah yang sejati dari Allah yang sejati, "
        "diperanakkan, bukan dibuat, sehakekat dengan sang Bapa, yang dengan perantaraan-Nya "
        "segala sesuatu dibuat; yang telah turun dari sorga untuk kita manusia dan untuk keselamatan kita,"
    )

    deck = parse_blocks(
        [
            RawBlock("TATA IBADAH", "Heading 1", 0),
            RawBlock("PEMBACAAN ALKITAB", "Heading 1", 1),
            RawBlock(creed, "Normal", 2),
        ],
        max_lines_per_slide=7,
    )

    reading_slides = [slide for slide in deck.slides if slide.type == SlideType.BIBLE_READING]

    assert len(reading_slides) > 1
    assert all(len(slide.content.splitlines()) <= 7 for slide in reading_slides)
    assert all(
        len(line) <= DEFAULT_MAX_CHARS_PER_LINE
        for slide in reading_slides
        for line in slide.content.splitlines()
    )


def test_slide_builder_enforces_max_lines_for_body_slide_types():
    long_text = (
        "Satu dua tiga empat lima enam tujuh delapan sembilan sepuluh sebelas dua belas "
        "tiga belas empat belas lima belas enam belas tujuh belas delapan belas sembilan belas dua puluh. "
        "Dua puluh satu dua puluh dua dua puluh tiga dua puluh empat dua puluh lima dua puluh enam."
    )
    blocks = [
        RawBlock("TATA IBADAH", "Heading 1", 0),
        RawBlock("NKB 3 Terpujilah Allah", "Normal", 1),
        RawBlock(long_text, "Normal", 2),
        RawBlock("DOA PENYEMBAHAN", "Normal", 3, has_bold=True),
        RawBlock(long_text, "Normal", 4),
        RawBlock("NAS PEMBIMBING", "Normal", 5, has_bold=True),
        RawBlock(long_text, "Normal", 6),
        RawBlock("BERKAT", "Normal", 7, has_bold=True),
        RawBlock(long_text, "Normal", 8),
    ]

    deck = parse_blocks(blocks, max_lines_per_slide=6)
    checked_types = {SlideType.SONG_LYRICS, SlideType.PRAYER, SlideType.BIBLE_READING, SlideType.BLESSING}

    assert any(slide.type == SlideType.SONG_LYRICS for slide in deck.slides)
    assert all(
        len(slide.content.splitlines()) <= 6
        for slide in deck.slides
        if slide.type in checked_types
    )
