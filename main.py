import sys

from PySide6.QtWidgets import QApplication

from raven.games import GamesWindow
from raven.home import HomeWindow
from raven.login import LoginWindow
from raven.music import MusicWindow
from raven.signup import SignUpWindow
from raven.video import VideoWindow


class Application:
    def __init__(self):
        self.login_window = LoginWindow()
        self.signup_window = SignUpWindow()
        self.home_window = HomeWindow()
        self.video_window = VideoWindow()
        self.music_window = MusicWindow()
        self.games_window = GamesWindow()
        self.windows = (
            self.login_window,
            self.signup_window,
            self.home_window,
            self.video_window,
            self.music_window,
            self.games_window,
        )

        self.login_window.signup_requested.connect(lambda: self.show_window(self.signup_window))
        self.login_window.login_successful.connect(self.open_home)
        self.signup_window.login_requested.connect(lambda: self.show_window(self.login_window))
        self.signup_window.google_signed_in.connect(self.open_home)
        self.home_window.video_requested.connect(lambda: self.show_window(self.video_window))
        self.home_window.music_requested.connect(lambda: self.show_window(self.music_window))
        self.home_window.games_requested.connect(lambda: self.show_window(self.games_window))
        self.home_window.logout_requested.connect(self.sign_out)
        self.video_window.back_requested.connect(lambda: self.show_window(self.home_window))
        self.music_window.back_requested.connect(lambda: self.show_window(self.home_window))
        self.games_window.back_requested.connect(lambda: self.show_window(self.home_window))

    def show_window(self, window):
        for current_window in self.windows:
            current_window.hide()
        window.show()

    def open_home(self, name):
        self.home_window.set_user(name)
        self.show_window(self.home_window)

    def sign_out(self):
        self.music_window._stop()
        self.login_window.clear_fields()
        self.show_window(self.login_window)


def main():
    app = QApplication(sys.argv)
    application = Application()
    application.show_window(application.login_window)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
