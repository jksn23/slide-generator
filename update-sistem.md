# Panduan Pengembangan Aplikasi LiturgiSlide GMIM

## Latar Belakang Masalah

Proses pembuatan slide tata ibadah di gereja GMIM saat ini masih dilakukan secara manual menggunakan Microsoft PowerPoint. Tim multimedia harus:

* Copy-paste isi tata ibadah dari Word ke PowerPoint
* Menyesuaikan format slide satu per satu
* Mengatur background, font, dan layout secara manual
* Memecah lirik lagu dan liturgi ke banyak slide
* Menyesuaikan bentuk tata ibadah GMIM Bentuk I–V
* Menambahkan acara khusus seperti:

  * Baptisan
  * Perjamuan Kudus
  * Pelantikan
  * HUT Jemaat
  * Hari Raya Kristen
  * dan variasi kegiatan lainnya

Masalah utama:

```text
Pembuatan slide memakan waktu lama,
repetitif,
dan rawan kesalahan.
```

Tujuan aplikasi ini adalah:

```text
Mengurangi pekerjaan manual 70–90%
dan mempercepat proses pembuatan slide tata ibadah
dari beberapa jam menjadi beberapa menit.
```

---

# Target Aplikasi

Aplikasi ini bukan sekadar converter Word ke PowerPoint.

Aplikasi ini adalah:

```text
Liturgi Slide Builder
```

yang berfungsi sebagai:

```text
Asisten multimedia gereja
untuk membuat draft slide tata ibadah secara otomatis,
namun tetap fleksibel untuk diedit sebelum export.
```

---

# Konsep Utama Sistem

Jangan menggunakan arsitektur:

```text
DOCX → PPTX langsung
```

Gunakan arsitektur:

```text
DOCX
→ Parser
→ Struktur Tata Ibadah JSON
→ Slide Builder
→ Template Engine
→ Preview / Editor
→ PPTX Export
```

---

# Teknologi yang Digunakan

## Core Stack

```text
Python
PySide6
python-docx
python-pptx
```

## Tambahan Teknologi

| Teknologi   | Fungsi                      |
| ----------- | --------------------------- |
| PySide6     | UI desktop modern           |
| python-docx | Membaca Word                |
| python-pptx | Membuat PowerPoint          |
| Pillow      | Manipulasi gambar           |
| Pydantic    | Validasi model data         |
| SQLite      | Penyimpanan template/preset |
| PyMuPDF     | Preview slide/PDF           |
| pytest      | Testing parser              |
| PyInstaller | Build .exe                  |

---

# Arsitektur Sistem

```text
+--------------------------------------------------+
|                  INPUT LAYER                     |
|--------------------------------------------------|
| Import DOCX                                      |
| Import Background                                |
| Import Template                                  |
+--------------------------------------------------+

                    ↓

+--------------------------------------------------+
|                  PARSER LAYER                    |
|--------------------------------------------------|
| DOCX Reader                                      |
| Block Classifier                                 |
| Section Detector                                 |
| Song Detector                                    |
| Speaker Detector (P/J/P+J)                       |
| Event Module Detector                            |
+--------------------------------------------------+

                    ↓

+--------------------------------------------------+
|               SERVICE MODEL LAYER                |
|--------------------------------------------------|
| ServiceDocument                                  |
| SectionModel                                     |
| SongModel                                        |
| PrayerModel                                      |
| AnnouncementModel                                |
+--------------------------------------------------+

                    ↓

+--------------------------------------------------+
|               SLIDE BUILDER LAYER                |
|--------------------------------------------------|
| Slide Generator                                  |
| Text Splitter                                    |
| Overflow Detector                                |
| Auto Pagination                                  |
+--------------------------------------------------+

                    ↓

+--------------------------------------------------+
|               TEMPLATE ENGINE                    |
|--------------------------------------------------|
| Background Resolver                              |
| Font Resolver                                    |
| Layout Resolver                                  |
| Theme Engine                                     |
+--------------------------------------------------+

                    ↓

+--------------------------------------------------+
|               PREVIEW & EDITOR                   |
|--------------------------------------------------|
| Slide Preview                                    |
| Fullscreen Preview                               |
| Slide Editor                                     |
| Reorder Slide                                    |
| Split / Merge Slide                              |
+--------------------------------------------------+

                    ↓

+--------------------------------------------------+
|                 EXPORT LAYER                     |
|--------------------------------------------------|
| Export PPTX                                      |
| Save Project                                     |
| Export Preview PDF                               |
+--------------------------------------------------+
```

---

# Konsep Struktur Tata Ibadah

Semua tata ibadah harus diubah menjadi struktur data internal.

Contoh:

```json
{
  "service_form": "GMIM Bentuk II",
  "theme": "Iman Kamu Jangan Bergantung...",
  "modules": [
    "baptisan",
    "pelantikan"
  ],
  "sections": [
    {
      "type": "section",
      "title": "Persiapan"
    },
    {
      "type": "song_title",
      "title": "KJ No. 14"
    },
    {
      "type": "song_lyrics",
      "content": "Muliakan Tuhan Allah..."
    }
  ]
}
```

---

# Preset Tata Ibadah

Aplikasi harus mendukung preset:

