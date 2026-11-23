from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class HomeWindow(QWidget):
    video_requested = Signal()
    music_requested = Signal()
    games_requested = Signal()
    logout_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Raven")
        self.resize(420, 360)

        layout = QVBoxLayout(self)
        title = QLabel("Raven")
        title_font = title.font()
        title_font.setPointSize(16)
        title.setFont(title_font)
        layout.addWidget(title)

        self.account_label = QLabel("Signed in")
        layout.addWidget(self.account_label)
        layout.addWidget(QLabel("Multimedia"))

        video_button = QPushButton("Video")
        music_button = QPushButton("Music")
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
