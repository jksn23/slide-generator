import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class SlideType(Enum):
    COVER = "cover"
    NOTICE = "notice"
    INSTRUKSI = "notice"
    START = "start"
    SECTION = "section"
    BAGIAN = "section"
    SONG_TITLE = "song_title"
    JUDUL_LAGU = "song_title"
    SONG_LYRICS = "song_lyrics"
    LIRIK_LAGU = "song_lyrics"
    LITURGY_DIALOG = "liturgy_dialog"
    LITURGI = "liturgy_dialog"
    PRAYER = "prayer"
    BIBLE_READING = "bible_reading"
    BACAAN = "bible_reading"
    SERMON = "sermon"
    OFFERING = "offering"
    ANNOUNCEMENT = "announcement"
    BLESSING = "blessing"
    CLOSING = "closing"
    PENUTUP = "closing"
    BLANK = "blank"

    @property
    def label(self) -> str:
        return SLIDE_TYPE_LABELS[self]

    @classmethod
    def from_any(cls, value: Any) -> "SlideType":
        if isinstance(value, SlideType):
            return value
        if value is None:
            return cls.BLANK
        normalized = str(value).strip().lower().replace(" ", "_").replace("-", "_")
        return SLIDE_TYPE_ALIASES.get(normalized, cls(normalized))


SLIDE_TYPE_LABELS = {
    SlideType.COVER: "Cover",
    SlideType.NOTICE: "Instruksi",
    SlideType.START: "Mulai Ibadah",
    SlideType.SECTION: "Judul Bagian",
    SlideType.SONG_TITLE: "Judul Lagu",
    SlideType.SONG_LYRICS: "Lirik Lagu",
    SlideType.LITURGY_DIALOG: "Liturgi",
    SlideType.PRAYER: "Doa",
    SlideType.BIBLE_READING: "Bacaan",
    SlideType.SERMON: "Khotbah",
    SlideType.OFFERING: "Persembahan",
    SlideType.ANNOUNCEMENT: "Pengumuman",
    SlideType.BLESSING: "Berkat",
    SlideType.CLOSING: "Penutup",
    SlideType.BLANK: "Kosong",
}

SLIDE_TYPE_ALIASES = {
    "instruksi": SlideType.NOTICE,
    "judul_bagian": SlideType.SECTION,
    "bagian": SlideType.SECTION,
    "judul_lagu": SlideType.SONG_TITLE,
    "lirik_lagu": SlideType.SONG_LYRICS,
    "liturgi": SlideType.LITURGY_DIALOG,
    "bacaan": SlideType.BIBLE_READING,
    "penutup": SlideType.CLOSING,
    "berkat": SlideType.BLESSING,
    "doa": SlideType.PRAYER,
}


@dataclass
class SpeakerLine:
    speaker: str
    text: str

    def to_dict(self) -> dict:
        return {"speaker": self.speaker, "text": self.text}

    @classmethod
    def from_dict(cls, data: dict) -> "SpeakerLine":
        return cls(speaker=str(data.get("speaker", "")).strip(), text=str(data.get("text", "")))


@dataclass
class SlideBackground:
    color: Optional[str] = None
    image: Optional[str] = None
    overlay_color: str = "#000000"
    overlay_opacity: float = 0.0

    def to_dict(self) -> dict:
        return {
            "color": self.color,
            "image": self.image,
            "overlay_color": self.overlay_color,
            "overlay_opacity": self.overlay_opacity,
        }

    @classmethod
    def from_any(cls, value: Any) -> Optional["SlideBackground"]:
        if value is None:
            return None
        if isinstance(value, SlideBackground):
            return value
        if isinstance(value, str):
            return cls(image=value)
        if isinstance(value, dict):
            return cls(
                color=value.get("color"),
                image=value.get("image"),
                overlay_color=value.get("overlay_color", "#000000"),
                overlay_opacity=float(value.get("overlay_opacity", 0.0)),
            )
        raise TypeError(f"Unsupported background value: {value!r}")


