import pytest
from ninja.testing import TestClient

from api.router import api

client = TestClient(api)


@pytest.mark.django_db
class TestRegister:
    def test_register_reader(self):
        resp = client.post("/auth/register", json={
            "email": "new@example.com",
            "username": "newuser",
            "password": "secure123",
            "role": "reader",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access" in data
        assert "refresh" in data

    def test_register_author(self):
        resp = client.post("/auth/register", json={
            "email": "author@example.com",
            "username": "authoruser",
            "password": "secure123",
            "role": "author",
        })
        assert resp.status_code == 201

    def test_duplicate_email_rejected(self, reader):
        resp = client.post("/auth/register", json={
            "email": "reader@example.com",
            "username": "other",
            "password": "secure123",
        })
        assert resp.status_code == 400

    def test_invalid_role_rejected(self):
        resp = client.post("/auth/register", json={
            "email": "x@example.com",
            "username": "x",
            "password": "secure123",
            "role": "admin",
        })
        assert resp.status_code == 400


@pytest.mark.django_db
class TestLogin:
    def test_valid_credentials(self, reader):
        resp = client.post("/auth/login", json={
            "email": "reader@example.com",
            "password": "testpass123",
        })
        assert resp.status_code == 200
        assert "access" in resp.json()

    def test_wrong_password(self, reader):
        resp = client.post("/auth/login", json={
            "email": "reader@example.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_unknown_email(self):
        resp = client.post("/auth/login", json={
            "email": "nobody@example.com",
            "password": "whatever",
        })
        assert resp.status_code == 401


@pytest.mark.django_db
class TestMe:
    def test_get_own_profile(self, reader, reader_token):
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {reader_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "reader@example.com"
        assert data["role"] == "reader"

    def test_unauthenticated(self):
        resp = client.get("/auth/me")
        assert resp.status_code == 401


@pytest.mark.django_db
class TestRefresh:
    def test_refresh_issues_new_access_token(self, reader):
        from api.auth import create_refresh_token
        refresh = create_refresh_token(reader.pk)
        resp = client.post("/auth/refresh", json={"refresh": refresh})
        assert resp.status_code == 200
        assert "access" in resp.json()

    def test_access_token_rejected_as_refresh(self, reader_token):
        resp = client.post("/auth/refresh", json={"refresh": reader_token})
        assert resp.status_code == 401
