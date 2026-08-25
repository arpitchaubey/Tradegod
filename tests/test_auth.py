import pytest
import time
from httpx import AsyncClient, ASGITransport

from app.main import app

@pytest.mark.asyncio
async def test_auth_full_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ts = int(time.time() * 1000)
        test_email = f"tester_{ts}@tradegod.ai"
        initial_password = "initial_password_123"
        new_password = "new_secure_password_456"

        # 1. Register a new test user
        reg_resp = await client.post("/api/auth/register", json={
            "email": test_email,
            "password": initial_password,
            "full_name": "Quant Tester"
        })
        assert reg_resp.status_code == 200
        reg_data = reg_resp.json()
        assert "token" in reg_data
        assert reg_data["user"]["email"] == test_email

        # 2. Login with valid credentials
        login_resp = await client.post("/api/auth/login", json={
            "email": test_email,
            "password": initial_password
        })
        assert login_resp.status_code == 200
        login_data = login_resp.json()
        assert "token" in login_data
        assert login_data["user"]["email"] == test_email
        token = login_data["token"]

        # 3. Test /me endpoint with Bearer token
        me_resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        assert me_resp.json()["user"]["email"] == test_email

        # 4. Request password reset (Forgot Password)
        forgot_resp = await client.post("/api/auth/forgot-password", json={
            "email": test_email
        })
        assert forgot_resp.status_code == 200
        forgot_data = forgot_resp.json()
        assert forgot_data["status"] == "success"
        assert "reset_code" in forgot_data
        reset_code = forgot_data["reset_code"]
        assert len(reset_code) == 6

        # 4b. Forgot password for unknown user
        unknown_resp = await client.post("/api/auth/forgot-password", json={
            "email": f"unknown_user_{ts}@tradegod.ai"
        })
        assert unknown_resp.status_code == 404

        # 5. Reset password with wrong code
        bad_reset_resp = await client.post("/api/auth/reset-password", json={
            "email": test_email,
            "reset_code": "000000",
            "new_password": new_password
        })
        assert bad_reset_resp.status_code == 400

        # 6. Reset password with valid code
        good_reset_resp = await client.post("/api/auth/reset-password", json={
            "email": test_email,
            "reset_code": reset_code,
            "new_password": new_password
        })
        assert good_reset_resp.status_code == 200
        reset_result = good_reset_resp.json()
        assert reset_result["status"] == "success"
        assert "token" in reset_result
        assert reset_result["user"]["email"] == test_email

        # 7. Old password no longer works
        old_login_resp = await client.post("/api/auth/login", json={
            "email": test_email,
            "password": initial_password
        })
        assert old_login_resp.status_code == 400

        # 8. Login with new password
        new_login_resp = await client.post("/api/auth/login", json={
            "email": test_email,
            "password": new_password
        })
        assert new_login_resp.status_code == 200
        new_token = new_login_resp.json()["token"]

        # 9. Test change password for authenticated user
        change_resp = await client.put("/api/auth/change-password", 
            headers={"Authorization": f"Bearer {new_token}"},
            json={
                "old_password": new_password,
                "new_password": "final_password_789"
            }
        )
        assert change_resp.status_code == 200
