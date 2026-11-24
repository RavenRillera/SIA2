import re

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


class SignUpWindow(QWidget):
    login_requested = Signal()
    google_signed_in = Signal(str)

    def __init__(self):
        super().__init__()
        self.database = UserDatabase()
        self.login_worker = None
        self.verification_url = ""
        self.setWindowTitle("Media & Entertainment")
        self.resize(460, 560)

        layout = QVBoxLayout(self)
        title = QLabel("Create account")
        title_font = title.font()
        title_font.setPointSize(16)
        title.setFont(title_font)
        layout.addWidget(title)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email address")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm password")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.username_input)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.confirm_password_input)

        self.show_password = QCheckBox("Show password")
        self.show_password.toggled.connect(self.toggle_password_visibility)
        layout.addWidget(self.show_password)

        create_button = QPushButton("Create account")
        create_button.clicked.connect(self.register_account)
        layout.addWidget(create_button)

        layout.addWidget(QLabel("or sign up with"))
        self.google_button = QPushButton("Google")
        self.google_button.clicked.connect(self.start_google_sign_in)
        layout.addWidget(self.google_button)
        self.google_status = QLabel("")
        self.google_status.setWordWrap(True)
        layout.addWidget(self.google_status)

        row = QHBoxLayout()
        row.addWidget(QLabel("Already have an account?"))
        login_button = QPushButton("Log in")
        login_button.clicked.connect(self.login_requested.emit)
        row.addWidget(login_button)
        layout.addLayout(row)
        layout.addStretch(1)

    def toggle_password_visibility(self, checked):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.password_input.setEchoMode(mode)
        self.confirm_password_input.setEchoMode(mode)

    def validate_email(self, email):
        pattern = r"^[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def validate_inputs(self):
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not username or not email or not password or not confirm_password:
            QMessageBox.warning(self, "Missing information", "Please complete all fields.")
            return False
        if len(username) < 3:
            QMessageBox.warning(self, "Invalid username", "Username must contain at least 3 characters.")
            return False
        if not self.validate_email(email):
            QMessageBox.warning(self, "Invalid email", "Please enter a valid email address.")
            return False
        if len(password) < 8:
            QMessageBox.warning(self, "Weak password", "Password must contain at least 8 characters.")
            return False
        if password != confirm_password:
            QMessageBox.warning(self, "Password mismatch", "Passwords do not match.")
            return False
        return True

    def register_account(self):
        if not self.validate_inputs():
            return
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        try:
            success, message = self.database.register_user(username, email, password)
        except Exception as error:
            QMessageBox.critical(self, "Database error", str(error))
            return
        if success:
            QMessageBox.information(self, "Registration successful", message)
            self.clear_fields()
            self.login_requested.emit()
            return
        QMessageBox.warning(self, "Registration failed", message)

    def clear_fields(self):
        self.username_input.clear()
        self.email_input.clear()
        self.password_input.clear()
        self.confirm_password_input.clear()
        self.show_password.setChecked(False)

    def start_google_sign_in(self):
        if self.login_worker and self.login_worker.isRunning():
            return
        client_id, client_secret = load_google_config()
        if not client_id or not client_secret:
            self.google_status.setText("Google sign-up needs a client id and client secret in oauth_config.json.")
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
        self.google_signed_in.emit(email)

    def google_failed(self, message):
        self.google_status.setText(f"Google sign-up failed: {message}")

    def closeEvent(self, event):
        if self.login_worker and self.login_worker.isRunning():
            self.login_worker.stop()
            self.login_worker.wait(2000)
        super().closeEvent(event)
