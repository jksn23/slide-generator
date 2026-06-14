def get_stylesheet():
    return """
    QMainWindow {
        background-color: #F4F6F4;
    }
    
    QLabel#AppTitle {
        font-family: "Segoe UI", "Inter";
        font-weight: bold;
        font-size: 26px;
        color: #FFFFFF;
        letter-spacing: 0.5px;
    }
    
    QLabel#AppSubtitle {
        font-family: "Segoe UI", "Inter";
        font-size: 14px;
        color: #E2EFE7;
        opacity: 0.9;
    }
    
    QFrame#Header {
        background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #1B4332, stop: 1 #2D6A4F);
        border-bottom: 2px solid #102B20;
    }
    
    QFrame.Card {
        background-color: #FFFFFF;
        border: 1px solid #E0E5E1;
        border-radius: 14px;
    }
    
    QPushButton.PrimaryButton {
        background-color: #2D6A4F;
        color: #FFFFFF;
        border-radius: 8px;
        padding: 10px 18px;
        font-family: "Segoe UI Semibold", "Inter";
        font-size: 14px;
        border: none;
    }
    QPushButton.PrimaryButton:hover {
        background-color: #40916C;
    }
    QPushButton.PrimaryButton:pressed {
        background-color: #1B4332;
    }
    
    QPushButton.SecondaryButton {
        background-color: #FFFFFF;
        color: #2D6A4F;
        border: 1.5px solid #2D6A4F;
        border-radius: 8px;
        padding: 8px 16px;
        font-family: "Segoe UI Semibold", "Inter";
        font-size: 14px;
    }
    QPushButton.SecondaryButton:hover {
        background-color: #F2F7F4;
        color: #1B4332;
        border: 1.5px solid #1B4332;
    }
    QPushButton.SecondaryButton:pressed {
        background-color: #E2EFE7;
    }
    
    QLabel.SectionTitle {
        font-family: "Segoe UI Semibold", "Inter";
        font-size: 18px;
        color: #1E1E1E;
        padding-bottom: 4px;
    }
    
    QLabel.BodyText {
        font-family: "Segoe UI", "Inter";
        font-size: 14px;
        color: #3C423E;
    }
    
    QLineEdit, QComboBox, QSpinBox {
        background-color: #F9FAF9;
        border: 1px solid #D2D8D3;
        border-radius: 8px;
        min-height: 36px;
        padding: 6px 12px;
        color: #1E1E1E;
        font-family: "Segoe UI", "Inter";
        font-size: 14px;
    }
    QComboBox {
        padding-right: 32px;
    }
    QComboBox::drop-down {
        border-left: 1px solid transparent;
        width: 32px;
    }
    QComboBox::down-arrow {
        image: none;
        /* Optional: Add custom svg arrow here if needed */
    }
    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        border: 1px solid #D2D8D3;
        border-radius: 8px;
        selection-background-color: #E2EFE7;
        selection-color: #1B4332;
        outline: none;
    }
    QSpinBox {
        padding-right: 30px;
    }
    QSpinBox::up-button, QSpinBox::down-button {
        border-left: 1px solid #D2D8D3;
        width: 24px;
        background-color: #F4F6F4;
    }
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {
        background-color: #E2EFE7;
    }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
        border: 1.5px solid #2D6A4F;
        background-color: #FFFFFF;
    }
    
    QScrollArea#LeftPanelScroll {
        border: none;
        background-color: transparent;
    }
    QWidget#LeftPanelContent {
        background-color: transparent;
    }
    QFrame#SettingsCard QLabel.BodyText {
        color: #4A524C;
        font-size: 13px;
        margin-top: 4px;
    }
    
    QStatusBar {
        background-color: #F4F6F4;
        border-top: 1px solid #E0E5E1;
        color: #6C756F;
        font-size: 12px;
        font-family: "Segoe UI", "Inter";
    }
    
    /* Scroll area */
    QScrollArea {
        border: none;
        background-color: transparent;
    }
    QScrollBar:vertical {
        border: none;
        background: transparent;
        width: 8px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #C4CCC6;
        min-height: 30px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: #9AA39C;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar:horizontal {
        border: none;
        background: transparent;
        height: 8px;
        margin: 0px;
    }
    QScrollBar::handle:horizontal {
        background: #C4CCC6;
        min-width: 30px;
        border-radius: 4px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #9AA39C;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }
    
    /* Splitter */
    QSplitter::handle {
        background-color: transparent;
    }
    QSplitter::handle:horizontal {
        width: 12px;
    }
    QSplitter::handle:hover {
        background-color: #E2EFE7;
    }
    QSplitter::handle:pressed {
        background-color: #C0D6C8;
    }
    
    /* Checkbox */
    QCheckBox {
        spacing: 8px;
        font-family: "Segoe UI", "Inter";
        font-size: 14px;
        color: #3C423E;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border: 1px solid #D2D8D3;
        border-radius: 4px;
        background-color: #FFFFFF;
    }
    QCheckBox::indicator:hover {
        border: 1px solid #2D6A4F;
    }
    QCheckBox::indicator:checked {
        background-color: #2D6A4F;
        border: 1px solid #2D6A4F;
        /* Note: Checkmark image would be ideal here */
    }
    """
