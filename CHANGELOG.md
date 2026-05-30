# Changelog

## V2 Tahap 1-2 Awal - Service JSON dan Universal Parser

Ringkasan:
- Menambahkan model JSON `ServiceDocument`, `ServiceSection`, dan `ServiceItem` sebagai layer struktur tata ibadah sebelum menjadi slide.
- Memperluas `RawBlock` dengan `source_type`, `page_number`, `paragraph_index`, `style`, dan `metadata` untuk mendukung reader DOCX/PDF berikutnya tanpa merusak constructor lama.
- Menambahkan `UniversalParser` untuk mengubah `RawBlock` menjadi `ServiceDocument`.
- Menambahkan `ServiceSlideBuilder` untuk mengubah `ServiceDocument` menjadi `SlideDeck`/`SlideItem` yang tetap editable.
- Mempertahankan API lama `parse_docx`, `parse_docx_to_deck`, dan pipeline preview/export yang sudah berjalan.
- Menambahkan fallback keyword kosong untuk preset yang belum ada, sehingga bentuk ibadah baru seperti `GMIM Bentuk V` dapat masuk ke parser universal tanpa langsung gagal.

File yang diubah:
- `core/models.py`
- `core/parser.py`
- `core/universal_parser.py`
- `core/slide_builder.py`
- `tests/test_slide_model.py`
- `tests/test_universal_parser.py`

Test yang dijalankan:
- `python -m pytest tests\test_slide_model.py tests\test_universal_parser.py tests\test_parser_pipeline.py tests\test_slide_builder.py`
- `.\venv\Scripts\python.exe -m pytest`
- `.\venv\Scripts\python.exe -m compileall core tests`

Hasil test:
- Lulus: 15 passed untuk subset fondasi.
- Lulus: 67 passed untuk full regression via virtualenv proyek.
- Compileall `core` dan `tests` lulus.

Risiko tersisa:
- Pipeline UI lama belum memakai `ServiceDocument`; tahap berikutnya perlu mengintegrasikan jalur baru secara bertahap.
- PDF reader dan OCR belum dikerjakan sesuai urutan prioritas panduan v2.

## Perbaikan - Parser Style-Aware dan Dialog Liturgi

Ringkasan:
- `DOCXReader` sekarang membaca `paragraph.style.name`, `paragraph.alignment`, `run.bold`, `run.font.size`, dan `uppercase_ratio`.
- Parser mengenali heading bold/uppercase/keyword untuk `NAS PEMBIMBING`, `TAHBISAN DAN SALAM`, `DOA PENYEMBAHAN`, `PENGAKUAN DOSA`, `JANJI ANUGERAH ALLAH`, `PUJI-PUJIAN`, `FIRMAN TUHAN`, `PERSEMBAHAN`, `BERKAT`, `SAAT TEDUH`, `WARTA JEMAAT`, dan `KHOTBAH`.
- Regex speaker diperluas untuk `P:`, `P :`, `P `, `P ,`, `J:`, `J :`, `J `, `P+J:`, `P+J `, `PK:`, `PK `, `L:`, dan `S:`.
- Dialog liturgi berurutan sekarang digabung dalam satu `liturgy_dialog` sampai bertemu heading/section/song title baru, bukan dipotong hanya karena `max_lines`.
- Preview dan export memakai kontrak warna speaker yang sama: `P` putih, `J` kuning, `P+J` kuning.
- `Mazmur 9:8-9` setelah `NAS PEMBIMBING` tidak lagi salah diklasifikasikan sebagai judul lagu.

File yang diubah:
- `core/parser.py`
- `core/renderers.py`
- `ui/components.py`
- `templates/gmim_default.json`
- `templates/gmim_dark.json`
- `tests/test_docx_reader_style.py`
- `tests/test_parser_liturgy.py`
- `tests/test_section_detector.py`
- `tests/test_pptx_renderer.py`
- `tests/test_preview_components.py`

Test yang dijalankan:
- `.\\venv\\Scripts\\python.exe -m pytest`
- `.\\venv\\Scripts\\python.exe -m compileall .`

Hasil test:
- Lulus: 40 passed.
- Compileall seluruh project lulus.

Risiko tersisa:
- Deteksi heading masih heuristik. Dokumen dengan format visual yang sangat berbeda tetap mungkin perlu koreksi manual melalui editor.

## Perbaikan - Export Teks Tidak Sama Dengan Preview

