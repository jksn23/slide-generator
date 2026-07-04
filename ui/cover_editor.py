import json
import os
from PyQt5.QtWidgets import (
    QGraphicsTextItem, QGraphicsItem, QDialog, QGraphicsScene, 
    QGraphicsView, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QLabel, QFontComboBox, QSpinBox, QCheckBox, QColorDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QBrush, QPainter

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

class CoverDesignerDialog(QDialog):
    def __init__(self, detected_title: str, existing_layout: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Interactive Cover Designer Wizard")
        self.resize(1100, 700)
        
        # Inisialisasi Kanvas dengan Aspek Rasio Widescreen (16:9)
        self.scene = QGraphicsScene(0, 0, 1600, 900)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.TextAntialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Load Teks
        actual_text = existing_layout["text"] if existing_layout and "text" in existing_layout else detected_title
        self.title_item = CoverTextItem(actual_text)
        
        # Load Posisi X/Y jika ada, jika tidak gunakan default
        if existing_layout and "pos_x" in existing_layout and "pos_y" in existing_layout:
            scene_w, scene_h = 1600, 900
            self.title_item.setPos(existing_layout["pos_x"] * scene_w, existing_layout["pos_y"] * scene_h)
        else:
            self.title_item.setPos(200, 300)
            
        # Load font profile jika ada
        font = self.title_item.font()
        font.setPointSize(44)
        self.text_color = "#000000"
        
        if existing_layout and "title_font_profile" in existing_layout and existing_layout["title_font_profile"]:
            profile = existing_layout["title_font_profile"]
            if "family" in profile:
                font.setFamily(profile["family"])
            if "size" in profile:
                font.setPointSize(profile["size"])
            if "bold" in profile:
                font.setBold(profile["bold"])
            if "color" in profile:
                self.text_color = profile["color"]
                from PyQt5.QtGui import QColor
                self.title_item.setDefaultTextColor(QColor(self.text_color))
                
        self.title_item.setFont(font)
        self.scene.addItem(self.title_item)
        
        self.bg_image_path = existing_layout.get("bg_image") if existing_layout else None
        
        # Load Background jika ada
        if self.bg_image_path and os.path.exists(self.bg_image_path):
            self.apply_background(self.bg_image_path)
            
        self.init_layout()
        
    def init_layout(self):
        main_layout = QHBoxLayout(self)
        
        # Panel Kiri: Area Kerja Kanvas Preview
        main_layout.addWidget(self.view, stretch=3)
        
        # Panel Kanan: Sidebar Controls (Toolbox)
        sidebar = QVBoxLayout()
        
        sidebar.addWidget(QLabel("Pengaturan Font:"))
        self.combo_font = QFontComboBox()
        self.combo_font.currentFontChanged.connect(self.update_font)
        sidebar.addWidget(self.combo_font)
        
        sidebar.addWidget(QLabel("Ukuran Font:"))
        self.spin_size = QSpinBox()
        self.spin_size.setRange(10, 200)
        self.spin_size.setValue(self.title_item.font().pointSize())
        self.spin_size.valueChanged.connect(self.update_font)
        sidebar.addWidget(self.spin_size)
        
        self.check_bold = QCheckBox("Tebal (Bold)")
        self.check_bold.setChecked(self.title_item.font().bold())
        self.check_bold.stateChanged.connect(self.update_font)
        sidebar.addWidget(self.check_bold)
        
        btn_color = QPushButton("Pilih Warna Teks")
        btn_color.clicked.connect(self.choose_color)
        sidebar.addWidget(btn_color)
        
        sidebar.addWidget(QLabel("Latar Belakang:"))
        btn_bg = QPushButton("Impor Gambar Latar")
        btn_bg.clicked.connect(self.choose_background)
        sidebar.addWidget(btn_bg)
        
        sidebar.addStretch()
        
        btn_save_preset = QPushButton("💾 Simpan sebagai Preset")
        btn_save_preset.clicked.connect(self.save_preset)
        
        btn_load_preset = QPushButton("📂 Muat Preset")
        btn_load_preset.clicked.connect(self.load_preset)
        
        sidebar.addWidget(btn_save_preset)
        sidebar.addWidget(btn_load_preset)
        
        btn_done = QPushButton("Selesai & Lanjutkan ke Editor")
        btn_done.clicked.connect(self.accept)
        sidebar.addWidget(btn_done)
        
        main_layout.addLayout(sidebar, stretch=1)
        
    def update_font(self):
        font = self.combo_font.currentFont()
        font.setPointSize(self.spin_size.value())
        font.setBold(self.check_bold.isChecked())
        self.title_item.setFont(font)
        
    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.text_color = color.name()
            self.title_item.setDefaultTextColor(color)
        
    def apply_background(self, file_path: str):
        self.bg_image_path = file_path
        pixmap = QPixmap(file_path).scaled(1600, 900, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.scene.setBackgroundBrush(QBrush(pixmap))

    def choose_background(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Pilih Gambar Latar", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.apply_background(file_path)
            
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
                
                # Font profile loading
                if "title_font_profile" in preset_data:
                    profile = preset_data["title_font_profile"]
                    font = self.title_item.font()
                    if "family" in profile:
                        font.setFamily(profile["family"])
                        # update combobox implicitly or explicitly?
                        self.combo_font.setCurrentFont(font)
                    if "size" in profile:
                        font.setPointSize(profile["size"])
                        self.spin_size.setValue(profile["size"])
                    if "bold" in profile:
                        font.setBold(profile["bold"])
                        self.check_bold.setChecked(profile["bold"])
                    if "color" in profile:
                        self.text_color = profile["color"]
                        from PyQt5.QtGui import QColor
                        self.title_item.setDefaultTextColor(QColor(self.text_color))
                    self.title_item.setFont(font)
                    
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Gagal memuat preset: {e}")
            
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
            "bg_image": self.bg_image_path,
            "title_font_profile": {
                "family": self.combo_font.currentFont().family(),
                "size": self.spin_size.value(),
                "color": self.text_color,
                "bold": self.check_bold.isChecked()
            }
        }
