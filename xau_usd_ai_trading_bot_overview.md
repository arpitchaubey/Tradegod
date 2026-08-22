# XAU/USD AI Trading Signal Bot --- Project Overview

## 1. Project Goal

Build a trading-analysis bot focused initially on **XAU/USD (gold priced
in US dollars)** that:

-   receives live and historical market data;
-   analyzes multiple chart timeframes;
-   follows a user-defined trading strategy;
-   detects valid setups rather than guessing;
-   calculates entry, stop-loss (SL), take-profit (TP), risk/reward and
    optional position size;
-   sends structured alerts to Telegram;
-   supports backtesting and paper trading before live use;
-   can later be connected to a broker for automated execution, if
    legally and technically appropriate.

**Important:** The AI should explain and assist with analysis, but
deterministic strategy/risk rules should make the actual signal decision
wherever possible.

------------------------------------------------------------------------

## 2. High-Level Architecture

``` text
                 ┌──────────────────────────┐
                 │       MARKET DATA        │
                 │                          │
                 │ XAU/USD candles/prices   │
                 │ Historical + live        │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │      DATA PROCESSOR      │
                 │                          │
                 │ Clean/normalize candles  │
                 │ Validate timestamps       │
                 │ Store historical data     │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │   TECHNICAL ANALYSIS     │
                 │                          │
                 │ EMA/SMA, RSI, MACD       │
                 │ ATR, VWAP                 │
                 │ S/R, structure, breakout │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │     STRATEGY ENGINE      │
                 │                          │
                 │ User-defined rules        │
                 │ Entry conditions          │
                 │ Exit conditions           │
                 │ Confirmation rules        │
                 └────────────┬─────────────┘
                              │
                     Valid setup?
                       /          \
                     NO            YES
                     │              │
                     ▼              ▼
                  WAIT       ┌──────────────────┐
                             │   RISK ENGINE    │
                             │                  │
                             │ Entry            │
                             │ SL               │
                             │ TP1/TP2          │
                             │ R:R              │
                             │ Position size    │
                             └────────┬─────────┘
                                      │
                                      ▼
                             ┌──────────────────┐
                             │  AI EXPLANATION  │
                             │                  │
                             │ Why setup exists │
                             │ Market context    │
                             │ Confidence*       │
                             └────────┬─────────┘
                                      │
                                      ▼
                             ┌──────────────────┐
                             │     TELEGRAM     │
                             │                  │
                             │ BUY / SELL / WAIT│
                             │ Entry / SL / TP  │
                             └──────────────────┘

* "Confidence" should be treated as a rule-based score, not a guarantee.
```

------------------------------------------------------------------------

## 3. Recommended First Version

### Phase 1 --- Free development

Do **not** start with live automated trading.

Use a free/limited market-data source suitable for development and
historical testing. One candidate discussed for XAU/USD is Twelve Data,
subject to its current plan limits and terms.

Build:

1.  historical XAU/USD download;
2.  local database/files;
3.  candlestick chart;
4.  indicator calculations;
5.  strategy engine;
6.  backtesting;
7.  Telegram test alerts.

### Phase 2 --- Paper trading

The bot receives live market data and produces signals, but does not
place real orders.

### Phase 3 --- Live alerts

Telegram receives real-time XAU/USD signals.

### Phase 4 --- Optional broker execution

Only after extensive testing should broker order execution be
considered.

------------------------------------------------------------------------

# 4. Market Data

## Instrument

Initial instrument:

``` text
XAU/USD
```

This means the price of one troy ounce of gold quoted in US dollars.

### Important broker distinction

Different providers can have slightly different prices, spreads and
candle construction.

If the eventual trading account is with a broker such as OANDA, the
production system should ideally use the broker's own data/execution
environment so that the analyzed price and executable price are aligned
as closely as possible.

For development, a separate free/limited XAU/USD data provider can be
used.

------------------------------------------------------------------------

# 5. Chart Timeframes

The bot should support multiple timeframes.

Recommended initial configuration:

``` text
Higher timeframe:
1H

Setup timeframe:
15M

Entry timeframe:
5M

Optional execution refinement:
1M
```

