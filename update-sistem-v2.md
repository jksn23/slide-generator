# Panduan Update Aplikasi LiturgiSlide untuk AI Agent Codex

## Tujuan Update

Lakukan refactor dan pengembangan aplikasi `slide-generator` agar sistem tidak lagi bergantung langsung pada proses:

```text
DOCX → PPTX
```

Tetapi menggunakan pipeline baru:

```text
DOCX / PDF
→ Document Reader
→ RawBlock
→ Universal Parser
→ Service JSON
→ SlideItem
→ Template Engine
→ Preview Editor
→ PPTX Export
```

Target utama adalah agar aplikasi lebih fleksibel untuk membaca tata ibadah GMIM dari DOCX maupun PDF, khususnya Bentuk I–V dan variasi ibadah kreatif.

---

# Instruksi Awal untuk Codex

Sebelum menulis kode:

1. Baca seluruh struktur repository.
2. Identifikasi file utama untuk:

   * import DOCX
   * parsing teks
   * generate slide
   * UI preview
   * export PPTX
3. Jangan langsung menghapus kode lama.
4. Buat layer baru secara bertahap.
5. Pastikan aplikasi lama tetap bisa berjalan setelah update.
6. Semua perubahan harus modular dan mudah diuji.

---

# Target Arsitektur Baru

Gunakan struktur konsep berikut:

```text
src/
  core/
    models/
      service_document.py
      slide_item.py
      template_preset.py

    readers/
      base_reader.py
      docx_reader.py
      pdf_reader.py

    parser/
      universal_parser.py
      block_classifier.py
      section_detector.py
      song_detector.py
      speaker_detector.py

    builder/
      slide_builder.py
      text_splitter.py
      overflow_handler.py

    template/
      template_engine.py
      template_loader.py
      background_resolver.py

    renderer/
      pptx_renderer.py

    preview/
      preview_renderer.py
```

Sesuaikan folder dengan struktur repo yang sudah ada. Jika repo belum memakai `src/`, boleh gunakan struktur yang paling dekat dengan kode saat ini.

---

# Tahap 1 — Buat Arsitektur JSON

Buat model data utama agar hasil parsing tidak langsung menjadi PPTX.

## Model: ServiceDocument

Berisi data tata ibadah secara keseluruhan.

Field minimal:

```python
service_form: str
title: str
theme_monthly: str | None
theme_weekly: str | None
bible_reading: str | None
church_name: str | None
date: str | None
sections: list[ServiceSection]
metadata: dict
```

## Model: ServiceSection

```python
id: str
type: str
title: str
content: list[str]
items: list[ServiceItem]
```

## Model: ServiceItem

```python
id: str
type: str
title: str | None
content: str | None
speaker: str | None
raw_text: str
```

## Model: SlideItem

```python
id: str
type: str
section: str | None
title: str | None
content: str | None
speaker_lines: list[dict]
background: str | None
template: str | None
include: bool
metadata: dict
```

Gunakan `dataclass` atau `pydantic`. Jika dependency Pydantic belum ada, pakai `dataclass` dulu agar ringan.

---

# Tahap 2 — Buat Universal Parser

Jangan buat parser khusus DOCX dan PDF secara terpisah.

Buat sistem:

```text
DOCXReader → RawBlock
PDFReader  → RawBlock
RawBlock   → UniversalParser
```

## RawBlock

```python
text: str
source_type: str
page_number: int | None
paragraph_index: int | None
style: str | None
metadata: dict
```

DOCXReader boleh mengisi `style`, PDFReader boleh mengisi `page_number`.

## Universal Parser harus mendeteksi:

* Judul tata ibadah
* Bentuk ibadah
* Tema bulanan
* Tema mingguan
* Bacaan Alkitab
* Nama gereja
* Tanggal
* Section besar
* Lagu
* Lirik lagu
* P/J/P+J
* Doa
* Khotbah
* Persembahan
* Warta Jemaat
* Kolekte Extra
* Berkat
* Saat Teduh

## Keyword section awal

Gunakan keyword:

```text
PEMBUKAAN
PERSIAPAN
TAHBISAN
PENGAKUAN DOSA
BERITA ANUGERAH ALLAH
PENGANTAR PEMBACAAN ALKITAB DAN KHOTBAH
PEMBACAAN ALKITAB DAN KHOTBAH
PERSEMBAHAN
DOA SYUKUR
DOA SYAFAAT
WARTA JEMAAT
KOLEKTE EXTRA
PENUTUP
BERKAT
SAAT TEDUH
```

## Deteksi lagu

Deteksi pola:

```text
Menyanyi
KJ No.
NKB No.
PKJ No.
NNBT No.
```

Contoh:

```text
Menyanyi “Hari Ini Ku Rasa Bahagia”
Menyanyi PKJ No. 146 Bawa Persembahanmu
Menyanyi “Jao Jao Tuhan So Pilih pa Torang”
```

---

# Tahap 3 — Buat Template Engine

Buat folder:

```text
templates/
  gmim_default.json
  gmim_creative.json
```

Contoh struktur template:

