"""
Pro Trading Terminal v4.0 - FastAPI Backend
Main entry point for the trading terminal application
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import json
from datetime import datetime
from pathlib import Path
import asyncio

# Import backend modules
from backend.config.settings import Settings
from backend.domain.strategies import StrategyRegistry
from backend.domain.indicators import apply_all_indicators
from backend.core.candle import Candle
import pandas as pd

# Create FastAPI app
app = FastAPI(
    title="Pro Trading Terminal v4.0",
    description="Professional trading system with 6 strategies",
    version="4.0.0"
)

# Add CORS middleware (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════════════════
# WEBSOCKET CONNECTION MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class ConnectionManager:
    def __init__(self):
        self.active_connections: list = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            if connection in self.active_connections:
                self.active_connections.remove(connection)

manager = ConnectionManager()

# ═══════════════════════════════════════════════════════════════════════════
# WEBSOCKET ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "subscribe":
                symbol = message.get("symbol", "BTC-USD")
                interval = message.get("interval", "5m")
                
                # Send status message
                status_msg = {
                    "type": "status",
                    "open_markets": ["US", "Crypto"],
                    "any_open": True
                }
                await websocket.send_json(status_msg)
                
            elif message.get("type") == "ping":
                # Respond to ping
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# ═══════════════════════════════════════════════════════════════════════════
# REST API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/test")
def test_endpoint():
    """Test endpoint to verify backend is running"""
    return {
        "status": "ok",
        "message": "Pro Trading Terminal Backend is Running!",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/status")
def get_status():
    """Get system status"""
    try:
        import yfinance as yf
        ticker = yf.Ticker("BTC-USD")
        price = ticker.fast_info.get("lastPrice", 0)
        return {
            "status": "ok",
            "backend": "running",
            "frontend": "ready",
            "btc_price": price,
            "timestamp": datetime.utcnow().isoformat(),
            "data_source": "yfinance",
            "open_markets": ["US", "Crypto"],
            "any_open": True
        }
    except Exception as e:
        return {
            "status": "ok",
            "backend": "running",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "open_markets": [],
            "any_open": False
        }

@app.get("/api/strategies")
def list_strategies():
    """List all available strategies with metadata"""
    strategies = []
    for key in StrategyRegistry.all_keys():
        strategy = StrategyRegistry.get(key)
        strategies.append({
            "key": key,
            "name": strategy.name,
            "description": strategy.description,
            "signals_day": strategy.signals_per_day_range,
            "best_for": strategy.best_for_timeframes,
            "style": strategy.style,
            "color": strategy.color,
        })
    return strategies

@app.get("/api/chartdata")
def get_chart_data(symbol: str = "BTC-USD", interval: str = "5m", strategy: str = "pro_mtf"):
    """
    Get chart data with indicators and signals
    
    Args:
        symbol: Trading symbol (e.g., BTC-USD, AAPL)
        interval: Timeframe (5m, 15m, 1h, 1d, 1wk)
        strategy: Strategy name (pro_mtf, vwap_ema, etc.)
    """
    try:
        import yfinance as yf
        
        # Determine period based on interval
        period_map = {
            "1m": "7d", "2m": "7d", "5m": "60d", "15m": "60d",
            "30m": "60d", "1h": "730d", "1d": "2y", "1wk": "10y"
        }
        period = period_map.get(interval, "60d")
        
        # Fetch data
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
        
        if df is None or df.empty:
            return {"error": f"No data for {symbol}"}
        
        if len(df) < 50:
            return {"error": f"Insufficient data for {symbol}"}
        
        # Apply indicators
        df = apply_all_indicators(df)
        
        # Get strategy and generate signals
        strat = StrategyRegistry.get(strategy)
        if not strat:
            return {"error": f"Strategy {strategy} not found"}
        
        # Prepare timestamp function
        def ts_fn(idx):
            if hasattr(idx, 'timestamp'):
                return int(idx.timestamp())
            return int(pd.Timestamp(idx).timestamp())
        
        # Generate signals
        signals = strat.run(df, ts_fn, symbol)
        
        # Format candles
        candles = []
        for idx, row in df.iterrows():
            candles.append({
                "time": ts_fn(idx),
                "open": round(float(row['Open']), 4),
                "high": round(float(row['High']), 4),
                "low": round(float(row['Low']), 4),
                "close": round(float(row['Close']), 4),
                "volume": round(float(row['Volume']), 2) if 'Volume' in row else 0
            })
        
        # Format indicators
        ema9 = [{"time": ts_fn(idx), "value": round(float(val), 4)} 
                for idx, val in df['ema_9'].items()]
        ema21 = [{"time": ts_fn(idx), "value": round(float(val), 4)} 
                 for idx, val in df['ema_21'].items()]
        ema200 = [{"time": ts_fn(idx), "value": round(float(val), 4)} 
                  for idx, val in df['ema_200'].items()]
        
        # Format signals
        signal_list = [sig.to_dict() for sig in signals]
        
        return {
            "symbol": symbol,
            "interval": interval,
            "strategy": strategy,
            "candles": candles[-300:],  # Last 300 candles
            "ema9": ema9[-300:],
            "ema21": ema21[-300:],
            "ema200": ema200[-300:],
            "signals": signal_list,
            "data_count": len(candles),
            "signals_count": len(signals)
        }
        
    except Exception as e:
        print(f"Error in get_chart_data: {e}")
        return {
            "error": str(e),
            "symbol": symbol,
            "interval": interval,
            "strategy": strategy
        }

@app.get("/api/watchlist")
def get_watchlist():
    """Get watchlist"""
    watchlist = [
        {"sym": "BTC-USD", "name": "Bitcoin", "last_signal_type": None, "last_signal_price": None},
        {"sym": "AAPL", "name": "Apple", "last_signal_type": None, "last_signal_price": None},
        {"sym": "MSFT", "name": "Microsoft", "last_signal_type": None, "last_signal_price": None},
    ]
    return watchlist

@app.post("/api/watchlist")
def add_watchlist(sym: str, name: str = ""):
    """Add symbol to watchlist"""
    return {"success": True, "symbol": sym, "name": name}

@app.delete("/api/watchlist/{symbol}")
def remove_watchlist(symbol: str):
    """Remove symbol from watchlist"""
    return {"success": True, "removed": symbol}

@app.get("/api/news/{symbol}")
def get_news(symbol: str):
    """Get news for symbol"""
    return {
        "symbol": symbol,
        "news": [
            {"title": "Market Update", "source": "News", "age": "1h ago", "sentiment": "neutral", "score": 50}
        ]
    }

@app.get("/api/predict/{symbol}")
def get_prediction(symbol: str):
    """Get prediction for symbol"""
    return {
        "symbol": symbol,
        "direction": "NEUTRAL",
        "confidence": 50.0,
        "tp1": None,
        "tp2": None,
        "sl": None,
    }

@app.get("/api/trades/active")
def get_active_trades():
    """Get all active trades"""
    return {"trades": [], "count": 0}

@app.get("/api/trade/{symbol}")
def get_trade(symbol: str):
    """Get active trade for symbol"""
    return {"symbol": symbol, "trade": None}

@app.delete("/api/trade/{symbol}")
def close_trade(symbol: str, price: float = 0):
    """Close trade for symbol"""
    return {"success": True, "symbol": symbol, "closed_at": price}

@app.get("/")
def serve_index():
    """Serve index.html"""
    return FileResponse("frontend/index.html")

# ═══════════════════════════════════════════════════════════════════════════
# STATIC FILES
# ═══════════════════════════════════════════════════════════════════════════

# Serve CSS and JS files
try:
    app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
    app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
except Exception as e:
    print(f"Warning: Could not mount static files: {e}")

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║        Pro Trading Terminal v4.0 - Backend Server             ║
║                                                                ║
║  🚀 Starting server...                                         ║
║  📍 API: http://localhost:8000                                 ║
║  📍 WebSocket: ws://localhost:8000/ws                          ║
║  📊 Frontend: http://localhost:8001                            ║
║  📚 Documentation: http://localhost:8001                       ║
║                                                                ║
║  Strategies Available: 6                                       ║
║  Indicators Available: 10+                                     ║
║                                                                ║
║  Press Ctrl+C to stop                                          ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )