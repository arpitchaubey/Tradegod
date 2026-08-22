from typing import Dict, Any
from app.signals.models import SignalPayload
from app.data.chart_info import ActiveChartInfo

def format_telegram_signal(signal: SignalPayload) -> str:
    """Formats a signal payload into Telegram markdown alert."""
    icon = "🟢" if signal.direction.upper() == "BUY" else "🔴"
    chart = signal.chart_info or {}

    confirm_lines = "\n".join([f"  {c}" for c in signal.confirmations])

    msg = (
        f"{icon} *{signal.symbol} {signal.direction.upper()} SETUP*\n\n"
        f"📍 *Entry:* `{signal.entry_price}`\n"
        f"🛑 *Stop Loss:* `{signal.stop_loss}`\n"
        f"🎯 *Take Profit 1:* `{signal.take_profit_1}`\n"
        f"🎯 *Take Profit 2:* `{signal.take_profit_2}`\n\n"
        f"⚖️ *Risk/Reward:* `1:{signal.risk_reward_ratio}`\n"
        f"📦 *Position Size:* `{signal.position_size_lots} lots`\n"
        f"📈 *Confidence Score:* `{signal.confidence_score}/100`\n\n"
        f"📊 *ACTIVE CHART INFO*\n"
        f"• Symbol: `{chart.get('symbol', signal.symbol)}` ({chart.get('display_name', '')})\n"
        f"• Timeframes: Trend `{chart.get('timeframes', {}).get('trend', '1H')}` | Entry `{signal.timeframe.upper()}`\n"
        f"• Data Source: `{chart.get('provider', 'mock').upper()}`\n"
        f"• Last Sync: `{chart.get('last_updated', '')[:19]}`\n\n"
        f"✅ *CONFIRMATIONS:*\n{confirm_lines}\n\n"
        f"🆔 *Signal ID:* `{signal.alert_id}`\n"
        f"⚠️ _Educational/automated-system output; trade at your own risk._"
    )
    return msg

def format_status_message(chart_info: ActiveChartInfo) -> str:
    """Formats active chart and engine status for Telegram /status command."""
    return (
        f"🤖 *TRADEGOD AI BOT STATUS*\n\n"
        f"📊 *Active Chart:* `{chart_info.symbol}` ({chart_info.display_name})\n"
        f"💰 *Last Price:* `{chart_info.last_price}` (Bid: `{chart_info.bid_price}` / Ask: `{chart_info.ask_price}`)\n"
        f"📏 *Spread:* `{chart_info.spread}` pips\n"
        f"⏳ *Timeframe Stack:* Trend `{chart_info.timeframes.get('trend', '1h')}` | Setup `{chart_info.timeframes.get('setup', '15m')}` | Entry `{chart_info.timeframes.get('entry', '5m')}`\n"
        f"📡 *Data Provider:* `{chart_info.provider.upper()}`\n"
        f"🕯️ *Loaded Candles:* `{chart_info.candle_count}`\n"
        f"🟢 *Engine Status:* `RUNNING ({chart_info.status})`"
    )
