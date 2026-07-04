Langkah yang sangat tepat. Mengingat fondasi arsitektur Anda sekarang sudah sangat kokoh, fokus implementasi selanjutnya haruslah pada peningkatan **Quality of Life (QoL)** atau kenyamanan penggunaan bagi pengguna akhir (operator multimedia gereja).

Berdasarkan analisis sebelumnya, saya telah menyusun draf panduan tahap kelima (**V5**) yang berfokus pada **Sistem Re-Edit Cover** dan **Manajemen Preset JSON**. Dua fitur ini akan mencegah pengguna membuang waktu mengatur ulang tata letak gambar dan teks setiap hari Minggu.

Berikut adalah draf panduan yang bisa langsung Anda salin dan berikan kepada AI Agent di IDE Anda:

---

### Salin Teks di Bawah Ini ke AI Agent Anda:

```markdown
# 📋 BLUEPRINT PENGEMBANGAN SISTEM (V5)
### 🛠️ Fitur: Cover Re-Editor & JSON Preset Management
**Target Eksekusi:** AI Agent / IDE Extension

---

## 1. KONTEKS & TUJUAN
Pada versi sebelumnya, kita telah mengimplementasikan `CoverDesignerDialog` yang muncul di awal (fase landing). Namun, ada dua kekurangan utama saat ini:
1. Jika pengguna salah mengetik judul saat sudah masuk ke *Deck Editor*, mereka tidak bisa mengedit ulang tata letak cover tersebut.
2. Pengguna harus mengatur posisi teks dan mengunggah gambar latar secara manual setiap kali aplikasi dibuka.

**Tujuan V5:** * Menambahkan kemampuan mengedit ulang (*Re-edit*) slide tipe `COVER` dari `ui/main_window.py`.
* Menambahkan fitur Simpan/Muat (Save/Load) Preset tata letak cover ke format `.json` di `ui/cover_editor.py`.

---

## 2. MODIFIKASI COVER DESIGNER DIALOG
**File Target:** `ui/cover_editor.py`

Ubah `CoverDesignerDialog` agar dapat menerima *state* (data layout sebelumnya) saat diinisialisasi, dan tambahkan fitur manajemen Preset.

### 2.1 Penyesuaian `__init__` dan Tata Letak Awal
```python
import json
import os
from PyQt5.QtWidgets import QDialog, QGraphicsScene, QGraphicsView, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QMessageBox
# ... (import eksisting lainnya)

class CoverDesignerDialog(QDialog):
    def __init__(self, detected_title: str, existing_layout: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Interactive Cover Designer Wizard")
        self.resize(1100, 700)
        
        self.scene = QGraphicsScene(0, 0, 1600, 900)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QBrush.texture)
        
        # Load Teks
        actual_text = existing_layout["text"] if existing_layout else detected_title
        self.title_item = CoverTextItem(actual_text)
        
        # Load Posisi X/Y jika ada, jika tidak gunakan default
        if existing_layout:
            scene_w, scene_h = 1600, 900
            self.title_item.setPos(existing_layout["pos_x"] * scene_w, existing_layout["pos_y"] * scene_h)
        else:
            self.title_item.setPos(200, 300)
            
        self.scene.addItem(self.title_item)
        self.bg_image_path = existing_layout.get("bg_image") if existing_layout else None
        
        # Load Background jika ada
        if self.bg_image_path and os.path.exists(self.bg_image_path):
            self.apply_background(self.bg_image_path)
            
        self.init_layout()

```

### 2.2 Penambahan Tombol Preset di Sidebar

Di dalam method `init_layout`, tambahkan dua tombol baru: "Simpan Preset" dan "Muat Preset".

```python
        # Di dalam init_layout()
        btn_save_preset = QPushButton("💾 Simpan sebagai Preset")
        btn_save_preset.clicked.connect(self.save_preset)
        
        btn_load_preset = QPushButton("📂 Muat Preset")
        btn_load_preset.clicked.connect(self.load_preset)
        
        sidebar.addWidget(btn_save_preset)
        sidebar.addWidget(btn_load_preset)
        # ... (tombol lainnya)

