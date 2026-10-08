"""Aplikasi Flask PBL RKS 516: landing page, login, dan dashboard."""

import hmac
import os
import secrets
from functools import wraps

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

app = Flask(__name__)

# Secret key dibaca dari environment; fallback acak per proses (bukan hardcode).
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# Kredensial demo dibaca dari environment (default hanya untuk praktikum).
VALID_USER = os.environ.get("APP_USERNAME", "admin")
VALID_PASS = os.environ.get("APP_PASSWORD", "admin123")


def get_csrf_token():
    """Mengembalikan token CSRF sesi; dibuat baru jika belum ada."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return session["csrf_token"]


app.jinja_env.globals["csrf_token"] = get_csrf_token


def login_required(view):
    """Dekorator yang mewajibkan pengguna sudah login."""

    @wraps(view)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
            flash("Silakan login terlebih dahulu", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return decorated_function


def credentials_valid(username, password):
    """Membandingkan kredensial dengan waktu konstan."""
    user_ok = hmac.compare_digest(username.encode(), VALID_USER.encode())
    pass_ok = hmac.compare_digest(password.encode(), VALID_PASS.encode())
    return user_ok and pass_ok


@app.route("/")
def index():
    """Menampilkan landing page."""
    return render_template("index.html")


@app.route("/health")
def health():
    """Endpoint health check untuk smoke test dan monitoring."""
    return {"status": "ok"}, 200


@app.route("/login", methods=["GET", "POST"])
def login():
    """Menampilkan form login dan memproses autentikasi."""
    if "logged_in" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        token = request.form.get("csrf_token", "")
        expected = session.get("csrf_token", "")
        if not expected or not hmac.compare_digest(token, expected):
            flash("Token CSRF tidak valid", "error")
            return render_template("login.html"), 400

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username dan password wajib diisi", "error")
        elif credentials_valid(username, password):
            session.clear()
            session["logged_in"] = True
            session["username"] = username
            flash("Login berhasil!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Username atau password salah", "error")

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    """Menampilkan dashboard untuk pengguna yang sudah login."""
    return render_template("dashboard.html", username=session.get("username"))


@app.route("/logout")
def logout():
    """Menghapus sesi dan kembali ke halaman login."""
    session.clear()
    flash("Anda telah logout", "info")
    return redirect(url_for("login"))


@app.route("/about")
def about():
    """Halaman informasi aplikasi untuk pengujian CI/CD."""
    return {
        "app_name": "Aplikasi PBL RKS 516",
        "status": "Active",
        "message": "Route /about berhasil di-deploy melalui CI/CD pipeline!"
    }, 200


@app.route("/info")
def info():
    """Route tambahan untuk cek versi atau info sistem."""
    return {
        "version": "1.1.0",
        "environment": "Testing CI/CD"
    }, 200


if __name__ == "__main__":
    # Debug mati; host dikontrol lewat env (Dockerfile mengatur 0.0.0.0)..
    app.run(
        host=os.environ.get("FLASK_HOST", "127.0.0.1"),
        port=int(os.environ.get("FLASK_PORT", "5000")),
    )