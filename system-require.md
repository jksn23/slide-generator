Berikut panduan pengembangan yang saya sarankan.

## Arah besar sistem

Ubah sistem dari:

```text
DOCX → parsing teks → PPTX sederhana
```

menjadi:

```text
DOCX → struktur ibadah → slide model JSON → template engine → preview/editor → PPTX final
```

## Tech stack yang disarankan

Tetap gunakan stack utama repo saat ini:

```text
Python
PyQt5 / PySide6
python-docx
python-pptx
Pillow
```

Tambahan yang saya sarankan:

```text
PySide6          → opsi pengganti PyQt5, lebih modern
Pydantic         → validasi data SlideItem / Template
pytest           → testing parser
Pillow           → manipulasi background/gambar
PyMuPDF          → render preview PDF/slide/image jika dibutuhkan
Jinja2           → template teks/konfigurasi opsional
PyInstaller      → build aplikasi desktop .exe
```

Untuk penyimpanan konfigurasi:

```text
JSON / YAML
```

Untuk tahap awal, jangan langsung pakai database.

---

# Roadmap Pengembangan

## Tahap 1 — Rapikan struktur data slide

Buat model utama, misalnya:

```python
SlideItem:
    id
    type
    section
    title
    content
    speaker_lines
    background
    template
    include
```

Tipe slide yang perlu ada:

```text
cover
notice
start
section
song_title
song_lyrics
liturgy_dialog
prayer
bible_reading
sermon
offering
announcement
blessing
closing
blank
```

Tujuannya supaya parser dan generator tidak langsung saling bergantung.

---

## Tahap 2 — Buat parser bertahap

Jangan langsung DOCX ke slide. Buat alur:

```text
DOCXReader → RawBlock → BlockClassifier → SectionDetector → SlideBuilder
```

Fitur parser:

```text
Deteksi judul ibadah
Deteksi tema
Deteksi khadim
Deteksi tanggal
Deteksi bagian besar
Deteksi lagu KJ/NKB/PKJ/NNBT
Deteksi P/J/P+J
Deteksi bacaan Alkitab
Deteksi doa
Deteksi persembahan
Deteksi berkat
```

Output parser sebaiknya berupa JSON dulu, bukan langsung PPTX.

---

## Tahap 3 — Buat template engine

Buat folder:

```text
templates/
  gmim_default.json
  gmim_dark.json

assets/
  backgrounds/
  logos/
  icons/
  fonts/
```

Contoh konfigurasi template:

```json
{
  "song_lyrics": {
    "background": "dark.jpg",
    "font_family": "Impact",
    "font_size": 46,
    "color": "#FFFFFF",
    "align": "center"
  },
  "liturgy_dialog": {
    "background": "prayer.jpg",
    "font_size": 38,
    "speaker_colors": {
      "P": "#FFFFFF",
      "J": "#FFFF00",
      "P+J": "#FFFF00"
    }
  }
}
```

Dengan ini, tampilan bisa mengikuti PDF contoh tanpa hardcode di generator.

---

## Tahap 4 — Ubah ukuran slide menjadi 1:1

PDF contoh memakai format kotak. Tambahkan pilihan:

```text
1:1 Square
16:9 Landscape
4:3 Standard
```

Default untuk GMIM bisa dibuat:

```text
1:1 Square
```

Di `python-pptx`, atur:

```python
prs.slide_width = Inches(10)
prs.slide_height = Inches(10)
```

---

## Tahap 5 — Buat renderer PPTX baru

Renderer harus mendukung:

```text
Background image full slide
Overlay gelap/transparan
Text shadow
Text outline jika memungkinkan
Auto-fit font size
Rich text warna P/J/P+J
Center text untuk lagu
Left align untuk liturgi
Template berbeda per section
```

Pisahkan renderer:

```text
PPTXRenderer
TextRenderer
BackgroundRenderer
TemplateResolver
```

---

## Tahap 6 — Perbaiki preview UI

Preview sekarang belum akurat. Idealnya preview menampilkan hasil berdasarkan `SlideItem + Template`.

Fitur preview:

```text
Thumbnail slide
Checkbox include/exclude
Edit teks slide
Ganti tipe slide
Ganti background
Pecah slide
Gabung slide
Reorder slide
Preview besar di kanan
```

Untuk tahap awal, cukup:

```text
List slide kiri
Preview slide tengah
Panel edit kanan
```

---

## Tahap 7 — Tambahkan editor manual

Ini penting karena tata ibadah tidak selalu konsisten.

Fitur editor:

```text
Edit judul
Edit isi slide
Ubah tipe slide
Ubah section
Ubah background
Ubah alignment
Duplicate slide
Delete slide
Move up/down
```

Ini akan membuat sistem terasa “sempurna” meski parser belum 100% akurat.

---

## Tahap 8 — Tambahkan preset GMIM

Buat preset khusus:

```text
GMIM Bentuk I
GMIM Bentuk II
GMIM Bentuk III
Ibadah Kolom
Ibadah Pemuda
Ibadah ASM
Ibadah Syukur
```

Setiap preset punya:

```text
urutan section
keyword section
background default
template default
aturan parser
```

---

## Tahap 9 — Tambahkan testing

Buat folder:

```text
tests/
  test_parser_song.py
  test_parser_liturgy.py
  test_section_detector.py
  test_slide_builder.py
```

Gunakan contoh DOCX nyata sebagai test case.

Target test:

```text
Jumlah slide benar
Lagu terdeteksi benar
P/J/P+J terdeteksi benar
Bagian ibadah tidak salah jadi lirik
Slide tidak kosong
Teks tidak overflow
```

---

## Tahap 10 — Build aplikasi

Untuk distribusi:

```text
PyInstaller
```

Output:

```text
LiturgiSlide.exe
assets/
templates/
config.json
```

---

# Prioritas fitur versi 1

Fokus dulu pada ini:

```text
1. Parser baru berbasis section
2. Slide model JSON
3. Template engine 1:1
4. Background image per bagian
5. Renderer PPTX baru
6. Preview + edit sederhana
```

Setelah itu baru:

```text
7. Rich text P/J
8. Auto-fit font
9. Preset GMIM
10. Build .exe
```

Saran saya: mulai dari **Slide Model + Template Engine**, karena dua bagian itu akan menjadi fondasi semua fitur berikutnya.