Ringkasan:
- Memperbaiki posisi textbox di export PPTX agar margin template 10x10 diskalakan ke ukuran slide aktual.
- Pada rasio 16:9 dan 4:3, area teks sekarang tetap berada di tengah slide seperti preview, bukan terkunci pada area kiri.
- Menambahkan test agar textbox export 16:9 berada di tengah horizontal dan vertikal slide.

File yang diubah:
- `core/renderers.py`
- `tests/test_pptx_renderer.py`

Test yang dijalankan:
- `.\\venv\\Scripts\\python.exe -m pytest tests\\test_pptx_renderer.py tests\\test_slide_size.py`
- `.\\venv\\Scripts\\python.exe -m pytest`

Hasil test:
- Lulus: 6 passed untuk test renderer/rasio.
- Lulus: 33 passed untuk full regression.

Risiko tersisa:
- Jika template custom memakai margin absolut non-10x10, hasilnya akan dianggap margin berbasis desain 10x10 dan ikut diskalakan.

## Perbaikan - Max Baris per Slide

Ringkasan:
- Memperbaiki pemecahan teks panjang agar tidak hanya bergantung pada tanda baca.
- Baris panjang sekarang dipotong lagi berdasarkan kata dengan batas karakter aman untuk preview/export square.
- Slide builder tetap membagi konten sesuai nilai `Max baris per slide`, sehingga satu slide tidak membawa lebih dari jumlah baris yang dipilih.

File yang diubah:
- `core/parser.py`
- `tests/test_slide_builder.py`

Test yang dijalankan:
- `.\\venv\\Scripts\\python.exe -m pytest tests\\test_slide_builder.py`
- `.\\venv\\Scripts\\python.exe -m pytest`

Hasil test:
- Lulus: 3 passed untuk test khusus slide builder.
- Lulus: 32 passed untuk full regression.

Risiko tersisa:
- Dokumen dengan kata sangat panjang tanpa spasi masih bisa melewati batas visual; kasus itu perlu aturan hyphenation/manual edit.

## Tahap 1 - Rapikan Struktur Data Slide

Ringkasan:
- Menambahkan kontrak model `SlideItem` baru berbasis JSON dengan field `id`, `type`, `section`, `title`, `content`, `speaker_lines`, `background`, `template`, dan `include`.
- Menambahkan `SlideDeck`, `SpeakerLine`, dan `SlideBackground` sebagai fondasi `DOCX -> struktur ibadah -> SlideDeck JSON`.
- Menjaga kompatibilitas atribut lama `slide_type`, `included`, dan `bg_image` agar UI/generator lama tetap bisa berjalan selama migrasi.

File yang diubah:
- `core/models.py`
- `requirements.txt`
- `tests/test_slide_model.py`

Test yang dijalankan:
- `.\\venv\\Scripts\\python.exe -m pytest tests\\test_slide_model.py`

Hasil test:
- Lulus: 3 passed.

Risiko tersisa:
- Parser dan renderer masih memakai pola lama; tahap berikutnya akan memindahkan parser ke pipeline bertahap.

Rencana tahap berikutnya:
- Tahap 2: buat parser bertahap `DOCXReader -> RawBlock -> BlockClassifier -> SectionDetector -> SlideBuilder`.

## Tahap 2 - Parser Bertahap

Ringkasan:
- Mengubah parser menjadi pipeline `DOCXReader -> RawBlock -> BlockClassifier -> SectionDetector -> SlideBuilder`.
- Menambahkan `parse_docx_to_deck(...)` untuk output `SlideDeck` JSON dan mempertahankan `parse_docx(...)` untuk kompatibilitas UI lama.
- Menambahkan deteksi dasar untuk judul ibadah, metadata tema/khadim/tanggal, section, lagu KJ/NKB/PKJ/NNBT, speaker P/J/P+J, bacaan, doa, persembahan, khotbah, pengumuman, berkat, dan penutup.

File yang diubah:
- `core/parser.py`
- `tests/test_parser_pipeline.py`

Test yang dijalankan:
- `.\\venv\\Scripts\\python.exe -m pytest tests\\test_parser_pipeline.py tests\\test_slide_model.py`

Hasil test:
- Lulus: 7 passed.

Risiko tersisa:
- Heuristik parser masih berbasis teks dan style sederhana; preset GMIM tahap 8 akan membuat keyword per bentuk ibadah lebih mudah disesuaikan.

