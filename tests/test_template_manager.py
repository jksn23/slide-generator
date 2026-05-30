import json

import pytest

from core.template_manager import TemplateManager, TemplateValidationError


def _template(name="Template A"):
    return {
        "name": name,
        "defaults": {"font_family": "Segoe UI", "font_size": 40},
        "slides": {"section": {"align": "center"}},
        "aspect_ratios": {"square": {"width": 10, "height": 10}},
        "default_aspect_ratio": "square",
    }


def test_template_manager_duplicate_rename_export_import(tmp_path):
    (tmp_path / "base.json").write_text(json.dumps(_template("base")), encoding="utf-8")
    manager = TemplateManager(tmp_path)

    assert manager.list_templates() == ["base"]
    manager.duplicate("base", "copy")
    manager.rename("copy", "renamed")
    export_path = tmp_path / "exported.json"
    manager.export_template("renamed", str(export_path))
    manager.import_template(str(export_path), name="imported")

    assert {"base", "renamed", "imported"}.issubset(set(manager.list_templates()))
    assert manager.preview_style("base", "section")["align"] == "center"


def test_template_manager_rejects_invalid_template(tmp_path):
    manager = TemplateManager(tmp_path)

    with pytest.raises(TemplateValidationError):
        manager.validate({"name": "Broken", "slides": []})
