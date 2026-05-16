---

# **Gemini.md — System Instructions: Slide Ibadah Generator (Standalone Python UI)**

---

## **1. Tujuan dan Fungsionalitas Utama**

**Tujuan Sistem:**
Aplikasi ini bertujuan untuk **mengubah dokumen Word tata ibadah gereja menjadi file PowerPoint siap tampil** secara **semi-otomatis**, menghemat waktu pembuatan slide yang sebelumnya dilakukan manual.

**Fungsionalitas Utama yang Harus Dicapai oleh Sistem:**

1. **Upload Dokumen Word (.docx)**

   * Pengguna dapat **mengunggah file Word tata ibadah** yang berisi seluruh teks ibadah: tema, tanggal, lagu, doa, bacaan Alkitab, liturgi P/J/P+J, pengumuman, dan penutup.
   * Sistem harus menolak file selain `.docx`.

2. **Parsing dan Analisis Dokumen**

   * Sistem harus membaca teks dari Word menggunakan **heading styles, keywords, dan speaker tags (P, J, P+J)**.
   * Sistem harus **mengidentifikasi dan mengklasifikasikan setiap blok teks** menjadi kategori:

     * Cover / Tema
     * Instruksi / Slide Informasi
     * Judul Bagian (Persiapan, Doa, Puji-Pujian, dsb.)
     * Judul Lagu
     * Lirik Lagu
     * Liturgi / Dialog (P/J/P+J)
     * Bacaan Alkitab
     * Penutup / Berkat

3. **Split Otomatis ke Slide**

   * Teks panjang (doa, liturgi, lirik lagu) harus dipisah menjadi beberapa slide:

     * **Slide Judul Bagian:** 1 judul = 1 slide
     * **Slide Judul Lagu:** 1 lagu = 1 slide
     * **Slide Lirik:** Maksimal 4–6 baris per slide
     * **Slide Liturgi:** Maksimal 6–8 baris per slide
     * **Split teks berdasarkan tanda baca, pergantian speaker, atau marker `Refr` pada lagu.**

4. **Template Slide Otomatis**

   * Aplikasi harus menerapkan **template slide** sesuai jenis konten:

     * **Cover Slide** → tema, tanggal, gereja, khadim, background foto gereja
     * **Slide Instruksi** → “Dimohon Untuk”, “Mulai Ibadah”
     * **Judul Bagian** → teks besar di tengah, background sederhana
     * **Judul Lagu** → menampilkan nomor dan nama lagu
     * **Slide Lirik Lagu** → teks besar, rata tengah, background gelap
     * **Liturgi P/J/P+J** → teks kiri (P), kanan (J), tengah (P+J), warna berbeda untuk J jika perlu
     * **Bacaan Alkitab** → teks utama + nomor ayat
     * **Penutup / Berkat** → teks besar, rata tengah, background sesuai template

5. **Preview dan Konfirmasi**

   * Sistem menampilkan **preview daftar slide yang akan dibuat** sebelum generate PowerPoint.
   * Pengguna dapat melakukan **scroll, check, dan optional edit kecil** sebelum generate final.

6. **Generate File PowerPoint (.pptx)**

   * Sistem menghasilkan **file PowerPoint lengkap** dengan semua slide sesuai template dan urutan dokumen.
   * Output harus bisa langsung dipakai untuk ibadah.

---

## **2. Struktur Navigasi**

**Aplikasi Desktop ini harus memiliki layout tunggal (window utama)** dengan elemen-elemen berikut:

1. **Header / Judul Aplikasi**

   * Menampilkan teks: **“Slide Ibadah Generator – GMIM Syaloem”**
   * Teks besar, rata tengah

2. **Panel Upload Dokumen**

   * **Label:** “Upload File Word Tata Ibadah”
   * **Tombol Upload:** “Browse File” → file `.docx`
   * **Info File:** Menampilkan nama file yang dipilih + ukuran

3. **Panel Preview Teks / Slide**

   * **Tampilan List atau Tree:** Menampilkan urutan blok teks hasil parsing:

     * Cover → Judul Bagian → Judul Lagu → Lirik Lagu → Liturgi → Bacaan → Penutup
   * **Checkbox** di tiap slide untuk memilih apakah akan di-generate atau tidak (opsional)