@dataclass
class ServiceItem:
    type: str
    raw_text: str
    id: str = ""
    title: Optional[str] = None
    content: Optional[str] = None
    speaker: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = f"item-{uuid.uuid4().hex[:10]}"
        self.type = str(self.type or "body")
        self.raw_text = self.raw_text or ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "content": self.content,
            "speaker": self.speaker,
            "raw_text": self.raw_text,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ServiceItem":
        return cls(
            id=data.get("id", ""),
            type=data.get("type", "body"),
            title=data.get("title"),
            content=data.get("content"),
            speaker=data.get("speaker"),
            raw_text=data.get("raw_text", data.get("content", "")),
            metadata=data.get("metadata") or {},
        )


@dataclass
class ServiceSection:
    title: str
    type: str = "section"
    id: str = ""
    content: list[str] = field(default_factory=list)
    items: list[ServiceItem] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = f"section-{uuid.uuid4().hex[:10]}"
        self.type = str(self.type or "section")
        self.title = self.title or ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "content": list(self.content),
            "items": [item.to_dict() for item in self.items],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ServiceSection":
        return cls(
            id=data.get("id", ""),
            type=data.get("type", "section"),
            title=data.get("title", ""),
            content=list(data.get("content") or []),
            items=[ServiceItem.from_dict(item) for item in data.get("items", [])],
            metadata=data.get("metadata") or {},
        )


@dataclass
class ServiceDocument:
    service_form: str = ""
    title: str = ""
    theme_monthly: Optional[str] = None
    theme_weekly: Optional[str] = None
    bible_reading: Optional[str] = None
    church_name: Optional[str] = None
    date: Optional[str] = None
    sections: list[ServiceSection] = field(default_factory=list)
    modules: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "service_form": self.service_form,
            "title": self.title,
            "theme_monthly": self.theme_monthly,
            "theme_weekly": self.theme_weekly,
            "bible_reading": self.bible_reading,
            "church_name": self.church_name,
            "date": self.date,
            "sections": [section.to_dict() for section in self.sections],
            "modules": self.modules,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ServiceDocument":
        return cls(
            service_form=data.get("service_form", ""),
            title=data.get("title", ""),
            theme_monthly=data.get("theme_monthly"),
            theme_weekly=data.get("theme_weekly"),
            bible_reading=data.get("bible_reading"),
            church_name=data.get("church_name"),
            date=data.get("date"),
            sections=[ServiceSection.from_dict(section) for section in data.get("sections", [])],
            modules=list(data.get("modules") or []),
            metadata=data.get("metadata") or {},
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, value: str) -> "ServiceDocument":
        return cls.from_dict(json.loads(value))


@dataclass
class TemplatePreset:
    name: str
    default: dict[str, Any] = field(default_factory=dict)
    slides: dict[str, dict[str, Any]] = field(default_factory=dict)
    sections: dict[str, dict[str, Any]] = field(default_factory=dict)
    aspect_ratios: dict[str, dict[str, float]] = field(default_factory=dict)
    default_aspect_ratio: str = "square"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "defaults": self.default,
            "slides": self.slides,
            "sections": self.sections,
            "aspect_ratios": self.aspect_ratios,
            "default_aspect_ratio": self.default_aspect_ratio,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TemplatePreset":
        return cls(
            name=data.get("name", ""),
            default=data.get("defaults") or data.get("default") or {},
            slides=data.get("slides") or {},
            sections=data.get("sections") or {},
            aspect_ratios=data.get("aspect_ratios") or {},
            default_aspect_ratio=data.get("default_aspect_ratio", data.get("slide_size", "square")),
            metadata={
                key: value
                for key, value in data.items()
                if key not in {"name", "defaults", "default", "slides", "sections", "aspect_ratios", "default_aspect_ratio"}
            },
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, value: str) -> "TemplatePreset":
        return cls.from_dict(json.loads(value))


