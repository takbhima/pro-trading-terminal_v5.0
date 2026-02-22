/* frontend/js/constants.js - Global constants and configuration */

const API_BASE = '';
const WS_URL = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws`;

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
