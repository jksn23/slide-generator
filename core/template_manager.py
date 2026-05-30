import json
import logging
import re
import shutil
from pathlib import Path
from typing import Any

from core.models import TemplatePreset
from core.template_engine import DEFAULT_TEMPLATE_DIR, TemplateResolver


logger = logging.getLogger(__name__)


class TemplateValidationError(ValueError):
    pass


class TemplateManager:
    def __init__(self, template_dir: Path | str = DEFAULT_TEMPLATE_DIR) -> None:
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)

    def list_templates(self) -> list[str]:
        return sorted(path.stem for path in self.template_dir.glob("*.json"))

    def load(self, name: str) -> TemplatePreset:
        path = self._path(name)
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.validate(data)
        return TemplatePreset.from_dict(data)

    def duplicate(self, source_name: str, new_name: str) -> str:
        source = self._path(source_name)
        target = self._path(new_name, must_exist=False)
        if target.exists():
            raise FileExistsError(f"Template already exists: {new_name}")
        data = json.loads(source.read_text(encoding="utf-8"))
        data["name"] = new_name
        self.validate(data)
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Duplicated template %s to %s", source_name, target.stem)
        return target.stem

    def rename(self, old_name: str, new_name: str) -> str:
        source = self._path(old_name)
        target = self._path(new_name, must_exist=False)
        if target.exists():
            raise FileExistsError(f"Template already exists: {new_name}")
        source.rename(target)
        data = json.loads(target.read_text(encoding="utf-8"))
        data["name"] = new_name
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Renamed template %s to %s", old_name, target.stem)
        return target.stem

    def delete(self, name: str) -> None:
        if name == "gmim_default":
            raise ValueError("Template default tidak boleh dihapus.")
        self._path(name).unlink()
        logger.info("Deleted template %s", name)

    def import_template(self, source_path: str, name: str | None = None) -> str:
        source = Path(source_path)
        data = json.loads(source.read_text(encoding="utf-8"))
        self.validate(data)
        target_name = name or source.stem
        target = self._path(target_name, must_exist=False)
        if target.exists():
            raise FileExistsError(f"Template already exists: {target_name}")
        shutil.copyfile(source, target)
        logger.info("Imported template %s as %s", source_path, target.stem)
        return target.stem

    def export_template(self, name: str, output_path: str) -> str:
        shutil.copyfile(self._path(name), output_path)
        logger.info("Exported template %s to %s", name, output_path)
        return output_path

    def validate(self, data: dict[str, Any]) -> None:
        if not isinstance(data, dict):
            raise TemplateValidationError("Template harus berupa object JSON.")
        if not data.get("defaults") and not data.get("default"):
            raise TemplateValidationError("Template harus memiliki `defaults` atau `default`.")
        if not isinstance(data.get("slides", {}), dict):
            raise TemplateValidationError("Field `slides` harus berupa object.")
        ratios = data.get("aspect_ratios", {})
        if ratios and not isinstance(ratios, dict):
            raise TemplateValidationError("Field `aspect_ratios` harus berupa object.")

    def preview_style(self, template_name: str, slide_type: str = "section") -> dict[str, Any]:
        return TemplateResolver(template_name, template_dir=self.template_dir).resolve(slide_type)

    def _path(self, name: str, must_exist: bool = True) -> Path:
        safe = self._safe_name(name)
        path = self.template_dir / f"{safe}.json"
        if must_exist and not path.exists():
            raise FileNotFoundError(f"Template not found: {safe}")
        return path

    def _safe_name(self, name: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9_-]+", "_", (name or "").strip()).strip("_")
        if not safe:
            raise ValueError("Nama template tidak valid.")
        return safe
