from core.parser import RawBlock
from core.universal_parser import parse_blocks_to_service_document


def test_module_detector_stores_modules_in_service_document():
    document = parse_blocks_to_service_document(
        [
            RawBlock("TATA IBADAH", "Heading 1", 0),
            RawBlock("PELANTIKAN PANITIA PEMILIHAN", "Heading 1", 1),
            RawBlock("Baptisan Kudus", "Heading 1", 2),
            RawBlock("HUT Jemaat ke-100", "Heading 1", 3),
        ]
    )

    module_ids = {module["id"] for module in document.modules}

    assert {"pelantikan", "baptisan_kudus", "hut_jemaat"}.issubset(module_ids)
    assert document.metadata["modules"] == document.modules
