/* frontend/js/app.js - Main application entry point */

document.addEventListener('DOMContentLoaded', () => {
  console.log('Pro Trading Terminal v4.0 - Initialized');

  // Initialize managers (order matters)
  // UIManager initializes first (sets up all event listeners)
  // ChartManager initializes with chart
  // WebSocketManager connects and starts receiving data
  // DataManager is utility-only, used by others

  // Load initial data
  uiManager.loadWatchlist();
  uiManager.loadStrategies();

  // Load chart for default symbol
  setTimeout(() => {
    uiManager.scanSymbol();
  }, 500);

  // Update status every 10 seconds
  setInterval(() => {
    DataManager.getStatus().then(status => {
      if (status) {
        let statusText = '🔴 Markets Closed';
        if (status.open_markets && status.open_markets.length > 0) {
          statusText = `🟢 ${status.open_markets.join(', ')} Open`;
        }
        if (uiManager) {
          uiManager.setStatus(statusText);
        }
      }
    });
  }, 10000);
});
