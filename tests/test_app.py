"""Unit test dasar untuk aplikasi Flask."""

import pytest

from app import app


@pytest.fixture(name="client")
def client_fixture():
    """Membuat test client Flask."""
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def get_token(client):
    """Mengambil token CSRF dari halaman login."""
    page = client.get("/login").get_data(as_text=True)
    marker = 'name="csrf_token" value="'
    start = page.index(marker) + len(marker)
    end = page.index('"', start)
    return page[start:end]


def test_index_ok(client):
    """Landing page dapat diakses."""
    assert client.get("/").status_code == 200


def test_health(client):
    """Endpoint health mengembalikan status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_dashboard_requires_login(client):
    """Dashboard tanpa login diarahkan ke /login."""
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_without_csrf_rejected(client):
    """POST tanpa token CSRF ditolak."""
    response = client.post("/login", data={"username": "admin", "password": "x"})
    assert response.status_code == 400


def test_login_wrong_password(client):
    """Password salah tidak membuat sesi login."""
    token = get_token(client)
    response = client.post(
        "/login",
        data={"username": "admin", "password": "salah", "csrf_token": token},
    )
    assert response.status_code == 200
    assert client.get("/dashboard").status_code == 302


def test_login_success_and_logout(client):
    """Login valid membuka dashboard; logout menutupnya."""
    token = get_token(client)
    response = client.post(
        "/login",
        data={"username": "admin", "password": "admin123", "csrf_token": token},
    )
    assert response.status_code == 302
    assert client.get("/dashboard").status_code == 200
    client.get("/logout")
    assert client.get("/dashboard").status_code == 302
