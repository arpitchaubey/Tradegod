import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.main import app
from app.broker.paper import PaperBrokerAdapter
from app.execution.manager import ExecutionManager
from app.news.filter import EconomicNewsFilter
from app.signals.state_machine import SignalStateMachine
from app.signals.models import SignalPayload, SignalStatus
from app.ai.strategy_builder import parse_natural_language_strategy

client = TestClient(app)

@pytest.mark.asyncio
async def test_paper_broker_order_placement_and_pnl():
    broker = PaperBrokerAdapter(initial_balance=10000.0)
    summary = await broker.get_account_summary()
    assert summary.balance == 10000.0

    order = await broker.place_order(
        symbol="XAU/USD",
        direction="BUY",
        entry_price=3345.0,
        stop_loss=3335.0,
        take_profit_1=3355.0,
        take_profit_2=3365.0,
        size_lots=0.1,
        alert_id="TEST-ALERT-1"
    )
    assert order.order_id.startswith("PAPER-")
    assert order.status == "FILLED"

    positions = await broker.get_positions()
    assert len(positions) == 1

    # Update live price up by 10 points -> 0.1 lots * 10 * 100 = +$100 PnL
    broker.update_live_prices("XAU/USD", 3355.0)
    summary_updated = await broker.get_account_summary()
    assert summary_updated.unrealized_pnl == 100.0

    # Close position at 3355.0
    await broker.close_position(order.order_id, 3355.0)
    summary_final = await broker.get_account_summary()
    assert summary_final.balance == 10100.0
    assert len(await broker.get_positions()) == 0

@pytest.mark.asyncio
async def test_execution_manager_kill_switch():
    mgr = ExecutionManager()
    mgr.set_execution_mode("PAPER_TRADING")
    assert not mgr.is_kill_switch_active

    mgr.toggle_kill_switch(True)
    assert mgr.is_kill_switch_active

    status = await mgr.get_execution_status()
    assert status["is_kill_switch_active"] is True
    assert status["mode"] == "PAPER_TRADING"

def test_natural_language_strategy_builder():
    prompt = "Buy XAU/USD on the 5M chart when 20 EMA > 50 EMA and RSI > 60 with 1:3 risk/reward ratio"
    strategy = parse_natural_language_strategy(prompt)
    assert strategy.symbol == "XAU/USD"
    assert strategy.direction == "long"
    assert strategy.risk_reward_ratio == 3.0
    assert len(strategy.rules) > 0

def test_execution_api_routes():
    response = client.get("/api/execution/status")
    assert response.status_code == 200
    data = response.json()
    assert "mode" in data
    assert "account" in data

    response_mode = client.post("/api/execution/mode", json={"mode": "PAPER_TRADING"})
    assert response_mode.status_code == 200
    assert response_mode.json()["mode"] == "PAPER_TRADING"

    response_news = client.get("/api/execution/news")
    assert response_news.status_code == 200
    assert "is_blackout_active" in response_news.json()

def test_strategy_parse_api():
    # Register & Login test user for auth token
    reg = client.post("/api/auth/register", json={"email": "test_parse@tradegod.ai", "password": "password123", "full_name": "Test Parser"})
    token = reg.json()["token"] if reg.status_code == 200 else client.post("/api/auth/login", json={"email": "test_parse@tradegod.ai", "password": "password123"}).json()["token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/strategy/parse", json={"text": "Buy XAU/USD when EMA20 > EMA50 and RSI > 55 with 1:2 R:R"}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "XAU/USD"
    assert data["risk_reward_ratio"] == 2.0
