import sys
from types import SimpleNamespace

from core.readers import PDFReader, read_document_blocks
from core.universal_parser import parse_blocks_to_service_document


class _TextPage:
    def __init__(self, text):
        self._text = text

    def get_text(self, mode):
        return self._text


def test_pdf_reader_text_based_outputs_raw_blocks(monkeypatch, tmp_path):
    pdf_path = tmp_path / "ibadah.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    fake_fitz = SimpleNamespace(open=lambda path: [_TextPage("TATA IBADAH\nPEMBUKAAN")])
    monkeypatch.setitem(sys.modules, "fitz", fake_fitz)

    blocks = PDFReader().read(str(pdf_path))

    assert len(blocks) == 1
    assert blocks[0].source_type == "pdf"
    assert blocks[0].page_number == 1
    assert blocks[0].metadata["ocr_used"] is False


def test_pipeline_pdf_to_service_document(monkeypatch, tmp_path):
    pdf_path = tmp_path / "ibadah.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    fake_fitz = SimpleNamespace(
        open=lambda path: [
            _TextPage("TATA IBADAH GMIM BENTUK V"),
            _TextPage("Tema Mingguan: Melayani dengan kasih"),
        ]
    )
    monkeypatch.setitem(sys.modules, "fitz", fake_fitz)

    document = parse_blocks_to_service_document(read_document_blocks(str(pdf_path)), preset_name="GMIM Bentuk V")

    assert document.service_form == "GMIM Bentuk V"
    assert document.title == "TATA IBADAH GMIM BENTUK V"
    assert document.theme_weekly == "Melayani dengan kasih"
    assert document.sections[0].items[0].metadata["ocr_used"] is False
