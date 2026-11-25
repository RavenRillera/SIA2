from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtGui import QDesktopServices

from SIA.google_oauth import LoginWorker, load_google_config


class GoogleSignInController(QObject):
    """Ikinakabit sa isang button at status label. Ginagamit ng login at signup."""

    signed_in = Signal(str)  # email

    def __init__(self, button, status_label, database, parent=None):
        super().__init__(parent)
        self.button = button
        self.status_label = status_label
        self.database = database
        self.worker = None
        button.clicked.connect(self.start)

    def start(self):
        if self.worker and self.worker.isRunning():
            return
        client_id, client_secret = load_google_config()
        if not client_id or not client_secret:
            self.status_label.setText("Google sign-in needs a client id and client secret in oauth_config.json.")
            return
        self.button.setEnabled(False)
        self.status_label.setText("Calling Google for sign-in.")
        self.worker = LoginWorker(client_id, client_secret)
        self.worker.message.connect(self.status_label.setText)
        self.worker.browser_ready.connect(lambda url: QDesktopServices.openUrl(QUrl(url)))
        self.worker.succeeded.connect(self._succeeded)
        self.worker.failed.connect(lambda msg: self.status_label.setText(f"Google sign-in failed: {msg}"))
        self.worker.finished.connect(lambda: self.button.setEnabled(True))
        self.worker.start()

    def _succeeded(self, _token, email):
        self.database.get_or_create_google_user(email)  # ise-save sa users.db
        self.status_label.setText(f"Signed in as {email}.")
        self.signed_in.emit(email)

    def stop(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(2000)