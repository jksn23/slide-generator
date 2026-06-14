Tentu, ini adalah versi teks yang sudah dirapikan kembali ke dalam format Markdown yang bersih dan terstruktur. Beberapa bagian yang sebelumnya menyatu (seperti tabel dan blok kode) telah saya perbaiki agar sesuai dengan standar Markdown.

Anda dapat langsung menyalin teks di bawah ini dan menyimpannya sebagai file `update-sistem-v4-v2.md`:

```markdown
# 📋 ARSITUR & BLUEPRINT PENGEMBANGAN SISTEM (V4-V2)
### 🛠️ Fitur: Interactive Cover Designer & Heuristic Metadata Extractor
**Target Eksekusi:** AI Agent / IDE Extension (Cursor, Windsurf, Copilot, Cline)

---

## 1. WORKFLOW & PIPELINE UTAMA
Modul ini menambahkan gerbang interseptor penanganan dokumen awal (*Pre-processing & Landing Window*) sebelum slide masuk ke antrean *Deck Editor* utama. Alur kerja wajib dieksekusi secara linear sebagai berikut:

```text
[Aplikasi Dijalankan]
          │
          ▼
┌────────────────────────────────┐
│   Landing Window: Buka File    │ ──► Menerima format dokumen .docx, .doc, .pdf
└────────────────────────────────┘
          │
          ▼
┌────────────────────────────────┐
│ Heuristic Metadata Extractor   │ ──► Memindai Page 1 untuk mencari teks berbobot terbesar
└────────────────────────────────┘
          │
          ▼
┌────────────────────────────────┐
│   Interactive Cover Designer   │ ──► WYSIWYG Canvas (Drag, Drop, Style, & Background Impor)
└────────────────────────────────┘
          │
          ▼
┌────────────────────────────────┐
│   Main Deck Editor (Eksisting) │ ──► Slide Cover disisipkan ke indeks 0 dari SlideDeck
└────────────────────────────────┘

```

---

## 2. SPESIFIKASI MODIFIKASI DATA LAYER

**File Target:** `core/models.py`

AI Agent wajib menambahkan tipe slide baru dan sekumpulan atribut penempatan posisi absolut (koordinat relatif 0.0 - 1.0) pada dataclass `SlideItem` untuk merekam koordinat komponen teks dari kanvas UI.

### 2.1 Penambahan Enum `SlideType`

```python
class SlideType(Enum):
    COVER = "COVER"
    # Tipe lain yang sudah ada tetap dipertahankan...

```

### 2.2 Penambahan Atribut pada `SlideItem`

Tambahkan field berikut ke dalam kelas `SlideItem` dengan nilai bawaan (*default values*):

| Nama Atribut | Tipe Data | Nilai Bawaan | Deskripsi |
| --- | --- | --- | --- |
| `is_absolute_layout` | `bool` | `False` | Ditandai `True` khusus untuk tipe `SlideType.COVER` |
| `title_pos_x` | `float` | `0.1` | Koordinat X relatif terhadap lebar slide (0.0 s.d 1.0) |
| `title_pos_y` | `float` | `0.3` | Koordinat Y relatif terhadap tinggi slide (0.0 s.d 1.0) |
| `title_width` | `float` | `0.8` | Lebar kotak teks relatif terhadap lebar slide |
| `title_height` | `float` | `0.2` | Tinggi kotak teks relatif terhadap tinggi slide |
| `title_font_profile` | `dict` | `None` | Menyimpan konfigurasi font kustom: `{"family": str, "size": int, "color": str, "bold": bool}` |

---

## 3. SPESIFIKASI HEURISTIC EXTRACTION ENGINE

**File Target:** `core/readers.py` (atau `core/universal_parser.py`)

Mesin ekstraksi bertugas memindai halaman pertama dokumen liturgi secara otomatis untuk mendeteksi judul utama ibadah berdasarkan bobot visual elemen teks.

### 3.1 Algoritma Pembaca Word (`python-docx`)

```python
def extract_cover_title_from_docx(doc_path: str) -> str:
    from docx import Document
    doc = Document(doc_path)
    
    best_text = ""
    max_weight = 0
    
    # Evaluasi maksimal 5 paragraf pertama di halaman awal
    for p in doc.paragraphs[:5]:
        text = p.text.strip()
        if not text:
            continue
            
        weight = 0
        # Heuristik 1: Ukuran font paragraf atau run teks
        if p.style.font.size:
            weight += p.style.font.size.pt
        
        # Heuristik 2: Atribut cetak tebal (Bold)
        if p.style.font.bold:
            weight += 15
            
        # Heuristik 3: Seluruh teks menggunakan HURUF KAPITAL
        if text.isupper():
            weight += 10
            
        if weight > max_weight:
            max_weight = weight
            best_text = text
            
    return best_text if best_text else "TATA IBADAH REKAYASA"

