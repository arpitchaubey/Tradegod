from typing import Dict, Any, Tuple
import pandas as pd

from app.strategy.schemas import StrategyRule
from app.indicators.trend import calculate_ema, calculate_sma, evaluate_trend_alignment
from app.indicators.momentum import calculate_rsi, calculate_macd
from app.indicators.volatility import calculate_atr
from app.indicators.structure import detect_breakout

from app.indicators.trend import calculate_ema, calculate_sma, evaluate_trend_alignment, evaluate_adx_gate
from app.indicators.momentum import calculate_rsi, calculate_macd
from app.indicators.volatility import calculate_atr, calculate_atr_percentile
from app.indicators.structure import detect_breakout

def evaluate_rule(
    rule: StrategyRule,
    tf_dataframes: Dict[str, pd.DataFrame]
) -> Tuple[bool, str]:
    """
    Evaluates a single strategy rule against the target dataframe.
    Returns: (passed: bool, explanation: str)
    """
    df = tf_dataframes.get(rule.timeframe)
    if df is None or df.empty or len(df) < 10:
        df = list(tf_dataframes.values())[0] if tf_dataframes else None
        if df is None or df.empty:
            return False, f"Rule {rule.id}: Missing data for timeframe {rule.timeframe}"

    latest_close = float(df["close"].iloc[-1])
    latest_open = float(df["open"].iloc[-1])

    cond_type = rule.condition_type.lower().strip()

    # 1. ADX Trend Strength Pre-gate for 1H Trend Rules
    if rule.timeframe == "trend" or "trend" in rule.id.lower():
        adx_val, regime, adx_pass = evaluate_adx_gate(df, adx_threshold=20.0)
        if not adx_pass:
            return False, f"{rule.description} [ADX={adx_val:.1f} < 20.0 — Ranging Market] -> FAILED"

    # 2. Indicator & Threshold comparisons with Dynamic RSI scaling
    if cond_type in ["indicator_compare", "threshold_check", "price_action", "structure"]:
        left_val = _get_operand_val(rule.left_operand, df)
        right_val = _get_operand_val(rule.right_operand, df)

        # Dynamic RSI scaling based on Volatility (ATR Percentile Rank)
        if str(rule.left_operand).lower() == "rsi" or str(rule.right_operand).lower() == "rsi":
            atr_pct = calculate_atr_percentile(df, 14, 100)
            if atr_pct < 30.0:
                right_val = max(right_val, 60.0)  # Scale up threshold in low-volatility chop
            elif atr_pct > 70.0:
                right_val = min(right_val, 52.0)  # Relax slightly in high-volatility trend

        passed = _apply_operator(left_val, rule.operator, right_val)
        status = "PASSED" if passed else "FAILED"
        msg = f"{rule.description} [{rule.left_operand}={left_val:.2f} {rule.operator} {right_val:.2f}] -> {status}"
        return passed, msg

    elif cond_type in ["breakout", "candle_close"]:
        bo_info = detect_breakout(df, pip_threshold=0.2, atr_multiplier=0.1, swing_window=3)
        if cond_type == "breakout":
            passed = bo_info.is_breakout
        else:  # candle_close / anti-fakeout confirmation
            passed = bo_info.confirmed

        status = "PASSED" if passed else "FAILED"
        msg = f"{rule.description} [Breakout Level={bo_info.level:.2f}, Confirmed={bo_info.confirmed}] -> {status}"
        return passed, msg

    else:
        left_val = _get_operand_val(rule.left_operand, df)
        right_val = _get_operand_val(rule.right_operand, df)
        passed = _apply_operator(left_val, rule.operator, right_val)
        return passed, f"{rule.description} -> {'PASSED' if passed else 'FAILED'}"

def _get_operand_val(operand: Any, df: pd.DataFrame) -> float:
    if isinstance(operand, (int, float)):
        return float(operand)

    op_str = str(operand).lower().strip()
    if op_str == "close":
        return float(df["close"].iloc[-1])
    elif op_str == "open":
        return float(df["open"].iloc[-1])
    elif op_str == "high":
        return float(df["high"].iloc[-1])
    elif op_str == "low":
        return float(df["low"].iloc[-1])
    elif op_str == "ema20":
        return float(calculate_ema(df, 20).iloc[-1])
    elif op_str == "ema50":
        return float(calculate_ema(df, 50).iloc[-1])
    elif op_str == "ema200":
        return float(calculate_ema(df, min(len(df), 200)).iloc[-1])
    elif op_str == "rsi":
        rsi_series = calculate_rsi(df, 14)
        return float(rsi_series.iloc[-1]) if not rsi_series.empty else 55.0
    elif op_str == "atr":
        atr_series = calculate_atr(df, 14)
        return float(atr_series.iloc[-1]) if not atr_series.empty else 2.5
    elif op_str in ["macd", "macd_line"]:
        macd_line, _, _ = calculate_macd(df)
        return float(macd_line.iloc[-1]) if not macd_line.empty else 0.5
    elif op_str in ["macd_signal", "signal_line"]:
        _, signal_line, _ = calculate_macd(df)
        return float(signal_line.iloc[-1]) if not signal_line.empty else 0.2
    elif op_str in ["macd_hist", "histogram"]:
        _, _, hist = calculate_macd(df)
        return float(hist.iloc[-1]) if not hist.empty else 0.3
    elif op_str in ["volume", "vol"]:
        if "volume" in df.columns and not df["volume"].empty:
            return float(df["volume"].iloc[-1])
        return 1500.0
    elif op_str in ["volume_sma", "volume_sma20", "vol_sma"]:
        if "volume" in df.columns and len(df) >= 20:
            vol_sma = df["volume"].rolling(20).mean()
            return float(vol_sma.iloc[-1]) if not vol_sma.empty else 1000.0
        return 1000.0
    else:
        try:
            return float(operand)
        except (ValueError, TypeError):
            return 0.0

def _apply_operator(left: float, operator: str, right: float) -> bool:
    op = operator.strip()
    if op == ">":
        return left > right
    elif op == "<":
        return left < right
    elif op == ">=":
        return left >= right
    elif op == "<=":
        return left <= right
    elif op == "==":
        return abs(left - right) < 1e-5
    return False
