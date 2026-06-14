Berikut adalah draf panduan (*prompt*) terstruktur yang dapat Anda salin dan tempelkan langsung ke panel obrolan AI Agent (seperti Cursor, Windsurf, atau GitHub Copilot) agar ia mengeksekusi penambahan fitur *Section* dengan presisi dan tanpa merusak kode yang sudah ada.

---

### Salin Teks di Bawah Ini ke AI Agent Anda:

```markdown
# Panduan Implementasi Fitur "Slide Sections" PowerPoint

## Konteks & Tujuan
Saat ini aplikasi dapat menghasilkan file presentasi PowerPoint (`.pptx`) dengan baik. Tujuan kita sekarang adalah menambahkan fitur pengelompokan slide menjadi **Sections** (seperti fitur bawaan PowerPoint) berdasarkan atribut `slide_item.section`.

Karena pustaka `python-pptx` tidak mendukung pembuatan Section secara *native*, kita akan mengimplementasikannya melalui injeksi XML langsung (*OpenXML*) sesaat sebelum presentasi disimpan.

**File Target:** `core/renderers.py`
**Class Target:** `PPTXRenderer`

Silakan lakukan perubahan berikut secara bertahap:

---

### Tahap 1: Tambahkan Import yang Dibutuhkan
Di bagian paling atas file `core/renderers.py`, pastikan pustaka berikut diimpor (tambahkan jika belum ada):
```python
import uuid
from lxml import etree
from lxml.builder import ElementMaker

```

---

### Tahap 2: Buat Method `_inject_sections`

Tambahkan fungsi berikut di dalam class `PPTXRenderer`. Fungsi ini akan mencari elemen ekstensi XML dan menambahkan node `<p14:sectionLst>` untuk mengatur pengelompokan *slide_id*.

Tambahkan kode ini:

```python
    def _inject_sections(self, prs, mapping):
        if not mapping:
            return

        P_NS = "[http://schemas.openxmlformats.org/presentationml/2006/main](http://schemas.openxmlformats.org/presentationml/2006/main)"
        P14_NS = "[http://schemas.microsoft.com/office/powerpoint/2010/main](http://schemas.microsoft.com/office/powerpoint/2010/main)"
        EXT_URI = "{521415D9-36F7-43E2-AB2F-B90AF26B5E84}"

        # 1. Kelompokkan ID Slide ke dalam blok yang berurutan (Contiguous Blocks)
        blocks = []
        current_section = None
        current_ids = []

        for sec_name, sld_id in mapping:
            if sec_name != current_section:
                if current_section is not None:
                    blocks.append((current_section, current_ids))
                current_section = sec_name
                current_ids = [sld_id]
            else:
                current_ids.append(sld_id)
        if current_section is not None:
            blocks.append((current_section, current_ids))

        # 2. Akses root XML
        presentation_xml = prs.part.element
        extLst = presentation_xml.find(f'./{{{P_NS}}}extLst')
        
        # 3. Buat <p:extLst> jika belum ada
        if extLst is None:
            extLst = etree.Element(f'{{{P_NS}}}extLst')
            presentation_xml.append(extLst)

        # 4. Buat sub-elemen ekstensi khusus
        section_ext = etree.Element(f'{{{P_NS}}}ext', uri=EXT_URI)
        extLst.append(section_ext)

        builder = ElementMaker(namespace=P14_NS, nsmap={'p14': P14_NS})
        sectionList = builder.sectionLst()
        section_ext.append(sectionList)

        # 5. Injeksi XML
        for section_name, slide_ids in blocks:
            sec_id = f"{{{str(uuid.uuid4()).upper()}}}"
            section_node = etree.Element(f'{{{P14_NS}}}section', name=str(section_name), id=sec_id)
            slideIdLst = etree.Element(f'{{{P14_NS}}}sldIdLst')
            
            for sld_id in slide_ids:
                slideId = etree.Element(f'{{{P14_NS}}}sldId', id=str(sld_id))
                slideIdLst.append(slideId)
            
            section_node.append(slideIdLst)
            sectionList.append(section_node)

