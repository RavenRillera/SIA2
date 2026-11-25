import sys

from PySide6.QtWidgets import QApplication, QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget

from SIA.games import GamesWindow
from SIA.home import HomeWindow
from SIA.login import LoginWindow
from SIA.music import MusicWindow
from SIA.signup import SignUpWindow
from SIA.theme import DARK_STYLE
from SIA.video import VideoWindow

WINDOW_SIZE = (900, 780)   # iisang laki ng window para sa lahat ng screen (fixed)
FORM_WIDTH = 460           # lapad ng login / sign up / home card sa gitna


def centered(page, width=FORM_WIDTH):
    """Inilalagay sa gitna ang maliliit na screen para hindi mukhang bakante ang window."""
    page.setFixedWidth(width)
    page.setObjectName("card")  # may styling sa theme.py
    page.layout().setContentsMargins(28, 28, 28, 28)
    page.layout().setSpacing(10)
    holder = QWidget()
    row = QHBoxLayout(holder)
    row.setContentsMargins(0, 0, 0, 0)
    column = QVBoxLayout()
    column.addStretch(1)
    column.addWidget(page)
    column.addStretch(1)
    row.addStretch(1)
    row.addLayout(column)
    row.addStretch(1)
    return holder


class MainWindow(QWidget):
    """Iisang window lang. Ang bawat screen ay page sa loob ng QStackedWidget."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(*WINDOW_SIZE)  # hindi na ma-maximize o ma-resize
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        self.holders = {}
        self.current = None

    def add_page(self, page, center=False):
        holder = centered(page) if center else page
        self.holders[page] = holder
        self.stack.addWidget(holder)

    def show_page(self, page):
        # humihinto ang music/video/snake kapag umalis ka sa screen nila
        if self.current is not None and self.current is not page and hasattr(self.current, "on_leave"):
            self.current.on_leave()
        self.current = page
        self.stack.setCurrentWidget(self.holders[page])
        self.setWindowTitle(page.windowTitle())

    def closeEvent(self, event):
        for page in self.holders:
            page.close()  # para ma-trigger ang closeEvent ng bawat page (stop playback, Google worker)
        super().closeEvent(event)


class Application:
    def __init__(self):
        self.login_window = LoginWindow()
        self.signup_window = SignUpWindow()
        self.home_window = HomeWindow()
        self.video_window = VideoWindow()
        self.music_window = MusicWindow()
        self.games_window = GamesWindow()

        self.window = MainWindow()
        for page in (self.login_window, self.signup_window, self.home_window):
            self.window.add_page(page, center=True)
        for page in (self.video_window, self.music_window, self.games_window):
            self.window.add_page(page)

        show = self.show_window
        self.login_window.signup_requested.connect(lambda: show(self.signup_window))
        self.login_window.login_successful.connect(self.open_home)
        self.signup_window.login_requested.connect(lambda: show(self.login_window))
        self.signup_window.google_signed_in.connect(self.open_home)
        self.home_window.video_requested.connect(lambda: show(self.video_window))
        self.home_window.music_requested.connect(lambda: show(self.music_window))
        self.home_window.games_requested.connect(lambda: show(self.games_window))
        self.home_window.logout_requested.connect(self.sign_out)
        for page in (self.video_window, self.music_window, self.games_window):
            page.back_requested.connect(lambda: show(self.home_window))

    def show_window(self, target):
        self.window.show_page(target)

    def open_home(self, name):
        self.home_window.set_user(name)
        self.show_window(self.home_window)

    def sign_out(self):
        self.login_window.clear_fields()
        self.show_window(self.login_window)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLE)
    application = Application()
    application.show_window(application.login_window)
    application.window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()