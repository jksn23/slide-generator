from core.models import SlideType
from core.parser import RawBlock, parse_blocks
from core.presets import PresetRegistry


def test_preset_registry_lists_required_gmim_presets():
    names = PresetRegistry().names()

    assert "GMIM Bentuk I" in names
    assert "GMIM Bentuk II" in names
    assert "Ibadah Pemuda" in names
    assert "Ibadah Syukur" in names


def test_parser_applies_preset_defaults_to_deck():
    deck = parse_blocks([RawBlock("TATA IBADAH", "Heading 1", 0)], preset_name="GMIM Bentuk III")

    assert deck.preset_name == "GMIM Bentuk III"
    assert deck.template_name == "gmim_dark"
    assert deck.aspect_ratio == "square"


def test_parser_uses_preset_keywords_for_section_type():
    deck = parse_blocks(
        [
            RawBlock("TATA IBADAH", "Heading 1", 0),
            RawBlock("RENUNGAN", "Heading 1", 1),
            RawBlock("Kasih Tuhan besar.", "Normal", 2),
        ],
        preset_name="Ibadah Kolom",
    )

    assert any(slide.type == SlideType.SERMON for slide in deck.slides)
