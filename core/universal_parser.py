import re
from typing import Optional

from core.models import ServiceDocument, ServiceItem, ServiceSection, SlideType
from core.modules import ModuleDetector
from core.parser import ClassifiedBlock, SectionDetector
from core.raw_block import RawBlock
from core.readers import DOCXReader, read_document_blocks
from core.text_splitter import normalize_content_line


class UniversalParser:
    """Convert reader RawBlocks into a ServiceDocument JSON model."""

    MAJOR_SECTION_KEYWORDS = (
        # Kata kunci liturgi utama GMIM
        "PERSIAPAN",
        "PEMBUKAAN",
        "PANGGILAN",
        "VOTUM",
        "KEMULIAAN",
        "PENYEMBAHAN",
        "PENGAKUAN",
        "ANUGERAH",
        "PETUNJUK HIDUP",
        "PEMBACAAN FIRMAN",
        "PELAYANAN FIRMAN",
        "PEMBERITAAN FIRMAN",
        "RESPONS",
        "PENGAKUAN IMAN",
        "HUKUM TUHAN",
        "PERSEMBAHAN",
        "DOA SYUKUR",
        "DOA SYAFAAT",
        "DOA PENUTUP",
        "DOA UMUM",
        "DOA PENYEMBAHAN",
        "WARTA JEMAAT",
        "PENUTUP",
        "BERKAT",
        "BAPTISAN",
        "SIDI",
        "PERJAMUAN",
        "PENEGUHAN",
        "PERTANYAAN",
        "TAHBISAN",
        "BERITA ANUGERAH",
        "PENGANTAR PEMBACAAN",
        "JANJI ANUGERAH",
        "PENGUTUSAN",
        "FIRMAN TUHAN",
        "KOLEKTE",
        "PELANTIKAN",
        "NYANYIAN MASUK",
        "NYANYIAN PENUTUP",
        "SALAM DAN BERKAT",
        "MENGHADAP TUHAN",
        "JAWABAN JEMAAT",
        "NAS PEMBIMBING",
        "PUJI-PUJIAN",
        "SAAT TEDUH",
        "KHOTBAH",
        "RENUNGAN",
    )

    def _is_major_section(self, text: str) -> bool:
        text_upper = text.strip().upper()
        
        # 0. Kalimat panjang tidak mungkin judul section (lirik, doa, ayat alkitab, dsb)
        if len(text_upper) > 80:
            return False
        
        # 1. Tolak jika itu adalah instruksi menyanyi atau judul lagu
        if any(song_kw in text_upper for song_kw in ["MENYANYI", "KJ NO", "NKB NO", "PKJ NO", "NNBT NO", "KJ.", "NKB.", "PKJ."]):
            return False
            
        # 2. Cek terhadap daftar kata kunci major section menggunakan word boundary
        #    sehingga "PERSEMBAHAN" tidak memicu "PERSEMBAHANMU"
        for kw in self._all_major_keywords:
            # Ganti spasi dalam keyword multi-kata dengan pencocokan bebas spasi
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, text_upper):
                return True
                
        # 3. Fallback: Jika teks 100% huruf kapital dan pendek (maks 6 kata), 
        # anggap sebagai section utama (mengantisipasi nama bab yang tidak ada di list)
        words = text_upper.split()
        if text.isupper() and len(words) <= 6 and "(" not in text:
             return True
             
        return False

    def __init__(self, preset_name: str = "GMIM Bentuk I") -> None:
        self.preset_name = preset_name
        self.detector = SectionDetector(preset_name=preset_name)
        self.module_detector = ModuleDetector()
        # Bangun set kata kunci major section yang diperkaya dari preset aktif
        self._all_major_keywords: list[str] = list(self.MAJOR_SECTION_KEYWORDS)
        try:
            from core.presets import PresetRegistry
            preset = PresetRegistry().get(preset_name)
            # Tambahkan nama-nama section dari preset ke daftar kata kunci
            for section_name in preset.get("sections", []):
                kw = section_name.upper().strip()
                if kw and kw not in self._all_major_keywords:
                    self._all_major_keywords.append(kw)
            # Tambahkan semua nilai dari keywords preset
            for category_keywords in preset.get("keywords", {}).values():
                for kw in category_keywords:
                    kw_upper = kw.upper().strip()
                    if kw_upper and kw_upper not in self._all_major_keywords:
                        self._all_major_keywords.append(kw_upper)
        except (KeyError, Exception):
            pass  # Fallback ke keyword statis jika preset tidak ditemukan

    def parse(self, blocks: list[RawBlock]) -> ServiceDocument:
        document = ServiceDocument(
            service_form=self.preset_name,
            metadata={"preset_name": self.preset_name},
        )
        current_section: Optional[ServiceSection] = None
        pending_speaker: Optional[str] = None

        for block in self.detector.detect(blocks):
            if block.kind == "metadata":
                self._apply_metadata(document, block)
                continue

            if block.kind == "cover":
                if not document.title:
                    document.title = block.text
                self._infer_service_form(document, block.text)
                current_section = self._ensure_section(document, current_section, "cover", "Cover")
                current_section.items.append(self._item(block, "cover", title=block.text, content=block.text))
                continue

            if block.kind in {"section", "song_title"}:
                item_type = block.slide_type.value
                body_type = self._body_type_for_heading(block)
                
                if self._is_major_section(block.text):
                    clean_section_name = block.text.split('(')[0].strip().title()
                    current_section = ServiceSection(
                        type="section",
                        title=clean_section_name,
                        metadata={"body_type": body_type, "source_kind": block.kind},
                    )
                    current_section.items.append(
                        self._item(block, item_type if block.kind == "song_title" else "section", title=block.text, content=block.text)
                    )
                    document.sections.append(current_section)
                else:
                    # Minor section / Song title -> append to existing section
                    current_section = self._ensure_section(document, current_section, "body", "Tata Ibadah")
                    current_section.metadata["body_type"] = body_type
                    current_section.items.append(
                        self._item(block, item_type if block.kind == "song_title" else "section", title=block.text, content=block.text)
                    )
                continue

            current_section = self._ensure_section(document, current_section, "body", "Isi Ibadah")

            if block.kind == "speaker":
                if not block.text.strip():
                    pending_speaker = block.speaker
                    continue
                current_section.items.append(
                    self._item(
                        block,
                        SlideType.LITURGY_DIALOG.value,
                        content=block.text,
                        speaker=block.speaker,
                    )
                )
                pending_speaker = None
                continue

            item_type = block.slide_type.value if block.kind == "notice" else self._body_type(current_section)
            if (
                item_type != SlideType.LITURGY_DIALOG.value
                and block.raw.text[:1] in {"\t", " ", "\xa0"}
                and current_section.items
                and current_section.items[-1].type == SlideType.LITURGY_DIALOG.value
            ):
                item_type = SlideType.LITURGY_DIALOG.value
            content = (
                normalize_content_line(block.text)
                if item_type == SlideType.LITURGY_DIALOG.value
                else block.text.strip()
            )
            current_section.content.append(content)
            speaker = pending_speaker if item_type == SlideType.LITURGY_DIALOG.value else None
            current_section.items.append(self._item(block, item_type, content=content, speaker=speaker))
            pending_speaker = None

        self.module_detector.detect(document)
        return document

    def _apply_metadata(self, document: ServiceDocument, block: ClassifiedBlock) -> None:
        key = (block.metadata_key or "").strip().lower()
        value = (block.metadata_value or "").strip()
        if not key or not value:
            return

        document.metadata[key] = value
        normalized = re.sub(r"\s+", " ", key)
        if normalized in {"bentuk", "bentuk ibadah", "tata ibadah"}:
            document.service_form = self._canonical_service_form(value)
        elif normalized in {"tema bulanan", "tema bulan"}:
            document.theme_monthly = value
        elif normalized in {"tema", "tema mingguan"}:
            document.theme_weekly = value
        elif normalized in {"bacaan", "bacaan alkitab"}:
            document.bible_reading = value
        elif normalized in {"gereja", "nama gereja", "jemaat"}:
            document.church_name = value
        elif normalized in {"tanggal", "hari/tanggal"}:
            document.date = value

    def _infer_service_form(self, document: ServiceDocument, text: str) -> None:
        if document.service_form and document.service_form != self.preset_name:
            return
        match = re.search(r"\b(?:GMIM\s+)?BENTUK\s+([IVX]+|\d+)\b", text, re.I)
        if match:
            document.service_form = self._canonical_service_form(match.group(0))

    def _canonical_service_form(self, value: str) -> str:
        match = re.search(r"\b(?:GMIM\s+)?BENTUK\s+([IVX]+|\d+)\b", value, re.I)
        if not match:
            return value
        return f"GMIM Bentuk {match.group(1).upper()}"

    def _body_type_for_heading(self, block: ClassifiedBlock) -> str:
        upper = block.text.upper()
        if block.kind == "song_title" or block.slide_type == SlideType.SONG_TITLE:
            return SlideType.SONG_LYRICS.value
        if "SAAT TEDUH" in upper:
            return SlideType.CLOSING.value
        return block.slide_type.value

    def _ensure_section(
        self,
        document: ServiceDocument,
        current_section: Optional[ServiceSection],
        section_type: str,
        title: str,
    ) -> ServiceSection:
        if current_section is not None:
            return current_section
        section = ServiceSection(type=section_type, title=title)
        document.sections.append(section)
        return section

    def _body_type(self, section: ServiceSection) -> str:
        return str(section.metadata.get("body_type") or section.type or SlideType.LITURGY_DIALOG.value)

    def _item(
        self,
        block: ClassifiedBlock,
        item_type: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        speaker: Optional[str] = None,
    ) -> ServiceItem:
        metadata = {
            "source_kind": block.kind,
            "source_type": block.raw.source_type,
            "page_number": block.raw.page_number,
            "paragraph_index": block.raw.paragraph_index,
            "style": block.raw.style,
        }
        metadata.update(block.raw.metadata)
        return ServiceItem(
            type=item_type,
            title=title,
            content=content,
            speaker=speaker,
            raw_text=block.text,
            metadata=metadata,
        )


def parse_blocks_to_service_document(
    blocks: list[RawBlock],
    preset_name: str = "GMIM Bentuk I",
) -> ServiceDocument:
    return UniversalParser(preset_name=preset_name).parse(blocks)


def parse_docx_to_service_document(
    file_path: str,
    preset_name: str = "GMIM Bentuk I",
) -> ServiceDocument:
    blocks = DOCXReader().read(file_path)
    return parse_blocks_to_service_document(blocks, preset_name=preset_name)


def parse_file_to_service_document(
    file_path: str,
    preset_name: str = "GMIM Bentuk I",
    use_ocr: bool = False,
) -> ServiceDocument:
    blocks = read_document_blocks(file_path, use_ocr=use_ocr)
    return parse_blocks_to_service_document(blocks, preset_name=preset_name)
