from core.modules import ModuleRegistry


def test_module_registry_loads_gmim_modules():
    registry = ModuleRegistry()

    assert "Baptisan Kudus" in registry.names()
    assert registry.get("pelantikan").default_template == "gmim_default"
