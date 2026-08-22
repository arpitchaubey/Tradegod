import pytest
import pandas as pd
from datetime import datetime, timedelta, timezone

from app.strategy.schemas import get_default_gold_strategy
from app.strategy.engine import StrategyEngine
from app.risk.manager import RiskManager
from app.risk.position_size import calculate_position_size
from app.signals.deduplicator import deduplicator

def create_df():
    records = []
    now = datetime.now(timezone.utc)
    price = 3345.0
    for i in range(100):
        price += 0.2
        records.append({
            "timestamp": now + timedelta(minutes=5*i),
            "open": price - 0.1,
            "high": price + 0.5,
            "low": price - 0.2,
            "close": price,
            "volume": 1000.0
        })
    return pd.DataFrame(records)

def test_strategy_engine():
    df = create_df()
    strategy = get_default_gold_strategy()
    engine = StrategyEngine(strategy)
    tf_dfs = {"1h": df, "15m": df, "5m": df}

    res = engine.evaluate(tf_dfs)
    assert res.strategy_id == "gold_breakout_default"
    assert res.confidence_score > 0
    assert isinstance(res.rule_results, list)

def test_position_sizing():
    # Test XAU/USD (Gold - 100 oz)
    gold_lots = calculate_position_size(account_balance=10000.0, risk_percent=1.0, entry_price=3345.0, stop_loss_price=3340.0, symbol="XAU/USD")
    assert gold_lots > 0
    # $100 risk / ($5 risk per oz * 100 oz) = 0.20 lots
    assert abs(gold_lots - 0.20) < 0.05

    # Test EUR/USD (Forex - 100,000 units)
    forex_lots = calculate_position_size(account_balance=10000.0, risk_percent=1.0, entry_price=1.0850, stop_loss_price=1.0800, symbol="EUR/USD")
    assert forex_lots > 0

def test_risk_manager():
    df = create_df()
    rm = RiskManager(account_balance=10000.0, risk_percent=1.0)
    plan = rm.calculate_trade_plan("XAU/USD", "BUY", df, target_rr=2.0)

    assert plan.symbol == "XAU/USD"
    assert plan.entry_price > 0
    assert plan.stop_loss < plan.entry_price
    assert plan.take_profit_2 > plan.entry_price
    assert plan.risk_reward_ratio >= 1.5

def test_deduplicator():
    alert_id = deduplicator.generate_alert_id("XAU/USD", "5m", "BUY", "2026-08-22T14:00:00Z")
    assert "XAUUSD-5M-BUY" in alert_id
    assert not deduplicator.is_duplicate(alert_id)

    deduplicator.register_alert(alert_id)
    assert deduplicator.is_duplicate(alert_id)
