from core.models import SlideType
from core.parser import DOCXReader, RawBlock, parse_blocks


def test_parser_detects_song_title_and_lyrics():
    deck = parse_blocks(
        [
            RawBlock("TATA IBADAH MINGGU", "Heading 1", 0),
            RawBlock("Menyanyi KJ 1 Haleluya", "Normal", 1),
            RawBlock("Haleluya, pujilah Tuhan", "Normal", 2),
        ]
    )

    assert [slide.type for slide in deck.slides] == [
        SlideType.COVER,
        SlideType.SONG_TITLE,
        SlideType.SONG_LYRICS,
    ]
    assert deck.slides[2].section == "Menyanyi KJ 1 Haleluya"


def test_parser_detects_liturgy_speaker_lines():
    deck = parse_blocks(
        [
            RawBlock("PERSIAPAN", "Heading 1", 0),
            RawBlock("P: Tuhan menyertai saudara.", "Normal", 1),
            RawBlock("J: Dan menyertai saudara juga.", "Normal", 2),
            RawBlock("P+J: Amin.", "Normal", 3),
        ]
    )

    liturgy = [slide for slide in deck.slides if slide.type == SlideType.LITURGY_DIALOG]

    assert [slide.speaker for slide in liturgy] == ["P", "J", "P+J"]
    assert liturgy[0].speaker_lines[0].text == "Tuhan menyertai saudara."


def test_parser_collects_worship_metadata():
    deck = parse_blocks(
        [
            RawBlock("Tema: Bersyukur dalam Pelayanan", "Normal", 0),
            RawBlock("Khadim: Pdt. Contoh", "Normal", 1),
            RawBlock("TATA IBADAH", "Heading 1", 2),
        ]
    )

    assert deck.metadata["tema"] == "Bersyukur dalam Pelayanan"
    assert deck.metadata["khadim"] == "Pdt. Contoh"
    assert deck.slides[0].type == SlideType.COVER


def test_docx_reader_reads_real_docx_fixture():
    blocks = DOCXReader().read("test.docx")

    assert blocks
    assert all(block.text for block in blocks)
