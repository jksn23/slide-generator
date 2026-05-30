from core.models import SlideType
from core.parser import DOCXReader, RawBlock, parse_blocks
from core.readers import DOCXReader as CanonicalDOCXReader
from core.slide_builder import ServiceSlideBuilder
from core.universal_parser import UniversalParser, parse_blocks_to_service_document


def test_raw_block_v2_fields_keep_legacy_constructor_compatible():
    block = RawBlock("PEMBUKAAN", "Heading 1", 7)

    restored = RawBlock.from_dict(block.to_dict())

    assert restored.style_name == "Heading 1"
    assert restored.style == "Heading 1"
    assert restored.index == 7
    assert restored.paragraph_index == 7
    assert restored.source_type == "docx"


def test_universal_parser_outputs_service_document_json():
    document = parse_blocks_to_service_document(
        [
            RawBlock("Tema: Hidup dalam Kasih", "Normal", 0),
            RawBlock("TATA IBADAH MINGGU", "Heading 1", 1),
            RawBlock("PEMBUKAAN", "Heading 1", 2),
            RawBlock("P: Marilah kita beribadah.", "Normal", 3),
            RawBlock("J: Amin.", "Normal", 4),
        ],
        preset_name="GMIM Bentuk V",
    )

    assert document.service_form == "GMIM Bentuk V"
    assert document.theme_weekly == "Hidup dalam Kasih"
    assert document.title == "TATA IBADAH MINGGU"
    assert document.sections[1].title == "PEMBUKAAN"
    assert document.sections[1].items[1].speaker == "P"
    assert document.sections[1].items[2].speaker == "J"
    assert document.to_dict()["sections"][1]["items"][1]["metadata"]["source_type"] == "docx"


def test_service_slide_builder_builds_editable_slide_deck():
    document = UniversalParser().parse(
        [
            RawBlock("TATA IBADAH MINGGU", "Heading 1", 0),
            RawBlock("Menyanyi PKJ No. 146 Bawa Persembahanmu", "Normal", 1),
            RawBlock("Bawa persembahanmu dalam rumah Tuhan.", "Normal", 2),
        ]
    )

    deck = ServiceSlideBuilder().build(document)

    assert deck.slides[0].type == SlideType.COVER
    assert any(slide.type == SlideType.SONG_TITLE for slide in deck.slides)
    assert all(slide.slide_number for slide in deck.slides)


def test_public_docx_reader_is_canonical_reader():
    assert DOCXReader is CanonicalDOCXReader


def test_parse_blocks_uses_service_document_before_slide_deck():
    deck = parse_blocks(
        [
            RawBlock("Tema Mingguan: Hidup Dalam Kasih", "Normal", 0),
            RawBlock("TATA IBADAH GMIM BENTUK V", "Heading 1", 1),
            RawBlock("Menyanyi PKJ No. 146 Bawa Persembahanmu", "Normal", 2),
            RawBlock("Bawa persembahanmu dalam rumah Tuhan.", "Normal", 3),
        ],
        preset_name="GMIM Bentuk V",
    )

    assert deck.metadata["tema mingguan"] == "Hidup Dalam Kasih"
    assert deck.metadata["service_document"]["theme_weekly"] == "Hidup Dalam Kasih"
    assert deck.metadata["service_document"]["service_form"] == "GMIM Bentuk V"
    assert [slide.type for slide in deck.slides] == [
        SlideType.COVER,
        SlideType.SONG_TITLE,
        SlideType.SONG_LYRICS,
    ]
