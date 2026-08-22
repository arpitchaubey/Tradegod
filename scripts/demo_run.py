import sys
import os
import asyncio
import json

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data.historical import candle_buffer
from app.data.symbols import list_supported_symbols
from app.signals.generator import SignalGenerator
from app.backtest.engine import BacktestEngine
from app.telegram.formatter import format_telegram_signal, format_status_message

async def main():
    print("=" * 60)
    print("🚀 Tradegod AI Trading Bot Engine Demo Run")
    print("=" * 60)

    # 1. List Supported Symbols
    symbols = list_supported_symbols()
    print(f"\n[1] Supported Symbols ({len(symbols)}):")
    for s in symbols:
        print(f"  • {s['symbol']} ({s['display_name']}) - Category: {s['category']}")

    # 2. Get Active Chart Info for Default Symbol (XAU/USD)
    chart_info = await candle_buffer.get_active_chart_info("XAU/USD")
    print(f"\n[2] Active Chart Metadata (Default: XAU/USD):")
    print(json.dumps(chart_info.model_dump(), indent=2))

    # 3. Generate Signal for XAU/USD
    generator = SignalGenerator()
    print("\n[3] Running Signal Pipeline for XAU/USD...")
    signal = await generator.analyze_and_generate_signal("XAU/USD", force_generate=True)
    if signal:
        print("\n--- Formatted Telegram Signal Alert ---")
        print(format_telegram_signal(signal))
        print("---------------------------------------")

    # 4. Run Backtest Simulation for XAU/USD
    print("\n[4] Running Historical Candle Backtest for XAU/USD (5M timeframe, 200 candles)...")
    bt_engine = BacktestEngine()
    bt_report = await bt_engine.run_backtest("XAU/USD", "5m", candle_limit=200)
    print(f"  • Total Candles: {bt_report.total_candles}")
    print(f"  • Total Trades: {bt_report.total_trades}")
    print(f"  • Win Rate: {bt_report.win_rate_percent}%")
    print(f"  • Profit Factor: {bt_report.profit_factor}")
    print(f"  • Net Profit: ${bt_report.net_profit}")
    print(f"  • Max Drawdown: {bt_report.max_drawdown_percent}%")
    print(f"  • Expectancy: ${bt_report.expectancy}")

    print("\n" + "=" * 60)
    print("✅ Demo Run Completed Successfully!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
