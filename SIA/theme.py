"""Dark navy + teal theme (inspired by the Nexify design)."""

DARK_STYLE = """
QWidget {
    background-color: #04121c;
    color: #e8f1f5;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 14px;
}

QLabel, QCheckBox { background: transparent; }

QWidget#card {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0d3a40, stop:0.45 #0a2230, stop:1 #07192a);
    border: 1px solid #16394a;
    border-radius: 18px;
}

QLabel#title {
    font-size: 26px;
    font-weight: 700;
    color: #ffffff;
}

/* ---------- Buttons ---------- */
QPushButton {
    background-color: #0f2b3a;
    border: 1px solid #16394a;
    border-radius: 12px;
    padding: 10px 18px;
}
QPushButton:hover    { background-color: #143a4d; border-color: #2af5c8; }
QPushButton:pressed  { background-color: #1a4a5f; }
QPushButton:disabled { color: #5f7b88; background-color: #0a1f2b; border-color: #11303f; }

QPushButton#primary {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2af5c8, stop:1 #1fd6e6);
    color: #04121c;
    border: none;
    font-weight: 700;
}
QPushButton#primary:hover   { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5ffbdc, stop:1 #4fe3f0); }
QPushButton#primary:pressed { background-color: #1fc4b0; }
QPushButton#primary:disabled { background-color: #17424b; color: #6f9aa0; }

/* ---------- Inputs ---------- */
QLineEdit, QComboBox {
    background-color: #0a2230;
    border: 1px solid #16394a;
    border-radius: 12px;
    padding: 10px 12px;
    selection-background-color: #1fd6e6;
    selection-color: #04121c;
}
QLineEdit:focus, QComboBox:focus { border-color: #2af5c8; }
QComboBox QAbstractItemView {
    background-color: #0a2230;
    selection-background-color: #1fd6e6;
    selection-color: #04121c;
    border: 1px solid #16394a;
}

/* ---------- Lists ---------- */
QListWidget {
    background-color: #081c29;
    border: 1px solid #16394a;
    border-radius: 12px;
    padding: 4px;
    outline: none;
}
QListWidget::item { padding: 9px; border-radius: 8px; }
QListWidget::item:hover    { background-color: #0f2b3a; }
QListWidget::item:selected { background-color: #1fd6e6; color: #04121c; }

/* ---------- Tabs ---------- */
QTabWidget::pane {
    border: 1px solid #16394a;
    border-radius: 12px;
    top: -1px;
}
QTabBar::tab {
    background-color: #0a2230;
    border: 1px solid #16394a;
    padding: 9px 20px;
    margin-right: 4px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
}
QTabBar::tab:selected { background-color: #1fd6e6; color: #04121c; font-weight: 700; border-color: #1fd6e6; }
QTabBar::tab:hover:!selected { background-color: #0f2b3a; }

/* ---------- Sliders ---------- */
QSlider::groove:horizontal {
    height: 6px;
    background: #16394a;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2af5c8, stop:1 #1fd6e6);
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #ffffff;
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}

/* ---------- Checkbox ---------- */
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #16394a;
    border-radius: 4px;
    background: #0a2230;
}
QCheckBox::indicator:checked { background: #2af5c8; border-color: #2af5c8; }

QMessageBox, QInputDialog { background-color: #04121c; }
"""