from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from SIA.database import UserDatabase
from SIA.google_controller import GoogleSignInController
from SIA.ui import make_title


class LoginWindow(QWidget):
    signup_requested = Signal()
    login_successful = Signal(str)

    def __init__(self):
        super().__init__()
        self.database = UserDatabase()
        self.setWindowTitle("Log in")
        self.resize(420, 360)

        layout = QVBoxLayout(self)
        layout.addWidget(make_title("Media & Entertainment"))
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
        layout.addWidget(self.google_button)
        self.google_status = QLabel("")
        self.google_status.setWordWrap(True)
        layout.addWidget(self.google_status)
        self.google = GoogleSignInController(self.google_button, self.google_status, self.database, parent=self)
        self.google.signed_in.connect(self.login_successful.emit)

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

    def closeEvent(self, event):
        self.google.stop()
        super().closeEvent(event)