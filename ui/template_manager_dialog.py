from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.template_manager import TemplateManager


class TemplateManagerDialog(QDialog):
    def __init__(self, manager: TemplateManager | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Template Manager")
        self.resize(420, 360)
        self.manager = manager or TemplateManager()
        self.list_widget = QListWidget()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)
        buttons = QHBoxLayout()
        actions = [
            ("Duplicate", self.duplicate_template),
            ("Rename", self.rename_template),
            ("Delete", self.delete_template),
            ("Import", self.import_template),
            ("Export", self.export_template),
        ]
        for label, handler in actions:
            button = QPushButton(label)
            button.clicked.connect(handler)
            buttons.addWidget(button)
        layout.addLayout(buttons)

    def refresh(self):
        self.list_widget.clear()
        self.list_widget.addItems(self.manager.list_templates())

    def current_template(self):
        item = self.list_widget.currentItem()
        return item.text() if item else None

    def duplicate_template(self):
        name = self.current_template()
        if not name:
            return
        new_name, ok = QInputDialog.getText(self, "Duplicate Template", "Nama template baru:", text=f"{name}_copy")
        if ok and new_name:
            self._run(lambda: self.manager.duplicate(name, new_name))

    def rename_template(self):
        name = self.current_template()
        if not name:
            return
        new_name, ok = QInputDialog.getText(self, "Rename Template", "Nama baru:", text=name)
        if ok and new_name:
            self._run(lambda: self.manager.rename(name, new_name))

    def delete_template(self):
        name = self.current_template()
        if not name:
            return
        if QMessageBox.question(self, "Hapus Template", f"Hapus template {name}?") == QMessageBox.Yes:
            self._run(lambda: self.manager.delete(name))

    def import_template(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Template", "", "JSON (*.json)")
        if path:
            self._run(lambda: self.manager.import_template(path))

    def export_template(self):
        name = self.current_template()
        if not name:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Template", f"{name}.json", "JSON (*.json)")
        if path:
            self._run(lambda: self.manager.export_template(name, path))

    def _run(self, action):
        try:
            action()
            self.refresh()
        except Exception as exc:
            QMessageBox.critical(self, "Template Error", str(exc))
