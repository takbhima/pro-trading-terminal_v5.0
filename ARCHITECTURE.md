# Pro Trading Terminal — Refactored Architecture

## 🏗️ Design Principles

This refactored system follows:
- **SOLID Principles** (Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion)
- **DRY** (Don't Repeat Yourself) — Common logic extracted to utilities
- **KISS** (Keep It Simple, Stupid) — Clear, minimal, focused modules
- **Design Patterns**:
  - **Strategy Pattern** — Interchangeable trading strategies
  - **Factory Pattern** — Creating strategies, indicators, data sources
  - **Observer Pattern** — WebSocket events and signal broadcasts
  - **Dependency Injection** — Loose coupling between modules
  - **Repository Pattern** — Data persistence abstraction

---

## 📁 Project Structure

```
pro-trading-refactored/
├── backend/
│   ├── config/                          # Configuration & constants
│   │   ├── __init__.py
│   │   ├── settings.py                  # App config (timeframes, markets, etc.)
│   │   └── constants.py                 # Magic numbers, enums
│   │
│   ├── core/                            # Core domain logic (no external deps)
│   │   ├── __init__.py
│   │   ├── market.py                    # Market & trading hours definitions
│   │   ├── candle.py                    # Candle/OHLCV data model
│   │   ├── signal.py                    # Trade signal model
│   │   ├── trade.py                     # Trade lifecycle model
│   │   └── position.py                  # Position & risk models
│   │
│   ├── domain/                          # Business logic (trading strategies, indicators)
│   │   ├── __init__.py
│   │   ├── indicators/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # Abstract indicator interface
│   │   │   ├── moving_average.py        # EMA, SMA
│   │   │   ├── momentum.py              # RSI, MACD
│   │   │   ├── volatility.py            # ATR, Bollinger Bands
│   │   │   ├── trend.py                 # Supertrend, ADX
│   │   │   └── factory.py               # Indicator factory
│   │   │
│   │   ├── strategies/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # Abstract strategy interface
│   │   │   ├── pro_mtf.py               # Strategy: Pro MTF
│   │   │   ├── vwap_ema.py              # Strategy: VWAP + EMA
│   │   │   ├── rsi_reversal.py          # Strategy: RSI Reversal
│   │   │   ├── bollinger_breakout.py    # Strategy: Bollinger
│   │   │   ├── macd_crossover.py        # Strategy: MACD
│   │   │   ├── supertrend_scalper.py    # Strategy: ST Scalper
│   │   │   ├── registry.py              # Strategy registry & factory
│   │   │   └── helpers.py               # Common strategy logic (signal building)
│   │   │
│   │   └── analysis/
│   │       ├── __init__.py
│   │       ├── predictor.py             # Technical + sentiment prediction
│   │       ├── news_analyzer.py         # News sentiment analysis
│   │       └── confidence_calculator.py # Confidence scoring
│   │
│   ├── infrastructure/                  # Data fetching & external integrations
│   │   ├── __init__.py
│   │   ├── data_provider.py             # Abstract data provider interface
│   │   ├── yfinance_provider.py         # yfinance implementation
│   │   ├── cache.py                     # Data caching layer
│   │   ├── news_provider.py             # Abstract news provider
│   │   ├── yfinance_news.py             # yfinance news implementation
│   │   ├── rss_news.py                  # RSS feed news implementation
│   │   └── provider_factory.py          # Factory for providers
│   │
│   ├── services/                        # Business services (high-level)
│   │   ├── __init__.py
│   │   ├── market_service.py            # Market hours, open markets checking
│   │   ├── data_service.py              # Fetch candles, apply indicators
│   │   ├── strategy_service.py          # Run strategies, generate signals
│   │   ├── trade_service.py             # Trade management, exits
│   │   ├── news_service.py              # Fetch & analyze news
│   │   ├── prediction_service.py        # Generate predictions
│   │   ├── watchlist_service.py         # Watchlist persistence & queries
│   │   └── event_bus.py                 # Event publishing (Observer)
│   │
│   ├── utils/                           # Utilities & helpers
│   │   ├── __init__.py
│   │   ├── time_utils.py                # Timezone, timestamp conversions
│   │   ├── math_utils.py                # Rounding, formatting
│   │   ├── logger.py                    # Structured logging
│   │   └── retry.py                     # Retry logic with exponential backoff
│   │
│   ├── api/                             # FastAPI routes
│   │   ├── __init__.py
│   │   ├── main.py                      # FastAPI app setup
│   │   ├── websocket_handler.py         # WebSocket logic (completely isolated)
│   │   ├── rest_routes.py               # REST endpoints
│   │   └── dependencies.py              # FastAPI dependency injection
│   │
│   └── __init__.py
│
├── frontend/
│   └── index.html                       # Single-file UI (Lightweight Charts v4)
│
├── tests/
│   ├── __init__.py
│   ├── unit/                            # Unit tests per module
│   ├── integration/                     # Integration tests
│   └── fixtures/                        # Test data
│
├── requirements.txt
├── ARCHITECTURE.md                      # This file
├── README.md
└── main.py                              # Entry point
```

---

## 🎯 Design Patterns Used

### 1. **Strategy Pattern** (Strategies)
- **Purpose**: Make strategies interchangeable
- **Implementation**: 
  - `BaseStrategy` abstract class
  - Each strategy (ProMTF, VWAP, RSI, etc.) extends it
  - `StrategyRegistry` factory for dynamic strategy loading
- **Benefit**: Adding new strategies requires only creating a new class; no main.py changes

### 2. **Factory Pattern** (Indicators, Strategies, Providers)
- **IndicatorFactory**: Create indicators by name (`ema`, `rsi`, `atr`)
- **StrategyRegistry**: Create strategies by key (`pro_mtf`, `vwap_ema`)
- **ProviderFactory**: Create data providers (yfinance, mock, cache)
- **Benefit**: Centralized object creation; easy to swap implementations

### 3. **Observer Pattern** (Event Bus)
- **Purpose**: Decouple signal generation from UI broadcasting
- **Implementation**:
  - `EventBus` acts as a central event broker
  - Services publish events (`signal_generated`, `trade_opened`, `trade_closed`)
  - WebSocket handler subscribes to events
- **Benefit**: Services don't know about WebSocket; can be tested independently

### 4. **Repository Pattern** (Data Persistence)
- **Purpose**: Abstract data storage (JSON, DB, memory)
- **Implementation**:
  - `WatchlistRepository` interface
  - `JsonWatchlistRepository` implementation
  - Easy to swap with `DatabaseWatchlistRepository` later
- **Benefit**: Storage implementation is pluggable

### 5. **Dependency Injection**
- **Purpose**: Decouple components
- **Implementation**: 
  - Services accept dependencies via constructor
  - FastAPI's `Depends()` for injecting services
- **Benefit**: Easy to test with mock dependencies

### 6. **Template Method Pattern** (BaseStrategy, BaseIndicator)
- **Purpose**: Define algorithm skeleton, let subclasses fill in details
- **Implementation**: 
  - `BaseStrategy.run()` → subclass implements `generate_signals()`
  - Common signal building logic in `BaseStrategy`
- **Benefit**: Consistent behavior across all strategies

---

## 🔄 Data Flow

### WebSocket Real-Time Tick Flow
```
1. WebSocket client sends: {"type": "subscribe", "symbol": "BTC-USD", "interval": "5m"}
   ↓
2. WebSocket handler calls: data_service.subscribe(symbol, interval)
   ↓
3. Every 5s: price_updater fetches yfinance.Ticker(symbol).fast_info
   ↓
4. bar_state_machine.update(price) → updates H/L/C of current bar
   ↓
5. event_bus.publish("price_tick", {symbol, price, bar, live_pnl})
   ↓
6. WebSocket handler sends to all clients: {"type": "tick", ...}
   ↓
7. Browser Lightweight Charts updates candle in real-time
```

### Signal Generation Flow
```
1. Every 60s: strategy_service.scan_watchlist()
   ↓
2. For each symbol:
   a) data_service.get_candles(symbol, interval) → DataFrame
   b) data_service.apply_indicators(df) → adds EMA, RSI, ATR, etc.
   c) strategy.run(df) → returns signals list
   ↓
3. If new signal detected:
   a) signal_builder.build_full_signal(signal_dict)
   b) event_bus.publish("signal_generated", signal)
   c) trade_service.open_trade(signal) → creates trade
   ↓
4. WebSocket broadcasts to all clients
```

### Trade Exit Flow
```
1. Every 5s (with price tick): trade_service.check_exits(symbol, current_price)
   ↓
2. For each active trade:
   a) Check target hit (price ≥ TP for BUY, ≤ TP for SELL)
   b) Check stop loss
   c) Check time-based exit
   d) Check EOD exit
   ↓
3. If any condition met:
   a) trade_service.close_trade(symbol, exit_price, reason)
   b) event_bus.publish("trade_closed", exit_event)
   c) WebSocket broadcasts to all clients
```

---

## 📦 Module Responsibilities

| Module | Responsibility | Depends On |
|--------|----------------|-----------|
| `core.candle` | OHLCV data model | Nothing |
| `core.signal` | Trade signal model | Nothing |
| `core.trade` | Trade lifecycle | core.signal, core.position |
| `domain.indicators` | Technical calculations | pandas, numpy |
| `domain.strategies` | Strategy logic | domain.indicators, core.signal |
| `domain.analysis` | Prediction logic | domain.indicators, infrastructure.news |
| `infrastructure.providers` | External data fetching | yfinance, RSS, HTTP |
| `services.data_service` | High-level data ops | infrastructure.providers, domain.indicators |
| `services.strategy_service` | Strategy execution | domain.strategies, services.data_service |
| `services.trade_service` | Trade management | core.trade, services.watchlist_service |
| `api.routes` | HTTP endpoints | All services |
| `api.websocket_handler` | WebSocket logic | All services, event_bus |

---

## 🧪 Testing Strategy

### Unit Tests
- Test each indicator independently (EMA, RSI, ATR)
- Test each strategy with mock data
- Test signal building logic
- No external API calls

### Integration Tests
- Test data_service with real yfinance
- Test strategy_service end-to-end
- Test trade_service lifecycle
- Test event broadcasting

### Fixtures
- Sample OHLCV data (BTC, NIFTY, etc.)
- Mock signals
- Predefined trade scenarios

---

## 🚀 Extensibility

### Adding a New Strategy
```python
# 1. Create new file: backend/domain/strategies/my_new_strategy.py
from backend.domain.strategies.base import BaseStrategy

class MyNewStrategy(BaseStrategy):
    def generate_signals(self, df):
        # Your logic here
        pass

# 2. Register in backend/domain/strategies/registry.py
STRATEGY_REGISTRY['my_new_strategy'] = {
    'class': MyNewStrategy,
    'name': 'My Strategy',
    'description': '...',
}

# 3. Done! ✓ No changes to main.py needed
```

### Adding a New Indicator
```python
# 1. Create new file: backend/domain/indicators/my_indicator.py
from backend.domain.indicators.base import BaseIndicator

class MyIndicator(BaseIndicator):
    def calculate(self, series, params):
        # Your logic
        pass

# 2. Register in factory
IndicatorFactory.register('my_indicator', MyIndicator)

# 3. Use in any strategy or analysis
```

### Adding a New Data Source
```python
# 1. Create: backend/infrastructure/my_provider.py
from backend.infrastructure.data_provider import BaseDataProvider

class MyDataProvider(BaseDataProvider):
    def fetch_candles(self, symbol, interval, period):
        # Your logic
        pass

# 2. Update factory
provider = ProviderFactory.create('my_provider', config)

# 3. Inject into data_service
data_service = DataService(provider)
```

---

## 🔒 SOLID Principle Adherence

### Single Responsibility
- Each module has one reason to change
- E.g., `ema_indicator.py` only calculates EMA; doesn't fetch data or build signals

### Open/Closed
- Open for extension (create new Strategy subclass)
- Closed for modification (don't edit BaseStrategy)

### Liskov Substitution
- Any Strategy can replace BaseStrategy
- Any DataProvider can replace yfinance_provider

### Interface Segregation
- BaseStrategy defines only required methods
- DataProvider interface is minimal
- Services accept only what they need

### Dependency Inversion
- Services depend on abstractions (BaseStrategy, DataProvider)
- Not on concrete implementations

---

## 📊 Performance & Scaling

### Caching
- Candle data cached (configurable TTL)
- Indicator calculations cached
- News cached per symbol per interval

### Async Operations
- WebSocket handlers are non-blocking
- Data fetching uses asyncio
- Trade scanning in background tasks

### Database-Ready
- Current: JSON file storage (watchlist)
- Future: Easy swap to SQLAlchemy (Repository pattern)
- Indicator calculation results can be cached in Redis

---

## 🔗 Dependencies Graph

```
main.py
  ├── api.main (FastAPI setup)
  │   ├── api.websocket_handler
  │   │   ├── services.data_service
  │   │   ├── services.strategy_service
  │   │   ├── services.trade_service
  │   │   ├── services.event_bus
  │   │   └── services.market_service
  │   │
  │   └── api.rest_routes
  │       ├── services.data_service
  │       ├── services.strategy_service
  │       ├── services.news_service
  │       └── services.watchlist_service
  │
  services.*
    ├── infrastructure.providers
    │   └── (external APIs: yfinance, RSS)
    │
    └── domain.*
        ├── indicators
        └── strategies
```

---

## 🛠️ Migration Path from Old to New

| Old Module | New Location | Notes |
|----------|----------|-------|
| `data_fetcher.py` | `infrastructure/yfinance_provider.py` | Now pluggable |
| `indicators.py` | `domain/indicators/` | Split by category |
| `strategies.py` | `domain/strategies/` | Each strategy is a file |
| `trade_manager.py` | `services/trade_service.py` | Added state machine |
| `news_fetcher.py` | `infrastructure/news/` | Split by source |
| `predictor.py` | `services/prediction_service.py` | Cleaner separation |
| `watchlist_store.py` | `services/watchlist_service.py` | Repository pattern |
| `main.py` | `api/main.py` + `api/websocket_handler.py` | Separated concerns |

