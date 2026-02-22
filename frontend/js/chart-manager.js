/* frontend/js/chart-manager.js - Manages TradingView Lightweight Charts */

class ChartManager {
  constructor() {
    this.chart = null;
    this.candleSeries = null;
    this.ema9Series = null;
    this.ema21Series = null;
    this.ema200Series = null;
    this.buyMarkers = [];
    this.sellMarkers = [];
    this.init();
  }

  init() {
    const chartDiv = document.getElementById('chart');
    this.chart = LightweightCharts.createChart(chartDiv, {
      layout: {
        background: { color: '#080f1a' },
        textColor: '#dce8ff',
        fontSize: 12,
      },
      grid: {
        horzLines: { color: '#1a2d48' },
        vertLines: { color: '#1a2d48' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: true,
      },
    });

    this.candleSeries = this.chart.addCandlestickSeries({
      upColor: '#00e676',
      downColor: '#ff3d57',
      wickUpColor: '#00e676',
      wickDownColor: '#ff3d57',
    });

    this.ema9Series = this.chart.addLineSeries({
      color: '#ff9800',
      lineWidth: 1,
      title: 'EMA 9',
    });

    this.ema21Series = this.chart.addLineSeries({
      color: '#f44336',
      lineWidth: 1,
      title: 'EMA 21',
    });

    this.ema200Series = this.chart.addLineSeries({
      color: '#9c27b0',
      lineWidth: 1,
      title: 'EMA 200',
    });

    window.addEventListener('resize', () => this.chart.applyOptions({ width: this.chart.containerElement.clientWidth }));
  }

  loadChart(symbol, interval, strategy = 'pro_mtf') {
    const loadDiv = document.getElementById('chart-load');
    loadDiv.style.display = 'flex';

    fetch(`${API_BASE}/api/chartdata?symbol=${symbol}&interval=${interval}&strategy=${strategy}`)
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          alert(data.error);
          return;
        }

        this.candleSeries.setData(data.candles);
        this.ema9Series.setData(data.ema9);
        this.ema21Series.setData(data.ema21);
        this.ema200Series.setData(data.ema200);

        // Clear old markers
        this.buyMarkers.forEach(m => this.candleSeries.removeMarker(m));
        this.sellMarkers.forEach(m => this.candleSeries.removeMarker(m));
        this.buyMarkers = [];
        this.sellMarkers = [];

        // Add signal markers
        if (data.signals) {
          data.signals.forEach(sig => {
            const marker = {
              time: sig.time,
              position: sig.type === 'BUY' ? 'belowBar' : 'aboveBar',
              color: sig.type === 'BUY' ? '#00e676' : '#ff3d57',
              shape: sig.type === 'BUY' ? 'arrowUp' : 'arrowDown',
              text: sig.confidence.toFixed(0) + '%',
            };
            this.candleSeries.addMarker(marker);
            if (sig.type === 'BUY') this.buyMarkers.push(marker);
            else this.sellMarkers.push(marker);
          });
        }

        // Update signal list in UI
        if (window.uiManager && data.signals) {
          uiManager.updateSignalList(data.signals);
        }

        // Update status
        document.getElementById('ct-sigs').textContent = `${data.signals?.length || 0} signals`;

        this.chart.timeScale().fitContent();
        loadDiv.style.display = 'none';
      })
      .catch(e => {
        console.error('Failed to load chart', e);
        loadDiv.style.display = 'none';
      });
  }

  updateLiveCandle(bar) {
    if (!bar || !this.candleSeries) return;
    this.candleSeries.update(bar);
  }

  addSignal(signal) {
    if (!signal || !this.candleSeries) return;
    const marker = {
      time: signal.time,
      position: signal.type === 'BUY' ? 'belowBar' : 'aboveBar',
      color: signal.type === 'BUY' ? '#00e676' : '#ff3d57',
      shape: signal.type === 'BUY' ? 'arrowUp' : 'arrowDown',
      text: signal.confidence.toFixed(0) + '%',
    };
    this.candleSeries.addMarker(marker);
    if (signal.type === 'BUY') this.buyMarkers.push(marker);
    else this.sellMarkers.push(marker);
  }
}

const chartManager = new ChartManager();