```text
GMIM Bentuk I
GMIM Bentuk II
GMIM Bentuk III
GMIM Bentuk IV
GMIM Bentuk V
```

Preset hanya menentukan:

* urutan umum ibadah
* keyword section
* default template
* default background
* aturan parser

---

# Sistem Modul Tambahan

Acara tambahan tidak dibuat sebagai bentuk ibadah baru.

Gunakan konsep:

```text
Preset + Module
```

Contoh:

```text
GMIM Bentuk II
+ Modul Baptisan
+ Modul Pelantikan
+ Modul HUT Jemaat
```

Module yang perlu didukung:

```text
Baptisan Kudus
Perjamuan Kudus
Pelantikan
HUT Jemaat
Peneguhan Sidi
Ibadah Syukur
Natal
Paskah
Jumat Agung
Kenaikan Yesus
Pentakosta
```

---

# Jenis Slide

Sistem harus mendukung tipe slide berikut:

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

---

# Parser System

## Tahapan Parser

```text
DOCX Reader
→ Raw Block
→ Block Classifier
→ Section Detector
→ Slide Builder
```

## Deteksi yang Wajib

Parser harus mampu mendeteksi:

```text
Judul ibadah
Tema
Tanggal
Khadim
Bentuk ibadah
Section besar
Lagu KJ/NKB/PKJ/NNBT
P/J/P+J
Doa
Pembacaan Alkitab
Persembahan
Berkat
Warta Jemaat
```

---

# Template Engine

## Struktur Folder

```text
templates/
assets/
backgrounds/
fonts/
logos/
icons/
```

## Contoh Template

```json
{
  "song_lyrics": {
    "font_family": "Impact",
    "font_size": 46,
    "color": "#FFFFFF",
    "align": "center",
    "background": "song_dark.jpg"
  },

  "liturgy_dialog": {
    "font_family": "Montserrat",
    "font_size": 38,
    "background": "prayer.jpg",

    "speaker_colors": {
      "P": "#FFFFFF",
      "J": "#FFFF00",
      "P+J": "#FFFF00"
    }
  }
}
```

---

# Slide Renderer

Renderer harus mendukung:

```text
Background image full slide
Overlay transparan
Text shadow
Auto-fit font size
Text wrapping
Rich text warna P/J
Center align
Left align
Slide pagination otomatis
```

---

# Sistem Overflow

Masalah utama slide terpotong harus diselesaikan dengan:

## Auto Pagination

Jika teks terlalu panjang:

```text
otomatis pecah ke slide berikutnya
```

## Dynamic Font Scaling

Jika sedikit overflow:

```text
perkecil font otomatis
```

## Safe Area System

Semua teks harus berada dalam:

```text
safe content area
```

agar tidak keluar slide.

---

# Preview System

Aplikasi wajib memiliki:

## Preview Slide

```text
Thumbnail slide
Preview besar
```

## Fullscreen Preview

Mirip mode slideshow PowerPoint.

Tujuan:

```text
cek overflow,
cek layout,
cek keterbacaan
sebelum export.
```

---

# Editor System

User harus bisa:

```text
Edit teks
Edit title
Ganti background
Split slide
Merge slide
Duplicate slide
Delete slide
Reorder slide
Include / exclude slide
```

---

# Workflow Aplikasi

## Workflow Utama

```text
1. User buka aplikasi

2. Pilih preset:
   - Bentuk I
   - Bentuk II
   - dst

3. Import DOCX tata ibadah

4. Parser membaca dokumen

5. Sistem mendeteksi:
   - section
   - lagu
   - liturgi
   - acara tambahan

6. Sistem membentuk struktur ibadah JSON

7. Slide Builder membuat draft slide

8. Template Engine menerapkan desain

9. Preview slide ditampilkan

10. User melakukan koreksi

11. Export PPTX
```

---

# Struktur Data Utama

## ServiceDocument

Representasi tata ibadah keseluruhan.

## SectionModel

Representasi section ibadah.

## SlideItem

Representasi setiap slide.

## TemplatePreset

Aturan visual.

---

# Prioritas Pengembangan

## Versi 1 (MVP)

Fokus:

```text
Import DOCX
Parser section dasar
Generate slide otomatis
Template engine dasar
Preview sederhana
Export PPTX
```

## Versi 2

Tambahkan:

```text
Fullscreen preview
Editor slide
Preset Bentuk I–V
Module system
Overflow handling
```

## Versi 3

Tambahkan:

```text
Bank lagu
Bank background
Bank template
Rich text
Theme manager
```

## Versi 4

Tambahkan:

```text
Cloud sync
Multi-user
Web app
Realtime collaboration
```

---

# Prinsip Pengembangan

## Jangan mengejar otomatis 100%

Target realistis:

```text
80–90% otomatis
10–20% koreksi manual
```

## Fokus ke fleksibilitas

Karena tata ibadah gereja sering berubah.

## Gunakan struktur data internal

Jangan langsung generate PPT dari Word.

## Semua hasil harus bisa diedit

User tetap memegang kontrol penuh.

---

# Goal Akhir

```text
Membantu komisi multimedia gereja
membuat slide tata ibadah lebih cepat,
lebih konsisten,
lebih rapi,
dan lebih mudah dikelola.
```
