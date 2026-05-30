import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.models import ServiceDocument


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODULE_PATH = PROJECT_ROOT / "presets" / "modules" / "gmim_modules.json"
logger = logging.getLogger(__name__)


@dataclass
class EventModule:
    id: str
    name: str
    keywords: list[str] = field(default_factory=list)
    default_sections: list[str] = field(default_factory=list)
    default_slide_types: dict[str, str] = field(default_factory=dict)
    default_template: str | None = None
    insertion_rules: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "keywords": self.keywords,
            "default_sections": self.default_sections,
            "default_slide_types": self.default_slide_types,
            "default_template": self.default_template,
            "insertion_rules": self.insertion_rules,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EventModule":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            keywords=list(data.get("keywords") or []),
            default_sections=list(data.get("default_sections") or []),
            default_slide_types=dict(data.get("default_slide_types") or {}),
            default_template=data.get("default_template"),
            insertion_rules=dict(data.get("insertion_rules") or {}),
            metadata=dict(data.get("metadata") or {}),
        )


class ModuleRegistry:
    def __init__(self, module_path: Path | str = DEFAULT_MODULE_PATH) -> None:
        self.module_path = Path(module_path)
        self.modules = self._load()

    def names(self) -> list[str]:
        return [module.name for module in self.modules]

    def get(self, module_id: str) -> EventModule:
        for module in self.modules:
            if module.id == module_id:
                return module
        raise KeyError(f"Module not found: {module_id}")

    def _load(self) -> list[EventModule]:
        if not self.module_path.exists():
            return []
        with self.module_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        modules = [EventModule.from_dict(item) for item in data.get("modules", [])]
        logger.info("Loaded %s event module(s) from %s", len(modules), self.module_path)
        return modules


class ModuleDetector:
    def __init__(self, registry: ModuleRegistry | None = None) -> None:
        self.registry = registry or ModuleRegistry()

    def detect(self, document: ServiceDocument) -> list[EventModule]:
        haystack = "\n".join(self._document_text(document)).lower()
        detected: list[EventModule] = []
        for module in self.registry.modules:
            if any(keyword.lower() in haystack for keyword in module.keywords):
                detected.append(module)
        document.modules = [module.to_dict() for module in detected]
        document.metadata["modules"] = document.modules
        logger.info("Detected %s event module(s)", len(detected))
        return detected

    def _document_text(self, document: ServiceDocument) -> list[str]:
        values = [document.title, document.service_form, document.theme_monthly or "", document.theme_weekly or ""]
        for section in document.sections:
            values.append(section.title)
            values.extend(section.content)
            values.extend(item.raw_text for item in section.items)
        return values


class ModuleTemplateResolver:
    def template_for(self, module: EventModule, fallback: str = "gmim_default") -> str:
        return module.default_template or fallback
