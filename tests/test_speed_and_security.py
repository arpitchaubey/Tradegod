import pytest
import time
from httpx import AsyncClient, ASGITransport
import pandas as pd

from app.main import app
from app.api.routes_auth import _RESET_CODES
from app.bot.worker import omni_bot_worker
from app.data.historical import candle_buffer
from app.telegram.bot import telegram_bot
from app.signals.generator import signal_generator

@pytest.mark.asyncio
async def test_forgot_password_security_and_brute_force_protection():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ts = int(time.time() * 1000)
        test_email = f"sec_user_{ts}@tradegod.ai"
        
        # 1. Register test user
        reg_resp = await client.post("/api/auth/register", json={
            "email": test_email,
            "password": "SecurePassword123!",
            "full_name": "Security Test User"
        })
        assert reg_resp.status_code == 200

        # 2. Forgot password request
        forgot_resp = await client.post("/api/auth/forgot-password", json={
            "email": test_email
        })
        assert forgot_resp.status_code == 200
        forgot_data = forgot_resp.json()
        assert forgot_data["status"] == "success"
        
        # CRITICAL SECURITY CHECK: Ensure OTP is NOT exposed in the HTTP response
        assert "reset_code" not in forgot_data
        assert "code" not in forgot_data
        assert "A 6-digit verification code has been sent" in forgot_data["message"]

        # Read the secure OTP stored server-side for verification testing
        assert test_email in _RESET_CODES
        valid_otp = _RESET_CODES[test_email]["code"]
        assert len(valid_otp) == 6

        # 3. Test Brute-force failed attempts tracking
        for attempt in range(5):
            bad_resp = await client.post("/api/auth/reset-password", json={
                "email": test_email,
                "reset_code": "000000",
                "new_password": "NewPassword123!"
            })
            assert bad_resp.status_code == 400
            assert "Invalid verification code" in bad_resp.json()["detail"]

        # 6th attempt should lock/invalidate the code completely
        locked_resp = await client.post("/api/auth/reset-password", json={
            "email": test_email,
            "reset_code": "000000",
            "new_password": "NewPassword123!"
        })
        assert locked_resp.status_code == 400
        assert "Too many failed verification attempts" in locked_resp.json()["detail"]
        assert test_email not in _RESET_CODES

        # 4. Request new OTP and verify successful password reset
        forgot_resp2 = await client.post("/api/auth/forgot-password", json={
            "email": test_email
        })
        assert forgot_resp2.status_code == 200
        new_otp = _RESET_CODES[test_email]["code"]

        success_reset = await client.post("/api/auth/reset-password", json={
            "email": test_email,
            "reset_code": new_otp,
            "new_password": "BrandNewPassword456!"
        })
        assert success_reset.status_code == 200
        assert "token" in success_reset.json()

@pytest.mark.asyncio
async def test_high_speed_parallel_data_buffer():
    # Test parallel multi-timeframe fetching
    start_t = time.time()
    tf_dfs = await candle_buffer.get_multi_timeframe_dfs("XAU/USD")
    cold_elapsed = time.time() - start_t
    
    assert "1h" in tf_dfs
    assert "15m" in tf_dfs
    assert "5m" in tf_dfs
    assert not tf_dfs["5m"].empty
    # Cold parallel fetch should be reasonably fast (< 5.0s)
    assert cold_elapsed < 5.0

    # Test warm cached fetch (sub-millisecond)
    start_cached = time.time()
    tf_cached = await candle_buffer.get_multi_timeframe_dfs("XAU/USD")
    warm_elapsed = time.time() - start_cached
    assert warm_elapsed < 0.1
    assert not tf_cached["5m"].empty

@pytest.mark.asyncio
async def test_signal_generation_accuracy():
    # Test accurate signal generation with institutional parameters
    sig = await signal_generator.analyze_and_generate_signal("XAU/USD", force_generate=True)
    assert sig is not None
    assert sig.symbol == "XAU/USD"
    assert sig.direction in ["BUY", "SELL"]
    assert sig.entry_price > 0
    assert sig.stop_loss > 0
    assert sig.take_profit_1 > 0
    assert sig.take_profit_2 > 0
    assert sig.risk_reward_ratio >= 1.0
    assert len(sig.confirmations) > 0
    assert sig.confidence_score > 0

@pytest.mark.asyncio
async def test_omni_bot_worker_watchlist_cycle():
    # Test background autonomous cycle
    initial_scans = omni_bot_worker.scan_count
    await omni_bot_worker.execute_cycle()
    assert omni_bot_worker.scan_count == initial_scans + 1
    assert omni_bot_worker.last_scan_time is not None