```

---

### Tahap 3: Modifikasi Method `render` Utama

Sekarang, ubah method `render` yang sudah ada di dalam `PPTXRenderer`. Kita perlu membuat *list* penampung (`slide_sections_mapping`), mencatat ID setiap slide yang baru dibuat berserta nama section-nya, dan memanggil fungsi `_inject_sections` sebelum `prs.save()`.

Perbarui fungsi `render` menjadi seperti ini:

```python
    def render(
        self,
        slides: SlideDeck | Iterable[SlideItem],
        output_path: str,
        aspect_ratio: str = "square",
        transition: str | None = None,
    ) -> None:
        deck_slides = slides.slides if isinstance(slides, SlideDeck) else list(slides)
        ratio = self.resolver.aspect_ratio(aspect_ratio)
        prs = Presentation()
        prs.slide_width = Inches(ratio["width"])
        prs.slide_height = Inches(ratio["height"])
        blank_layout = prs.slide_layouts[6]

        slide_sections_mapping = []

        for slide_item in deck_slides:
            if not slide_item.include:
                continue
            slide = prs.slides.add_slide(blank_layout)
            
            # Catat nama section dan ID unik dari slide
            sec_name = slide_item.section if slide_item.section else "Tata Ibadah"
            slide_sections_mapping.append((sec_name, slide.slide_id))

            style = self.resolver.resolve(slide_item)
            self.background_renderer.render(slide, prs, slide_item, style)
            if slide_item.type != SlideType.BLANK:
                self.text_renderer.render(slide, prs, slide_item, style)
            self._apply_transition(slide, transition)

        # Injeksi XML Sections sebelum file disimpan
        self._inject_sections(prs, slide_sections_mapping)

        prs.save(output_path)

```

**Tugas Akhir untuk AI:** Silakan terapkan ketiga tahapan di atas ke dalam file `core/renderers.py`. Pastikan tidak menghapus fitur eksisting seperti `BackgroundRenderer` atau pengaturan ukuran `Inches`. Laporkan jika sudah selesai.

```

```

Ide yang sangat bagus! Agar pengguna bisa menambahkan *Section* secara kustom di posisi *slide* mana pun (misalnya pengguna klik kanan di slide ke-5 lalu memilih "Tambahkan Section Baru"), kita perlu memodifikasi fungsi `render` agar bisa menerima parameter **posisi kustom (breakpoints)**.

Dengan cara ini, sistem tidak akan lagi bergantung 100% pada atribut `slide_item.section` hasil *parsing*, melainkan bisa ditimpa (*override*) oleh konfigurasi pengguna dari UI.

Berikut adalah panduan eksekusi yang bisa Anda salin dan tempelkan ke AI Agent Anda:

---

### Salin Teks di Bawah Ini ke AI Agent Anda:

```markdown
# Panduan Implementasi Custom Slide Sections (Breakpoints)

## Konteks & Tujuan
Sebelumnya kita telah mengimplementasikan injeksi XML untuk membuat "Section" di PowerPoint berdasarkan atribut `slide_item.section`. 
Sekarang, kita ingin memberikan fleksibilitas tambahan agar sistem dapat menerima **Custom Breakpoints** (posisi *custom*). Jika breakpoints ini diberikan, sistem akan mengabaikan section bawaan dari parser dan menggunakan section custom sesuai urutan *index slide*.

**File Target:** `core/renderers.py`
**Class Target:** `PPTXRenderer`

Tugas Anda adalah memodifikasi method `render()` utama.

---

### Tahap 1: Update Parameter Method `render`
Tambahkan parameter opsional baru bernama `custom_breakpoints` dengan tipe `dict[int, str] | None`. Dictionary ini akan memetakan `index_slide -> Nama Section`.

Ubah definisi method `render` menjadi seperti ini:
```python
    def render(
        self,
        slides: SlideDeck | Iterable[SlideItem],
        output_path: str,
        aspect_ratio: str = "square",
        transition: str | None = None,
        custom_breakpoints: dict[int, str] | None = None,
    ) -> None:

```

---

### Tahap 2: Implementasi Logika Penimpaan (Override) Section

