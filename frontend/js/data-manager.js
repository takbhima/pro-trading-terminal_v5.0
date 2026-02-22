/* frontend/js/data-manager.js - Manages API data fetching */

class DataManager {
  static async getChartData(symbol, interval, strategy) {
    try {
      const resp = await fetch(`${API_BASE}/api/chartdata?symbol=${symbol}&interval=${interval}&strategy=${strategy}`);
      return await resp.json();
    } catch (e) {
      console.error('getChartData failed:', e);
      return null;
    }
  }

  static async getStrategies() {
    try {
      const resp = await fetch(`${API_BASE}/api/strategies`);
      return await resp.json();
    } catch (e) {
      console.error('getStrategies failed:', e);
      return [];
    }
  }

  static async getWatchlist() {
    try {
      const resp = await fetch(`${API_BASE}/api/watchlist`);
      return await resp.json();
    } catch (e) {
      console.error('getWatchlist failed:', e);
      return [];
    }
  }

  static async addWatchlist(symbol, name) {
    try {
      const resp = await fetch(`${API_BASE}/api/watchlist?sym=${symbol}&name=${name}`, {
        method: 'POST',
      });
      return await resp.json();
    } catch (e) {
      console.error('addWatchlist failed:', e);
      return null;
    }
  }

  static async removeWatchlist(symbol) {
    try {
      const resp = await fetch(`${API_BASE}/api/watchlist/${symbol}`, {
        method: 'DELETE',
      });
      return await resp.json();
    } catch (e) {
      console.error('removeWatchlist failed:', e);
      return null;
    }
  }

  static async getNews(symbol) {
    try {
      const resp = await fetch(`${API_BASE}/api/news/${symbol}`);
      return await resp.json();
    } catch (e) {
      console.error('getNews failed:', e);
      return [];
    }
  }

  static async getPredict(symbol) {
    try {
      const resp = await fetch(`${API_BASE}/api/predict/${symbol}`);
      return await resp.json();
    } catch (e) {
      console.error('getPredict failed:', e);
      return null;
    }
  }

  static async getActiveTrades() {
    try {
      const resp = await fetch(`${API_BASE}/api/trades/active`);
      return await resp.json();
    } catch (e) {
      console.error('getActiveTrades failed:', e);
      return [];
    }
  }

  static async getTradeHistory(symbol) {
    try {
      const resp = await fetch(`${API_BASE}/api/trade/${symbol}/history`);
      return await resp.json();
    } catch (e) {
      console.error('getTradeHistory failed:', e);
      return [];
    }
  }

  static async closeTraade(symbol, price) {
    try {
      const resp = await fetch(`${API_BASE}/api/trade/${symbol}?price=${price}`, {
        method: 'DELETE',
      });
      return await resp.json();
    } catch (e) {
      console.error('closeTrade failed:', e);
      return null;
    }
  }

  static async getStatus() {
    try {
      const resp = await fetch(`${API_BASE}/api/status`);
      return await resp.json();
    } catch (e) {
      console.error('getStatus failed:', e);
      return null;
    }
  }
}
