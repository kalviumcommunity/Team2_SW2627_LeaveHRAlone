import pytest
from httpx import AsyncClient

from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_user_registration_and_login_flow(client: AsyncClient):
    # 1. Register a new user
    register_payload = {
        "name": "Arjun Sharma",
        "email": "arjun.sharma@example.com",
        "password": "StrongPassword123!",
        "role": "EMPLOYEE",
        "region": "India",
        "country": "India",
        "department": "Engineering",
        "employment_type": "Full-Time",
    }
    reg_res = await client.post("/api/auth/register", json=register_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert "refresh_token" in reg_data
    assert reg_data["user"]["email"] == "arjun.sharma@example.com"
    assert reg_data["user"]["region"] == "India"
    assert reg_data["user"]["role"] == "EMPLOYEE"

    # 2. Register with duplicate email should fail (400)
    dup_res = await client.post("/api/auth/register", json=register_payload)
    assert dup_res.status_code == 400

    # 3. Login with correct credentials
    login_res = await client.post(
        "/api/auth/login",
        json={"email": "arjun.sharma@example.com", "password": "StrongPassword123!"},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]

    # 4. Login with incorrect password should fail (401)
    wrong_login = await client.post(
        "/api/auth/login",
        json={"email": "arjun.sharma@example.com", "password": "WrongPassword!"},
    )
    assert wrong_login.status_code == 401

    # 5. Access /api/auth/me with valid Bearer token
    me_res = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "arjun.sharma@example.com"
    assert me_data["name"] == "Arjun Sharma"

    # 6. Access /api/auth/me without token should fail (401)
    no_token_res = await client.get("/api/auth/me")
    assert no_token_res.status_code == 401

    # 7. Refresh token flow
    refresh_res = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    refresh_data = refresh_res.json()
    assert "access_token" in refresh_data
    assert "refresh_token" in refresh_data

    # 8. Logout
    logout_res = await client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_res.status_code == 200


@pytest.mark.asyncio
async def test_google_auth_flow(client: AsyncClient):
    payload = {
        "id_token": "priya.nair@example.com",
        "region": "India",
        "country": "India",
    }
    res = await client.post("/api/auth/google", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "priya.nair@example.com"
    assert data["user"]["name"] == "Priya Nair"
    assert data["user"]["region"] == "India"


@pytest.mark.asyncio
async def test_rbac_access_control(client: AsyncClient):
    # Register an EMPLOYEE
    emp_res = await client.post(
        "/api/auth/register",
        json={
            "name": "Normal Employee",
            "email": "employee@example.com",
            "password": "Password123!",
            "role": "EMPLOYEE",
            "region": "India",
            "country": "India",
        },
    )
    emp_token = emp_res.json()["access_token"]

    # Register an HR_ADMIN
    admin_res = await client.post(
        "/api/auth/register",
        json={
            "name": "HR Manager",
            "email": "admin@example.com",
            "password": "Password123!",
            "role": "HR_ADMIN",
            "region": "India",
            "country": "India",
        },
    )
    admin_token = admin_res.json()["access_token"]

    # Both can access /api/auth/me
    emp_me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {emp_token}"})
    assert emp_me.status_code == 200
    assert emp_me.json()["role"] == "EMPLOYEE"

    admin_me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_me.status_code == 200
    assert admin_me.json()["role"] == "HR_ADMIN"