Example:

``` text
1H  → determine broad trend
15M → identify structure and setup
5M  → confirm entry
1M  → optional precision entry
```

The timeframe configuration must be user-editable.

------------------------------------------------------------------------

# 6. Strategy Input

The user should be able to describe a strategy in plain English.

Example:

> Analyze XAU/USD on the 5-minute chart. Buy when price breaks
> resistance, the 20 EMA is above the 50 EMA, RSI is above 55, and the
> breakout candle closes above resistance. Use a 1:2 risk/reward ratio.

The AI Strategy Builder converts this into structured rules.

Example internal representation:

``` json
{
  "symbol": "XAUUSD",
  "timeframes": {
    "trend": "1h",
    "setup": "15m",
    "entry": "5m"
  },
  "direction": "long",
  "conditions": [
    "ema20 > ema50",
    "rsi > 55",
    "break_resistance",
    "candle_close_above_resistance"
  ],
  "risk_reward": 2
}
```

The AI should not silently invent missing rules. If a critical rule is
ambiguous, the system should mark it as requiring configuration.

------------------------------------------------------------------------

# 7. Strategy Engine

The strategy engine is the core decision-making layer.

It should evaluate deterministic rules such as:

``` text
Trend
Structure
Support/resistance
Indicator conditions
Breakout/retest
Candlestick confirmation
Trading session
Volatility
Spread
News filter (optional)
```

Example:

``` text
IF
  1H trend = bullish
AND
  15M market structure = bullish
AND
  5M price breaks resistance
AND
  5M candle closes above resistance
AND
  EMA20 > EMA50
AND
  RSI > 55
THEN
  LONG_SETUP = TRUE
ELSE
  LONG_SETUP = FALSE
```

------------------------------------------------------------------------

# 8. Technical Indicators

The first version can support:

-   EMA
-   SMA
-   RSI
-   MACD
-   ATR
-   VWAP
-   Bollinger Bands
-   Volume, where the data source provides meaningful volume
-   Previous high/low
-   Daily high/low
-   Session high/low

Advanced market-structure features can be added later:

-   Higher High / Higher Low
-   Lower High / Lower Low
-   Break of Structure (BOS)
-   Change of Character (CHOCH)
-   Liquidity sweep
-   Fair Value Gap (FVG)
-   Order blocks

Do not add every indicator initially. Start with only the indicators
required by the strategy.

------------------------------------------------------------------------

# 9. Entry Logic

The bot should be event-driven instead of checking for a new trade every
few seconds.

Bad design:

``` text
Every 5 seconds:
  "Should I BUY?"
```

Better design:

``` text
Market update
     ↓
New candle / price event
     ↓
Check setup
     ↓
If no setup → WAIT
     ↓
If setup appears → confirmation
     ↓
Calculate entry/SL/TP
     ↓
Send signal
```

For candle-close strategies:

``` text
Price approaches resistance
        ↓
Breakout occurs
        ↓
Wait for candle close
        ↓
Confirm strategy
        ↓
Generate signal
```

This reduces duplicate and noisy alerts.

------------------------------------------------------------------------

# 10. Entry Price

Entry should come from the strategy, not from an arbitrary AI guess.

Possible entry models:

### Market entry

``` text
BUY at current executable price
```

### Limit entry

``` text
BUY LIMIT at pullback level
```

### Breakout entry

``` text
BUY above breakout level
```

### Confirmation entry

``` text
Wait for candle close
Then enter on confirmation
```

The strategy configuration should specify which model is used.

------------------------------------------------------------------------

# 11. Stop Loss

SL should be rule-based.

Possible methods:

``` text
Structure-based:
SL below swing low

ATR-based:
SL = Entry - ATR × multiplier

Fixed distance:
SL = Entry - fixed points

Hybrid:
SL below structure with ATR minimum
```

For a long trade:

``` text
Entry
  |
  |
  |     TP
  |-----●
  |
  |     Entry
  |-----●
  |
  |     SL
  |-----●
```

------------------------------------------------------------------------

# 12. Take Profit

Supported methods:

``` text
Fixed R:R
Previous resistance
Previous swing high
ATR multiple
Multiple targets
```

