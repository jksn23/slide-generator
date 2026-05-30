def get_stylesheet():
    return """
    QMainWindow {
        background-color: #F7F8F6;
    }
    
    QLabel#AppTitle {
        font-family: "Segoe UI Semibold";
        font-size: 24px;
        color: #FFFFFF;
    }
    
    QLabel#AppSubtitle {
        font-family: "Segoe UI";
        font-size: 14px;
        color: #FFF3C4;
    }
    
    QFrame#Header {
        background-color: #1F4D3A;
    }
    
    QFrame.Card {
        background-color: #FFFFFF;
        border: 1px solid #D9DED8;
        border-radius: 12px;
    }
    
    QPushButton.PrimaryButton {
        background-color: #1F4D3A;
        color: #FFFFFF;
        border-radius: 8px;
        padding: 10px 16px;
        font-family: "Segoe UI Semibold";
        font-size: 14px;
    }
    QPushButton.PrimaryButton:hover {
        background-color: #123326;
    }
    
    QPushButton.SecondaryButton {
        background-color: #FFFFFF;
        color: #1F4D3A;
        border: 1px solid #1F4D3A;
        border-radius: 8px;
        padding: 8px 14px;
        font-family: "Segoe UI Semibold";
        font-size: 14px;
    }
    QPushButton.SecondaryButton:hover {
        background-color: #F7F8F6;
    }
    
    QLabel.SectionTitle {
        font-family: "Segoe UI Semibold";
        font-size: 18px;
        color: #1E1E1E;
    }
    
    QLabel.BodyText {
        font-family: "Segoe UI";
        font-size: 14px;
        color: #1E1E1E;
    }
    
    QLineEdit, QComboBox, QSpinBox {
        background-color: #FFFFFF;
        border: 1px solid #D9DED8;
        border-radius: 8px;
        min-height: 34px;
        padding: 6px 10px;
        color: #1E1E1E;
        font-family: "Segoe UI";
        font-size: 14px;
    }
    QComboBox {
        padding-right: 30px;
    }
    QComboBox::drop-down {
        border-left: 1px solid #D9DED8;
        width: 28px;
    }
    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        border: 1px solid #D9DED8;
        selection-background-color: #EAF2EE;
        selection-color: #1E1E1E;
    }
    QSpinBox {
        padding-right: 28px;
    }
    QSpinBox::up-button, QSpinBox::down-button {
        border-left: 1px solid #D9DED8;
        width: 22px;
    }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
        border: 1px solid #1F4D3A;
    }
    QScrollArea#LeftPanelScroll {
        border: none;
        background-color: transparent;
    }
    QWidget#LeftPanelContent {
        background-color: transparent;
    }
    QFrame#SettingsCard QLabel.BodyText {
        color: #2C332E;
        font-size: 13px;
    }
    
    QStatusBar {
        background-color: #F7F8F6;
        border-top: 1px solid #D9DED8;
        color: #5F665F;
        font-size: 12px;
    }
    
    /* Scroll area */
    QScrollArea {
        border: none;
        background-color: transparent;
    }
    QScrollBar:vertical {
        border: none;
        background: #F7F8F6;
        width: 10px;
        margin: 0px 0px 0px 0px;
    }
    QScrollBar::handle:vertical {
        background: #D9DED8;
        min-height: 20px;
        border-radius: 5px;
    }
    QScrollBar::handle:vertical:hover {
        background: #8A928A;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    """
