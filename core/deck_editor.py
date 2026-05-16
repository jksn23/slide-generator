from copy import deepcopy
from typing import Any

from core.models import SlideBackground, SlideDeck, SlideItem, SlideType


class DeckEditor:
    def __init__(self, deck: SlideDeck) -> None:
        self.deck = deck

    def update_slide(
        self,
        slide_id: str,
        *,
        title: str | None = None,
        content: str | None = None,
        slide_type: Any = None,
        section: str | None = None,
        background_image: str | None = None,
        background_color: str | None = None,
        alignment: str | None = None,
    ) -> SlideItem:
        slide = self.get(slide_id)
        if title is not None:
            slide.title = title
        if content is not None:
            slide.content = content
            for line in slide.speaker_lines:
                line.text = content
        if slide_type is not None:
            slide.type = SlideType.from_any(slide_type)
            slide.template = slide.type.value
        if section is not None:
            slide.section = section
        if background_image:
            slide.bg_image = background_image
        if background_color:
            slide.background = slide.background or SlideBackground()
            slide.background.color = background_color
        if alignment:
            slide.metadata.setdefault("style", {})["align"] = alignment
        return slide

    def duplicate(self, slide_id: str) -> SlideItem:
        slide = deepcopy(self.get(slide_id))
        slide.id = f"{slide.id}-copy"
        index = self._index(slide_id)
        self.deck.slides.insert(index + 1, slide)
        self.deck.assign_numbers()
        return slide

    def delete(self, slide_id: str) -> None:
        index = self._index(slide_id)
        del self.deck.slides[index]
        self.deck.assign_numbers()

    def move(self, slide_id: str, direction: int) -> None:
        index = self._index(slide_id)
        new_index = max(0, min(len(self.deck.slides) - 1, index + direction))
        if new_index == index:
            return
        slide = self.deck.slides.pop(index)
        self.deck.slides.insert(new_index, slide)
        self.deck.assign_numbers()

    def get(self, slide_id: str) -> SlideItem:
        return self.deck.slides[self._index(slide_id)]

    def _index(self, slide_id: str) -> int:
        for index, slide in enumerate(self.deck.slides):
            if slide.id == slide_id:
                return index
        raise KeyError(f"Slide not found: {slide_id}")
