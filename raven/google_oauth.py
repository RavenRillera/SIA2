import base64
import hashlib
import json
import secrets
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests
from PySide6.QtCore import QThread, Signal

CONFIG_PATH = Path(__file__).resolve().parent.parent / "oauth_config.json"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
SCOPES = "openid email profile"


def load_google_config():
    if not CONFIG_PATH.exists():
        return "", ""
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    client_id = str(data.get("client_id") or "").strip()
    client_secret = str(data.get("client_secret") or "").strip()
    return client_id, client_secret


def sign_in(client_id, client_secret, should_stop, open_browser):
    """OAuth 2.0 authorization-code flow. Google's page is the only browser step."""
    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(16)
    server = _LoopbackServer()
    try:
        redirect_uri = f"http://127.0.0.1:{server.server_address[1]}"
        open_browser(_authorization_url(client_id, redirect_uri, challenge, state))
        code = _wait_for_code(server, state, should_stop)
        if code is None:
            return None
        return _exchange_code(client_id, client_secret, code, verifier, redirect_uri)
    finally:
        server.server_close()


class LoginWorker(QThread):
    message = Signal(str)
    browser_ready = Signal(str)
    succeeded = Signal(str, str)
    failed = Signal(str)

    def __init__(self, client_id, client_secret):
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            self.message.emit("Calling Google for sign-in.")
            token = sign_in(
                self.client_id,
                self.client_secret,
                lambda: self._stop,
                lambda url: self.browser_ready.emit(url),
            )
            if token is None:
                return
            self.message.emit("Google returned a token. Asking who signed in.")
            self.succeeded.emit(token, fetch_account_name(token))
        except Exception as error:
            self.failed.emit(str(error))


def fetch_account_name(token):
    response = requests.get(
        USERINFO_URL,
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    response.raise_for_status()
    profile = response.json()
    return profile.get("email") or profile.get("name") or "Google user"


def _pkce_pair():
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def _authorization_url(client_id, redirect_uri, challenge, state):
    query = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": SCOPES,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
            "prompt": "select_account",
        }
    )
    return f"{AUTH_URL}?{query}"


def _wait_for_code(server, state, should_stop):
    deadline = time.time() + 180
    while not should_stop() and time.time() < deadline:
        server.handle_request()
        if server.auth_error:
            if server.auth_error == "access_denied":
                raise RuntimeError("Google sign-in was cancelled.")
            raise RuntimeError(server.auth_error)
        if not server.auth_code:
            continue
        if server.auth_state != state:
            raise RuntimeError("Google returned a sign-in response Raven did not start.")
        return server.auth_code
    if should_stop():
        return None
    raise RuntimeError("Google sign-in timed out.")


def _exchange_code(client_id, client_secret, code, verifier, redirect_uri):
    response = requests.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "code_verifier": verifier,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        },
        timeout=20,
    )
    payload = response.json()
    if response.status_code != 200 or not payload.get("access_token"):
        detail = payload.get("error_description") or payload.get("error") or response.text
        raise RuntimeError(detail)
    return payload["access_token"]


class _LoopbackServer(HTTPServer):
    allow_reuse_address = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), _CallbackHandler)
        self.timeout = 0.5
        self.auth_code = None
        self.auth_error = None
        self.auth_state = None


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/favicon.ico":
            self.send_response(404)
            self.end_headers()
            return

        query = urllib.parse.parse_qs(parsed.query)
        self.server.auth_code = (query.get("code") or [None])[0]
        self.server.auth_error = (query.get("error") or [None])[0]
        self.server.auth_state = (query.get("state") or [None])[0]
        body = b"<html><body><p>Signed in. You can close this tab and return to Raven.</p></body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return
