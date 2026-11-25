from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from SIA.ui import make_title


class HomeWindow(QWidget):
    video_requested = Signal()
    music_requested = Signal()
    games_requested = Signal()
    logout_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard")
        self.resize(420, 360)

        layout = QVBoxLayout(self)
        layout.addWidget(make_title("Dashboard"))

        self.account_label = QLabel("Signed in")
        layout.addWidget(self.account_label)
        video_button = QPushButton("Movies and TV Shows")
        music_button = QPushButton("Music and Audio")
        games_button = QPushButton("Games")
        video_button.clicked.connect(self.video_requested.emit)
        music_button.clicked.connect(self.music_requested.emit)
        games_button.clicked.connect(self.games_requested.emit)
        layout.addWidget(video_button)
        layout.addWidget(music_button)
        layout.addWidget(games_button)

        sign_out = QPushButton("Sign out")
        sign_out.clicked.connect(self.logout_requested.emit)
        layout.addWidget(sign_out)
        layout.addStretch(1)

    def set_user(self, name):
        self.account_label.setText(f"Signed in as {name}")