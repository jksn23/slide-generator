from core.models import ServiceDocument, ServiceItem, ServiceSection, SlideDeck, SlideItem, SlideType, SpeakerLine
from core.text_splitter import normalize_content_line, split_visual_lines_to_chunks, wrap_text_to_visual_lines


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

    def build(
        self,
        document: ServiceDocument,
        max_lines_per_slide: int = DEFAULT_MAX_LINES,
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
            self._append_section(deck, section, max_lines_per_slide=max_lines_per_slide)

        if not deck.slides:
            deck.slides.append(
                SlideItem(type=SlideType.COVER, section="Cover", content="Tidak ada teks ditemukan.")
            )
        deck.assign_numbers()
        return deck

    def _append_section(self, deck: SlideDeck, section: ServiceSection, max_lines_per_slide: int) -> None:
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
        for item in section.items:
            item_type = SlideType.from_any(item.type)
            if item_type == SlideType.COVER:
                continue
            if item_type == SlideType.LITURGY_DIALOG:
                speaker_group.append(item)
                continue

            self._flush_speakers(deck, section, speaker_group, max_lines_per_slide)
            speaker_group = []
            self._append_item(deck, section, item, item_type, max_lines_per_slide)

        self._flush_speakers(deck, section, speaker_group, max_lines_per_slide)

    def _append_item(
        self,
        deck: SlideDeck,
        section: ServiceSection,
        item: ServiceItem,
        item_type: SlideType,
        max_lines_per_slide: int,
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

        for chunk in split_visual_lines_to_chunks(content, max_lines=max_lines_per_slide):
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

    def _flush_speakers(
        self,
        deck: SlideDeck,
        section: ServiceSection,
        speaker_items: list[ServiceItem],
        max_lines_per_slide: int,
    ) -> None:
        if not speaker_items:
            return
        lines = [
            SpeakerLine(item.speaker or "", item.content or item.raw_text)
            for item in speaker_items
            if (item.content or item.raw_text or "").strip()
        ]
        lines = self._wrap_speaker_lines(self._merge_speaker_continuations(lines))
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

    def _wrap_speaker_lines(self, lines: list[SpeakerLine]) -> list[SpeakerLine]:
        wrapped: list[SpeakerLine] = []
        for line in lines:
            prefix_width = len(f"{line.speaker} : ") if line.speaker else 0
            for index, text in enumerate(wrap_text_to_visual_lines(line.text, max(18, 42 - prefix_width))):
                wrapped.append(SpeakerLine(line.speaker if index == 0 else "", text))
        return wrapped
