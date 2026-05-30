import sys
from types import SimpleNamespace

import pytest

from core.readers import PDFReader, PDFTextExtractionError


class _EmptyPage:
    def get_text(self, mode):
        return ""


def test_pdf_reader_empty_scan_raises_clear_warning(monkeypatch, tmp_path):
    pdf_path = tmp_path / "scan.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    monkeypatch.setitem(sys.modules, "fitz", SimpleNamespace(open=lambda path: [_EmptyPage()]))

    reader = PDFReader()

    with pytest.raises(PDFTextExtractionError, match="kemungkinan hasil scan"):
        reader.read(str(pdf_path))

    assert reader.warnings == ["PDF ini kemungkinan hasil scan/gambar. Gunakan OCR atau upload DOCX."]