Example:

``` text
Risk = 10 points

TP1 = 10 points  → 1R
TP2 = 20 points  → 2R
TP3 = 30 points  → 3R
```

The bot should support partial exits if the eventual execution system
supports them.

------------------------------------------------------------------------

# 13. Risk Management

Risk management must be independent from the AI explanation layer.

Example:

``` text
Account balance = ₹100,000
Risk per trade = 1%

Maximum money risk = ₹1,000
```

Position sizing should use the instrument's contract specifications and
broker rules.

Generic concept:

``` text
Position Size =
Maximum Money Risk / Monetary Loss Per Unit at SL
```

The exact formula depends on the broker's XAU/USD contract
specifications, quote precision, and account currency.

Safety controls should include:

``` text
Maximum risk per trade
Maximum daily loss
Maximum number of trades per day
Maximum consecutive losses
Maximum open positions
Maximum spread
Trading session filter
Kill switch
Pause/resume
```

------------------------------------------------------------------------

# 14. AI Layer

The AI should primarily do:

### Strategy translation

Plain English → structured rules.

### Market explanation

Explain why the deterministic engine produced a signal.

### Summary

Turn raw calculations into a human-readable Telegram message.

### Configuration assistance

Help the user define:

-   indicators;
-   timeframes;
-   entry conditions;
-   SL rules;
-   TP rules;
-   risk rules.

The AI should NOT be the only source of truth for:

-   entry price;
-   SL;
-   TP;
-   position size;
-   whether a trade is allowed.

Those should come from deterministic calculations.

------------------------------------------------------------------------

# 15. Telegram Bot

Telegram is the notification/control layer.

Example commands:

``` text
/start
/help
/status
/analyze XAUUSD
/strategy
/setrisk 1
/pause
/resume
/today
/backtest
```

Example signal:

``` text
🟢 XAU/USD BUY SETUP

Direction: BUY

Entry:
4xxx.xx – 4xxx.xx

Stop Loss:
4xxx.xx

Take Profit:
TP1: 4xxx.xx
TP2: 4xxx.xx

Risk/Reward:
1:2

Timeframe:
5M

Higher TF:
1H bullish

Setup:
Breakout + retest

Confirmation:
✓ EMA
✓ RSI
✓ Structure
✓ Candle close

Status:
CONFIRMED

⚠️ Educational/automated-system output; market conditions can change.
```

The bot should have an alert ID so that duplicate signals are not
repeatedly sent.

------------------------------------------------------------------------

# 16. Web Dashboard

A dashboard is optional but highly recommended.

Suggested layout:

``` text
┌────────────────────────────────────────────────────┐
│ XAU/USD                         Timeframe: 5M       │
├────────────────────────────────────────────────────┤
│                                                    │
│                   CANDLE CHART                     │
│                                                    │
│      Resistance ─────────────────────              │
│                         ↑                          │
│                    BREAKOUT                       │
│                         ↑                          │
│                  Entry ───────                    │
│                  TP    ───────                    │
│                  SL    ───────                    │
│                                                    │
├────────────────────────────────────────────────────┤
│ RSI                                                 │
├────────────────────────────────────────────────────┤
│ Strategy: Breakout                                │
│ Trend: Bullish                                    │
│ Signal: BUY                                       │
│ Risk/Reward: 1:2                                  │
└────────────────────────────────────────────────────┘
```

The dashboard should show:

-   live price;
-   candles;
-   indicators;
-   support/resistance;
-   entry;
-   SL;
-   TP;
-   current strategy state;
-   signal history;
-   backtest statistics.

------------------------------------------------------------------------

# 17. Database

Use PostgreSQL for the production system.

Possible tables:

``` text
users
strategies
strategy_versions
market_candles
market_ticks
indicators
signals
trades
risk_settings
telegram_users
backtests
backtest_trades
system_events
```

For a very early prototype, SQLite is sufficient.

------------------------------------------------------------------------

# 18. Recommended Technology Stack

## Backend

``` text
Python
FastAPI
```

## Data processing

``` text
Pandas
NumPy
```

## Technical analysis

