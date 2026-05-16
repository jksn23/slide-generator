from core.models import SlideDeck, SlideItem, SlideType, SpeakerLine


def test_slide_item_json_round_trip_supports_new_contract():
    slide = SlideItem(
        type=SlideType.LITURGY_DIALOG,
        section="Votum",
        title="Votum dan Salam",
        content="Tuhan menyertai saudara.",
        speaker_lines=[SpeakerLine("P", "Tuhan menyertai saudara.")],
        template="liturgy_dialog",
    )

    restored = SlideItem.from_json(slide.to_json())

    assert restored.type == SlideType.LITURGY_DIALOG
    assert restored.section == "Votum"
    assert restored.speaker_lines[0].speaker == "P"
    assert restored.template == "liturgy_dialog"


def test_slide_item_keeps_legacy_attribute_names_working():
    slide = SlideItem(slide_type=SlideType.BAGIAN, content="PERSIAPAN", included=False)
    slide.bg_image = "assets/backgrounds/persiapan.jpg"

    assert slide.type == SlideType.SECTION
    assert slide.slide_type == SlideType.SECTION
    assert slide.include is False
    assert slide.included is False
    assert slide.bg_image.endswith("persiapan.jpg")


def test_slide_deck_serializes_to_json_with_square_default():
    deck = SlideDeck(slides=[SlideItem(type="cover", content="TATA IBADAH")])
    deck.assign_numbers()

    restored = SlideDeck.from_json(deck.to_json())

    assert restored.aspect_ratio == "square"
    assert restored.slides[0].slide_number == 1
    assert restored.slides[0].type == SlideType.COVER
