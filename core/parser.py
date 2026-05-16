import re
from dataclasses import dataclass
from typing import Optional

from core.models import SlideDeck, SlideItem, SlideType, SpeakerLine
from core.presets import PresetRegistry


DEFAULT_MAX_CHARS_PER_LINE = 58


def split_long_text(text: str, max_chars_per_line: int = DEFAULT_MAX_CHARS_PER_LINE) -> list[str]:
    """Split a text block into readable lines without breaking punctuation first."""
    result: list[str] = []
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        if len(line) <= max_chars_per_line:
            result.append(line)
            continue

        current = ""
        for part in re.split(r"(?<=[.;?,])\s+", line):
            if len(part) > max_chars_per_line:
                if current:
                    result.append(current)
                    current = ""
                result.extend(_split_by_words(part, max_chars_per_line))
                continue
            if not current:
                current = part
            elif len(current) + len(part) + 1 <= max_chars_per_line:
                current = f"{current} {part}"
            else:
                result.append(current)
                current = part
        if current:
            result.append(current)
    return result


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


@dataclass
class RawBlock:
    text: str
    style_name: str = ""
    index: int = 0
    alignment: Optional[int] = None
    has_bold: bool = False
    max_font_size: Optional[float] = None
    uppercase_ratio: float = 0.0

    def __post_init__(self) -> None:
        if not self.uppercase_ratio:
            self.uppercase_ratio = _uppercase_ratio(self.text)


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


class DOCXReader:
    def read(self, file_path: str) -> list[RawBlock]:
        try:
            import docx
        except ImportError:
            return [RawBlock("Error: python-docx not installed.", "Error", 0)]

        document = docx.Document(file_path)
        blocks: list[RawBlock] = []
        for index, paragraph in enumerate(document.paragraphs):
            text = paragraph.text.strip()
            if text:
                font_sizes = [
                    float(run.font.size.pt)
                    for run in paragraph.runs
                    if run.font.size is not None
                ]
                blocks.append(
                    RawBlock(
                        text=text,
                        style_name=paragraph.style.name,
                        index=index,
                        alignment=paragraph.alignment,
                        has_bold=any(run.bold for run in paragraph.runs),
                        max_font_size=max(font_sizes) if font_sizes else None,
                        uppercase_ratio=_uppercase_ratio(text),
                    )
                )
        return blocks