```

### 3.2 Algoritma Pembaca PDF (`PyMuPDF / fitz`)

```python
def extract_cover_title_from_pdf(pdf_path: str) -> str:
    import fitz
    doc = fitz.open(pdf_path)
    if len(doc) == 0:
        return ""
        
    page = doc[0] # Ambil halaman pertama saja
    blocks = page.get_text("dict")["blocks"]
    
    best_text = ""
    max_font_size = 0
    
    for b in blocks:
        if "lines" in b:
            for l in b["lines"]:
                for s in l["spans"]:
                    text = s["text"].strip()
                    size = s["size"]
                    
                    # Heuristik: Cari ukuran font murni terbesar di page 1
                    if size > max_font_size and len(text) > 3:
                        max_font_size = size
                        best_text = text
                        
    return best_text

```

---

## 4. UI INTERACTIVE COVER DESIGNER CANVAS

**File Baru:** `ui/cover_editor.py`

Buat komponen antarmuka berbasis `QGraphicsView` dan `QGraphicsScene` untuk memfasilitasi manipulasi desain cover secara visual (*WYSIWYG Layout*).

### 4.1 Kelas Komponen Teks Interaktif

```python
from PyQt5.QtWidgets import QGraphicsTextItem, QGraphicsItem
from PyQt5.QtCore import Qt

class CoverTextItem(QGraphicsTextItem):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        # Aktifkan flag drag, select, dan update geometri internal PyQt
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setTextInteractionFlags(Qt.TextEditorInteraction)

```

### 4.2 Struktur Jendela Dialog Designer Canvas

```python
from PyQt5.QtWidgets import QDialog, QGraphicsScene, QGraphicsView, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog
from PyQt5.QtGui import QPixmap, QBrush