Rencana tahap berikutnya:
- Tahap 3: tambahkan template engine berbasis JSON dan template default GMIM.

## Tahap 3 - Template Engine JSON

Ringkasan:
- Menambahkan `TemplateResolver` untuk membaca template JSON dan menggabungkan default, style per tipe slide, dan override per section.
- Menambahkan `templates/gmim_default.json` dan `templates/gmim_dark.json`.
- Menambahkan struktur `assets/backgrounds`, `assets/logos`, `assets/icons`, dan `assets/fonts`.

File yang diubah:
- `core/template_engine.py`
- `templates/gmim_default.json`
- `templates/gmim_dark.json`
- `assets/backgrounds/.gitkeep`
- `assets/logos/.gitkeep`
- `assets/icons/.gitkeep`
- `assets/fonts/.gitkeep`
- `tests/test_template_engine.py`

Test yang dijalankan:
- `.\\venv\\Scripts\\python.exe -m pytest tests\\test_template_engine.py tests\\test_parser_pipeline.py tests\\test_slide_model.py`

Hasil test:
- Lulus: 10 passed.

Risiko tersisa:
- Renderer lama belum memakai template config; itu akan ditangani pada Tahap 5.

Rencana tahap berikutnya:
- Tahap 4: jadikan ukuran slide default 1:1 dan tambahkan opsi rasio.

## Tahap 4 - Ukuran Slide 1:1 Default

Ringkasan:
- Mengubah `generate_pptx(...)` agar membaca ukuran slide dari template JSON.
- Menjadikan `square` 10x10 inch sebagai default GMIM.
- Menambahkan opsi `landscape_16_9` dan `standard_4_3` melalui konfigurasi template.

File yang diubah:
- `core/generator.py`
- `tests/test_slide_size.py`

Test yang dijalankan:
- `.\\venv\\Scripts\\python.exe -m pytest tests\\test_slide_size.py tests\\test_template_engine.py tests\\test_parser_pipeline.py tests\\test_slide_model.py`

Hasil test:
- Lulus: 12 passed.

Risiko tersisa:
- Posisi textbox generator lama masih lebih cocok untuk 16:9; Tahap 5 akan mengganti renderer menjadi berbasis template config dan margin relatif.

Rencana tahap berikutnya:
- Tahap 5: buat renderer PPTX baru yang terpisah dan berbasis template.

## Tahap 5 - Renderer PPTX Baru

Ringkasan:
- Mengganti generator monolitik dengan `PPTXRenderer`, `BackgroundRenderer`, dan `TextRenderer`.
- Renderer sekarang membaca style dari `TemplateResolver`, termasuk background, overlay, margin, alignment, font, text shadow sederhana, auto-fit font, dan rich text P/J/P+J.
- `generate_pptx(...)` tetap dipertahankan sebagai API publik agar UI lama tidak perlu langsung berubah.

File yang diubah:
- `core/renderers.py`
- `core/generator.py`
- `templates/gmim_default.json`
- `tests/test_pptx_renderer.py`

Test yang dijalankan:
- `.\\venv\\Scripts\\python.exe -m pytest tests\\test_pptx_renderer.py tests\\test_slide_size.py tests\\test_template_engine.py tests\\test_parser_pipeline.py tests\\test_slide_model.py`

Hasil test:
- Lulus: 14 passed.

Risiko tersisa:
- Text outline PowerPoint belum dibuat sebagai efek native; renderer saat ini menyiapkan text shadow sederhana untuk keterbacaan.

Rencana tahap berikutnya:
- Tahap 6: ubah preview UI agar memakai `SlideItem + Template` dan layout list/preview/editor awal.

## Tahap 6 - Preview UI Berbasis Template

Ringkasan:
- Mengubah preview visual menjadi square dan membaca style dari `TemplateResolver`.
- Menata area kerja menjadi list slide, preview utama, dan panel edit awal.
- Menambahkan pilihan template dan rasio slide di UI.

File yang diubah:
- `ui/components.py`
- `ui/main_window.py`
- `tests/test_preview_components.py`

Test yang dijalankan:
- `.\\venv\\Scripts\\python.exe -m pytest tests\\test_preview_components.py tests\\test_pptx_renderer.py tests\\test_slide_size.py tests\\test_template_engine.py tests\\test_parser_pipeline.py tests\\test_slide_model.py`

Hasil test:
- Lulus: 16 passed.