4. **Panel Pengaturan Slide (Opsional)**

   * **Jumlah Baris Maksimal per Slide:** input angka
   * **Template Background:** dropdown (Cover, Lirik, Liturgi, Penutup)
   * **Font Size dan Font Family:** input

5. **Panel Action**

   * **Tombol Preview Slide:** generate preview sederhana
   * **Tombol Generate PPT:** finalisasi dan simpan file `.pptx`
   * **Label Status:** menampilkan pesan sukses / error

---

## **3. Detail Komponen per Halaman**

### **3.1 Halaman Utama / Window**

* **Header:** “Slide Ibadah Generator – GMIM Syaloem” (teks besar)
* **Upload Panel:**

  * Label: **“Upload File Word Tata Ibadah”**
  * Tombol: **“Browse File”**
  * Info File: nama file yang dipilih
* **Preview Panel:**

  * **Tree/List view:** menampilkan blok teks terklasifikasi:

    * Cover
    * Slide Instruksi
    * Judul Bagian
    * Judul Lagu
    * Lirik Lagu
    * Liturgi P/J/P+J
    * Bacaan Alkitab
    * Penutup / Berkat
  * **Checkbox** di setiap slide untuk memilih skip atau include
* **Pengaturan Panel (Opsional):**

  * Input: **“Max lines per slide”**
  * Dropdown: **“Template Background”**
  * Input: **“Font size”**, **“Font family”**
* **Action Panel:**

  * Tombol: **“Preview Slide”**
  * Tombol: **“Generate PPT”**
  * Label Status: menampilkan **“Generating... Done / Error”**

---

### **3.2 Komponen Upload**

* **Browse File Button:** trigger open file dialog (.docx)
* Setelah upload, sistem mengekstrak teks → tampil di Preview Panel

---

### **3.3 Komponen Preview**

* **List / Tree view** menampilkan blok teks:

  * Cover → Judul Bagian → Judul Lagu → Lirik → Liturgi → Bacaan → Penutup
* **Checkbox** untuk setiap slide (include / skip)
* **Double-click** blok teks → tampilkan isi teks lengkap (opsional)

---

### **3.4 Komponen Pengaturan**

* **Max lines per slide:** default 6
* **Template Background:**

  * Cover
  * Instruksi
  * Judul Bagian
  * Judul Lagu
  * Lirik Lagu
  * Liturgi
  * Bacaan
  * Penutup
* **Font Size:** default 40
* **Font Family:** default Arial / Segoe UI

---

### **3.5 Komponen Action**

* **Preview Slide Button:**

  * Generate preview sederhana → menampilkan list slide dengan urutan
* **Generate PPT Button:**

  * Generate file `.pptx` → simpan di folder user pilih
* **Status Label:**

  * Menampilkan teks **“Ready / Generating / Done / Error”**

---

## **4. Aturan Penulisan untuk Agen AI**

1. Gunakan **Python 3.x**
2. Gunakan library **`python-docx`** untuk parsing Word
3. Gunakan library **`python-pptx`** untuk generate PowerPoint
4. Gunakan library GUI **PyQt5** (atau Tkinter jika PyQt5 tidak memungkinkan)
5. Semua teks slide harus **mengikuti template yang ditentukan** berdasarkan kategori blok teks
6. Pastikan **urutan slide sama persis** dengan urutan di dokumen Word
7. Split teks panjang sesuai aturan baris maksimal per slide
8. Teks **P/J/P+J harus diposisikan sesuai speaker**:

   * **P:** kiri
   * **J:** kanan, optional warna kuning
   * **P+J:** tengah
9. Semua label penting, tombol, panel harus **sesuai instruksi di atas**
10. Semua slide harus memiliki **background sesuai kategori**
11. Semua fitur utama harus diberi **highlight** di kode agar mudah di-maintain
12. Preview slide harus menampilkan **urutan slide, tipe, dan teks awal**

---

Dokumen ini berfungsi sebagai **blueprint penuh** untuk agen AI pembuat kode otonom agar menghasilkan **aplikasi generator slide ibadah berbasis Python UI** yang **langsung bisa digunakan**.

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.
