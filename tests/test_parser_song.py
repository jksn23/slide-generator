from core.models import SlideType
from core.parser import RawBlock, parse_blocks


def test_song_keywords_create_title_and_lyrics_slides():
    deck = parse_blocks(
        [
            RawBlock("TATA IBADAH", "Heading 1", 0),
            RawBlock("NKB 3 Terpujilah Allah", "Normal", 1),
            RawBlock("Terpujilah Allah hikmat-Nya besar", "Normal", 2),
            RawBlock("Kasih-Nya nyata di dalam dunia", "Normal", 3),
        ]
    )

    assert deck.slides[1].type == SlideType.SONG_TITLE
    assert deck.slides[2].type == SlideType.SONG_LYRICS
    assert deck.slides[2].content


def test_song_lyrics_are_split_by_max_lines():
    deck = parse_blocks(
        [
            RawBlock("TATA IBADAH", "Heading 1", 0),
            RawBlock("PKJ 1 Nyanyian Pembuka", "Normal", 1),
            RawBlock("Baris satu\nBaris dua\nBaris tiga\nBaris empat", "Normal", 2),
        ],
        max_lines_per_slide=2,
    )

    lyric_slides = [slide for slide in deck.slides if slide.type == SlideType.SONG_LYRICS]
    assert len(lyric_slides) == 2
    assert all(slide.content for slide in lyric_slides)


def test_song_lyrics_from_separate_docx_paragraphs_are_grouped_by_max_lines():
    deck = parse_blocks(
        [
            RawBlock("TATA IBADAH", "Heading 1", 0),
            RawBlock("PKJ 1 Nyanyian Pembuka", "Normal", 1),
            RawBlock("Baris satu", "Normal", 2),
            RawBlock("Baris dua", "Normal", 3),
            RawBlock("Baris tiga", "Normal", 4),
            RawBlock("Baris empat", "Normal", 5),
            RawBlock("Baris lima", "Normal", 6),
            RawBlock("Baris enam", "Normal", 7),
            RawBlock("Baris tujuh", "Normal", 8),
        ],
        max_lines_per_slide=6,
    )

    lyric_slides = [slide for slide in deck.slides if slide.type == SlideType.SONG_LYRICS]

    assert len(lyric_slides) == 2
    assert lyric_slides[0].content.splitlines() == [
        "Baris satu",
        "Baris dua",
        "Baris tiga",
        "Baris empat",
        "Baris lima",
        "Baris enam",
    ]
    assert lyric_slides[1].content == "Baris tujuh"