class BlockClassifier:
    SONG_RE = re.compile(r"^(menyanyi|nyanyian|kj|nkb|pkj2?|nnbt|mazmur|hymne|kidung)\b", re.I)
    SPEAKER_RE = re.compile(r"^(P\+J|P\s*\+\s*J|PK|P|J|L|S)\s*(?::|\s)\s*(.*)$", re.I)
    DATE_RE = re.compile(r"\b(\d{1,2}\s+\w+\s+\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b", re.I)
    SECTION_KEYWORDS = {
        "NAS PEMBIMBING": SlideType.BIBLE_READING,
        "TAHBISAN DAN SALAM": SlideType.LITURGY_DIALOG,
        "DOA PENYEMBAHAN": SlideType.PRAYER,
        "PENGAKUAN DOSA": SlideType.PRAYER,
        "JANJI ANUGERAH ALLAH": SlideType.BIBLE_READING,
        "PUJI-PUJIAN": SlideType.SONG_TITLE,
        "FIRMAN TUHAN": SlideType.SERMON,
        "PERSEMBAHAN": SlideType.OFFERING,
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
        self.preset_keywords = PresetRegistry().keywords(preset_name)

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
            speaker = speaker_match.group(1).upper().replace(" ", "")
            if speaker == "PK":
                speaker = "PK"
            speaker_text = speaker_match.group(2).strip().lstrip(" ,.-").strip()
            return ClassifiedBlock(
                RawBlock(speaker_text, block.style_name, block.index),
                "speaker",
                SlideType.LITURGY_DIALOG,
                speaker=speaker,
            )

        if self.SONG_RE.match(text) and not self._looks_like_bible_reference(text):
            return ClassifiedBlock(block, "song_title", SlideType.SONG_TITLE, section=text)

        if self._is_notice(text, lower):
            return ClassifiedBlock(block, "notice", SlideType.START if "mulai ibadah" in lower else SlideType.NOTICE)

        if not has_cover and self._is_cover_title(upper):
            return ClassifiedBlock(block, "cover", SlideType.COVER)

        if self._is_heading(block, text):
            return ClassifiedBlock(block, "section", self._section_type(upper), section=text)

        if not has_cover:
            return ClassifiedBlock(block, "cover", SlideType.COVER)

        return ClassifiedBlock(block, "body", SlideType.LITURGY_DIALOG)

    def _metadata(self, text: str) -> Optional[tuple[str, str]]:
        match = re.match(r"^(tema|khadim|pelayan|tanggal|hari/tanggal)\s*:\s*(.+)$", text, re.I)
        if match:
            return match.group(1).lower(), match.group(2).strip()
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
            or any(keyword in upper for keyword in self.SECTION_KEYWORDS)
            or (block.has_bold and len(text) <= 90 and block.uppercase_ratio >= 0.65)
            or (text.isupper() and len(text) <= 90)
            or (block.max_font_size is not None and block.max_font_size >= 14 and block.uppercase_ratio >= 0.65)
        )

    def _is_cover_title(self, upper: str) -> bool:
        return "TATA IBADAH" in upper or upper.startswith("IBADAH ")

    def _looks_like_bible_reference(self, text: str) -> bool:
        return bool(re.search(r"\b\d+\s*:\s*\d+", text))

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

    def build(self, blocks: list[ClassifiedBlock], max_lines_per_slide: int = 6) -> SlideDeck:
        deck = SlideDeck()
        current_body_type = SlideType.LITURGY_DIALOG
        current_section = ""
        cover_lines: list[str] = []
        dialog_lines: list[SpeakerLine] = []

        def flush_dialog() -> None:
            nonlocal dialog_lines
            if not dialog_lines:
                return
            content = "\n".join(
                f"{line.speaker} : {line.text}" if line.speaker else line.text
                for line in dialog_lines
                if line.text.strip()
            )
            if content:
                deck.slides.append(
                    self._slide(
                        SlideType.LITURGY_DIALOG,
                        content,
                        current_section,
                        "liturgy_dialog",
                        speaker_lines=dialog_lines,
                    )
                )
            dialog_lines = []

        for block in blocks:
            if block.kind == "metadata":
                if block.metadata_key:
                    deck.metadata[block.metadata_key] = block.metadata_value
                continue

            if block.kind == "cover":
                flush_dialog()
                cover_lines.extend(split_long_text(block.text))
                continue

            if cover_lines:
                deck.slides.append(self._slide(SlideType.COVER, "\n".join(cover_lines), "Cover", "cover"))
                cover_lines = []

            if block.kind == "notice":
                flush_dialog()
                deck.slides.append(self._slide(block.slide_type, block.text, current_section, block.slide_type.value))
                continue

            if block.kind == "song_title":
                flush_dialog()
                current_section = block.text
                current_body_type = SlideType.SONG_LYRICS
                deck.slides.append(self._slide(SlideType.SONG_TITLE, block.text, current_section, "song_title", title=block.text))
                continue

            if block.kind == "section":
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
                dialog_lines.append(SpeakerLine(block.speaker or "", block.text))
                continue

            if current_body_type == SlideType.LITURGY_DIALOG:
                dialog_lines.append(SpeakerLine("", block.text))
                continue

            flush_dialog()
            self._append_chunked(
                deck,
                slide_type=current_body_type,
                text=block.text,
                section=current_section,
                template=current_body_type.value,
                max_lines=max_lines_per_slide,
            )

        flush_dialog()
        if cover_lines:
            deck.slides.append(self._slide(SlideType.COVER, "\n".join(cover_lines), "Cover", "cover"))

        if not deck.slides:
            deck.slides.append(self._slide(SlideType.COVER, "Tidak ada teks ditemukan.", "Cover", "cover"))

        deck.assign_numbers()
        return deck

    def _append_chunked(
        self,
        deck: SlideDeck,
        slide_type: SlideType,
        text: str,
        section: str,
        template: str,
        max_lines: int,
        speaker: Optional[str] = None,
    ) -> None:
        lines = split_long_text(text)
        chunks = [lines[i:i + max_lines] for i in range(0, len(lines), max_lines)] or [[""]]
        for chunk in chunks:
            content = "\n".join(chunk)
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
    detected = SectionDetector(preset_name=preset_name).detect(blocks)
    deck = SlideBuilder().build(detected, max_lines_per_slide=max_lines_per_slide)
    preset = PresetRegistry().get(preset_name)
    deck.preset_name = preset_name
    deck.template_name = preset.get("template", deck.template_name)
    deck.aspect_ratio = preset.get("aspect_ratio", deck.aspect_ratio)
    return deck


def parse_docx_to_deck(file_path: str, max_lines_per_slide: int = 6, preset_name: str = "GMIM Bentuk I") -> SlideDeck:
    blocks = DOCXReader().read(file_path)
    return parse_blocks(blocks, max_lines_per_slide=max_lines_per_slide, preset_name=preset_name)


def parse_docx(file_path: str, max_lines_per_slide: int = 6, preset_name: str = "GMIM Bentuk I") -> list[SlideItem]:
    return parse_docx_to_deck(file_path, max_lines_per_slide=max_lines_per_slide, preset_name=preset_name).slides