Risiko tersisa:
- Panel edit masih hanya menampilkan detail; kontrol edit manual penuh dikerjakan pada Tahap 7.

Rencana tahap berikutnya:
- Tahap 7: tambahkan editor manual dasar untuk judul, isi, tipe, duplicate/delete, dan move up/down.

## Tahap 7 - Editor Manual Dasar

Ringkasan:
- Menambahkan `DeckEditor` untuk edit judul, isi, tipe slide, section, background, alignment, duplicate, delete, dan move up/down.
- Menghubungkan panel edit PyQt ke slide yang dipilih pada preview.
- Menambahkan style override per slide melalui `metadata.style`, sehingga alignment manual ikut dipakai oleh template resolver.

File yang diubah:
- `core/deck_editor.py`
- `core/template_engine.py`
- `ui/main_window.py`
- `tests/test_deck_editor.py`

Test yang dijalankan:
- `.\\venv\\Scripts\\python.exe -m pytest tests\\test_deck_editor.py tests\\test_preview_components.py tests\\test_pptx_renderer.py tests\\test_slide_size.py tests\\test_template_engine.py tests\\test_parser_pipeline.py tests\\test_slide_model.py`

Hasil test:
- Lulus: 18 passed.

Risiko tersisa:
- UI editor belum menyediakan file picker background khusus di panel kanan; background masih tersedia dari item section dan service editor sudah mendukung path background.

Rencana tahap berikutnya:
- Tahap 8: tambahkan preset GMIM dengan keyword section dan template default per bentuk ibadah.

## Tahap 8 - Preset GMIM

Ringkasan:
- Menambahkan `presets/gmim_presets.json` untuk GMIM Bentuk I, II, III, Ibadah Kolom, Ibadah Pemuda, Ibadah ASM, dan Ibadah Syukur.
- Menambahkan `PresetRegistry` untuk membaca template default, aspect ratio, urutan section, dan keyword parser per preset.
- Parser kini menerima `preset_name` dan mengisi `SlideDeck.preset_name`, `template_name`, dan `aspect_ratio`.
- UI menambahkan pilihan preset GMIM dan menerapkan default template/rasio dari preset.

File yang diubah:
- `presets/gmim_presets.json`
- `core/presets.py`
- `core/parser.py`
- `ui/main_window.py`
- `tests/test_presets.py`

Test yang dijalankan:
- `.\\venv\\Scripts\\python.exe -m pytest tests\\test_presets.py tests\\test_deck_editor.py tests\\test_preview_components.py tests\\test_pptx_renderer.py tests\\test_slide_size.py tests\\test_template_engine.py tests\\test_parser_pipeline.py tests\\test_slide_model.py`

Hasil test:
- Lulus: 21 passed.

Risiko tersisa:
- Keyword preset masih konfigurasi awal; perlu disesuaikan dari lebih banyak dokumen GMIM nyata.

Rencana tahap berikutnya:
- Tahap 9: lengkapi test parser/song/liturgy/section/slide builder sesuai target roadmap.

## Tahap 9 - Testing Parser dan Slide Builder

Ringkasan:
- Menambahkan test khusus untuk parser lagu, liturgi P/J/P+J, section detector, dan slide builder.
- Mengunci target utama: jumlah slide hasil split, lagu terdeteksi, P/J/P+J terdeteksi, bagian ibadah tidak salah menjadi lirik, slide tidak kosong, dan urutan nomor slide stabil.

File yang diubah:
- `tests/test_parser_song.py`
- `tests/test_parser_liturgy.py`
- `tests/test_section_detector.py`
- `tests/test_slide_builder.py`

Test yang dijalankan:
- `.\\venv\\Scripts\\python.exe -m pytest tests\\test_parser_song.py tests\\test_parser_liturgy.py tests\\test_section_detector.py tests\\test_slide_builder.py tests\\test_presets.py tests\\test_deck_editor.py tests\\test_preview_components.py tests\\test_pptx_renderer.py tests\\test_slide_size.py tests\\test_template_engine.py tests\\test_parser_pipeline.py tests\\test_slide_model.py`

Hasil test:
- Lulus: 29 passed.

Risiko tersisa:
- Belum ada fixture DOCX besar dari banyak format tata ibadah; test saat ini memakai blok sintetis dan satu `test.docx` kecil.

Rencana tahap berikutnya:
- Tahap 10: tambahkan konfigurasi packaging PyInstaller, dokumentasi build, dan jalankan full regression.