@dataclass(init=False)
class SlideItem:
    id: str
    type: SlideType
    section: str
    title: Optional[str]
    content: str
    speaker_lines: list[SpeakerLine]
    background: Optional[SlideBackground]
    template: Optional[str]
    include: bool
    slide_number: int
    speaker: Optional[str]
    is_nyanyian: bool
    metadata: dict[str, Any]

    def __init__(
        self,
        type: Any = None,
        content: str = "",
        id: Optional[str] = None,
        section: str = "",
        title: Optional[str] = None,
        speaker_lines: Optional[list[Any]] = None,
        background: Any = None,
        template: Optional[str] = None,
        include: bool = True,
        slide_number: int = 0,
        speaker: Optional[str] = None,
        is_nyanyian: bool = False,
        metadata: Optional[dict[str, Any]] = None,
        slide_type: Any = None,
        included: Optional[bool] = None,
        bg_image: Optional[str] = None,
    ) -> None:
        self.id = id or f"slide-{uuid.uuid4().hex[:10]}"
        self.type = SlideType.from_any(slide_type if slide_type is not None else type)
        self.section = section or ""
        self.title = title
        self.content = content or ""
        self.speaker_lines = [
            line if isinstance(line, SpeakerLine) else SpeakerLine.from_dict(line)
            for line in (speaker_lines or [])
        ]
        if bg_image and background is None:
            background = SlideBackground(image=bg_image)
        self.background = SlideBackground.from_any(background)
        self.template = template
        self.include = include if included is None else bool(included)
        self.slide_number = slide_number
        self.speaker = speaker
        self.is_nyanyian = is_nyanyian
        self.metadata = metadata or {}

    @property
    def slide_type(self) -> SlideType:
        return self.type

    @slide_type.setter
    def slide_type(self, value: Any) -> None:
        self.type = SlideType.from_any(value)

    @property
    def included(self) -> bool:
        return self.include

    @included.setter
    def included(self, value: bool) -> None:
        self.include = bool(value)

    @property
    def bg_image(self) -> Optional[str]:
        return self.background.image if self.background else None

    @bg_image.setter
    def bg_image(self, value: Optional[str]) -> None:
        if value:
            self.background = self.background or SlideBackground()
            self.background.image = value
        elif self.background:
            self.background.image = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "section": self.section,
            "title": self.title,
            "content": self.content,
            "speaker_lines": [line.to_dict() for line in self.speaker_lines],
            "background": self.background.to_dict() if self.background else None,
            "template": self.template,
            "include": self.include,
            "slide_number": self.slide_number,
            "speaker": self.speaker,
            "is_nyanyian": self.is_nyanyian,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SlideItem":
        return cls(
            id=data.get("id"),
            type=data.get("type"),
            section=data.get("section", ""),
            title=data.get("title"),
            content=data.get("content", ""),
            speaker_lines=data.get("speaker_lines") or [],
            background=data.get("background"),
            template=data.get("template"),
            include=bool(data.get("include", True)),
            slide_number=int(data.get("slide_number", 0)),
            speaker=data.get("speaker"),
            is_nyanyian=bool(data.get("is_nyanyian", False)),
            metadata=data.get("metadata") or {},
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, value: str) -> "SlideItem":
        return cls.from_dict(json.loads(value))


@dataclass
class SlideDeck:
    slides: list[SlideItem] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    template_name: str = "gmim_default"
    aspect_ratio: str = "square"
    preset_name: str = "GMIM Bentuk I"

    def assign_numbers(self) -> None:
        for index, slide in enumerate(self.slides, start=1):
            slide.slide_number = index

    def to_dict(self) -> dict:
        return {
            "metadata": self.metadata,
            "template_name": self.template_name,
            "aspect_ratio": self.aspect_ratio,
            "preset_name": self.preset_name,
            "slides": [slide.to_dict() for slide in self.slides],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SlideDeck":
        deck = cls(
            metadata=data.get("metadata") or {},
            template_name=data.get("template_name", "gmim_default"),
            aspect_ratio=data.get("aspect_ratio", "square"),
            preset_name=data.get("preset_name", "GMIM Bentuk I"),
            slides=[SlideItem.from_dict(item) for item in data.get("slides", [])],
        )
        deck.assign_numbers()
        return deck

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, value: str) -> "SlideDeck":
        return cls.from_dict(json.loads(value))
