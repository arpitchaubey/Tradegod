# Prompt: Improve TradeGod AI Signal Accuracy

Paste this into Claude Code (or your coding assistant of choice) inside the TradeGod project root so it has access to the actual files.

---

## Context

I have a trading bot called TradeGod (FastAPI backend + Next.js dashboard, SQLite DB at `tradegod.db`). It ingests XAU/USD OHLCV candles from Twelve Data (with Yahoo Finance and synthetic-data fallback), evaluates a 5-rule deterministic strategy engine across 1H/15M/5M timeframes, and fires BUY/SELL signals via Telegram when ALL rules pass.

Current rule set:
1. Trend (1H): EMA20 > EMA50
2. Setup (5M): EMA20 > EMA50
3. Momentum (5M): RSI > 55
4. Breakout: price breaks key resistance/support
5. Confirmation: candle closes above/below breakout level

I want to improve signal accuracy before any trade is suggested. Implement the following changes. Go file by file, show me the diffs, and don't change the Telegram/dashboard output format unless necessary.

## Required changes

### 1. Data integrity guard (highest priority)
- Add a `source` field (`twelvedata` / `yahoo` / `synthetic`) to every candle stored in `market_candles` and to whatever in-memory structure `CandleBufferManager` uses.
- In the signal evaluation path (`/api/signals/generate` and `/api/strategy/evaluate`), **hard-block** signal generation if any candle in the active evaluation window has `source == synthetic`. Return a clear error/status instead ("insufficient live data — signal suppressed") and log it to `execution_logs`.
- Log every fallback event (Twelve Data → Yahoo → synthetic) with timestamp and reason to `execution_logs`.

### 2. Confidence scoring instead of a rigid AND-gate
- Change `StrategyEngine.evaluate()` to compute a weighted confidence score (0–100%) across all 5 rules on every cycle, not just log a pass/fail when all 5 hit.
- Store this score on every row in `signal_logs`, including cycles where no trade fired, so I can see near-misses.
- Only broadcast to Telegram/dashboard when confidence crosses a configurable threshold (default: 100%, but expose it as a setting so I can experiment with e.g. 80%).
- Add a new endpoint `GET /api/signals/near-misses` returning recent high-confidence-but-not-fired evaluations.

### 3. Trend strength filter (ADX gate)
- Add ADX(14) calculation on the 1H timeframe.
- Add it as a precondition: only evaluate Rule 1 (EMA trend) when ADX > a configurable threshold (default 20). Below that, mark the market as "ranging" and suppress trend-following signals regardless of EMA state.
- Surface current ADX value and regime ("trending"/"ranging") on the dashboard chart-info endpoint.

### 4. Dynamic thresholds based on volatility regime
- Calculate ATR(14) on 1H and its rolling percentile rank over the last N periods (configurable, default 100).
- Scale the RSI momentum threshold (currently fixed at 55) up in low-volatility regimes and relax it slightly in high-volatility trending regimes — implement as a simple lookup/interpolation, not a black box.
- Use ATR (not a fixed pip/point value) for Stop Loss distance in `RiskManager`, if not already doing so.

### 5. Swing-based support/resistance instead of rolling min/max
- Replace (or add as an option) the current resistance/support detection with confirmed fractal/pivot detection (a local high/low confirmed by N candles on each side, configurable, default N=3).
- Rule 4 (breakout) should reference the nearest confirmed swing level, not a naive rolling high/low.

### 6. Stronger breakout confirmation (anti-fakeout)
- Change Rule 5 so confirmation requires EITHER:
  a) close beyond the breakout level by at least X × ATR (configurable, default 0.1), OR
  b) two consecutive candle closes beyond the level.
- Make this configurable per strategy, since the NLP strategy parser should be able to express it (e.g. "confirm breakout with 2 closes above resistance").

### 7. News/session filter
- Add a simple config-driven blackout window (start/end UTC times or a list of high-impact event timestamps I can populate manually or via a calendar API if one is easy to add) during which signal generation is suppressed.
- Tag each signal in `signal_logs` with the trading session it occurred in (Asian/London/New York) based on UTC time, for later analysis of which sessions perform best.

### 8. Backtest validation upgrade
- Check whether `/api/backtest/run` currently does a single in-sample pass. If so, add a walk-forward mode: split historical data into rolling train/test windows and report out-of-sample win rate, average R:R, and max drawdown per window, plus an aggregate.
- Return results in a structured JSON the dashboard can chart (equity curve, win rate over time, drawdown).

## Implementation notes
- Keep all new thresholds/parameters in a single config object or table (not hardcoded), so they're tunable without code changes.
- Add unit tests for the ADX gate, breakout confirmation logic, and synthetic-data block, since these are the parts most likely to silently break.
- After implementing, run the existing backtest across the same historical window as before and show me a before/after comparison (win rate, R:R, number of signals fired, number suppressed by each new filter).

## Deliverable
Show me:
1. Updated `StrategyEngine`, `CandleBufferManager`, and `RiskManager` code (diffs).
2. New/changed DB schema migrations.
3. New/changed API endpoints.
4. A before/after backtest comparison table.