``` text
pandas-ta or TA-Lib
Custom calculations where required
```

## Database

``` text
PostgreSQL
Redis
```

Redis is useful for real-time state, queues and duplicate-event
protection.

## Frontend

``` text
Next.js
React
TradingView Lightweight Charts
```

## Messaging

``` text
Telegram Bot API
```

## Deployment

``` text
Docker
Linux VPS / cloud server
```

------------------------------------------------------------------------

# 19. Suggested Folder Structure

``` text
xau-trading-bot/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── routes_market.py
│   │   ├── routes_strategy.py
│   │   ├── routes_signals.py
│   │   └── routes_backtest.py
│   │
│   ├── data/
│   │   ├── provider.py
│   │   ├── historical.py
│   │   ├── realtime.py
│   │   └── normalizer.py
│   │
│   ├── indicators/
│   │   ├── trend.py
│   │   ├── momentum.py
│   │   ├── volatility.py
│   │   └── structure.py
│   │
│   ├── strategy/
│   │   ├── engine.py
│   │   ├── parser.py
│   │   ├── conditions.py
│   │   └── schemas.py
│   │
│   ├── risk/
│   │   ├── manager.py
│   │   ├── position_size.py
│   │   └── limits.py
│   │
│   ├── signals/
│   │   ├── generator.py
│   │   ├── deduplicator.py
│   │   └── models.py
│   │
│   ├── ai/
│   │   ├── strategy_builder.py
│   │   └── explanation.py
│   │
│   ├── telegram/
│   │   ├── bot.py
│   │   ├── commands.py
│   │   └── formatter.py
│   │
│   ├── backtest/
│   │   ├── engine.py
│   │   ├── metrics.py
│   │   └── reports.py
│   │
│   └── database/
│       ├── models.py
│       └── connection.py
│
├── frontend/
│
├── tests/
│
├── scripts/
│
├── .env.example
├── docker-compose.yml
├── requirements.txt
└── README.md
```

------------------------------------------------------------------------

# 20. Environment Variables

Never hard-code secrets.

Example:

``` text
DATA_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

DATABASE_URL=

AI_API_KEY=

BROKER_API_KEY=
BROKER_ACCOUNT_ID=
```

Broker credentials should remain disabled until live execution is
intentionally enabled.

------------------------------------------------------------------------

# 21. Backtesting Flow

``` text
Historical XAU/USD
        ↓
Load candles
        ↓
Calculate indicators
        ↓
Run strategy rules candle-by-candle
        ↓
Generate hypothetical entry
        ↓
Calculate SL/TP
        ↓
Simulate trade
        ↓
Record result
        ↓
Calculate statistics
        ↓
Generate report
```

Backtest metrics:

``` text
Total trades
Win rate
Loss rate
Profit factor
Net return
Average R
Maximum drawdown
Average win
Average loss
Expectancy
Largest losing streak
Largest winning streak
Performance by session
Performance by timeframe
```

Avoid optimizing dozens of parameters until the backtest looks perfect.
That can create overfitting.

------------------------------------------------------------------------

# 22. Paper Trading Flow

``` text
Live XAU/USD
     ↓
Strategy engine
     ↓
Signal
     ↓
Paper order
     ↓
Track hypothetical entry
     ↓
Track SL/TP
     ↓
Record result
     ↓
Compare with backtest
```

Run paper trading long enough to observe real-world effects such as
spread, latency and changing volatility.

------------------------------------------------------------------------

# 23. Production Signal Flow

``` text
                 LIVE XAU/USD
                       │
                       ▼
              ┌────────────────┐
              │ Data Validator │
              └───────┬────────┘
                      ▼
              ┌────────────────┐
              │ Candle Builder │
              └───────┬────────┘
                      ▼
              ┌────────────────┐
              │ Multi-TF Data  │
              └───────┬────────┘
                      ▼
              ┌────────────────┐
              │ Indicators     │
              └───────┬────────┘
                      ▼
              ┌────────────────┐
              │ Strategy       │
              └───────┬────────┘
                      │
               Valid setup?
                /          \
              NO            YES
              │              │
             WAIT            ▼
                       Risk Engine
                            │
                            ▼
                     Entry/SL/TP
                            │
                            ▼
                       AI Summary
                            │
                            ▼
                         Telegram
```