```

### 2.3 Implementasi Logika Simpan/Muat Preset (JSON)

Tambahkan method helper untuk menerapkan background dan menangani I/O JSON.

```python
    def apply_background(self, file_path: str):
        self.bg_image_path = file_path
        pixmap = QPixmap(file_path).scaled(1600, 900, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.scene.setBackgroundBrush(QBrush(pixmap))

    def save_preset(self):
        preset_data = self.get_layout_data()
        file_path, _ = QFileDialog.getSaveFileName(self, "Simpan Preset Cover", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(preset_data, f, indent=4)
                QMessageBox.information(self, "Sukses", "Preset berhasil disimpan!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Gagal menyimpan preset: {e}")

    def load_preset(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Muat Preset Cover", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    preset_data = json.load(f)
                
                # Terapkan data ke kanvas
                if "text" in preset_data:
                    self.title_item.setPlainText(preset_data["text"])
                if "pos_x" in preset_data and "pos_y" in preset_data:
                    self.title_item.setPos(preset_data["pos_x"] * 1600, preset_data["pos_y"] * 900)
                if preset_data.get("bg_image") and os.path.exists(preset_data["bg_image"]):
                    self.apply_background(preset_data["bg_image"])
                    
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Gagal memuat preset: {e}")

```

---

## 3. INTEGRASI TOMBOL "EDIT COVER" DI MAIN WINDOW

**File Target:** `ui/main_window.py`

Sediakan mekanisme bagi pengguna untuk membuka ulang `CoverDesignerDialog` dari antarmuka list slide utama.

### 3.1 Penambahan Tombol UI

Di dalam fungsi pembuatan komponen editor (misalnya `_build_editor_panel`), tambahkan tombol khusus yang hanya aktif jika slide yang dipilih adalah tipe `COVER`.

```python
        # Di ui/main_window.py
        self.btn_edit_cover = QPushButton("🎨 Edit Tata Letak Cover")
        self.btn_edit_cover.clicked.connect(self.open_cover_reeditor)
        self.btn_edit_cover.setVisible(False) # Sembunyikan secara default
        layout.addWidget(self.btn_edit_cover)

```

### 3.2 Tampilkan/Sembunyikan Tombol Berdasarkan Tipe Slide

Cari fungsi yang menangani perubahan seleksi slide (contoh: `on_slide_selected` atau `load_slide_to_editor`). Di dalamnya, periksa tipe slide:

```python
        # Di dalam fungsi seleksi slide
        if slide_item.type == SlideType.COVER:
            self.btn_edit_cover.setVisible(True)
        else:
            self.btn_edit_cover.setVisible(False)

```

### 3.3 Logika Pemanggilan Ulang Wizard

Buat fungsi yang menangkap data absolut dari slide cover saat ini, mengirimkannya ke dialog, dan memperbarui slide jika pengguna menekan "Selesai".

```python
    def open_cover_reeditor(self):
        if self.current_slide_index is None:
            return
            
        cover_slide = self.slides[self.current_slide_index]
        
        # Susun data layout yang sudah ada
        existing_layout = {
            "text": cover_slide.content,
            "pos_x": getattr(cover_slide, 'title_pos_x', 0.1),
            "pos_y": getattr(cover_slide, 'title_pos_y', 0.3),
            "bg_image": cover_slide.background.image if cover_slide.background else None
        }
        
        from ui.cover_editor import CoverDesignerDialog
        designer = CoverDesignerDialog(detected_title=cover_slide.content, existing_layout=existing_layout, parent=self)
        
        if designer.exec_() == QDialog.Accepted:
            new_data = designer.get_layout_data()
            
            # Update atribut slide dengan data desain yang baru
            cover_slide.content = new_data["text"]
            cover_slide.title_pos_x = new_data["pos_x"]
            cover_slide.title_pos_y = new_data["pos_y"]
            cover_slide.title_width = new_data["width"]
            cover_slide.title_height = new_data["height"]
            
            if new_data["bg_image"]:
                from core.models import SlideBackground
                cover_slide.background = SlideBackground(image=new_data["bg_image"])
                
            self.refresh_preview_list()

```

---

⚠️ **Instruksi Eksekusi AI:** Pastikan pemanggilan impor modul disesuaikan dengan struktur file lokal yang ada. Perbarui `__init__` pada `CoverDesignerDialog` secara presisi agar tidak merusak logika alur saat aplikasi pertama kali membuka dokumen (di mana `existing_layout` akan bernilai `None`).

```