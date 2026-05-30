import re
from typing import Optional

from core.models import ServiceDocument, ServiceItem, ServiceSection, SlideType
from core.parser import ClassifiedBlock, DOCXReader, RawBlock, SectionDetector


class UniversalParser:
    """Convert reader RawBlocks into a ServiceDocument JSON model."""

    def __init__(self, preset_name: str = "GMIM Bentuk I") -> None:
        self.preset_name = preset_name
        self.detector = SectionDetector(preset_name=preset_name)

    def parse(self, blocks: list[RawBlock]) -> ServiceDocument:
        document = ServiceDocument(
            service_form=self.preset_name,
            metadata={"preset_name": self.preset_name},
        )
        current_section: Optional[ServiceSection] = None

        for block in self.detector.detect(blocks):
            if block.kind == "metadata":
                self._apply_metadata(document, block)
                continue

            if block.kind == "cover":
                if not document.title:
                    document.title = block.text
                current_section = self._ensure_section(document, current_section, "cover", "Cover")
                current_section.items.append(self._item(block, "cover", title=block.text, content=block.text))
                continue

            if block.kind in {"section", "song_title"}:
                item_type = block.slide_type.value
                section_type = item_type if block.kind == "song_title" else "section"
                current_section = ServiceSection(
                    type=section_type,
                    title=block.text,
                    metadata={"body_type": item_type, "source_kind": block.kind},
                )
                current_section.items.append(
                    self._item(block, item_type, title=block.text, content=block.text)
                )
                document.sections.append(current_section)
                continue

            current_section = self._ensure_section(document, current_section, "body", "Isi Ibadah")

            if block.kind == "speaker":
                current_section.items.append(
                    self._item(
                        block,
                        SlideType.LITURGY_DIALOG.value,
                        content=block.text,
                        speaker=block.speaker,
                    )
                )
                continue

            item_type = block.slide_type.value if block.kind == "notice" else self._body_type(current_section)
            current_section.content.append(block.text)
            current_section.items.append(self._item(block, item_type, content=block.text))

        return document

    def _apply_metadata(self, document: ServiceDocument, block: ClassifiedBlock) -> None:
        key = (block.metadata_key or "").strip().lower()
        value = (block.metadata_value or "").strip()
        if not key or not value:
            return

        document.metadata[key] = value
        normalized = re.sub(r"\s+", " ", key)
        if normalized in {"bentuk", "bentuk ibadah", "tata ibadah"}:
            document.service_form = value
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
        return ServiceItem(
            type=item_type,
            title=title,
            content=content,
            speaker=speaker,
            raw_text=block.text,
            metadata={
                "source_kind": block.kind,
                "source_type": block.raw.source_type,
                "page_number": block.raw.page_number,
                "paragraph_index": block.raw.paragraph_index,
                "style": block.raw.style,
            },
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
