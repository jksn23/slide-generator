from copy import deepcopy
from typing import Any
import uuid

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
        template: str | None = None,
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
        if template is not None:
            slide.template = template
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

    def split(self, slide_id: str, split_at_line: int | None = None) -> SlideItem:
        slide = self.get(slide_id)
        lines = slide.content.splitlines()
        if len(lines) < 2:
            words = slide.content.split()
            if len(words) < 2:
                raise ValueError("Slide content is too short to split")
            midpoint = max(1, len(words) // 2)
            lines = [" ".join(words[:midpoint]), " ".join(words[midpoint:])]

        split_at = split_at_line if split_at_line is not None else max(1, len(lines) // 2)
        split_at = max(1, min(split_at, len(lines) - 1))
        first = "\n".join(lines[:split_at]).strip()
        second = "\n".join(lines[split_at:]).strip()
        if not first or not second:
            raise ValueError("Split would create an empty slide")

        slide.content = first
        slide.speaker_lines = []
        new_slide = deepcopy(slide)
        new_slide.id = f"slide-{uuid.uuid4().hex[:10]}"
        new_slide.content = second
        new_slide.speaker_lines = []
        index = self._index(slide_id)
        self.deck.slides.insert(index + 1, new_slide)
        self.deck.assign_numbers()
        return new_slide

    def merge(self, slide_id: str, next_slide_id: str | None = None) -> SlideItem:
        index = self._index(slide_id)
        next_index = self._index(next_slide_id) if next_slide_id else index + 1
        if next_index <= index or next_index >= len(self.deck.slides):
            raise ValueError("No following slide available to merge")
        slide = self.deck.slides[index]
        next_slide = self.deck.slides.pop(next_index)
        slide.content = "\n".join(part for part in [slide.content, next_slide.content] if part).strip()
        slide.speaker_lines.extend(next_slide.speaker_lines)
        self.deck.assign_numbers()
        return slide

    def get(self, slide_id: str) -> SlideItem:
        return self.deck.slides[self._index(slide_id)]

    def _index(self, slide_id: str) -> int:
        for index, slide in enumerate(self.deck.slides):
            if slide.id == slide_id:
                return index
        raise KeyError(f"Slide not found: {slide_id}")
