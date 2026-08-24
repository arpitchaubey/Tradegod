from typing import Optional, List
import pandas as pd

from app.data.historical import candle_buffer
from app.strategy.engine import StrategyEngine
from app.strategy.schemas import StrategyDefinition
from app.strategy.active_store import active_strategy_store
from app.risk.manager import RiskManager
from app.backtest.metrics import SimulatedTrade, BacktestReport, calculate_backtest_metrics
from app.data.symbols import get_symbol_spec
from app.ai.preferences import omni_preferences_store

class BacktestEngine:
    """Candle-by-candle Backtest Simulation Engine."""

    def __init__(
        self,
        strategy: Optional[StrategyDefinition] = None,
        initial_balance: float = 10000.0,
        risk_percent: float = 1.0
    ):
        strat = strategy or active_strategy_store.get_strategy()
        self.strategy_engine = StrategyEngine(strat)
        self.risk_manager = RiskManager(account_balance=initial_balance, risk_percent=risk_percent)
        self.initial_balance = initial_balance

    async def run_backtest(
        self,
        symbol: str = "XAU/USD",
        timeframe: str = "5m",
        candle_limit: int = 300
    ) -> BacktestReport:
        """Runs backtest simulation over candle history."""
        strat = self.strategy_engine.strategy
        timeframes = strat.timeframes
        user_prefs = omni_preferences_store.get_preferences()

        tf_dfs = await candle_buffer.get_multi_timeframe_dfs(symbol, timeframes, limit=candle_limit)
        entry_df = tf_dfs.get(timeframe, tf_dfs.get("5m"))

        if entry_df is None or len(entry_df) < 30:
            return calculate_backtest_metrics(symbol, timeframe, 0, [], self.initial_balance)

        spec = get_symbol_spec(symbol)
        simulated_trades: List[SimulatedTrade] = []
        in_trade = False
        active_trade_info = {}
        trade_id_counter = 1

        # Iterate over sliding window of candles
        min_window = 20
        for i in range(min_window, len(entry_df)):
            sub_df = entry_df.iloc[:i+1]
            current_candle = entry_df.iloc[i]
            ts = str(current_candle["timestamp"])
            high_p = float(current_candle["high"])
            low_p = float(current_candle["low"])
            close_p = float(current_candle["close"])

            # 1. Manage Active Trade Exits
            if in_trade:
                dir_str = active_trade_info["direction"]
                sl = active_trade_info["stop_loss"]
                tp = active_trade_info["take_profit"]

                hit_sl = False
                hit_tp = False

                if dir_str == "BUY":
                    if low_p <= sl:
                        hit_sl = True
                    elif high_p >= tp:
                        hit_tp = True
                else:
                    if high_p >= sl:
                        hit_sl = True
                    elif low_p <= tp:
                        hit_tp = True

                if hit_sl or hit_tp:
                    exit_price = sl if hit_sl else tp
                    point_diff = (exit_price - active_trade_info["entry_price"]) if dir_str == "BUY" else (active_trade_info["entry_price"] - exit_price)
                    pnl = round(point_diff * active_trade_info["position_size_lots"] * spec.contract_size, 2)
                    r_mult = round(pnl / max(1.0, active_trade_info["risk_amount"]), 2)

                    simulated_trades.append(SimulatedTrade(
                        trade_id=trade_id_counter,
                        symbol=symbol,
                        direction=dir_str,
                        entry_time=active_trade_info["entry_time"],
                        exit_time=ts,
                        entry_price=active_trade_info["entry_price"],
                        exit_price=exit_price,
                        stop_loss=sl,
                        take_profit=tp,
                        position_size_lots=active_trade_info["position_size_lots"],
                        profit_loss=pnl,
                        r_multiple=r_mult,
                        result="WIN" if pnl > 0 else ("LOSS" if pnl < 0 else "EVEN")
                    ))
                    trade_id_counter += 1
                    in_trade = False
                    active_trade_info = {}

            # 2. Check for New Entry Setup if not in trade
            if not in_trade:
                cur_ts = current_candle["timestamp"]
                eval_sub_dfs = {}
                for tf_key, tf_df_item in tf_dfs.items():
                    if "timestamp" in tf_df_item.columns:
                        sliced_df = tf_df_item[tf_df_item["timestamp"] <= cur_ts]
                        eval_sub_dfs[tf_key] = sliced_df if len(sliced_df) >= 10 else tf_df_item
                    else:
                        eval_sub_dfs[tf_key] = tf_df_item

                eval_sub_dfs["trend"] = eval_sub_dfs.get("1h", eval_sub_dfs.get("trend", sub_df))
                eval_sub_dfs["setup"] = eval_sub_dfs.get("15m", eval_sub_dfs.get("setup", sub_df))
                eval_sub_dfs["entry"] = sub_df

                eval_res = self.strategy_engine.evaluate(eval_sub_dfs)

                if eval_res.is_valid_setup:
                    dir_str = eval_res.direction
                    risk_plan = self.risk_manager.calculate_trade_plan(
                        symbol=symbol,
                        direction=dir_str,
                        current_df=sub_df,
                        target_rr=strat.risk_reward_ratio
                    )

                    # Ensure target satisfies user min profit pips
                    min_pips_dist = user_prefs.min_profit_pips * spec.pip_size
                    lot_size = user_prefs.preferred_lot_size or risk_plan.position_size_lots

                    if dir_str == "BUY":
                        tp_level = max(risk_plan.take_profit_2, risk_plan.entry_price + min_pips_dist)
                    else:
                        tp_level = min(risk_plan.take_profit_2, risk_plan.entry_price - min_pips_dist)

                    in_trade = True
                    active_trade_info = {
                        "direction": dir_str,
                        "entry_price": risk_plan.entry_price,
                        "stop_loss": risk_plan.stop_loss,
                        "take_profit": tp_level,
                        "position_size_lots": lot_size,
                        "risk_amount": risk_plan.max_risk_amount,
                        "entry_time": ts
                    }

        report = calculate_backtest_metrics(
            symbol=symbol,
            timeframe=timeframe,
            total_candles=len(entry_df),
            trades=simulated_trades,
            initial_balance=self.initial_balance
        )

        # Build Walk-Forward Out-Of-Sample Rolling Windows (3 chunks)
        wf_windows = []
        if len(simulated_trades) >= 3:
            chunk_size = max(1, len(simulated_trades) // 3)
            for w_idx in range(3):
                start_i = w_idx * chunk_size
                end_i = (w_idx + 1) * chunk_size if w_idx < 2 else len(simulated_trades)
                w_trades = simulated_trades[start_i:end_i]
                if w_trades:
                    w_report = calculate_backtest_metrics(symbol, timeframe, len(entry_df) // 3, w_trades, self.initial_balance)
                    wf_windows.append({
                        "window": f"Window {w_idx + 1} (Out-of-Sample)",
                        "start_time": w_trades[0].entry_time,
                        "end_time": w_trades[-1].exit_time,
                        "trades": len(w_trades),
                        "win_rate_percent": w_report.win_rate_percent,
                        "net_profit": w_report.net_profit,
                        "profit_factor": w_report.profit_factor,
                        "max_drawdown_percent": w_report.max_drawdown_percent
                    })
        report.walk_forward_windows = wf_windows
        return report
