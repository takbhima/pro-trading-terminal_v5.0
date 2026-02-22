/* frontend/js/constants.js - Global constants and configuration */

const API_BASE = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws';

const TIMEFRAMES = ['5m', '15m', '1h', '1d', '1wk'];
const STRATEGIES = {};
const MARKETS = {};

const COLOR_MAP = {
  'pro_mtf': '#3b82f6',
  'vwap_ema': '#00d084',
  'rsi_reversal': '#a78bfa',
  'bollinger_breakout': '#f0b429',
  'macd_crossover': '#fb7185',
  'supertrend_scalper': '#f97316',
};

const SIGNAL_COLORS = {
  'BUY': '#00e676',
  'SELL': '#ff3d57',
};
