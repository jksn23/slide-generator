from typing import Protocol

from core.raw_block import RawBlock, uppercase_ratio


class DocumentReader(Protocol):
    def read(self, file_path: str) -> list[RawBlock]:
        ...


class DOCXReader:
    source_type = "docx"

    def read(self, file_path: str) -> list[RawBlock]:
        try:
            import docx
        except ImportError:
            return [RawBlock("Error: python-docx not installed.", "Error", 0)]

        document = docx.Document(file_path)
        blocks: list[RawBlock] = []
        for index, paragraph in enumerate(document.paragraphs):
            text = paragraph.text.rstrip()
            if text.strip():
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
                        uppercase_ratio=uppercase_ratio(text),
                        source_type=self.source_type,
                        paragraph_index=index,
                        style=paragraph.style.name,
                    )
                )
        return blocks
