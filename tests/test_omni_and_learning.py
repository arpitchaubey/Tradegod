import pytest
import pandas as pd
from datetime import datetime, timezone, timedelta

from app.indicators.volume_flow import calculate_vwap, calculate_rvol, calculate_obv, estimate_volume_delta
from app.indicators.patterns import calculate_c2c_velocity, detect_fair_value_gaps, detect_market_structure_events, detect_candlestick_formations
from app.indicators.choch_predictor import evaluate_choch_prediction
from app.learning.feedback_engine import feedback_engine
from app.ai.omni_engine import omni_engine

def generate_sample_df(n=50, base_price=3350.0, trend="up"):
    dates = [datetime.now(timezone.utc) - timedelta(minutes=5 * i) for i in range(n)][::-1]
    prices = []
    current = base_price
    for i in range(n):
        if trend == "up":
            current += 0.5 + (i * 0.05)
        else:
            current -= 0.5 + (i * 0.05)
        prices.append(current)

    return pd.DataFrame({
        "timestamp": dates,
        "open": [p - 0.3 for p in prices],
        "high": [p + 0.8 for p in prices],
        "low": [p - 0.8 for p in prices],
        "close": prices,
        "volume": [1200.0 + (i * 10) for i in range(n)]
    })

def test_volume_flow_indicators():
    df = generate_sample_df(30)
    vwap, up_band, low_band = calculate_vwap(df)
    assert not vwap.empty
    assert len(vwap) == len(df)
    assert vwap.iloc[-1] > 0

    rvol = calculate_rvol(df)
    assert rvol > 0.0

    obv, obv_trend = calculate_obv(df)
    assert not obv.empty
    assert obv_trend in ["accumulation", "distribution", "neutral"]

    delta = estimate_volume_delta(df)
    assert "buy_volume_pct" in delta
    assert "sell_volume_pct" in delta
    assert delta["buy_volume_pct"] + delta["sell_volume_pct"] == 100.0

def test_patterns_and_c2c_velocity():
    df = generate_sample_df(30, trend="up")
    c2c = calculate_c2c_velocity(df)
    assert "c2c_velocity" in c2c
    assert "velocity_state" in c2c
    assert c2c["velocity_state"] in ["accelerating_bullish", "steady_bullish", "accelerating_bearish", "steady_bearish", "flat_consolidation"]

    # FVG detection
    fvgs = detect_fair_value_gaps(df)
    assert isinstance(fvgs, list)

    # Structure events
    events = detect_market_structure_events(df)
    assert isinstance(events, list)

    # Candlestick pattern
    pattern = detect_candlestick_formations(df)
    assert "pattern" in pattern
    assert "bias" in pattern

def test_choch_trend_transition_predictor():
    df_1h = generate_sample_df(50, base_price=3350.0, trend="up")
    df_5m = generate_sample_df(30, base_price=3370.0, trend="up")

    report = evaluate_choch_prediction(df_1h, df_5m, symbol="XAU/USD")
    assert report.symbol == "XAU/USD"
    assert report.choch_risk_level in ["LOW", "ELEVATED", "HIGH", "CONFIRMED"]
    assert len(report.scenarios) >= 2
    for s in report.scenarios:
        assert s.probability_percent > 0
        assert s.trigger_level > 0

def test_feedback_engine_self_learning():
    initial_gen = feedback_engine.weights.tuning_generation
    feedback_engine.record_trade_completion(
        alert_id="test_alert_1",
        symbol="XAU/USD",
        direction="BUY",
        entry_price=3350.0,
        exit_price=3360.0,
        stop_loss=3345.0,
        take_profit=3360.0,
        result="WIN_TP2",
        r_multiple=2.0,
        session="LONDON",
        rvol=1.5,
        adx_1h=28.0,
        rsi_5m=60.0,
        confidence_score=85
    )

    feedback_engine.record_trade_completion(
        alert_id="test_alert_2",
        symbol="XAU/USD",
        direction="BUY",
        entry_price=3360.0,
        exit_price=3370.0,
        stop_loss=3355.0,
        take_profit=3370.0,
        result="WIN_TP2",
        r_multiple=2.0,
        session="LONDON",
        rvol=1.6,
        adx_1h=30.0,
        rsi_5m=62.0,
        confidence_score=88
    )

    feedback_engine.record_trade_completion(
        alert_id="test_alert_3",
        symbol="XAU/USD",
        direction="BUY",
        entry_price=3370.0,
        exit_price=3380.0,
        stop_loss=3365.0,
        take_profit=3380.0,
        result="WIN_TP2",
        r_multiple=2.0,
        session="NEW_YORK",
        rvol=1.4,
        adx_1h=26.0,
        rsi_5m=58.0,
        confidence_score=82
    )

    stats = feedback_engine.get_learning_stats()
    assert stats["total_trades_analyzed"] >= 3
    assert stats["overall_win_rate"] >= 50.0
    assert len(stats["session_performance"]) >= 1

@pytest.mark.asyncio
async def test_omni_engine_matrix_and_forecast():
    df_1h = generate_sample_df(60, base_price=3350.0, trend="up")
    df_15m = generate_sample_df(60, base_price=3365.0, trend="up")
    df_5m = generate_sample_df(60, base_price=3375.0, trend="up")

    tf_dfs = {"1h": df_1h, "15m": df_15m, "5m": df_5m}

    matrix = await omni_engine.analyze_market_matrix("XAU/USD", "5m", tf_dfs)
    assert matrix.symbol == "XAU/USD"
    assert matrix.vwap > 0
    assert matrix.rvol > 0
    assert "trend" in matrix.matrix_radar

    forecast = await omni_engine.generate_future_trade_forecast("XAU/USD", "5m", tf_dfs)
    assert forecast.symbol == "XAU/USD"
    assert forecast.win_probability_percent >= 50
    assert forecast.stop_loss > 0
    assert forecast.take_profit_1 > 0
    assert len(forecast.institutional_drivers) >= 1

def test_session_sweeps_and_sr_behavior():
    from app.indicators.session_sweeps import calculate_session_levels_and_sweeps
    from app.indicators.sr_behavior import analyze_sr_price_behavior

    df = generate_sample_df(60, base_price=3350.0, trend="up")
    report = calculate_session_levels_and_sweeps(df)
    assert report.asian_high >= 0
    assert report.asian_low >= 0
    assert report.prev_day_high >= 0
    assert report.liquidity_bias in ["bullish_reversal_sweep", "bearish_reversal_sweep", "neutral"]

    sr_rep = analyze_sr_price_behavior(df)
    assert sr_rep.dominant_behavior in ["NEUTRAL", "BULLISH_EXPANSION", "BEARISH_EXPANSION", "BULLISH_BOUNCE", "BEARISH_REJECTION"]
    assert sr_rep.summary != ""

