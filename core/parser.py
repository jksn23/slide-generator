import re
from dataclasses import dataclass
from typing import Optional

from core.models import SlideDeck, SlideItem, SlideType, SpeakerLine
from core.presets import PresetRegistry
from core.raw_block import RawBlock
from core.readers import DOCXReader
from core.text_splitter import (
    DEFAULT_MAX_CHARS_PER_LINE,
    max_chars_for_style,
    normalize_content_line,
    split_visual_lines_to_chunks,
    wrap_text_to_visual_lines,
)


def split_long_text(text: str, max_chars_per_line: int = DEFAULT_MAX_CHARS_PER_LINE) -> list[str]:
    """Compatibility wrapper for older tests/imports."""
    return wrap_text_to_visual_lines(text, max_chars_per_line=max_chars_per_line)


def _split_by_words(text: str, max_chars_per_line: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        if not current:
            current = word
        elif len(current) + len(word) + 1 <= max_chars_per_line:
            current = f"{current} {word}"
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _uppercase_ratio(text: str) -> float:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for char in letters if char.isupper()) / len(letters)


@dataclass
class ClassifiedBlock:
    raw: RawBlock
    kind: str
    slide_type: SlideType
    section: str = ""
    speaker: Optional[str] = None
    metadata_key: Optional[str] = None
    metadata_value: Optional[str] = None

    @property
    def text(self) -> str:
        return self.raw.text