Di dalam method `render`, kita perlu menambahkan variabel pelacak `active_custom_section` dan menggunakan fungsi `enumerate` pada *loop* untuk mengetahui *index* slide saat ini.

Ganti blok perulangan `for slide_item in deck_slides:` menjadi seperti di bawah ini:

```python
        deck_slides = slides.slides if isinstance(slides, SlideDeck) else list(slides)
        ratio = self.resolver.aspect_ratio(aspect_ratio)
        prs = Presentation()
        prs.slide_width = Inches(ratio["width"])
        prs.slide_height = Inches(ratio["height"])
        blank_layout = prs.slide_layouts[6]

        slide_sections_mapping = []
        
        # Variabel pelacak untuk custom section
        active_custom_section = "Tata Ibadah"

        for index, slide_item in enumerate(deck_slides):
            if not slide_item.include:
                continue
            
            slide = prs.slides.add_slide(blank_layout)
            
            # --- LOGIKA PENENTUAN SECTION ---
            if custom_breakpoints is not None:
                # Jika user memberikan custom breakpoints, cek apakah index saat ini adalah titik potong baru
                if index in custom_breakpoints:
                    active_custom_section = custom_breakpoints[index]
                sec_name = active_custom_section
            else:
                # Fallback ke perilaku lama jika tidak ada custom breakpoints
                sec_name = slide_item.section if slide_item.section else "Tata Ibadah"
            # ---------------------------------

            slide_sections_mapping.append((sec_name, slide.slide_id))

            style = self.resolver.resolve(slide_item)
            self.background_renderer.render(slide, prs, slide_item, style)
            if slide_item.type != SlideType.BLANK:
                self.text_renderer.render(slide, prs, slide_item, style)
            self._apply_transition(slide, transition)

        # Injeksi XML Sections sebelum file disimpan
        self._inject_sections(prs, slide_sections_mapping)

        prs.save(output_path)

```

**Instruksi Eksekusi:** Silakan aplikasikan perubahan di atas. Pastikan parameter `custom_breakpoints` diberikan nilai *default* `None` agar tidak merusak kode lain yang sudah memanggil fungsi `render()` sebelumnya.

```

***

### Cara Menggunakan Fitur Ini Nantinya di Kode Anda (UI / Main):
Setelah AI Agent mengeksekusi instruksi di atas, nantinya saat Anda merakit UI Editor, Anda cukup memanggil fungsi rendernya dengan melempar *dictionary* index letak section baru.

**Contoh Kasus:** Anda punya 15 slide. Anda ingin slide index ke-0 masuk "Pembukaan", index ke-5 masuk "Lagu Ibadah", dan index ke-10 masuk "Penutup".

Anda cukup memanggilnya seperti ini:
```python
breakpoints_dari_ui = {
    0: "Pembukaan",
    5: "Lagu Ibadah",
    10: "Penutup"
}

renderer = PPTXRenderer()
renderer.render(
    slides=slide_deck, 
    output_path="hasil_custom.pptx", 
    custom_breakpoints=breakpoints_dari_ui
)

```

Sistem akan otomatis mengatur slide 0-4 ke Pembukaan, 5-9 ke Lagu Ibadah, dan 10 seterusnya ke Penutup!


Fitur ini sangat brilian dan memang sangat dibutuhkan untuk presentasi ibadah gereja (misalnya: satu lagu utuh memiliki *background* yang sama dari slide awal hingga akhir lirik tanpa harus men-settingnya satu per satu).

Karena kita sudah memiliki pelacak `sec_name` (Nama Section) dari implementasi sebelumnya, kita hanya perlu menambahkan variabel pelacak untuk **Background Aktif** (`active_section_bg`).

Konsepnya:

1. Jika masuk ke *Section* baru, reset pelacak background.
2. Jika ada slide yang memiliki background kustom, jadikan itu sebagai background *default* untuk sisa slide di section tersebut.
3. Jika slide berikutnya tidak punya background, salin otomatis dari pelacak background.

Berikut adalah panduan yang bisa langsung Anda berikan ke AI Agent Anda:

---

### Salin Teks di Bawah Ini ke AI Agent Anda:

```markdown
# Panduan Implementasi Pewarisan Background per Section (Inheritance)