------------------------------------------------------------------------

# 24. Signal State Machine

Use explicit states to avoid duplicate alerts.

``` text
WAITING
   ↓
WATCHING
   ↓
SETUP_DETECTED
   ↓
CONFIRMING
   ↓
CONFIRMED
   ↓
SIGNAL_SENT
   ↓
ACTIVE
   ├── TP HIT
   ├── SL HIT
   └── CANCELLED
   ↓
CLOSED
```

Example:

``` text
WAITING
→ price approaches resistance
→ WATCHING
→ breakout occurs
→ SETUP_DETECTED
→ candle closes
→ CONFIRMING
→ all rules pass
→ CONFIRMED
→ Telegram alert
→ SIGNAL_SENT
```

------------------------------------------------------------------------

# 25. Alert Deduplication

A signal should have a unique identifier.

Example:

``` text
XAUUSD-5M-BUY-20260822-143500
```

Before sending:

``` text
Does this setup already have an alert ID?
    YES → do not resend
    NO  → create alert and send
```

------------------------------------------------------------------------

# 26. Failure Handling

The bot must fail safely.

Examples:

### Market-data failure

``` text
No valid data
→ do not generate signal
→ log error
→ notify administrator
```

### API timeout

``` text
Retry
→ if repeated failure
→ enter safe state
```

### Missing candle

``` text
Do not make a decision using incomplete data.
```

### Telegram failure

``` text
Store signal
→ retry delivery
→ avoid creating another trade signal
```

### Abnormal spread

``` text
Spread > configured maximum
→ NO TRADE
```

------------------------------------------------------------------------

# 27. Security

Never expose:

``` text
API keys
Telegram bot tokens
Broker credentials
Database passwords
AI API keys
```

Use:

``` text
.env
Secret manager
Encrypted deployment secrets
```

Telegram commands that change risk settings should require
authentication.

------------------------------------------------------------------------

# 28. Free Prototype Plan

The initial target should be:

``` text
₹0 development prototype
```

### Build order

``` text
1. Get historical XAU/USD data
2. Store candles
3. Display candlestick chart
4. Calculate indicators
5. Implement one strategy
6. Build backtester
7. Generate signals
8. Create Telegram bot
9. Connect live/streaming data when available
10. Paper trade
11. Validate
12. Consider paid/broker data only when needed
```

Do not pay for infrastructure or broker execution before the strategy
engine works.

------------------------------------------------------------------------

# 29. Data Provider Strategy

## Development

Use a free/limited provider that supplies XAU/USD historical data and,
where the plan permits, intraday/live data.

Potential provider:

``` text
Twelve Data
```

Always verify its current pricing, quotas, supported intervals, XAU/USD
availability and commercial/API terms before relying on it for
production.

## Production

Prefer the data source associated with the broker/execution venue that
you actually intend to trade.

If using OANDA later:

``` text
OANDA market data
        ↓
Strategy
        ↓
Signal
        ↓
OANDA execution
```

This minimizes differences between analyzed and executable prices.

------------------------------------------------------------------------

# 30. Important Difference: Chart vs Data

The bot does not need to "access a chart" as a screenshot.

It needs:

``` text
OHLC candles
Bid/Ask
Timestamp
Volume, if meaningful/available
Live price updates
```

The bot can create its own chart from those values.

Conceptually:

``` text
Market API
    ↓
JSON price/candle data
    ↓
Python
    ↓
DataFrame
    ↓
Indicators
    ↓
Strategy
    ↓
Chart + Telegram
```

------------------------------------------------------------------------

# 31. Example Candle Data

Conceptually:

``` text
timestamp           open     high     low      close
2026-08-22 14:00    3345.2   3348.6   3343.8   3347.9
2026-08-22 14:05    3347.9   3351.2   3346.5   3350.8
2026-08-22 14:10    3350.8   3353.4   3349.7   3352.1
```

The exact price values above are examples only, not a live market quote.

------------------------------------------------------------------------

