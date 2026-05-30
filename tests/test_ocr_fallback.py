import io
import sys
from types import SimpleNamespace

from PIL import Image

from core.readers import PDFReader


def _png_bytes():
    buffer = io.BytesIO()
    Image.new("RGB", (1, 1), "white").save(buffer, format="PNG")
    return buffer.getvalue()


class _ScanPixmap:
    def tobytes(self, fmt):
        return _png_bytes()


class _ScanPage:
    def get_text(self, mode):
        return ""

    def get_pixmap(self, matrix=None):
        return _ScanPixmap()


def test_ocr_fallback_outputs_raw_block(monkeypatch, tmp_path):
    pdf_path = tmp_path / "scan.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    fake_fitz = SimpleNamespace(open=lambda path: [_ScanPage()], Matrix=lambda x, y: (x, y))
    fake_tesseract = SimpleNamespace(
        image_to_string=lambda image: "TATA IBADAH HASIL OCR",
        image_to_data=lambda image, output_type=None: {"conf": ["90", "80"]},
        Output=SimpleNamespace(DICT="dict"),
    )
    monkeypatch.setitem(sys.modules, "fitz", fake_fitz)
    monkeypatch.setitem(sys.modules, "pytesseract", fake_tesseract)

    reader = PDFReader(use_ocr=True)
    blocks = reader.read(str(pdf_path))

    assert blocks[0].text == "TATA IBADAH HASIL OCR"
    assert blocks[0].metadata["ocr_used"] is True
    assert blocks[0].metadata["confidence"] == 85
    assert any("Hasil OCR" in warning for warning in reader.warnings)
