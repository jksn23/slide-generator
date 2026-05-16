import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from core.models import SlideItem, SlideType


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE_DIR = PROJECT_ROOT / "templates"


class TemplateResolver:
    def __init__(self, template_name: str = "gmim_default", template_dir: Path | str = DEFAULT_TEMPLATE_DIR) -> None:
        self.template_name = template_name
        self.template_dir = Path(template_dir)
        self.config = self._load_template(template_name)

    def resolve(self, slide: SlideItem | SlideType | str) -> dict[str, Any]:
        slide_type = slide.type if isinstance(slide, SlideItem) else SlideType.from_any(slide)
        template_key = slide.template if isinstance(slide, SlideItem) and slide.template else slide_type.value
        defaults = deepcopy(self.config.get("defaults", {}))
        specific = deepcopy(self.config.get("slides", {}).get(template_key, {}))
        section_overrides = {}
        if isinstance(slide, SlideItem) and slide.section:
            section_overrides = deepcopy(
                self.config.get("sections", {}).get(slide.section.lower(), {})
            )
        style = self._deep_merge(defaults, self._deep_merge(specific, section_overrides))
        if isinstance(slide, SlideItem):
            style = self._deep_merge(style, slide.metadata.get("style", {}))
        return style

    def aspect_ratio(self, name: str | None = None) -> dict[str, float]:
        ratios = self.config.get("aspect_ratios", {})
        ratio_name = name or self.config.get("default_aspect_ratio", "square")
        if ratio_name not in ratios:
            raise KeyError(f"Unknown aspect ratio '{ratio_name}' in template '{self.template_name}'")
        return ratios[ratio_name]

    def _load_template(self, template_name: str) -> dict[str, Any]:
        path = self.template_dir / f"{template_name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Template not found: {path}")
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        merged = deepcopy(base)
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = deepcopy(value)
        return merged
