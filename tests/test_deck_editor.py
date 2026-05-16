from core.deck_editor import DeckEditor
from core.models import SlideDeck, SlideItem, SlideType
from core.template_engine import TemplateResolver


def _deck():
    deck = SlideDeck(
        slides=[
            SlideItem(type=SlideType.COVER, content="Cover"),
            SlideItem(type=SlideType.SECTION, content="Persiapan"),
            SlideItem(type=SlideType.LITURGY_DIALOG, content="Amin"),
        ]
    )
    deck.assign_numbers()
    return deck


def test_deck_editor_updates_content_type_section_and_alignment():
    deck = _deck()
    target = deck.slides[1]

    updated = DeckEditor(deck).update_slide(
        target.id,
        title="Pembukaan",
        content="PERSIAPAN BARU",
        slide_type="prayer",
        section="Persiapan",
        alignment="left",
    )

    assert updated.title == "Pembukaan"
    assert updated.content == "PERSIAPAN BARU"
    assert updated.type == SlideType.PRAYER
    assert TemplateResolver().resolve(updated)["align"] == "left"


def test_deck_editor_duplicate_delete_and_move_keep_numbers():
    deck = _deck()
    editor = DeckEditor(deck)
    duplicate = editor.duplicate(deck.slides[0].id)
    editor.move(duplicate.id, 1)
    editor.delete(deck.slides[-1].id)

    assert len(deck.slides) == 3
    assert [slide.slide_number for slide in deck.slides] == [1, 2, 3]
    assert duplicate in deck.slides