class BlockClassifier:
    SONG_RE = re.compile(r"^(menyanyi|nyanyian|kj|nkb|pkj2?|nnbt|mazmur|hymne|kidung)\b", re.I)
    SPEAKER_RE = re.compile(r"^(P|J|P\+J|PK|p|Calon|L|S)\s*[:\t ]+(.*)$")
    DATE_RE = re.compile(r"\b(\d{1,2}\s+\w+\s+\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b", re.I)
    SECTION_KEYWORDS = {
        "PEMBUKAAN": SlideType.LITURGY_DIALOG,
        "PERSIAPAN": SlideType.LITURGY_DIALOG,
        "TAHBISAN": SlideType.LITURGY_DIALOG,
        "BERITA ANUGERAH ALLAH": SlideType.PRAYER,
        "PENGANTAR PEMBACAAN ALKITAB DAN KHOTBAH": SlideType.BIBLE_READING,
        "PEMBACAAN ALKITAB DAN KHOTBAH": SlideType.BIBLE_READING,
        "NYANYIAN MASUK": SlideType.LITURGY_DIALOG,
        "NAS PEMBIMBING": SlideType.BIBLE_READING,
        "TAHBISAN DAN SALAM": SlideType.LITURGY_DIALOG,
        "PENGAKUAN DOSA DAN BERITA ANUGERAH ALLAH": SlideType.PRAYER,
        "DOA PENYEMBAHAN": SlideType.PRAYER,
        "DOA UNTUK PEMBACAAN ALKITAB": SlideType.PRAYER,
        "PENGAKUAN DOSA": SlideType.PRAYER,
        "JANJI ANUGERAH ALLAH": SlideType.BIBLE_READING,
        "PEMBACAAN ALKITAB": SlideType.BIBLE_READING,
        "PENGAKUAN IMAN": SlideType.LITURGY_DIALOG,
        "PUJI-PUJIAN": SlideType.SONG_TITLE,
        "FIRMAN TUHAN": SlideType.SERMON,
        "PERSEMBAHAN": SlideType.OFFERING,
        "DOA SYUKUR": SlideType.PRAYER,
        "DOA SYAFAAT": SlideType.PRAYER,
        "KOLEKTE EXTRA": SlideType.OFFERING,
        "PELANTIKAN PANITIA PEMILIHAN PELAYAN KHUSUS": SlideType.LITURGY_DIALOG,
        "PENGAJARAN": SlideType.LITURGY_DIALOG,
        "PERTANYAAN-PERTANYAAN PELANTIKAN": SlideType.LITURGY_DIALOG,
        "PERTANYAAAN-PERTANYAAN PELANTIKAN": SlideType.LITURGY_DIALOG,
        "PELANTIKAN": SlideType.LITURGY_DIALOG,
        "NASEHAT DAN PENYERAHAN TUGAS-TUGAS": SlideType.LITURGY_DIALOG,
        "DOA UMUM": SlideType.PRAYER,
        "NYANYIAN PENUTUP": SlideType.LITURGY_DIALOG,
        "PENUTUP": SlideType.CLOSING,
        "SALAM DAN BERKAT": SlideType.BLESSING,
        "BERKAT": SlideType.BLESSING,
        "SAAT TEDUH": SlideType.PRAYER,
        "WARTA JEMAAT": SlideType.ANNOUNCEMENT,
        "KHOTBAH": SlideType.SERMON,
    }

    TYPE_BY_PRESET_KEY = {
        "song_title": SlideType.SONG_TITLE,
        "notice": SlideType.NOTICE,
        "prayer": SlideType.PRAYER,
        "bible_reading": SlideType.BIBLE_READING,
        "sermon": SlideType.SERMON,
        "offering": SlideType.OFFERING,
        "announcement": SlideType.ANNOUNCEMENT,
        "blessing": SlideType.BLESSING,
        "closing": SlideType.CLOSING,
    }

    def __init__(self, preset_name: str = "GMIM Bentuk I") -> None:
        self.preset_name = preset_name
        try:
            self.preset_keywords = PresetRegistry().keywords(preset_name)
        except KeyError:
            self.preset_keywords = {}

    def classify(self, block: RawBlock, has_cover: bool = False) -> ClassifiedBlock:
        text = block.text.strip()
        lower = text.lower()
        upper = text.upper()

        metadata = self._metadata(text)
        if metadata:
            key, value = metadata
            return ClassifiedBlock(block, "metadata", SlideType.COVER, metadata_key=key, metadata_value=value)

        speaker_match = self.SPEAKER_RE.match(text)
        if speaker_match:
            speaker = self._normalize_speaker(speaker_match.group(1))
            speaker_text = normalize_content_line(speaker_match.group(2).strip().lstrip(" ,.-"))
            if self._is_speaker_song_title_text(speaker_text):
                return ClassifiedBlock(
                    RawBlock(speaker_text, block.style_name, block.index),
                    "song_title",
                    SlideType.SONG_TITLE,
                    section=speaker_text,
                )
            return ClassifiedBlock(
                RawBlock(speaker_text, block.style_name, block.index),
                "speaker",
                SlideType.LITURGY_DIALOG,
                speaker=speaker,
            )

        if self._is_indented_text(block.text):
            return ClassifiedBlock(block, "body", SlideType.LITURGY_DIALOG)

        if self._is_song_title_text(text):
            return ClassifiedBlock(
                RawBlock(text, block.style_name, block.index),
                "song_title",
                SlideType.SONG_TITLE,
                section=text,
            )

        if self._is_notice(text, lower):
            return ClassifiedBlock(
                RawBlock(text, block.style_name, block.index),
                "notice",
                SlideType.START if "mulai ibadah" in lower else SlideType.NOTICE,
            )

        if not has_cover and self._is_cover_title(upper):
            return ClassifiedBlock(RawBlock(text, block.style_name, block.index), "cover", SlideType.COVER)

        if self._is_heading(block, text):
            return ClassifiedBlock(
                RawBlock(text, block.style_name, block.index),
                "section",
                self._section_type(upper),
                section=text,
            )

        if not has_cover:
            return ClassifiedBlock(block, "cover", SlideType.COVER)

        return ClassifiedBlock(block, "body", SlideType.LITURGY_DIALOG)

    def _metadata(self, text: str) -> Optional[tuple[str, str]]:
        match = re.match(
            r"^(bentuk(?:\s+ibadah)?|tata ibadah|tema(?:\s+(?:bulanan|bulan|mingguan))?|khadim|pelayan|tanggal|hari/tanggal|bacaan(?:\s+alkitab)?|gereja|nama gereja|jemaat)\s*:\s*(.+)$",
            text,
            re.I,
        )
        if match:
            return match.group(1).lower(), match.group(2).strip()
        form_match = re.search(r"\b(GMIM\s+)?BENTUK\s+([IVX]+|\d+)\b", text, re.I)
        if form_match and len(text) <= 80:
            if "TATA IBADAH" in text.upper():
                return None
            return "bentuk ibadah", form_match.group(0).strip()
        if self.DATE_RE.search(text) and len(text) <= 60:
            return "tanggal", text
        return None

    def _is_notice(self, text: str, lower: str) -> bool:
        return (
            "dimohon untuk" in lower
            or "mulai ibadah" in lower
            or text.startswith(("(", "[", "*"))
        )

    def _is_heading(self, block: RawBlock, text: str) -> bool:
        upper = text.upper()
        return (
            block.style_name.startswith("Heading")
            or self._has_section_heading_keyword(block, text, upper)
            or (block.has_bold and len(text) <= 90 and block.uppercase_ratio >= 0.65)
            or (text.isupper() and len(text) <= 90)
            or (block.max_font_size is not None and block.max_font_size >= 14 and block.uppercase_ratio >= 0.65)
        )

    def _has_section_heading_keyword(self, block: RawBlock, text: str, upper: str) -> bool:
        if not any(keyword in upper for keyword in self.SECTION_KEYWORDS):
            return False
        return (
            block.style_name.startswith("Heading")
            or block.has_bold
            or text.isupper()
            or block.uppercase_ratio >= 0.65
        )

    def _is_cover_title(self, upper: str) -> bool:
        return "TATA IBADAH" in upper or upper.startswith("IBADAH ")

    def _looks_like_bible_reference(self, text: str) -> bool:
        return bool(re.search(r"\b\d+\s*:\s*\d+", text))

    def _is_song_title_text(self, text: str) -> bool:
        return bool(text and not self._looks_like_bible_reference(text) and (
            self.SONG_RE.match(text)
            or re.search(r"\bmenyanyi\b", text, re.I)
        ))

    def _is_speaker_song_title_text(self, text: str) -> bool:
        return bool(text and not self._looks_like_bible_reference(text) and self.SONG_RE.match(text))

    def _normalize_speaker(self, speaker: str) -> str:
        if speaker in {"p", "Calon"}:
            return speaker
        return speaker.upper().replace(" ", "")

    def _is_indented_text(self, text: str) -> bool:
        return bool(text and text[0] in {"\t", " ", "\xa0"})

    def _section_type(self, upper: str) -> SlideType:
        for keyword, slide_type in self.SECTION_KEYWORDS.items():
            if keyword in upper:
                return slide_type
        for key, keywords in self.preset_keywords.items():
            if any(keyword.upper() in upper for keyword in keywords):
                return self.TYPE_BY_PRESET_KEY.get(key, SlideType.SECTION)
        if any(word in upper for word in ("BACAAN", "ALKITAB", "MAZMUR")):
            return SlideType.BIBLE_READING
        if any(word in upper for word in ("DOA", "PERSIAPAN", "PANGGILAN", "VOTUM", "SALAM")):
            return SlideType.PRAYER
        if any(word in upper for word in ("PERSEMBAHAN", "SYUKUR")):
            return SlideType.OFFERING
        if any(word in upper for word in ("KHOTBAH", "FIRMAN", "RENUNGAN")):
            return SlideType.SERMON
        if any(word in upper for word in ("PENGUMUMAN", "WARTA")):
            return SlideType.ANNOUNCEMENT
        if any(word in upper for word in ("BERKAT", "PENGUTUSAN")):
            return SlideType.BLESSING
        if any(word in upper for word in ("PENUTUP", "AMIN")):
            return SlideType.CLOSING
        if any(word in upper for word in ("LAGU", "MENYANYI", "KJ ", "NKB ", "PKJ ", "NNBT")):
            return SlideType.SONG_TITLE
        return SlideType.SECTION


