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


def test_deck_editor_split_and_merge_keep_numbers():
    deck = SlideDeck(
        slides=[
            SlideItem(type=SlideType.SONG_LYRICS, content="baris satu\nbaris dua\nbaris tiga\nbaris empat")
        ]
    )
    deck.assign_numbers()
    editor = DeckEditor(deck)

    new_slide = editor.split(deck.slides[0].id, split_at_line=2)
    merged = editor.merge(deck.slides[0].id, new_slide.id)

    assert len(deck.slides) == 1
    assert merged.content == "baris satu\nbaris dua\nbaris tiga\nbaris empat"
    assert deck.slides[0].slide_number == 1
