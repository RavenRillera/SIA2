import re

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from SIA.database import UserDatabase
from SIA.google_controller import GoogleSignInController
from SIA.ui import make_title


class SignUpWindow(QWidget):
    login_requested = Signal()
    google_signed_in = Signal(str)

    def __init__(self):
        super().__init__()
        self.database = UserDatabase()
        self.setWindowTitle("Sign up")
        self.resize(460, 560)

        layout = QVBoxLayout(self)
        layout.addWidget(make_title("Create account"))

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
        for field in (self.username_input, self.email_input, self.password_input, self.confirm_password_input):
            layout.addWidget(field)

        self.show_password = QCheckBox("Show password")
        self.show_password.toggled.connect(self.toggle_password_visibility)
        layout.addWidget(self.show_password)

        create_button = QPushButton("Create account")
        create_button.setObjectName("primary")
        create_button.clicked.connect(self.register_account)
        layout.addWidget(create_button)


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
        return re.match(r"^[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}$", email) is not None

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
        self.google_status.clear()

    def closeEvent(self, event):
        self.google.stop()
        super().closeEvent(event)