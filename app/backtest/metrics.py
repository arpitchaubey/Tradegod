from typing import List, Dict, Any
from pydantic import BaseModel

class SimulatedTrade(BaseModel):
    trade_id: int
    symbol: str
    direction: str  # "BUY" or "SELL"
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    position_size_lots: float
    profit_loss: float
    r_multiple: float
    result: str  # "WIN", "LOSS", or "EVEN"

class BacktestReport(BaseModel):
    symbol: str
    timeframe: str
    total_candles: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    even_trades: int
    win_rate_percent: float
    loss_rate_percent: float
    profit_factor: float
    net_profit: float
    gross_profit: float
    gross_loss: float
    max_drawdown_percent: float
    average_r: float
    expectancy: float
    max_winning_streak: int
    max_losing_streak: int
    trades: List[SimulatedTrade]
    equity_curve: List[Dict[str, Any]] = []
    walk_forward_windows: List[Dict[str, Any]] = []

def calculate_backtest_metrics(
    symbol: str,
    timeframe: str,
    total_candles: int,
    trades: List[SimulatedTrade],
    initial_balance: float = 10000.0
) -> BacktestReport:
    """Calculates comprehensive backtesting metrics from simulated trades."""
    if not trades:
        return BacktestReport(
            symbol=symbol,
            timeframe=timeframe,
            total_candles=total_candles,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            even_trades=0,
            win_rate_percent=0.0,
            loss_rate_percent=0.0,
            profit_factor=0.0,
            net_profit=0.0,
            gross_profit=0.0,
            gross_loss=0.0,
            max_drawdown_percent=0.0,
            average_r=0.0,
            expectancy=0.0,
            max_winning_streak=0,
            max_losing_streak=0,
            trades=[]
        )

    winning_trades = [t for t in trades if t.result == "WIN"]
    losing_trades = [t for t in trades if t.result == "LOSS"]
    even_trades = [t for t in trades if t.result == "EVEN"]

    total = len(trades)
    wins = len(winning_trades)
    losses = len(losing_trades)

    win_rate = round((wins / total) * 100.0, 2)
    loss_rate = round((losses / total) * 100.0, 2)

    gross_profit = sum(t.profit_loss for t in winning_trades)
    gross_loss = abs(sum(t.profit_loss for t in losing_trades))

    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (999.0 if gross_profit > 0 else 0.0)
    net_profit = round(gross_profit - gross_loss, 2)

    r_multiples = [t.r_multiple for t in trades]
    average_r = round(sum(r_multiples) / len(r_multiples), 2) if r_multiples else 0.0

    # Expectancy formula = (Win Rate * Avg Win) - (Loss Rate * Avg Loss)
    avg_win = gross_profit / wins if wins > 0 else 0.0
    avg_loss = gross_loss / losses if losses > 0 else 0.0
    expectancy = round(((wins / total) * avg_win) - ((losses / total) * avg_loss), 2)

    # Calculate Drawdown, Streaks & Equity Curve
    equity = initial_balance
    peak = initial_balance
    max_dd = 0.0

    current_win_streak = 0
    max_win_streak = 0
    current_loss_streak = 0
    max_loss_streak = 0

    equity_curve = [{"timestamp": "Start", "equity": initial_balance, "drawdown_percent": 0.0}]

    for t in trades:
        equity += t.profit_loss
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100.0
        if dd > max_dd:
            max_dd = dd

        equity_curve.append({
            "timestamp": t.exit_time,
            "equity": round(equity, 2),
            "drawdown_percent": round(dd, 2)
        })

        if t.result == "WIN":
            current_win_streak += 1
            current_loss_streak = 0
            max_win_streak = max(max_win_streak, current_win_streak)
        elif t.result == "LOSS":
            current_loss_streak += 1
            current_win_streak = 0
            max_loss_streak = max(max_loss_streak, current_loss_streak)

    return BacktestReport(
        symbol=symbol,
        timeframe=timeframe,
        total_candles=total_candles,
        total_trades=total,
        winning_trades=wins,
        losing_trades=losses,
        even_trades=len(even_trades),
        win_rate_percent=win_rate,
        loss_rate_percent=loss_rate,
        profit_factor=profit_factor,
        net_profit=net_profit,
        gross_profit=round(gross_profit, 2),
        gross_loss=round(gross_loss, 2),
        max_drawdown_percent=round(max_dd, 2),
        average_r=average_r,
        expectancy=expectancy,
        max_winning_streak=max_win_streak,
        max_losing_streak=max_loss_streak,
        trades=trades,
        equity_curve=equity_curve
    )
