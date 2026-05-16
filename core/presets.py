import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PRESET_PATH = PROJECT_ROOT / "presets" / "gmim_presets.json"


class PresetRegistry:
    def __init__(self, path: Path | str = DEFAULT_PRESET_PATH) -> None:
        self.path = Path(path)
        with self.path.open("r", encoding="utf-8") as handle:
            self._presets: dict[str, dict[str, Any]] = json.load(handle)

    def names(self) -> list[str]:
        return list(self._presets.keys())

    def get(self, name: str = "GMIM Bentuk I") -> dict[str, Any]:
        if name not in self._presets:
            raise KeyError(f"Preset not found: {name}")
        return self._presets[name]

    def default_template(self, name: str = "GMIM Bentuk I") -> str:
        return self.get(name).get("template", "gmim_default")

    def default_aspect_ratio(self, name: str = "GMIM Bentuk I") -> str:
        return self.get(name).get("aspect_ratio", "square")

    def keywords(self, name: str = "GMIM Bentuk I") -> dict[str, list[str]]:
        return self.get(name).get("keywords", {})