# 32. User Configuration

Create a configuration screen/file:

``` text
Symbol:
XAU/USD

Trend timeframe:
1H

Setup timeframe:
15M

Entry timeframe:
5M

Strategy:
Breakout + Retest

Risk per trade:
1%

Maximum daily loss:
2%

Maximum trades/day:
3

Risk/Reward:
1:2

Minimum confirmation:
All conditions

Trading session:
User configured

Telegram:
Enabled
```

------------------------------------------------------------------------

# 33. Example Strategy Definition

``` text
Strategy Name:
Gold Breakout Strategy

Instrument:
XAU/USD

Trend:
1H EMA20 > EMA50

Setup:
15M resistance identified

Entry:
5M closes above resistance

Confirmation:
RSI > 55
EMA20 > EMA50

Stop:
Below most recent 5M swing low

Take Profit:
2R

Risk:
1% account balance

Trade:
BUY only

If any required condition fails:
NO TRADE
```

------------------------------------------------------------------------

# 34. Example Telegram Messages

## Setup detected

``` text
👀 XAU/USD SETUP WATCH

Potential BUY setup detected.

Resistance: XXXX.XX
Current price: XXXX.XX

Waiting for:
✓ 5M candle close above resistance
✓ RSI confirmation
✓ EMA confirmation

Status: WAITING
```

## Confirmed signal

``` text
🟢 XAU/USD BUY

Entry: XXXX.XX
SL: XXXX.XX

TP1: XXXX.XX
TP2: XXXX.XX

Risk/Reward: 1:2

Trend: Bullish
Timeframe: 5M

Confirmation:
✓ Breakout
✓ EMA
✓ RSI
✓ Structure

Signal ID:
XAUUSD-5M-BUY-XXXXXXXX
```

## No trade

``` text
⚪ XAU/USD — NO TRADE

Reason:
Breakout occurred, but candle confirmation failed.

Status:
WAITING
```

------------------------------------------------------------------------

# 35. AI Confidence Score

If a confidence score is displayed, it should be a transparent scoring
model.

Example:

``` text
Trend alignment       +20
Structure              +20
Breakout               +20
Momentum               +15
Volume                 +10
Risk/reward             +15
----------------------------
Total                  100
```

Then:

``` text
80–100 → Strong setup
65–79  → Valid but weaker
50–64  → Watch
<50    → No trade
```

This is not a probability of profit unless statistically calibrated and
validated.

------------------------------------------------------------------------

# 36. News and Market Conditions

Optional later features:

``` text
Major economic news
US CPI
FOMC
NFP
Interest-rate decisions
Dollar index
Treasury yields
```

For gold, macroeconomic conditions can materially affect volatility.

A news filter can be:

``` text
High-impact event within 15 minutes?
    YES → block new trades
    NO  → normal strategy
```

This should be configurable.

------------------------------------------------------------------------

# 37. Observability

Log every important event:

``` text
data_received
candle_created
indicator_calculated
setup_detected
signal_confirmed
signal_rejected
telegram_sent
telegram_failed
risk_blocked
backtest_completed
system_error
```

This makes debugging possible.

------------------------------------------------------------------------

# 38. Testing Strategy

Write tests for:

``` text
Indicator calculations
Strategy conditions
Entry calculation
SL calculation
TP calculation
Risk calculation
Duplicate prevention
Candle-close behavior
Telegram formatting
Backtest results
API failure behavior
```

Also test edge cases:

``` text
Missing candles
Duplicate candles
Extreme volatility
Large spread
API outage
Market closed
Invalid strategy
Invalid risk settings
```

------------------------------------------------------------------------

# 39. Development Milestones

## Milestone 1

``` text
XAU/USD historical data
+
basic chart
```

## Milestone 2

``` text
Indicators
+
one deterministic strategy
```

## Milestone 3

``` text
Backtesting
+
performance report
```

## Milestone 4

``` text
Telegram alerts
```

## Milestone 5

``` text
Live market data
+
paper trading
```

## Milestone 6

``` text
Dashboard
+
strategy builder
```

## Milestone 7

``` text
Broker integration
```

Automated execution should be the final stage, not the starting point.

