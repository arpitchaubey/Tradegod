from typing import Dict, Any, Optional
import pandas as pd
from pydantic import BaseModel

from app.data.symbols import get_symbol_spec
from app.indicators.volatility import calculate_atr
from app.indicators.structure import find_swing_points
from app.risk.position_size import calculate_position_size

class TradeRiskPlan(BaseModel):
    symbol: str
    direction: str  # "BUY" or "SELL"
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    risk_reward_ratio: float
    account_balance: float
    risk_percent: float
    max_risk_amount: float
    position_size_lots: float
    is_valid_risk: bool
    risk_notes: str

class RiskManager:
    """Deterministic Risk Management & Target Calculation Engine."""

    def __init__(
        self,
        account_balance: float = 10000.0,
        risk_percent: float = 1.0,
        max_daily_loss_percent: float = 2.0,
        min_rr_ratio: float = 1.5
    ):
        self.account_balance = account_balance
        self.risk_percent = risk_percent
        self.max_daily_loss_percent = max_daily_loss_percent
        self.min_rr_ratio = min_rr_ratio

    def calculate_trade_plan(
        self,
        symbol: str,
        direction: str,
        current_df: pd.DataFrame,
        target_rr: float = 2.0,
        sl_method: str = "structure"
    ) -> TradeRiskPlan:
        spec = get_symbol_spec(symbol)
        latest_close = float(current_df["close"].iloc[-1])
        entry_price = round(latest_close, spec.quote_precision)

        atr_series = calculate_atr(current_df, 14)
        atr_val = float(atr_series.iloc[-1]) if not atr_series.empty else spec.pip_size * 20

        # Calculate Stop Loss with volatility-aware buffer
        sl_buffer = max(spec.pip_size * 5, atr_val * 0.4)
        if direction.upper() == "BUY":
            if sl_method == "structure":
                _, swing_lows = find_swing_points(current_df, window=3)
                if swing_lows:
                    recent_low = min([sl["price"] for sl in swing_lows[-3:]])
                    sl = recent_low - sl_buffer
                else:
                    sl = entry_price - (atr_val * 1.5)
            else:
                sl = entry_price - (atr_val * 1.5)
        else:
            if sl_method == "structure":
                swing_highs, _ = find_swing_points(current_df, window=3)
                if swing_highs:
                    recent_high = max([sh["price"] for sh in swing_highs[-3:]])
                    sl = recent_high + sl_buffer
                else:
                    sl = entry_price + (atr_val * 1.5)
            else:
                sl = entry_price + (atr_val * 1.5)

        sl = round(sl, spec.quote_precision)
        risk_distance = abs(entry_price - sl)

        if risk_distance <= 0:
            risk_distance = spec.pip_size * 10
            sl = entry_price - risk_distance if direction.upper() == "BUY" else entry_price + risk_distance

        # Calculate Take Profit Targets based on R:R
        if direction.upper() == "BUY":
            tp1 = entry_price + (risk_distance * 1.0)
            tp2 = entry_price + (risk_distance * target_rr)
        else:
            tp1 = entry_price - (risk_distance * 1.0)
            tp2 = entry_price - (risk_distance * target_rr)

        tp1 = round(tp1, spec.quote_precision)
        tp2 = round(tp2, spec.quote_precision)

        actual_rr = round(abs(tp2 - entry_price) / max(1e-5, risk_distance), 2)
        lots = calculate_position_size(self.account_balance, self.risk_percent, entry_price, sl, symbol)
        max_risk_amount = round(self.account_balance * (self.risk_percent / 100.0), 2)

        is_valid = actual_rr >= self.min_rr_ratio

        return TradeRiskPlan(
            symbol=spec.symbol,
            direction=direction.upper(),
            entry_price=entry_price,
            stop_loss=sl,
            take_profit_1=tp1,
            take_profit_2=tp2,
            risk_reward_ratio=actual_rr,
            account_balance=self.account_balance,
            risk_percent=self.risk_percent,
            max_risk_amount=max_risk_amount,
            position_size_lots=lots,
            is_valid_risk=is_valid,
            risk_notes=f"Valid risk plan with 1:{actual_rr} R:R and lot size {lots} lots."
        )
