from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from raven.database import UserDatabase
from raven.google_oauth import LoginWorker, load_google_config


class LoginWindow(QWidget):
    signup_requested = Signal()
    login_successful = Signal(str)

    def __init__(self):
        super().__init__()
        self.database = UserDatabase()
        self.login_worker = None
        self.verification_url = ""
        self.setWindowTitle("Raven")
        self.resize(420, 360)

        layout = QVBoxLayout(self)
        title = QLabel("Raven")
        title_font = title.font()
        title_font.setPointSize(16)
        title.setFont(title_font)
        layout.addWidget(title)
        layout.addWidget(QLabel("Log in to open the multimedia menu."))

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.log_in)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)

        self.show_password = QCheckBox("Show password")
        self.show_password.toggled.connect(self.toggle_password_visibility)
        layout.addWidget(self.show_password)

        login_button = QPushButton("Log in")
        login_button.clicked.connect(self.log_in)
        layout.addWidget(login_button)

        layout.addWidget(QLabel("or sign in with"))
        self.google_button = QPushButton("Google")
        self.google_button.clicked.connect(self.start_google_sign_in)
        layout.addWidget(self.google_button)
        self.google_status = QLabel("")
        self.google_status.setWordWrap(True)
        layout.addWidget(self.google_status)

        row = QHBoxLayout()
        row.addWidget(QLabel("Need an account?"))
        signup_button = QPushButton("Sign up")
        signup_button.clicked.connect(self.signup_requested.emit)
        row.addWidget(signup_button)
        layout.addLayout(row)
        layout.addStretch(1)

    def toggle_password_visibility(self, checked):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.password_input.setEchoMode(mode)

    def log_in(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not username or not password:
            QMessageBox.warning(self, "Missing information", "Enter your username and password.")
            return
        success, message = self.database.authenticate(username, password)
        if not success:
            QMessageBox.warning(self, "Log in failed", message)
            return
        self.password_input.clear()
        self.login_successful.emit(username)

    def clear_fields(self):
        self.username_input.clear()
        self.password_input.clear()
        self.show_password.setChecked(False)
        self.google_status.clear()

    def start_google_sign_in(self):
        if self.login_worker and self.login_worker.isRunning():
            return
        client_id, client_secret = load_google_config()
        if not client_id or not client_secret:
            self.google_status.setText("Google sign-in needs a client id and client secret in oauth_config.json.")
            return
        self.google_button.setEnabled(False)
        self.google_status.setText("Calling Google for sign-in.")
        self.login_worker = LoginWorker(client_id, client_secret)
        self.login_worker.message.connect(self.google_status.setText)
        self.login_worker.browser_ready.connect(self.open_google)
        self.login_worker.succeeded.connect(self.google_finished)
        self.login_worker.failed.connect(self.google_failed)
        self.login_worker.finished.connect(lambda: self.google_button.setEnabled(True))
        self.login_worker.start()

    def open_google(self, url):
        self.verification_url = url
        QDesktopServices.openUrl(QUrl(url))

    def google_finished(self, _token, email):
        self.google_status.setText(f"Signed in as {email}.")
        self.login_successful.emit(email)

    def google_failed(self, message):
        self.google_status.setText(f"Google sign-in failed: {message}")

    def closeEvent(self, event):
        if self.login_worker and self.login_worker.isRunning():
            self.login_worker.stop()
            self.login_worker.wait(2000)
        super().closeEvent(event)
