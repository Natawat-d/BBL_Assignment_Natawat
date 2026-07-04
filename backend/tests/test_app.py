"""End-to-end tests for auth and booking authorization.

Requires a running Postgres pointed at by ``DATABASE_URL`` (see conftest.py).
Run from the ``backend`` directory with: ``pytest``
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def login(username: str, password: str) -> str:
    """Log in and return the access token."""
    resp = client.post("/api/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- Authentication -------------------------------------------------------

def test_login_success_returns_token_and_user():
    resp = client.post("/api/login", json={"username": "alice", "password": "alice123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"] == {"username": "alice", "is_admin": False}


def test_login_admin_flag():
    resp = client.post("/api/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    assert resp.json()["user"]["is_admin"] is True


def test_login_wrong_password_rejected():
    resp = client.post("/api/login", json={"username": "alice", "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_user_rejected():
    resp = client.post("/api/login", json={"username": "ghost", "password": "x"})
    assert resp.status_code == 401


# --- Authentication required ---------------------------------------------

def test_bookings_requires_authentication():
    resp = client.get("/api/bookings")
    assert resp.status_code == 401


def test_invalid_token_rejected():
    resp = client.get("/api/bookings", headers=auth_header("not-a-real-token"))
    assert resp.status_code == 401


# --- Booking ownership (regular users) -----------------------------------

def test_user_sees_only_own_bookings():
    alice = login("alice", "alice123")
    bob = login("bob", "bob123")

    client.post("/api/bookings", json={"time_slot": "10am-11am"}, headers=auth_header(alice))
    client.post("/api/bookings", json={"time_slot": "1pm-2pm"}, headers=auth_header(bob))

    resp = client.get("/api/bookings", headers=auth_header(alice))
    assert resp.status_code == 200
    slots = resp.json()
    assert len(slots) == 1
    assert slots[0]["username"] == "alice"
    assert slots[0]["time_slot"] == "10am-11am"


def test_user_cannot_read_another_users_booking():
    alice = login("alice", "alice123")
    bob = login("bob", "bob123")

    created = client.post(
        "/api/bookings", json={"time_slot": "3pm-4pm"}, headers=auth_header(bob)
    ).json()

    resp = client.get(f"/api/bookings/{created['id']}", headers=auth_header(alice))
    assert resp.status_code == 404


def test_user_cannot_update_or_delete_another_users_booking():
    alice = login("alice", "alice123")
    bob = login("bob", "bob123")

    created = client.post(
        "/api/bookings", json={"time_slot": "3pm-4pm"}, headers=auth_header(bob)
    ).json()

    upd = client.put(
        f"/api/bookings/{created['id']}",
        json={"time_slot": "hacked"},
        headers=auth_header(alice),
    )
    assert upd.status_code == 404

    dele = client.delete(f"/api/bookings/{created['id']}", headers=auth_header(alice))
    assert dele.status_code == 404


def test_owner_can_update_and_delete_own_booking():
    alice = login("alice", "alice123")
    created = client.post(
        "/api/bookings", json={"time_slot": "10am-11am"}, headers=auth_header(alice)
    ).json()

    upd = client.put(
        f"/api/bookings/{created['id']}",
        json={"time_slot": "11am-12pm"},
        headers=auth_header(alice),
    )
    assert upd.status_code == 200
    assert upd.json()["time_slot"] == "11am-12pm"

    dele = client.delete(f"/api/bookings/{created['id']}", headers=auth_header(alice))
    assert dele.status_code == 204

    remaining = client.get("/api/bookings", headers=auth_header(alice)).json()
    assert remaining == []


# --- Admin privileges -----------------------------------------------------

def test_admin_sees_all_bookings():
    alice = login("alice", "alice123")
    bob = login("bob", "bob123")
    admin = login("admin", "admin123")

    client.post("/api/bookings", json={"time_slot": "10am-11am"}, headers=auth_header(alice))
    client.post("/api/bookings", json={"time_slot": "1pm-2pm"}, headers=auth_header(bob))

    resp = client.get("/api/bookings", headers=auth_header(admin))
    assert resp.status_code == 200
    owners = {b["username"] for b in resp.json()}
    assert owners == {"alice", "bob"}


def test_admin_can_manage_any_booking():
    alice = login("alice", "alice123")
    admin = login("admin", "admin123")

    created = client.post(
        "/api/bookings", json={"time_slot": "10am-11am"}, headers=auth_header(alice)
    ).json()

    assert client.get(
        f"/api/bookings/{created['id']}", headers=auth_header(admin)
    ).status_code == 200

    upd = client.put(
        f"/api/bookings/{created['id']}",
        json={"time_slot": "2pm-3pm"},
        headers=auth_header(admin),
    )
    assert upd.status_code == 200
    assert upd.json()["time_slot"] == "2pm-3pm"

    dele = client.delete(f"/api/bookings/{created['id']}", headers=auth_header(admin))
    assert dele.status_code == 204
