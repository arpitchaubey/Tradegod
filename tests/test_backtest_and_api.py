import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.backtest.engine import BacktestEngine

@pytest.mark.asyncio
async def test_backtest_engine():
    engine = BacktestEngine(initial_balance=10000.0, risk_percent=1.0)
    report = await engine.run_backtest(symbol="XAU/USD", timeframe="5m", candle_limit=100)

    assert report.symbol == "XAU/USD"
    assert report.total_candles > 0
    assert report.profit_factor >= 0

@pytest.mark.asyncio
async def test_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test Root
        resp = await client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "online"

        # Test Symbols
        resp = await client.get("/api/market/symbols")
        assert resp.status_code == 200
        assert resp.json()["default_symbol"] == "XAU/USD"

        # Test Active Chart Info
        resp = await client.get("/api/market/chart-info?symbol=XAU/USD")
        assert resp.status_code == 200
        data = resp.json()
        assert data["symbol"] == "XAU/USD"
        assert "timeframes" in data
        assert "last_price" in data

        # Test Candles
        resp = await client.get("/api/market/candles?symbol=XAU/USD&limit=20")
        assert resp.status_code == 200
        assert resp.json()["count"] == 20

        # Test Strategy Current
        resp = await client.get("/api/strategy/current")
        assert resp.status_code == 200

        # Test Signal Generation
        resp = await client.post("/api/signals/generate?symbol=XAU/USD")
        assert resp.status_code == 200

        # Test Backtest API
        resp = await client.post("/api/backtest/run?symbol=XAU/USD&limit=100")
        assert resp.status_code == 200
        assert "profit_factor" in resp.json()

@pytest.mark.asyncio
async def test_cors_headers():
    transport = ASGITransport(app=app)
    headers = {
        "Origin": "https://frontend-phi-snowy-59.vercel.app",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"
    }
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Preflight OPTIONS request
        resp = await client.options("/api/auth/register", headers=headers)
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == "https://frontend-phi-snowy-59.vercel.app"

        # POST request with origin
        post_headers = {"Origin": "https://frontend-phi-snowy-59.vercel.app"}
        resp = await client.post("/api/auth/login", json={"email": "nonexistent@test.com", "password": "wrong"}, headers=post_headers)
        assert resp.headers.get("access-control-allow-origin") == "https://frontend-phi-snowy-59.vercel.app"
