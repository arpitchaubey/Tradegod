from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class DBMarketCandle(Base):
    __tablename__ = "market_candles"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True)
    timeframe = Column(String(10), index=True)
    timestamp = Column(DateTime, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float, default=0.0)
    source = Column(String(20), default="twelvedata", index=True)

class DBSignalLog(Base):
    __tablename__ = "signal_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1, index=True)
    alert_id = Column(String(100), index=True)
    symbol = Column(String(20), index=True)
    direction = Column(String(10))
    entry_price = Column(Float)
    stop_loss = Column(Float)
    take_profit_1 = Column(Float)
    take_profit_2 = Column(Float)
    risk_reward_ratio = Column(Float)
    position_size_lots = Column(Float)
    confidence_score = Column(Integer)
    status = Column(String(30), default="CONFIRMED") # CONFIRMED, NEAR_MISS, SUPPRESSED_SYNTHETIC, NO_TRADE
    session = Column(String(20), default="LONDON") # ASIAN, LONDON, NEW_YORK, OFF_HOURS
    confirmations_json = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class DBBacktestRun(Base):
    __tablename__ = "backtest_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1, index=True)
    symbol = Column(String(20), index=True)
    timeframe = Column(String(10))
    total_trades = Column(Integer)
    win_rate_percent = Column(Float)
    profit_factor = Column(Float)
    net_profit = Column(Float)
    max_drawdown_percent = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class DBPosition(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1, index=True)
    position_id = Column(String(100), index=True)
    alert_id = Column(String(100), index=True)
    symbol = Column(String(20), index=True)
    direction = Column(String(10))
    entry_price = Column(Float)
    current_price = Column(Float)
    stop_loss = Column(Float)
    take_profit_1 = Column(Float)
    take_profit_2 = Column(Float)
    size_lots = Column(Float)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    status = Column(String(20), default="OPEN")  # OPEN, TP1_HIT, CLOSED, CANCELLED
    mode = Column(String(20), default="PAPER_TRADING")  # PAPER_TRADING, OANDA, MT5
    opened_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime, nullable=True)

class DBStrategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1, index=True)
    name = Column(String(100), index=True)
    description = Column(Text)
    raw_prompt = Column(Text)
    rules_json = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class DBBrokerAccount(Base):
    __tablename__ = "broker_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1, index=True)
    mode = Column(String(20), primary_key=False, index=True)
    balance = Column(Float, default=10000.0)
    equity = Column(Float, default=10000.0)
    margin_used = Column(Float, default=0.0)
    free_margin = Column(Float, default=10000.0)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class DBExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1, index=True)
    event_type = Column(String(50), index=True)
    message = Column(Text)
    details_json = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class DBUser(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    avatar_url = Column(String(255), nullable=True)
    plan_tier = Column(String(30), default="PRO")  # PRO, ENTERPRISE, FREE
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

