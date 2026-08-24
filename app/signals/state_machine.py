import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.signals.models import SignalPayload, SignalStatus
from app.broker.paper import paper_broker

logger = logging.getLogger("signal_state_machine")

class SignalStateMachine:
    """
    Signal State Machine enforcing Section 24 lifecycle transitions:
    WAITING -> WATCHING -> SETUP_DETECTED -> CONFIRMING -> CONFIRMED -> SIGNAL_SENT -> ACTIVE -> TP1_HIT / TP2_HIT / SL_HIT -> CLOSED
    """

    def __init__(self):
        self.active_signals: Dict[str, Dict[str, Any]] = {}

    def register_signal(self, signal: SignalPayload):
        """Registers a newly confirmed signal into the state machine."""
        self.active_signals[signal.alert_id] = {
            "payload": signal,
            "status": "ACTIVE",
            "tp1_hit": False,
            "tp2_hit": False,
            "sl_hit": False,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        logger.info(f"Signal {signal.alert_id} entered ACTIVE state.")

    async def update_tick_price(self, symbol: str, current_price: float) -> List[Dict[str, Any]]:
        """
        Evaluates active signals/positions against current live market price ticks/candles.
        Triggers TP1, TP2, and SL state transitions.
        """
        events: List[Dict[str, Any]] = []
        paper_broker.update_live_prices(symbol, current_price)

        for alert_id, item in list(self.active_signals.items()):
            signal: SignalPayload = item["payload"]
            if signal.symbol != symbol or item["status"] in ["CLOSED", "TP2_HIT", "SL_HIT", "CANCELLED"]:
                continue

            direction = signal.direction
            sl = signal.stop_loss
            tp1 = signal.take_profit_1
            tp2 = signal.take_profit_2

            if direction == "BUY" or direction == "long":
                # Stop Loss Hit
                if current_price <= sl and not item["sl_hit"]:
                    item["sl_hit"] = True
                    item["status"] = "SL_HIT"
                    events.append({
                        "alert_id": alert_id,
                        "event": "SL_HIT",
                        "price": current_price,
                        "message": f"🛑 Stop Loss hit for {symbol} at {current_price:.2f}"
                    })
                    await paper_broker.close_position(alert_id, current_price)
                    try:
                        from app.learning.feedback_engine import feedback_engine
                        feedback_engine.record_trade_completion(
                            alert_id=alert_id, symbol=symbol, direction="BUY",
                            entry_price=signal.entry_price, exit_price=current_price,
                            stop_loss=sl, take_profit=tp2, result="LOSS_SL", r_multiple=-1.0,
                            confidence_score=signal.confidence_score
                        )
                    except Exception:
                        pass

                # Take Profit 1 Hit
                elif current_price >= tp1 and not item["tp1_hit"]:
                    item["tp1_hit"] = True
                    item["status"] = "TP1_HIT"
                    events.append({
                        "alert_id": alert_id,
                        "event": "TP1_HIT",
                        "price": current_price,
                        "message": f"🎯 Take Profit 1 hit for {symbol} at {current_price:.2f}! Partial scale-out."
                    })
                    try:
                        from app.learning.feedback_engine import feedback_engine
                        feedback_engine.record_trade_completion(
                            alert_id=alert_id, symbol=symbol, direction="BUY",
                            entry_price=signal.entry_price, exit_price=current_price,
                            stop_loss=sl, take_profit=tp1, result="WIN_TP1", r_multiple=1.0,
                            confidence_score=signal.confidence_score
                        )
                    except Exception:
                        pass

                # Take Profit 2 Hit
                elif current_price >= tp2 and not item["tp2_hit"]:
                    item["tp2_hit"] = True
                    item["status"] = "TP2_HIT"
                    events.append({
                        "alert_id": alert_id,
                        "event": "TP2_HIT",
                        "price": current_price,
                        "message": f"🏆 Take Profit 2 hit for {symbol} at {current_price:.2f}! Full trade closed."
                    })
                    await paper_broker.close_position(alert_id, current_price)
                    try:
                        from app.learning.feedback_engine import feedback_engine
                        feedback_engine.record_trade_completion(
                            alert_id=alert_id, symbol=symbol, direction="BUY",
                            entry_price=signal.entry_price, exit_price=current_price,
                            stop_loss=sl, take_profit=tp2, result="WIN_TP2", r_multiple=signal.risk_reward_ratio,
                            confidence_score=signal.confidence_score
                        )
                    except Exception:
                        pass

            elif direction == "SELL" or direction == "short":
                # Stop Loss Hit
                if current_price >= sl and not item["sl_hit"]:
                    item["sl_hit"] = True
                    item["status"] = "SL_HIT"
                    events.append({
                        "alert_id": alert_id,
                        "event": "SL_HIT",
                        "price": current_price,
                        "message": f"🛑 Stop Loss hit for {symbol} short at {current_price:.2f}"
                    })
                    await paper_broker.close_position(alert_id, current_price)
                    try:
                        from app.learning.feedback_engine import feedback_engine
                        feedback_engine.record_trade_completion(
                            alert_id=alert_id, symbol=symbol, direction="SELL",
                            entry_price=signal.entry_price, exit_price=current_price,
                            stop_loss=sl, take_profit=tp2, result="LOSS_SL", r_multiple=-1.0,
                            confidence_score=signal.confidence_score
                        )
                    except Exception:
                        pass

                # Take Profit 1 Hit
                elif current_price <= tp1 and not item["tp1_hit"]:
                    item["tp1_hit"] = True
                    item["status"] = "TP1_HIT"
                    events.append({
                        "alert_id": alert_id,
                        "event": "TP1_HIT",
                        "price": current_price,
                        "message": f"🎯 Take Profit 1 hit for {symbol} short at {current_price:.2f}!"
                    })
                    try:
                        from app.learning.feedback_engine import feedback_engine
                        feedback_engine.record_trade_completion(
                            alert_id=alert_id, symbol=symbol, direction="SELL",
                            entry_price=signal.entry_price, exit_price=current_price,
                            stop_loss=sl, take_profit=tp1, result="WIN_TP1", r_multiple=1.0,
                            confidence_score=signal.confidence_score
                        )
                    except Exception:
                        pass

                # Take Profit 2 Hit
                elif current_price <= tp2 and not item["tp2_hit"]:
                    item["tp2_hit"] = True
                    item["status"] = "TP2_HIT"
                    events.append({
                        "alert_id": alert_id,
                        "event": "TP2_HIT",
                        "price": current_price,
                        "message": f"🏆 Take Profit 2 hit for {symbol} short at {current_price:.2f}!"
                    })
                    await paper_broker.close_position(alert_id, current_price)
                    try:
                        from app.learning.feedback_engine import feedback_engine
                        feedback_engine.record_trade_completion(
                            alert_id=alert_id, symbol=symbol, direction="SELL",
                            entry_price=signal.entry_price, exit_price=current_price,
                            stop_loss=sl, take_profit=tp2, result="WIN_TP2", r_multiple=signal.risk_reward_ratio,
                            confidence_score=signal.confidence_score
                        )
                    except Exception:
                        pass

        return events

state_machine = SignalStateMachine()
