from dataclasses import dataclass, field
from typing import Any, Optional


def uppercase_ratio(text: str) -> float:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for char in letters if char.isupper()) / len(letters)


@dataclass
class RawBlock:
    text: str
    style_name: str = ""
    index: int = 0
    alignment: Optional[int] = None
    has_bold: bool = False
    max_font_size: Optional[float] = None
    uppercase_ratio: float = 0.0
    source_type: str = "docx"
    page_number: Optional[int] = None
    paragraph_index: Optional[int] = None
    style: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.style is None:
            self.style = self.style_name or None
        elif not self.style_name:
            self.style_name = self.style
        if self.paragraph_index is None:
            self.paragraph_index = self.index
        if not self.uppercase_ratio:
            self.uppercase_ratio = uppercase_ratio(self.text)

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "source_type": self.source_type,
            "page_number": self.page_number,
            "paragraph_index": self.paragraph_index,
            "style": self.style,
            "style_name": self.style_name,
            "index": self.index,
            "alignment": self.alignment,
            "has_bold": self.has_bold,
            "max_font_size": self.max_font_size,
            "uppercase_ratio": self.uppercase_ratio,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RawBlock":
        return cls(
            text=data.get("text", ""),
            source_type=data.get("source_type", "docx"),
            page_number=data.get("page_number"),
            paragraph_index=data.get("paragraph_index"),
            style=data.get("style"),
            style_name=data.get("style_name", ""),
            index=int(data.get("index", data.get("paragraph_index") or 0)),
            alignment=data.get("alignment"),
            has_bold=bool(data.get("has_bold", False)),
            max_font_size=data.get("max_font_size"),
            uppercase_ratio=float(data.get("uppercase_ratio", 0.0)),
            metadata=data.get("metadata") or {},
        )