```json
{
  "slide_size": "1:1",
  "default": {
    "font_family": "Arial",
    "font_size": 36,
    "font_color": "#FFFFFF",
    "background": "default.jpg",
    "align": "center"
  },
  "section": {
    "font_size": 48,
    "font_color": "#FFFFFF",
    "align": "center"
  },
  "song_title": {
    "font_size": 42,
    "font_color": "#FFFFFF",
    "align": "center"
  },
  "song_lyrics": {
    "font_size": 44,
    "font_color": "#FFFFFF",
    "align": "center"
  },
  "liturgy_dialog": {
    "font_size": 34,
    "align": "left",
    "speaker_colors": {
      "P": "#FFFFFF",
      "J": "#FFFF00",
      "P+J": "#FFFF00",
      "PK": "#FFFFFF"
    }
  }
}
```

Template engine bertugas memilih style berdasarkan `SlideItem.type`.

---

# Tahap 4 — Buat Slide Builder

Slide Builder mengubah `ServiceDocument` menjadi list `SlideItem`.

Aturan dasar:

1. Cover menjadi slide `cover`.
2. Section besar menjadi slide `section`.
3. Judul lagu menjadi `song_title`.
4. Lirik lagu menjadi `song_lyrics`.
5. Dialog P/J menjadi `liturgy_dialog`.
6. Bacaan Alkitab menjadi `bible_reading`.
7. Khotbah menjadi `sermon`.
8. Persembahan menjadi `offering`.
9. Warta Jemaat menjadi `announcement`.
10. Berkat menjadi `blessing`.
11. Saat Teduh menjadi `closing`.

---

# Tahap 5 — Tambahkan Overflow Handler

Buat modul `text_splitter.py`.

Fungsi minimal:

```python
split_text_to_slides(text, max_lines, max_chars_per_line)
```

Target:

* Jangan memotong kata di tengah.
* Jangan membuat teks keluar slide.
* Jika lirik panjang, pecah menjadi beberapa slide.
* Jika dialog panjang, pecah berdasarkan batas baris aman.
* Jika sedikit overflow, boleh kecilkan font otomatis.

---

# Tahap 6 — Preview Editor

Update preview agar menggunakan `SlideItem + Template`, bukan langsung hasil PPTX saja.

Fitur minimal:

* List slide di kiri
* Preview besar di tengah
* Panel edit di kanan
* Edit title
* Edit content
* Ubah type slide
* Include/exclude slide
* Move up/down
* Split slide
* Merge slide

Tambahkan fullscreen preview jika memungkinkan.

---

# Tahap 7 — Tambahkan PDF Import

Tambahkan setelah pipeline JSON dan Universal Parser selesai.

Buat file:

```text
pdf_reader.py
```

Gunakan PyMuPDF jika tersedia:

```python
import fitz
```

Fungsi minimal:

```python
class PDFReader:
    def read(self, path: str) -> list[RawBlock]:
        ...
```

Alur:

```text
PDF → extract text per page → RawBlock → UniversalParser
```

Jika PDF tidak menghasilkan teks:

```text
Tampilkan pesan:
PDF ini kemungkinan hasil scan/gambar. Gunakan OCR atau upload DOCX.
```

Jangan langsung PDF to PPTX.

---

# Tahap 8 — Tambahkan OCR untuk PDF Scan

OCR adalah tahap terakhir, bukan prioritas awal.

Buat fallback:

```text
Jika PyMuPDF extract text kosong
→ render page jadi image
→ OCR dengan pytesseract
→ RawBlock
```

Namun beri tanda di UI:

```text
Hasil OCR mungkin tidak akurat. Mohon review ulang sebelum export.
```

---

# Tahap 9 — Testing

Tambahkan test:

```text
tests/
  test_docx_reader.py
  test_pdf_reader.py
  test_universal_parser.py
  test_slide_builder.py
  test_text_splitter.py
```

Test minimal:

1. PDF text-based berhasil dibaca.
2. Bentuk V terdeteksi.
3. Tema mingguan terdeteksi.
4. Lagu terdeteksi.
5. Section besar terdeteksi.
6. SlideItem berhasil dibuat.
7. Teks panjang tidak overflow.
8. Export PPTX tetap berhasil.

---

# Tahap 10 — Acceptance Criteria

Update dianggap berhasil jika:

1. Import DOCX lama tetap berjalan.
2. Import PDF text-based berhasil.
3. DOCX dan PDF masuk ke parser yang sama.
4. Output internal berupa ServiceDocument JSON.
5. SlideItem dapat diedit sebelum export.
6. Template engine bisa mengatur tampilan berdasarkan tipe slide.
7. Export PPTX berhasil.
8. Tidak ada teks yang terpotong.
9. PDF scan diberi warning jika belum OCR.
10. Kode modular dan mudah dikembangkan.

---

# Prioritas Eksekusi

Kerjakan berurutan:

```text
1. Tambahkan model JSON
2. Tambahkan RawBlock
3. Refactor DOCXReader agar menghasilkan RawBlock
4. Buat UniversalParser
5. Buat SlideBuilder dari ServiceDocument
6. Integrasikan TemplateEngine
7. Perbaiki PreviewEditor
8. Tambahkan PDFReader text-based
9. Tambahkan warning PDF scan
10. Tambahkan OCR fallback
```

Jangan mulai dari OCR. Jangan mulai dari PDF import jika pipeline JSON belum siap.

---

# Catatan Penting

Aplikasi ini tidak boleh mengejar otomatis 100%.

Target realistis:

```text
80–90% otomatis
10–20% koreksi manual
```

Karena tata ibadah GMIM sering berubah, hasil generate harus selalu bisa diedit sebelum export.
