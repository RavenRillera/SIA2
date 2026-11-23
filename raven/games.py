from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class GamesWindow(QWidget):
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Raven — Games")
        self.resize(520, 320)
        layout = QVBoxLayout(self)
        title = QLabel("Games")
        title_font = title.font()
        title_font.setPointSize(16)
        title.setFont(title_font)
        layout.addWidget(title)
        layout.addWidget(QLabel("The game screen will go here."))
        layout.addWidget(QLabel("This screen is not connected yet."))
        back = QPushButton("Back")
        back.clicked.connect(self.back_requested.emit)
        layout.addWidget(back)
        layout.addStretch(1)
