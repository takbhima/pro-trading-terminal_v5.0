/* frontend/js/ui-manager.js - Manages UI interactions and DOM updates */

class UIManager {
  constructor() {
    this.currentSymbol = 'BTC-USD';
    this.currentInterval = '5m';
    this.currentStrategy = 'pro_mtf';
    this.watchlist = [];
    this.init();
  }

  init() {
    this.setupEventListeners();
    this.loadWatchlist();
    this.loadStrategies();
  }

  setupEventListeners() {
    // Timeframe buttons
    const tfWrap = document.getElementById('tf-wrap');
    TIMEFRAMES.forEach(tf => {
      const btn = document.createElement('button');
      btn.className = `tf-btn ${tf === this.currentInterval ? 'active' : ''}`;
      btn.textContent = tf.toUpperCase();
      btn.onclick = () => this.switchTimeframe(tf);
      tfWrap.appendChild(btn);
    });

    // Scan button
    document.getElementById('scan-btn').onclick = () => this.scanSymbol();
    document.getElementById('sym-input').onkeyup = (e) => {
      if (e.key === 'Enter') this.scanSymbol();
    };

    // Watchlist add button
    document.getElementById('wl-add').onclick = () => this.showAddWatchlistModal();

    // Sidebar tabs
    document.querySelectorAll('.sb-tab').forEach(tab => {
      tab.onclick = (e) => this.switchTab(e.target.dataset.tab);
    });

    // Modal
    document.getElementById('modal-ok').onclick = () => this.addToWatchlist();
    document.getElementById('modal-cancel').onclick = () => this.closeModal();
    document.querySelector('.modal-close').onclick = () => this.closeModal();
  }

  switchTimeframe(tf) {
    this.currentInterval = tf;
    document.querySelectorAll('.tf-btn').forEach((btn, idx) => {
      btn.classList.toggle('active', TIMEFRAMES[idx] === tf);
    });
    if (window.chartManager) window.chartManager.loadChart(this.currentSymbol, tf);
    if (window.wsManager) window.wsManager.subscribe(this.currentSymbol, tf);
  }

  switchTab(tabName) {
    // Hide all panels
    document.querySelectorAll('.sb-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.sb-tab').forEach(t => t.classList.remove('active'));

    // Show selected panel
    document.getElementById(`panel-${tabName}`).classList.add('active');
    event.target.classList.add('active');
  }

  scanSymbol() {
    const sym = document.getElementById('sym-input').value.trim().toUpperCase();
    if (!sym) return;
    this.currentSymbol = sym;
    document.getElementById('ct-sym').textContent = sym;
    if (window.chartManager) window.chartManager.loadChart(sym, this.currentInterval);
    if (window.wsManager) window.wsManager.subscribe(sym, this.currentInterval);
  }

  loadWatchlist() {
    fetch(`${API_BASE}/api/watchlist`)
      .then(r => r.json())
      .then(data => {
        this.watchlist = data;
        this.renderWatchlist();
      })
      .catch(e => console.error('Failed to load watchlist', e));
  }

