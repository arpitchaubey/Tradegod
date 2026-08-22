import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import pandas as pd
from app.backtest.engine import BacktestEngine
from app.strategy.schemas import get_default_gold_strategy

async def run_comparison():
    engine = BacktestEngine(get_default_gold_strategy(), initial_balance=10000.0)
    report = await engine.run_backtest(symbol="XAU/USD", timeframe="5m", candle_limit=1000)

    print("=================================================================")
    print("           TRADEGOD AI — BACKTEST ACCURACY COMPARISON           ")
    print("=================================================================")
    print(f"Target Symbol           : {report.symbol}")
    print(f"Timeframe               : {report.timeframe}")
    print(f"Evaluated Candles       : {report.total_candles}")
    print(f"Total Simulated Trades  : {report.total_trades}")
    print(f"Winning Trades          : {report.winning_trades}")
    print(f"Losing Trades           : {report.losing_trades}")
    print(f"Win Rate Percentage     : {report.win_rate_percent}%")
    print(f"Profit Factor           : {report.profit_factor}")
    print(f"Net Profit              : ${report.net_profit:.2f}")
    print(f"Max Drawdown Percentage : {report.max_drawdown_percent}%")
    print(f"Average R:R Multiple    : 1:{report.average_r}")
    print("-----------------------------------------------------------------")
    print("Walk-Forward Rolling Windows:")
    for w in report.walk_forward_windows:
        print(f"  • {w['window']}: Trades={w['trades']} | Win Rate={w['win_rate_percent']}% | Net Profit=${w['net_profit']:.2f} | Max DD={w['max_drawdown_percent']}%")
    print("=================================================================")

if __name__ == "__main__":
    asyncio.run(run_comparison())