class SectionDetector:
    def __init__(self, classifier: Optional[BlockClassifier] = None, preset_name: str = "GMIM Bentuk I") -> None:
        self.classifier = classifier or BlockClassifier(preset_name=preset_name)

    def detect(self, blocks: list[RawBlock]) -> list[ClassifiedBlock]:
        current_section = ""
        has_cover = False
        classified: list[ClassifiedBlock] = []

        for block in blocks:
            item = self.classifier.classify(block, has_cover=has_cover)
            if item.kind in {"cover", "section", "song_title", "notice", "speaker", "body"}:
                has_cover = True
            if item.kind in {"section", "song_title"}:
                current_section = item.section or item.text
            item.section = item.section or current_section
            classified.append(item)
        return classified


class SlideBuilder:
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

    BODY_TYPE_BY_SECTION = {
        SlideType.SONG_TITLE: SlideType.SONG_LYRICS,
        SlideType.BIBLE_READING: SlideType.BIBLE_READING,
        SlideType.PRAYER: SlideType.PRAYER,
        SlideType.OFFERING: SlideType.OFFERING,
        SlideType.SERMON: SlideType.SERMON,
        SlideType.ANNOUNCEMENT: SlideType.ANNOUNCEMENT,
        SlideType.BLESSING: SlideType.BLESSING,
        SlideType.CLOSING: SlideType.CLOSING,
    }

    def build(
        self,
        blocks: list[ClassifiedBlock],
        max_lines_per_slide: int = 6,
        aspect_ratio: str = "square",
    ) -> SlideDeck:
        max_lines_per_slide = max(1, int(max_lines_per_slide or 1))
        deck = SlideDeck()
        current_body_type = SlideType.LITURGY_DIALOG
        current_section = ""
        cover_lines: list[str] = []
        dialog_lines: list[SpeakerLine] = []
        pending_dialog_speaker: Optional[str] = None
        body_lines: list[str] = []
        body_type = SlideType.LITURGY_DIALOG
        body_section = ""
        body_template = ""

        def flush_dialog() -> None:
            nonlocal dialog_lines, pending_dialog_speaker
            if not dialog_lines:
                pending_dialog_speaker = None
                return
            chunk: list[SpeakerLine] = []
            active_speaker = ""
            max_chars = self._max_chars_for_slide(SlideType.LITURGY_DIALOG, aspect_ratio)
            for line in self._chunk_dialog_lines(dialog_lines, max_chars):
                speaker = line.speaker
                if speaker:
                    active_speaker = speaker
                elif not chunk and active_speaker:
                    speaker = active_speaker
                if speaker:
                    active_speaker = speaker
                chunk.append(SpeakerLine(speaker, line.text))
                if len(chunk) == max_lines_per_slide:
                    append_dialog_chunk(chunk)
                    chunk = []
            if chunk:
                append_dialog_chunk(chunk)
            dialog_lines = []
            pending_dialog_speaker = None

        def append_dialog_chunk(lines: list[SpeakerLine]) -> None:
            content = self._dialog_content(lines)
            if content.strip():
                deck.slides.append(
                    self._slide(
                        SlideType.LITURGY_DIALOG,
                        content,
                        current_section,
                        "liturgy_dialog",
                        speaker_lines=lines,
                    )
                )

        def flush_body() -> None:
            nonlocal body_lines, body_type, body_section, body_template
            if not body_lines:
                return
            self._append_chunked(
                deck,
                slide_type=body_type,
                text="\n".join(body_lines),
                section=body_section,
                template=body_template,
                max_lines=max_lines_per_slide,
                aspect_ratio=aspect_ratio,
            )
            body_lines = []

        for block in blocks:
            if block.kind == "metadata":
                if block.metadata_key:
                    deck.metadata[block.metadata_key] = block.metadata_value
                continue

            if block.kind == "cover":
                flush_body()
                flush_dialog()
                cover_lines.extend(split_long_text(block.text))
                continue

            if cover_lines:
                deck.slides.append(self._slide(SlideType.COVER, "\n".join(cover_lines), "Cover", "cover"))
                cover_lines = []

            if block.kind == "notice":
                flush_body()
                flush_dialog()
                deck.slides.append(self._slide(block.slide_type, block.text, current_section, block.slide_type.value))
                continue

            if block.kind == "song_title":
                flush_body()
                flush_dialog()
                current_section = block.text
                current_body_type = SlideType.SONG_LYRICS
                deck.slides.append(self._slide(SlideType.SONG_TITLE, block.text, current_section, "song_title", title=block.text))
                continue

            if block.kind == "section":
                flush_body()
                flush_dialog()
                current_section = block.text
                current_body_type = self.BODY_TYPE_BY_SECTION.get(block.slide_type, SlideType.LITURGY_DIALOG)
                if block.slide_type == SlideType.SONG_TITLE:
                    current_body_type = SlideType.SONG_LYRICS
                    deck.slides.append(self._slide(SlideType.SONG_TITLE, block.text, current_section, "song_title", title=block.text))
                else:
                    deck.slides.append(self._slide(SlideType.SECTION, block.text, current_section, "section", title=block.text))
                continue

            if block.kind == "speaker":
                flush_body()
                text = normalize_content_line(block.text)
                if text:
                    dialog_lines.append(SpeakerLine(block.speaker or "", text))
                    pending_dialog_speaker = None
                else:
                    pending_dialog_speaker = block.speaker or None
                continue

            if dialog_lines and self._is_indented_continuation(block.text):
                flush_body()
                text = normalize_content_line(block.text)
                if text:
                    dialog_lines.append(SpeakerLine("", text))
                continue

            if current_body_type == SlideType.LITURGY_DIALOG:
                flush_body()
                text = normalize_content_line(block.text)
                if text:
                    dialog_lines.append(SpeakerLine(pending_dialog_speaker or "", text))
                    pending_dialog_speaker = None
                continue

            flush_dialog()
            body_type = current_body_type
            body_section = current_section
            body_template = current_body_type.value
            text = block.text
            if text:
                body_lines.append(text)

        flush_body()
        flush_dialog()
        if cover_lines:
            deck.slides.append(self._slide(SlideType.COVER, "\n".join(cover_lines), "Cover", "cover"))

        if not deck.slides:
            deck.slides.append(self._slide(SlideType.COVER, "Tidak ada teks ditemukan.", "Cover", "cover"))

        deck.assign_numbers()
        return deck

    def _chunk_dialog_lines(
        self,
        lines: list[SpeakerLine],
        max_chars_per_line: Optional[int] = None,
    ) -> list[SpeakerLine]:
        max_chars_per_line = max_chars_per_line or self._max_chars_for_slide(SlideType.LITURGY_DIALOG)
        rendered: list[SpeakerLine] = []
        for speaker_line in self._merge_dialog_continuations(lines):
            speaker = speaker_line.speaker
            prefix_width = len(f"{speaker} : ") if speaker else 0
            text_width = max(1, max_chars_per_line - prefix_width)
            wrapped_lines = wrap_text_to_visual_lines(speaker_line.text, text_width)
            for index, line in enumerate(wrapped_lines):
                rendered.append(SpeakerLine(speaker if index == 0 else "", line))
        return rendered

    def _merge_dialog_continuations(self, lines: list[SpeakerLine]) -> list[SpeakerLine]:
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

    def _dialog_content(self, lines: list[SpeakerLine]) -> str:
        return "\n".join(
            f"{line.speaker} : {line.text}" if line.speaker else line.text
            for line in lines
            if line.text.strip()
        )

    def _is_indented_continuation(self, text: str) -> bool:
        return bool(text and text[0] in {"\t", " ", "\xa0"})

    def _max_chars_for_slide(self, slide_type: SlideType, aspect_ratio: str = "square") -> int:
        return max_chars_for_style(
            font_size=self.DEFAULT_FONT_SIZE_BY_TYPE.get(slide_type, 40),
            aspect_ratio=aspect_ratio,
        )

    def _append_chunked(
        self,
        deck: SlideDeck,
        slide_type: SlideType,
        text: str,
        section: str,
        template: str,
        max_lines: int,
        speaker: Optional[str] = None,
        aspect_ratio: str = "square",
    ) -> None:
        max_chars = self._max_chars_for_slide(slide_type, aspect_ratio)
        for content in split_visual_lines_to_chunks(
            text,
            max_lines=max_lines,
            max_chars_per_line=max_chars,
        ):
            speaker_lines = [SpeakerLine(speaker, content)] if speaker else []
            deck.slides.append(
                self._slide(
                    slide_type,
                    content,
                    section,
                    template,
                    speaker=speaker,
                    speaker_lines=speaker_lines,
                    is_nyanyian=slide_type == SlideType.SONG_LYRICS,
                )
            )

    def _slide(
        self,
        slide_type: SlideType,
        content: str,
        section: str,
        template: str,
        title: Optional[str] = None,
        speaker: Optional[str] = None,
        speaker_lines: Optional[list[SpeakerLine]] = None,
        is_nyanyian: bool = False,
    ) -> SlideItem:
        return SlideItem(
            type=slide_type,
            section=section,
            title=title,
            content=content,
            speaker=speaker,
            speaker_lines=speaker_lines or [],
            template=template,
            is_nyanyian=is_nyanyian,
        )