class CoverDesignerDialog(QDialog):
    def __init__(self, detected_title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Interactive Cover Designer Wizard")
        self.resize(1100, 700)
        
        # Inisialisasi Kanvas dengan Aspek Rasio Widescreen (16:9)
        self.scene = QGraphicsScene(0, 0, 1600, 900)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QBrush.texture)
        
        # Tambahkan teks judul hasil deteksi heuristik ke kanvas
        self.title_item = CoverTextItem(detected_title)
        self.title_item.setPos(200, 300) # Koordinat spawn default awal
        self.scene.addItem(self.title_item)
        
        self.bg_image_path = None
        self.init_layout()
        
    def init_layout(self):
        main_layout = QHBoxLayout(self)
        
        # Panel Kiri: Area Kerja Kanvas Preview
        main_layout.addWidget(self.view, stretch=3)
        
        # Panel Kanan: Sidebar Controls (Toolbox)
        sidebar = QVBoxLayout()
        btn_bg = QPushButton("Impor Gambar Latar (Background)")
        btn_bg.clicked.connect(self.choose_background)
        
        btn_done = QPushButton("Selesai & Lanjutkan ke Editor")
        btn_done.clicked.connect(self.accept)
        
        sidebar.addWidget(btn_bg)
        sidebar.addStretch()
        sidebar.addWidget(btn_done)
        main_layout.addLayout(sidebar, stretch=1)
        
    def choose_background(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Pilih Gambar Latar", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.bg_image_path = file_path
            pixmap = QPixmap(file_path).scaled(1600, 900, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            self.scene.setBackgroundBrush(QBrush(pixmap))
            
    def get_layout_data(self) -> dict:
        """Mengembalikan data layout untuk disimpan ke objek SlideItem."""
        scene_w = self.scene.width()
        scene_h = self.scene.height()
        
        return {
            "text": self.title_item.toPlainText(),
            "pos_x": self.title_item.x() / scene_w,
            "pos_y": self.title_item.y() / scene_h,
            "width": self.title_item.boundingRect().width() / scene_w,
            "height": self.title_item.boundingRect().height() / scene_h,
            "bg_image": self.bg_image_path
        }

```

---

## 5. REFAKTORING TRANSLATOR OPENXML

**File Target:** `core/renderers.py` -> `PPTXRenderer`

Ubah logika pembuatan bentuk slide jika sistem mendeteksi slide bertipe koordinat absolut (`is_absolute_layout == True`). Pastikan untuk menggunakan properti internal `.part.element` untuk menghindari `AttributeError` pada spesifikasi objek `Presentation`.

Perubahan Kode Implementasi Render Slide Absolut:

```python
# Di dalam method render() milik PPTXRenderer:
for slide_item in deck_slides:
    if not slide_item.include:
        continue
    slide = prs.slides.add_slide(blank_layout)
    
    # JIKA SLIDE ADALAH COVER (LAYOUT ABSOLUT)
    if getattr(slide_item, 'is_absolute_layout', False):
        slide_w_inches = prs.slide_width
        slide_h_inches = prs.slide_height
        
        # Konversi kembali dari koordinat relatif UI ke Inches Aktual PPTX
        left = slide_w_inches * slide_item.title_pos_x
        top = slide_h_inches * slide_item.title_pos_y
        width = slide_w_inches * slide_item.title_width
        height = slide_h_inches * slide_item.title_height
        
        # Gambar background cover secara terpisah jika diunggah pengguna
        if slide_item.background and slide_item.background.image:
            self.background_renderer.render(slide, prs, slide_item, style)
            
        # Tambahkan Textbox posisi absolut langsung ke slide PPTX
        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = slide_item.content
        
        # Ambil pengaturan font dari title_font_profile kustom
        if slide_item.title_font_profile:
            p.font.name = slide_item.title_font_profile.get("family", "Arial")
            p.font.size = Pt(slide_item.title_font_profile.get("size", 44))
            # Tambahkan pewarnaan RGB kustom jika didefinisikan...
        continue

    # Alur pengerjaan slide standar (lirik liturgi bawaan parser) diletakkan di bawah sini...

```

---

## 6. PENJAHITAN WORKFLOW INTEGRASI UTAMA

**File Target:** `ui/main_window.py`

Ubah urutan fungsi penanganan pembacaan dokumen pada fungsi `generate_preview` (atau fungsi sejenis saat file di-load) agar wizard dialog cover di-intersepsi di awal:

```python
    def handle_file_imported(self, file_path: str):
        # 1. Jalankan Heuristic Extraction Engine berdasarkan format ekstensi file
        if file_path.endswith('.docx'):
            detected_title = extract_cover_title_from_docx(file_path)
        else:
            detected_title = extract_cover_title_from_pdf(file_path)
            
        # 2. Munculkan Dialog Wizard Interactive Designer secara Modal
        designer = CoverDesignerDialog(detected_title, parent=self)
        if designer.exec_() == QDialog.Accepted:
            cover_data = designer.get_layout_data()
            
            # 3. Bangun objek SlideItem baru khusus tipe COVER
            cover_slide = SlideItem(
                id="slide-cover-0",
                title="Slide Cover Utama",
                content=cover_data["text"],
                type=SlideType.COVER,
                section="Cover",
                is_absolute_layout=True,
                title_pos_x=cover_data["pos_x"],
                title_pos_y=cover_data["pos_y"],
                title_width=cover_data["width"],
                height=cover_data["height"]
            )
            if cover_data["bg_image"]:
                cover_slide.background = SlideBackground(image=cover_data["bg_image"])
                
            # 4. Parsing sisa isi dokumen lirik menggunakan parser lama Anda
            self.deck = parse_file_to_deck(file_path, ... )
            self.slides = self.deck.slides
            
            # 5. Suntik (Push) slide cover buatan wizard ke indeks teratas (Indeks 0)
            self.slides.insert(0, cover_slide)
            
            # 6. Refresh tampilan UI List Thumbnail Slide
            self.refresh_preview_list()

```

---

⚠️ **CATATAN STRIKTIF UNTUK AI AGENT:** Pastikan seluruh integrasi modul di atas tidak mengubah atau menghapus fungsionalitas pengelompokan penanda *Section* (`custom_breakpoints`) dan fitur pewarisan gambar latar belakang (*background inheritance*) yang telah dibangun pada pembaruan sistem sebelumnya. Periksa keselarasan variabel sebelum menyimpan file!

```

```