DARK_STYLE = """
QWidget {
    background-color: #17181c;
    color: #e6e6ea;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
}

QLabel, QCheckBox { background: transparent; }

QWidget#card {
    background-color: #1d1f25;
    border: 1px solid #3a3d46;
    border-radius: 16px;
}

QLabel#title {
    font-size: 26px;
    font-weight: 700;
    color: #ffffff;
}

QPushButton {
    background-color: #2a2c33;
    border: 1px solid #3a3d46;
    border-radius: 8px;
    padding: 8px 16px;
}
QPushButton:hover    { background-color: #353842; border-color: #6c5ce7; }
QPushButton:pressed  { background-color: #6c5ce7; }
QPushButton:disabled { color: #777a85; background-color: #212329; }

QLineEdit, QComboBox {
    background-color: #20222a;
    border: 1px solid #3a3d46;
    border-radius: 8px;
    padding: 8px 10px;
    selection-background-color: #6c5ce7;
}
QLineEdit:focus, QComboBox:focus { border-color: #6c5ce7; }
QComboBox QAbstractItemView {
    background-color: #20222a;
    selection-background-color: #6c5ce7;
}

QListWidget {
    background-color: #1d1f25;
    border: 1px solid #3a3d46;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}
QListWidget::item { padding: 8px; border-radius: 6px; }
QListWidget::item:hover    { background-color: #2a2c33; }
QListWidget::item:selected { background-color: #6c5ce7; color: #ffffff; }

QTabWidget::pane {
    border: 1px solid #3a3d46;
    border-radius: 8px;
    top: -1px;
}
QTabBar::tab {
    background-color: #20222a;
    border: 1px solid #3a3d46;
    padding: 8px 18px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}
QTabBar::tab:selected { background-color: #6c5ce7; color: #ffffff; }
QTabBar::tab:hover:!selected { background-color: #2a2c33; }

QSlider::groove:horizontal {
    height: 6px;
    background: #3a3d46;
    border-radius: 3px;
}
QSlider::sub-page:horizontal { background: #6c5ce7; border-radius: 3px; }
QSlider::handle:horizontal {
    background: #ffffff;
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #3a3d46;
    border-radius: 4px;
    background: #20222a;
}
QCheckBox::indicator:checked { background: #6c5ce7; border-color: #6c5ce7; }

QMessageBox, QInputDialog { background-color: #17181c; }
"""