  renderWatchlist() {
    const container = document.getElementById('wl-items');
    container.innerHTML = '';
    this.watchlist.forEach(item => {
      const div = document.createElement('div');
      div.className = `wl-item ${item.sym === this.currentSymbol ? 'active' : ''}`;
      div.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:start;">
          <div>
            <div class="wl-nm">${item.sym}</div>
            <div class="wl-tk">${item.name || 'Stock'}</div>
            <div class="wl-sig ${item.last_signal_type || 'NONE'}">${item.last_signal_type ? item.last_signal_type + ' (' + item.last_signal_price + ')' : 'No Signal'}</div>
          </div>
          <button class="wl-rm" onclick="uiManager.removeFromWatchlist('${item.sym}')">✕</button>
        </div>
      `;
      div.onclick = (e) => {
        if (!e.target.classList.contains('wl-rm')) {
          this.currentSymbol = item.sym;
          this.scanSymbol();
          document.querySelectorAll('.wl-item').forEach(x => x.classList.remove('active'));
          div.classList.add('active');
        }
      };
      container.appendChild(div);
    });
  }

  showAddWatchlistModal() {
    document.getElementById('modal-add-wl').style.display = 'flex';
    document.getElementById('modal-sym').focus();
  }

  closeModal() {
    document.getElementById('modal-add-wl').style.display = 'none';
  }

  addToWatchlist() {
    const sym = document.getElementById('modal-sym').value.trim().toUpperCase();
    const name = document.getElementById('modal-name').value.trim();
    if (!sym) return;

    fetch(`${API_BASE}/api/watchlist?sym=${sym}&name=${name}`, { method: 'POST' })
      .then(r => r.json())
      .then(() => {
        this.loadWatchlist();
        this.closeModal();
        document.getElementById('modal-sym').value = '';
        document.getElementById('modal-name').value = '';
      })
      .catch(e => console.error('Failed to add watchlist', e));
  }

  removeFromWatchlist(sym) {
    if (confirm(`Remove ${sym} from watchlist?`)) {
      fetch(`${API_BASE}/api/watchlist/${sym}`, { method: 'DELETE' })
        .then(() => this.loadWatchlist())
        .catch(e => console.error('Failed to remove', e));
    }
  }

  loadStrategies() {
    fetch(`${API_BASE}/api/strategies`)
      .then(r => r.json())
      .then(strategies => {
        const container = document.getElementById('strat-buttons');
        strategies.forEach(s => {
          const btn = document.createElement('button');
          btn.className = `strat-btn ${s.key === this.currentStrategy ? 'active' : ''}`;
          btn.innerHTML = `<span class="s-dot" style="background:${s.color}"></span>${s.name}<span class="s-badge">${s.signals_day}</span>`;
          btn.onclick = () => this.switchStrategy(s.key);
          container.appendChild(btn);
          STRATEGIES[s.key] = s;
        });
      });
  }

  switchStrategy(key) {
    this.currentStrategy = key;
    document.querySelectorAll('.strat-btn').forEach(btn => btn.classList.remove('active'));
    event.target.closest('.strat-btn').classList.add('active');
    if (window.chartManager) window.chartManager.loadChart(this.currentSymbol, this.currentInterval, key);
  }

  updateSignalList(signals) {
    const container = document.getElementById('signal-list');
    container.innerHTML = '';
    if (!signals || signals.length === 0) {
      container.innerHTML = '<div style="padding:10px;color:var(--dim);font-size:11px;">No signals</div>';
      return;
    }

    signals.slice(0, 20).forEach(sig => {
      const div = document.createElement('div');
      div.className = `sig-item ${sig.type}`;
      div.innerHTML = `
        <div class="sig-row">
          <span class="sig-lbl">${sig.type}</span>
          <span class="sig-val" style="color:${SIGNAL_COLORS[sig.type]}">${sig.confidence.toFixed(0)}%</span>
        </div>
        <div class="sig-row">
          <span class="sig-lbl">Price</span>
          <span class="sig-val">${sig.price.toFixed(4)}</span>
        </div>
        <div class="sig-row">
          <span class="sig-lbl">SL</span>
          <span class="sig-val">${sig.sl.toFixed(4)}</span>
        </div>
        <div class="sig-row">
          <span class="sig-lbl">TP</span>
          <span class="sig-val">${sig.tp.toFixed(4)}</span>
        </div>
        <div class="sig-row" style="margin-top:4px;padding-top:4px;border-top:1px solid var(--border);">
          <span class="sig-lbl">RSI</span>
          <span class="sig-val">${sig.rsi.toFixed(2)}</span>
        </div>
      `;
      container.appendChild(div);
    });
  }

  updateNewsList(news) {
    const container = document.getElementById('news-list');
    container.innerHTML = '';
    if (!news || news.length === 0) {
      container.innerHTML = '<div style="padding:10px;color:var(--dim);font-size:11px;">No news</div>';
      return;
    }

    news.slice(0, 15).forEach(item => {
      const div = document.createElement('div');
      div.className = 'news-item';
      div.innerHTML = `
        <div class="news-title">${item.title || 'News'}</div>
        <div class="news-meta">
          <span>${item.source || 'Source'}</span>
          <span>${item.age || 'recently'}</span>
          <span style="color:${item.sentiment === 'positive' ? 'var(--green)' : item.sentiment === 'negative' ? 'var(--red)' : 'var(--yellow)'};">${item.sentiment || 'neutral'}</span>
        </div>
      `;
      if (item.url && item.url !== '#') {
        div.style.cursor = 'pointer';
        div.onclick = () => window.open(item.url);
      }
      container.appendChild(div);
    });
  }

  updateTradesList(trades) {
    const container = document.getElementById('trades-list');
    container.innerHTML = '';
    if (!trades || trades.length === 0) {
      container.innerHTML = '<div style="padding:10px;color:var(--dim);font-size:11px;">No trades</div>';
      return;
    }

    trades.forEach(trade => {
      const div = document.createElement('div');
      const status = trade.status === 'ACTIVE' ? 'active' : (trade.pnl >= 0 ? 'profit' : 'loss');
      div.className = `trade-item ${status}`;
      div.innerHTML = `
        <div class="sig-row">
          <span class="sig-lbl">${trade.symbol}</span>
          <span class="sig-val">${trade.side} ${trade.timeframe}</span>
        </div>
        <div class="sig-row">
          <span class="sig-lbl">Entry</span>
          <span class="sig-val">${trade.entry_price?.toFixed(4) || '—'}</span>
        </div>
        <div class="sig-row">
          <span class="sig-lbl">P&L</span>
          <span class="sig-val" style="color:${(trade.pnl || 0) >= 0 ? 'var(--green)' : 'var(--red)'};">${trade.pnl?.toFixed(2) || '—'} (${trade.pnl_pct?.toFixed(1) || '—'}%)</span>
        </div>
      `;
      container.appendChild(div);
    });
  }

  setStatus(message) {
    document.getElementById('status-lbl').textContent = message;
  }

  setPrice(symbol, price, change, changePct) {
    document.getElementById('ct-px').textContent = `${symbol} ${price.toFixed(2)} ${change > 0 ? '+' : ''}${change.toFixed(2)} (${changePct > 0 ? '+' : ''}${changePct.toFixed(2)}%)`;
  }
}

const uiManager = new UIManager();