def parse_blocks(blocks: list[RawBlock], max_lines_per_slide: int = 6, preset_name: str = "GMIM Bentuk I") -> SlideDeck:
    from core.slide_builder import ServiceSlideBuilder
    from core.universal_parser import parse_blocks_to_service_document

    document = parse_blocks_to_service_document(blocks, preset_name=preset_name)
    try:
        preset = PresetRegistry().get(preset_name)
    except KeyError:
        preset = {}
    aspect_ratio = preset.get("aspect_ratio", "square")
    deck = ServiceSlideBuilder().build(
        document,
        max_lines_per_slide=max_lines_per_slide,
    )
    deck.preset_name = preset_name
    deck.template_name = preset.get("template", deck.template_name)
    deck.aspect_ratio = aspect_ratio
    return deck


def parse_docx_to_deck(file_path: str, max_lines_per_slide: int = 6, preset_name: str = "GMIM Bentuk I") -> SlideDeck:
    blocks = DOCXReader().read(file_path)
    return parse_blocks(blocks, max_lines_per_slide=max_lines_per_slide, preset_name=preset_name)


def parse_docx(file_path: str, max_lines_per_slide: int = 6, preset_name: str = "GMIM Bentuk I") -> list[SlideItem]:
    return parse_docx_to_deck(file_path, max_lines_per_slide=max_lines_per_slide, preset_name=preset_name).slides