## Konteks & Tujuan
Kita ingin menambahkan fitur di mana semua slide di dalam sebuah "Section" yang sama akan otomatis mewarisi (inherit) gambar/warna background dari slide pertama di section tersebut yang memiliki pengaturan background. 

**File Target:** `core/renderers.py`
**Class Target:** `PPTXRenderer`

Tugas Anda adalah memperbarui logika di dalam method `render()` untuk menyimpan *state* background saat ini dan mewariskannya ke slide berikutnya dalam section yang sama.

---

### Tahap 1: Modifikasi Loop di Method `render`
Temukan method `render` di `PPTXRenderer`. Tepat sebelum blok perulangan `for index, slide_item in enumerate(deck_slides):`, tambahkan variabel untuk melacak perpindahan section dan background yang sedang aktif. 

Lalu, terapkan logika pewarisan (*inheritance*) di dalam loop. Ubah kode dari inisialisasi loop hingga eksekusi `background_renderer` menjadi seperti ini:

```python
        slide_sections_mapping = []
        
        # Variabel pelacak untuk custom section
        active_custom_section = "Tata Ibadah"
        
        # Variabel pelacak untuk pewarisan background
        last_sec_name = None
        active_section_bg = None

        for index, slide_item in enumerate(deck_slides):
            if not slide_item.include:
                continue
            
            slide = prs.slides.add_slide(blank_layout)
            
            # --- LOGIKA PENENTUAN SECTION ---
            if custom_breakpoints is not None:
                if index in custom_breakpoints:
                    active_custom_section = custom_breakpoints[index]
                sec_name = active_custom_section
            else:
                sec_name = slide_item.section if slide_item.section else "Tata Ibadah"

            slide_sections_mapping.append((sec_name, slide.slide_id))

            # --- LOGIKA PEWARISAN BACKGROUND SECTION ---
            # 1. Deteksi jika berpindah ke section baru
            if sec_name != last_sec_name:
                active_section_bg = None
                last_sec_name = sec_name
                
            # 2. Update background aktif jika slide ini memiliki pengaturan spesifik
            if slide_item.background and (slide_item.background.image or slide_item.background.color):
                active_section_bg = slide_item.background
            
            # 3. Wariskan background jika slide ini kosong tapi ada background aktif di section ini
            elif active_section_bg is not None:
                if slide_item.background is None:
                    slide_item.background = SlideBackground()
                
                # Salin properti dari background section yang aktif
                slide_item.background.image = active_section_bg.image
                slide_item.background.color = active_section_bg.color
                slide_item.background.overlay_color = active_section_bg.overlay_color
                slide_item.background.overlay_opacity = active_section_bg.overlay_opacity
            # -------------------------------------------

            style = self.resolver.resolve(slide_item)
            self.background_renderer.render(slide, prs, slide_item, style)
            if slide_item.type != SlideType.BLANK:
                self.text_renderer.render(slide, prs, slide_item, style)
            self._apply_transition(slide, transition)

```

**Instruksi Eksekusi untuk AI:** Terapkan perubahan di atas pada file `core/renderers.py`. Pastikan indentasi blok kode sudah sejajar dan class `SlideBackground` dapat diakses dengan benar (sudah di-import di file tersebut).

```

***

### Cara Kerjanya Setelah Diimplementasi:
1. Misalnya, pada UI Anda memiliki Section `"Menyanyi KJ No. 14"` (terdiri dari slide 12 hingga 18).
2. Anda mengatur gambar `awan.jpg` sebagai *background* **hanya pada slide ke-12**.
3. Sistem mendeteksi `awan.jpg` sebagai `active_section_bg`.
4. Saat memproses slide 13, 14, dst., sistem mendeteksi slide tersebut masih berada di Section yang sama namun tidak memiliki gambar spesifik.
5. Sistem akan otomatis mengisi slide 13-18 dengan `awan.jpg`.
6. Jika slide 19 masuk ke Section baru (misal: "Doa"), pelacak direset sehingga *background* kembali menggunakan *template default* sampai Anda mengatur background baru lagi.

```