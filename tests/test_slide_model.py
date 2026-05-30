from core.models import (
    ServiceDocument,
    ServiceItem,
    ServiceSection,
    SlideDeck,
    SlideItem,
    SlideType,
    SpeakerLine,
)


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


def test_service_document_json_round_trip_supports_v2_contract():
    document = ServiceDocument(
        service_form="GMIM Bentuk V",
        title="TATA IBADAH MINGGU",
        theme_weekly="Hidup dalam kasih",
        bible_reading="Yohanes 3:16",
        church_name="GMIM Contoh",
        date="31 Mei 2026",
        sections=[
            ServiceSection(
                id="section-1",
                type="section",
                title="PEMBUKAAN",
                content=["P: Marilah kita beribadah."],
                items=[
                    ServiceItem(
                        id="item-1",
                        type="liturgy_dialog",
                        speaker="P",
                        content="Marilah kita beribadah.",
                        raw_text="P: Marilah kita beribadah.",
                    )
                ],
            )
        ],
    )

    restored = ServiceDocument.from_json(document.to_json())

    assert restored.service_form == "GMIM Bentuk V"
    assert restored.theme_weekly == "Hidup dalam kasih"
    assert restored.sections[0].items[0].speaker == "P"
