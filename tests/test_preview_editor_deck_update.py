from core.deck_editor import DeckEditor
from core.models import SlideDeck, SlideItem, SlideType


def test_preview_editor_deck_update_operations_are_export_ready():
    deck = SlideDeck(
        slides=[
            SlideItem(type=SlideType.SONG_LYRICS, content="satu\ndua\ntiga", template="song_lyrics"),
            SlideItem(type=SlideType.CLOSING, content="Amin"),
        ]
    )
    deck.assign_numbers()
    editor = DeckEditor(deck)

    updated = editor.update_slide(
        deck.slides[0].id,
        title="Lagu",
        content="satu\ndua\ntiga\nempat",
        slide_type="song_lyrics",
        template="gmim_dark",
    )
    split = editor.split(updated.id, split_at_line=2)
    editor.move(split.id, 1)
    merged = editor.merge(updated.id)
    merged.include = False

    assert merged.template == "gmim_dark"
    assert merged.include is False
    assert [slide.slide_number for slide in deck.slides] == [1, 2]
