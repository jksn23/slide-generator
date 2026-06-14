from PyQt5.QtWidgets import (
    QGraphicsTextItem, QGraphicsItem, QDialog, QGraphicsScene, 
    QGraphicsView, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QLabel, QFontComboBox, QSpinBox, QCheckBox, QColorDialog
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
    def __init__(self, detected_title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Interactive Cover Designer Wizard")
        self.resize(1100, 700)
        
        # Inisialisasi Kanvas dengan Aspek Rasio Widescreen (16:9)
        self.scene = QGraphicsScene(0, 0, 1600, 900)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.TextAntialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Tambahkan teks judul hasil deteksi heuristik ke kanvas
        self.title_item = CoverTextItem(detected_title)
        self.title_item.setPos(200, 300) # Koordinat spawn default awal
        font = self.title_item.font()
        font.setPointSize(44)
        self.title_item.setFont(font)
        self.scene.addItem(self.title_item)
        
        self.bg_image_path = None
        self.text_color = "#000000"
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
        self.spin_size.setValue(44)
        self.spin_size.valueChanged.connect(self.update_font)
        sidebar.addWidget(self.spin_size)
        
        self.check_bold = QCheckBox("Tebal (Bold)")
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
            "bg_image": self.bg_image_path,
            "title_font_profile": {
                "family": self.combo_font.currentFont().family(),
                "size": self.spin_size.value(),
                "color": self.text_color,
                "bold": self.check_bold.isChecked()
            }
        }