------------------------------------------------------------------------

# 40. Final Recommended Architecture

``` text
                         USER
                          │
                          ▼
                ┌─────────────────────┐
                │ Strategy Builder    │
                │ Natural Language    │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Strategy Definition │
                │ Structured Rules    │
                └──────────┬──────────┘
                           │
                           │
XAU/USD DATA ──────────────┤
                           ▼
                ┌─────────────────────┐
                │ Data Engine         │
                │ Historical + Live   │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Indicator Engine    │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Strategy Engine     │
                └──────────┬──────────┘
                           │
                  ┌────────┴────────┐
                  │                 │
                NO TRADE           SETUP
                  │                 │
                WAIT                ▼
                          ┌──────────────────┐
                          │ Risk Engine      │
                          │ Entry / SL / TP  │
                          └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │ Signal Manager   │
                          └───────┬──────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
             ┌─────────────┐             ┌─────────────┐
             │ AI Explain  │             │ Backtester  │
             └──────┬──────┘             └─────────────┘
                    │
                    ▼
             ┌─────────────┐
             │  Telegram   │
             └─────────────┘

                    OPTIONAL
                       │
                       ▼
              ┌─────────────────┐
              │ Broker Execution │
              │  (Final Stage)   │
              └─────────────────┘
```

------------------------------------------------------------------------

# 41. Golden Rules for the Project

1.  **Do not let an LLM randomly predict trades.**
2.  **Convert the user's strategy into explicit rules.**
3.  **Use deterministic calculations for entry, SL, TP and risk.**
4.  **Backtest before live signals.**
5.  **Paper trade before real execution.**
6.  **Use the same/similar data source as the eventual execution venue
    when going live.**
7.  **Never expose API credentials.**
8.  **Prevent duplicate alerts.**
9.  **Fail safely when market data is missing or abnormal.**
10. **Keep broker execution separate from the analysis engine.**
11. **Do not assume a high backtest result will continue in live
    markets.**
12. **Treat Telegram alerts as signals generated by a system, not
    guaranteed outcomes.**
13. **Check Indian regulatory, tax and broker/exchange requirements
    before live trading.**
14. **Start with XAU/USD only; add other instruments after the
    architecture is stable.**

------------------------------------------------------------------------

# 42. First Build Target

The first working prototype should do exactly this:

``` text
FREE / LIMITED DATA
       ↓
XAU/USD historical candles
       ↓
5M chart
       ↓
EMA20
EMA50
RSI
Support/Resistance
       ↓
User strategy
       ↓
BUY / SELL / NO TRADE
       ↓
Entry
SL
TP
R:R
       ↓
Telegram
       ↓
Backtest report
```

Once this works correctly, add live data.

Once live paper trading works correctly, evaluate whether a paid data
feed or broker API is justified.

------------------------------------------------------------------------

# 43. Project Success Criteria

The project is considered technically ready for paper trading when:

-   historical data loads reliably;
-   candles are correctly timestamped;
-   indicators match a trusted reference;
-   the strategy produces deterministic results;
-   backtests are reproducible;
-   duplicate signals are prevented;
-   SL/TP calculations are reproducible;
-   Telegram delivery works;
-   data/API failures are handled safely;
-   logs allow every signal to be reconstructed;
-   paper-trading results can be compared against backtest results.

It is **not** considered ready for live execution merely because the
strategy has a high backtest win rate.

------------------------------------------------------------------------

## End Goal

The finished system should let the user say:

> "Analyze XAU/USD on 5 minutes using my strategy."

The system then:

``` text
Gets XAU/USD data
       ↓
Analyzes higher timeframes
       ↓
Analyzes current 5M structure
       ↓
Checks the user's strategy
       ↓
Waits for confirmation
       ↓
Calculates Entry
       ↓
Calculates SL
       ↓
Calculates TP
       ↓
Calculates Risk/Reward
       ↓
Checks risk limits
       ↓
Sends Telegram alert
       ↓
Tracks the setup
       ↓
Records the result
       ↓
Uses the result for performance analysis
```

This is the recommended blueprint for building the project safely and
incrementally.
