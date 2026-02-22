/* frontend/js/websocket-manager.js - Manages real-time WebSocket connections */

class WebSocketManager {
  constructor() {
    this.ws = null;
    this.connected = false;
    this.currentSymbol = null;
    this.currentInterval = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.connect();
  }

  connect() {
    try {
      this.ws = new WebSocket(WS_URL);

      this.ws.onopen = () => {
        this.connected = true;
        this.reconnectAttempts = 0;
        console.log('WebSocket connected');
        if (window.uiManager) {
          uiManager.setStatus('🟢 Connected');
        }
      };

      this.ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        this.handleMessage(msg);
      };

      this.ws.onerror = (e) => {
        console.error('WebSocket error:', e);
      };

      this.ws.onclose = () => {
        this.connected = false;
        console.log('WebSocket disconnected');
        if (window.uiManager) {
          uiManager.setStatus('🔴 Disconnected');
        }
        this.attemptReconnect();
      };
    } catch (e) {
      console.error('Failed to connect WebSocket:', e);
      this.attemptReconnect();
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      console.log(`Reconnecting in ${delay}ms...`);
      setTimeout(() => this.connect(), delay);
    }
  }

  subscribe(symbol, interval) {
    if (!this.connected) return;
    this.currentSymbol = symbol;
    this.currentInterval = interval;
    this.send({
      type: 'subscribe',
      symbol: symbol,
      interval: interval,
    });
  }

  send(msg) {
    if (this.connected) {
      this.ws.send(JSON.stringify(msg));
    }
  }

  handleMessage(msg) {
    switch (msg.type) {
      case 'status':
        this.handleStatus(msg);
        break;
      case 'tick':
        this.handleTick(msg);
        break;
      case 'signal':
        this.handleSignal(msg);
        break;
      case 'exit':
        this.handleExit(msg);
        break;
      default:
        console.log('Unknown message type:', msg.type);
    }
  }

  handleStatus(msg) {
    let status = '🔴 Markets Closed';
    if (msg.open_markets && msg.open_markets.length > 0) {
      status = `🟢 ${msg.open_markets.join(', ')} Open`;
    } else if (msg.any_open) {
      status = '🟡 Some Markets Open';
    }
    if (window.uiManager) {
      uiManager.setStatus(status);
    }
  }

  handleTick(msg) {
    // Update price in UI
    if (msg.symbol === uiManager.currentSymbol && window.uiManager) {
      uiManager.setPrice(msg.symbol, msg.price, msg.change, msg.change_pct);
    }

    // Update live candle in chart
    if (msg.bar && window.chartManager) {
      chartManager.updateLiveCandle(msg.bar);
    }

    // Update live P&L
    if (msg.active_trade && msg.live_pnl !== null) {
      const pnlColor = msg.live_pnl >= 0 ? 'var(--green)' : 'var(--red)';
      // Display in UI if needed
    }
  }

  handleSignal(msg) {
    console.log('New signal:', msg);
    // Add to signals list in UI
    if (window.uiManager) {
      // Reload signal list for current symbol
      DataManager.getChartData(msg.symbol, uiManager.currentInterval, uiManager.currentStrategy)
        .then(data => {
          if (data && data.signals) {
            uiManager.updateSignalList(data.signals);
          }
        });
    }

    // Add marker to chart if current symbol
    if (msg.symbol === uiManager.currentSymbol && window.chartManager) {
      chartManager.addSignal(msg);
    }

    // Reload watchlist to update signal badges
    if (window.uiManager) {
      uiManager.loadWatchlist();
    }

    // Update news and predict
    DataManager.getNews(msg.symbol).then(news => {
      if (window.uiManager && news) {
        uiManager.updateNewsList(news);
      }
    });

    DataManager.getPredict(msg.symbol).then(predict => {
      if (window.uiManager && predict) {
        const div = document.getElementById('predict-box');
        if (div) {
          div.innerHTML = `
            <div style="font-size:11px;">
              <div style="margin-bottom:8px;">
                <div style="color:var(--subtext);font-size:10px;">Direction</div>
                <div style="color:${predict.direction === 'BULLISH' ? 'var(--green)' : predict.direction === 'BEARISH' ? 'var(--red)' : 'var(--yellow)'}; font-weight:700; font-size:14px;">${predict.direction}</div>
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:10px;">
                <div><span style="color:var(--subtext);">TP1</span> <div style="color:var(--text);font-weight:600;">${predict.tp1?.toFixed(4) || '—'}</div></div>
                <div><span style="color:var(--subtext);">TP2</span> <div style="color:var(--text);font-weight:600;">${predict.tp2?.toFixed(4) || '—'}</div></div>
                <div><span style="color:var(--subtext);">SL</span> <div style="color:var(--text);font-weight:600;">${predict.sl?.toFixed(4) || '—'}</div></div>
                <div><span style="color:var(--subtext);">Conf</span> <div style="color:var(--text);font-weight:600;">${predict.confidence?.toFixed(1) || '—'}%</div></div>
              </div>
              <div style="margin-top:8px;padding:6px;background:var(--card);border-radius:3px;">
                <div style="color:var(--subtext);font-size:9px;margin-bottom:4px;">Why</div>
                <div style="color:var(--text);font-size:9px;line-height:1.4;">
                  ${(predict.bull_reasons || []).slice(0, 3).map(r => `• ${r}`).join('<br>')}
                </div>
              </div>
            </div>
          `;
        }
      }
    });
  }

  handleExit(msg) {
    console.log('Trade exit:', msg);
    // Reload trades list
    DataManager.getActiveTrades().then(trades => {
      if (window.uiManager && trades) {
        uiManager.updateTradesList(trades);
      }
    });
  }
}

const wsManager = new WebSocketManager();
