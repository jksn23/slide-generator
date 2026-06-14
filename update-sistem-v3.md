Berdasarkan isi dari dokumen tata ibadah `Bentuk 2 14 Juni.docx` yang Anda unggah, saya dapat melihat bahwa penulisan formatnya cukup seragam. Namun, tantangan utama dalam *parsing* dokumen Word (DOCX) adalah membedakan mana yang merupakan **Garis Besar Ibadah / Bab Utama** (seperti "PERSIAPAN", "DOA PENYEMBAHAN", "DOA PENUTUP") dan mana yang merupakan **Sub-bagian / Judul Lagu** (seperti "Menyanyi KJ No. 14 Muliakan Tuhan Allah").

Sistem saat ini kemungkinan menangkap pergantian setiap teks yang tebal (*bold*) atau kapital sebagai `section` baru, sehingga judul lagu pun ikut menjadi *Section*.

Untuk mengatasi hal ini, pendekatan terbaik adalah menggunakan **Semantic Keyword Matching (Filter Kata Kunci Utama)** di dalam modul *Parser/Builder* Anda. Sistem hanya akan mengubah/membuat *Section* baru JIKA teks *heading* tersebut mengandung kata kunci tata ibadah GMIM yang valid.

Berikut adalah panduan yang bisa langsung Anda salin dan berikan kepada AI Agent Anda untuk mengeksekusi logika tersebut:

---

### Salin Teks di Bawah Ini ke AI Agent Anda:

```markdown
# Panduan Implementasi Filter Major Section (Garis Besar Ibadah)

## Konteks & Tujuan
Saat ini, sistem pembuat slide menetapkan atribut `section` untuk setiap teks heading atau judul lagu yang terdeteksi. Berdasarkan dokumen tata ibadah, kita hanya ingin membuat Section PowerPoint pada bagian **garis besar ibadah saja** (contoh: PERSIAPAN, PENGAKUAN DOSA, PEMBACAAN FIRMAN, DOA, PENUTUP), dan mengabaikan sub-heading atau judul nyanyian.

**File Target Utama:** `core/parser.py` (atau `core/slide_builder.py` jika logika pembentukan slide dipisah di sana).
**Class Target:** `SlideBuilder` atau kelas yang merakit `SlideItem` dan mengatur `current_section`.

Tugas Anda adalah memodifikasi logika penentuan `section` saat proses pembangunan slide.

---

### Tahap 1: Definisikan Kata Kunci Garis Besar Ibadah (Major Keywords)
Di bagian atas file atau di dalam class builder, tambahkan *tuple/list* konstanta yang berisi kata kunci standar tata ibadah GMIM.

```python
MAJOR_SECTION_KEYWORDS = (
    "PERSIAPAN",
    "PANGGILAN",
    "KEMULIAAN",
    "PENYEMBAHAN",
    "PENGAKUAN",
    "ANUGERAH",
    "PETUNJUK HIDUP",
    "PEMBACAAN FIRMAN",
    "PELAYANAN FIRMAN",
    "PEMBERITAAN FIRMAN",
    "RESPONS",
    "PENGAKUAN IMAN",
    "HUKUM TUHAN",
    "PERSEMBAHAN",
    "DOA SYUKUR",
    "DOA SYAFAAT",
    "DOA PENUTUP",
    "WARTA JEMAAT",
    "PENUTUP",
    "BERKAT",
    "BAPTISAN",
    "SIDI",
    "PERJAMUAN",
    "PENEGUHAN",
    "PERTANYAAN",
)

```

---

### Tahap 2: Buat Fungsi Evaluasi (Is Major Section)

Tambahkan sebuah *method* helper untuk mengecek apakah sebuah teks tergolong dalam garis besar ibadah atau bukan. Teks yang mengandung kata "Menyanyi", "KJ", "NKB", "PKJ", atau "NNBT" harus ditolak secara eksplisit.

```python
    def _is_major_section(self, text: str) -> bool:
        text_upper = text.strip().upper()
        
        # 1. Tolak jika itu adalah instruksi menyanyi atau judul lagu
        if any(song_kw in text_upper for song_kw in ["MENYANYI", "KJ NO", "NKB NO", "PKJ NO", "NNBT NO"]):
            return False
            
        # 2. Cek apakah cocok dengan kata kunci utama ibadah
        for kw in MAJOR_SECTION_KEYWORDS:
            if kw in text_upper:
                return True
                
        # 3. Fallback: Jika teks 100% huruf kapital dan pendek (kurang dari 5 kata), 
        # anggap sebagai section utama (mengantisipasi nama bab yang tidak ada di list)
        words = text_upper.split()
        if text.isupper() and len(words) <= 6 and not "(" in text:
             return True
             
        return False

```

---

### Tahap 3: Terapkan Filter pada Saat Pembuatan Slide (`SlideBuilder`)

Cari loop utama di mana sistem Anda membaca baris/blok teks hasil ekstraksi dan menetapkan nilai variabel pelacak `current_section` sebelum dimasukkan ke dalam `SlideItem`.

Ubah logikanya menjadi seperti ini:

```python
        # Variabel pelacak section yang sedang aktif
        current_section = "Tata Ibadah"

        for block in classified_blocks: # Sesuaikan dengan nama variabel blok Anda
            
            # Jika sistem mendeteksi blok ini adalah Heading / Judul Bagian
            if block.is_heading: # Sesuaikan dengan atribut blok Anda (contoh: block.type == BlockType.HEADING)
                
                # UJI: Apakah ini Major Section?
                if self._is_major_section(block.text):
                    # Bersihkan teks dari instruksi dalam kurung (misal: "DOA PENUTUP (Jemaat duduk)" -> "DOA PENUTUP")
                    clean_section_name = block.text.split('(')[0].strip()
                    current_section = clean_section_name.title() # Jadikan Title Case agar rapi
                
                # Jika bukan Major Section (misal: "Menyanyi KJ 14"), abaikan perubahan.
                # current_section TETAP menggunakan nama section utama sebelumnya!

            # Terapkan current_section ke item slide yang sedang dibuat
            slide_item = SlideItem(
                # ... atribut lainnya ...
                section=current_section
            )

```

**Instruksi Eksekusi untuk AI:** Silakan pelajari struktur file `parser.py` dan `slide_builder.py` di dalam *workspace*. Aplikasikan ketiga tahapan di atas pada logika *looping* pembuat slide. Pastikan `slide_item.section` tidak lagi berubah saat bertemu dengan lirik lagu atau sub-judul biasa.

```

***

### Cara Logika Ini Bekerja di Aplikasi Anda:
1. Saat sistem membaca **"PERSIAPAN"**, ia lolos uji tahap 2. Pelacak Section diubah menjadi `"Persiapan"`.
2. Saat sistem membaca **"KEMULIAAN BAGI ALLAH (Jemaat berdiri)"**, teks di dalam kurung akan dibuang, lalu Pelacak Section diubah menjadi `"Kemuliaan Bagi Allah"`.
3. Saat membaca **"Menyanyi KJ No. 14..."**, uji tahap 2 memblokirnya. Pelacak Section TIDAK berubah. Slide lirik lagu ini akan secara otomatis terkelompokkan (*masuk ke dalam Section*) `"Kemuliaan Bagi Allah"`.
4. PowerPoint yang dihasilkan akan terlihat sangat bersih dan terstruktur sempurna layaknya susunan bab buku!

```