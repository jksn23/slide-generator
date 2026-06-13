from core.models import ServiceDocument, ServiceItem, ServiceSection, SlideDeck, SlideItem, SlideType, SpeakerLine
from core.text_splitter import max_chars_for_style, normalize_content_line, split_visual_lines_to_chunks, wrap_text_to_visual_lines


class ServiceSlideBuilder:
    """Build editable SlideItems from a ServiceDocument."""

    DEFAULT_MAX_LINES = 6

    SECTION_BODY_TYPES = {
        SlideType.SECTION.value,
        SlideType.PRAYER.value,
        SlideType.BIBLE_READING.value,
        SlideType.SERMON.value,
        SlideType.OFFERING.value,
        SlideType.ANNOUNCEMENT.value,
        SlideType.BLESSING.value,
        SlideType.CLOSING.value,
    }
    DEFAULT_FONT_SIZE_BY_TYPE = {
        SlideType.COVER: 60,
        SlideType.SECTION: 60,
        SlideType.SONG_TITLE: 60,
        SlideType.SONG_LYRICS: 48,
        SlideType.LITURGY_DIALOG: 40,
        SlideType.PRAYER: 40,
        SlideType.BIBLE_READING: 40,
        SlideType.BLESSING: 60,
        SlideType.CLOSING: 60,
        SlideType.OFFERING: 40,
        SlideType.SERMON: 40,
        SlideType.ANNOUNCEMENT: 40,
    }

    def build(
        self,
        document: ServiceDocument,
        max_lines_per_slide: int = DEFAULT_MAX_LINES,
        aspect_ratio: str = "square",
    ) -> SlideDeck:
        deck = SlideDeck(
            metadata={**document.metadata, "service_document": document.to_dict()},
            preset_name=document.service_form or "GMIM Bentuk I",
        )

        if document.title:
            deck.slides.append(
                SlideItem(
                    type=SlideType.COVER,
                    section="Cover",
                    title=document.title,
                    content=document.title,
                    template=SlideType.COVER.value,
                )
            )

        for section in document.sections:
            self._append_section(
                deck,
                section,
                max_lines_per_slide=max_lines_per_slide,
                aspect_ratio=aspect_ratio,
            )

        if not deck.slides:
            deck.slides.append(
                SlideItem(type=SlideType.COVER, section="Cover", content="Tidak ada teks ditemukan.")
            )
        deck.assign_numbers()
        return deck

    def _append_section(
        self,
        deck: SlideDeck,
        section: ServiceSection,
        max_lines_per_slide: int,
        aspect_ratio: str,
    ) -> None:
        module_types = self._module_slide_types(deck)
        body_type = section.metadata.get("body_type")
        for section_name, slide_type in module_types.items():
            if section_name.lower() in section.title.lower() and body_type in {None, "section"}:
                section.metadata["body_type"] = slide_type

        if section.title and section.type not in {"cover", SlideType.SONG_TITLE.value}:
            deck.slides.append(
                SlideItem(
                    type=SlideType.SECTION,
                    section=section.title,
                    title=section.title,
                    content=section.title,
                    template=SlideType.SECTION.value,
                )
            )

        speaker_group: list[ServiceItem] = []
        body_group: list[ServiceItem] = []
        body_group_type: SlideType | None = None
        for item in section.items:
            item_type = SlideType.from_any(item.type)
            if item_type == SlideType.COVER:
                continue
            if item_type == SlideType.LITURGY_DIALOG:
                self._flush_body_items(deck, section, body_group, body_group_type, max_lines_per_slide, aspect_ratio)
                body_group = []
                body_group_type = None
                speaker_group.append(item)
                continue

            self._flush_speakers(deck, section, speaker_group, max_lines_per_slide, aspect_ratio)
            speaker_group = []
            if self._is_groupable_body_item(section, item, item_type):
                if body_group and body_group_type != item_type:
                    self._flush_body_items(deck, section, body_group, body_group_type, max_lines_per_slide, aspect_ratio)
                    body_group = []
                body_group.append(item)
                body_group_type = item_type
                continue

            self._flush_body_items(deck, section, body_group, body_group_type, max_lines_per_slide, aspect_ratio)
            body_group = []
            body_group_type = None
            self._append_item(deck, section, item, item_type, max_lines_per_slide, aspect_ratio)

        self._flush_body_items(deck, section, body_group, body_group_type, max_lines_per_slide, aspect_ratio)
        self._flush_speakers(deck, section, speaker_group, max_lines_per_slide, aspect_ratio)

    def _module_slide_types(self, deck: SlideDeck) -> dict[str, str]:
        modules = deck.metadata.get("service_document", {}).get("modules") or deck.metadata.get("modules") or []
        mapping: dict[str, str] = {}
        for module in modules:
            mapping.update(module.get("default_slide_types") or {})
        return mapping

    def _append_item(
        self,
        deck: SlideDeck,
        section: ServiceSection,
        item: ServiceItem,
        item_type: SlideType,
        max_lines_per_slide: int,
        aspect_ratio: str,
    ) -> None:
        content = item.content or item.raw_text or ""
        if not content.strip():
            return

        if item_type == SlideType.SECTION and content.strip() == section.title.strip():
            return

        if item_type == SlideType.SONG_TITLE:
            deck.slides.append(
                SlideItem(
                    type=SlideType.SONG_TITLE,
                    section=section.title,
                    title=item.title or content,
                    content=content,
                    template=SlideType.SONG_TITLE.value,
                )
            )
            return

        max_chars = self._max_chars_for_slide(item_type, aspect_ratio)
        for chunk in split_visual_lines_to_chunks(
            content,
            max_lines=max_lines_per_slide,
            max_chars_per_line=max_chars,
        ):
            deck.slides.append(
                SlideItem(
                    type=item_type,
                    section=section.title,
                    title=item.title,
                    content=chunk,
                    template=item_type.value,
                    metadata=dict(item.metadata),
                )
            )

    def _is_groupable_body_item(self, section: ServiceSection, item: ServiceItem, item_type: SlideType) -> bool:
        content = item.content or item.raw_text or ""
        if not content.strip():
            return False
        if item_type in {SlideType.COVER, SlideType.SECTION, SlideType.SONG_TITLE, SlideType.LITURGY_DIALOG}:
            return False
        if item_type == SlideType.SECTION and content.strip() == section.title.strip():
            return False
        return True

    def _flush_body_items(
        self,
        deck: SlideDeck,
        section: ServiceSection,
        items: list[ServiceItem],
        item_type: SlideType | None,
        max_lines_per_slide: int,
        aspect_ratio: str,
    ) -> None:
        if not items or item_type is None:
            return
        content = "\n".join(
            (item.content or item.raw_text or "").strip()
            for item in items
            if (item.content or item.raw_text or "").strip()
        )
        if not content.strip():
            return
        metadata = dict(items[0].metadata)
        max_chars = self._max_chars_for_slide(item_type, aspect_ratio)
        for chunk in split_visual_lines_to_chunks(
            content,
            max_lines=max_lines_per_slide,
            max_chars_per_line=max_chars,
        ):
            deck.slides.append(
                SlideItem(
                    type=item_type,
                    section=section.title,
                    title=items[0].title,
                    content=chunk,
                    template=item_type.value,
                    metadata=metadata,
                )
            )

    def _flush_speakers(
        self,
        deck: SlideDeck,
        section: ServiceSection,
        speaker_items: list[ServiceItem],
        max_lines_per_slide: int,
        aspect_ratio: str,
    ) -> None:
        if not speaker_items:
            return
        lines = [
            SpeakerLine(item.speaker or "", item.content or item.raw_text)
            for item in speaker_items
            if (item.content or item.raw_text or "").strip()
        ]
        max_chars = self._max_chars_for_slide(SlideType.LITURGY_DIALOG, aspect_ratio)
        lines = self._wrap_speaker_lines(self._merge_speaker_continuations(lines), max_chars)
        if not lines:
            return
        active_speaker = ""
        line_limit = max(1, max_lines_per_slide)
        for index in range(0, len(lines), line_limit):
            chunk = lines[index:index + max(1, max_lines_per_slide)]
            if chunk and not chunk[0].speaker and active_speaker:
                chunk[0] = SpeakerLine(active_speaker, chunk[0].text)
            for line in chunk:
                if line.speaker:
                    active_speaker = line.speaker
            content = "\n".join(
                f"{line.speaker} : {line.text}" if line.speaker else line.text
                for line in chunk
            )
            deck.slides.append(
                SlideItem(
                    type=SlideType.LITURGY_DIALOG,
                    section=section.title,
                    content=content,
                    speaker_lines=chunk,
                    template=SlideType.LITURGY_DIALOG.value,
                )
            )

    def _merge_speaker_continuations(self, lines: list[SpeakerLine]) -> list[SpeakerLine]:
        merged: list[SpeakerLine] = []
        for line in lines:
            text = normalize_content_line(line.text)
            if not text:
                continue
            if line.speaker or not merged:
                merged.append(SpeakerLine(line.speaker, text))
            else:
                merged[-1].text = f"{merged[-1].text} {text}"
        return merged

    def _wrap_speaker_lines(self, lines: list[SpeakerLine], max_chars_per_line: int = 42) -> list[SpeakerLine]:
        wrapped: list[SpeakerLine] = []
        for line in lines:
            prefix_width = len(f"{line.speaker} : ") if line.speaker else 0
            for index, text in enumerate(wrap_text_to_visual_lines(line.text, max(18, max_chars_per_line - prefix_width))):
                wrapped.append(SpeakerLine(line.speaker if index == 0 else "", text))
        return wrapped

    def _max_chars_for_slide(self, slide_type: SlideType, aspect_ratio: str = "square") -> int:
        return max_chars_for_style(
            font_size=self.DEFAULT_FONT_SIZE_BY_TYPE.get(slide_type, 40),
            aspect_ratio=aspect_ratio,
        )
