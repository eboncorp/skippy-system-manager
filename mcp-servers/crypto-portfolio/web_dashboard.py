"""
Web Dashboard for Crypto Portfolio Manager.

A modern, responsive web interface built with FastAPI and vanilla JS.
Provides real-time portfolio monitoring, analysis tools, and trading interface.
"""

import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from pathlib import Path

# FastAPI and related imports
try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("FastAPI not installed. Run: pip install fastapi uvicorn")


# Dashboard HTML template (embedded for simplicity)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Portfolio Dashboard</title>
    <style>
        :root {
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --accent-green: #3fb950;
            --accent-red: #f85149;
            --accent-blue: #58a6ff;
            --accent-yellow: #d29922;
            --border-color: #30363d;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
        }

        .dashboard {
            display: grid;
            grid-template-columns: 250px 1fr;
            min-height: 100vh;
        }

        /* Sidebar */
        .sidebar {
            background: var(--bg-secondary);
            border-right: 1px solid var(--border-color);
            padding: 1rem;
        }

        .logo {
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 2rem;
            padding: 0.5rem;
        }

        .logo span {
            color: var(--accent-blue);
        }

        .nav-item {
            display: flex;
            align-items: center;
            padding: 0.75rem 1rem;
            color: var(--text-secondary);
            text-decoration: none;
            border-radius: 6px;
            margin-bottom: 0.25rem;
            cursor: pointer;
            transition: all 0.2s;
        }

        .nav-item:hover, .nav-item.active {
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }

        .nav-item svg {
            margin-right: 0.75rem;
            width: 20px;
            height: 20px;
        }

        /* Main content */
        .main-content {
            padding: 1.5rem;
            overflow-y: auto;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }

        .header h1 {
            font-size: 1.5rem;
        }

        .connection-status {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent-red);
        }

        .status-dot.connected {
            background: var(--accent-green);
        }

        /* Cards */
        .card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }

        .card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.25rem;
        }

        .card-title {
            color: var(--text-secondary);
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
        }

        .card-value {
            font-size: 1.75rem;
            font-weight: 600;
        }

        .card-change {
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }

        .positive { color: var(--accent-green); }
        .negative { color: var(--accent-red); }

        /* Holdings table */
        .holdings-section {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin-bottom: 1.5rem;
        }

        .section-header {
            padding: 1rem 1.25rem;
            border-bottom: 1px solid var(--border-color);
            font-weight: 600;
        }

        .holdings-table {
            width: 100%;
            border-collapse: collapse;
        }

        .holdings-table th,
        .holdings-table td {
            padding: 1rem 1.25rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }

        .holdings-table th {
            color: var(--text-secondary);
            font-weight: 500;
            font-size: 0.875rem;
        }

        .holdings-table tr:last-child td {
            border-bottom: none;
        }

        .holdings-table tr:hover {
            background: var(--bg-tertiary);
        }

        .asset-info {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .asset-icon {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: var(--bg-tertiary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.75rem;
        }

        /* Charts placeholder */
        .chart-container {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.25rem;
            height: 300px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-secondary);
        }

        /* Alerts panel */
        .alerts-panel {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
        }

        .alert-item {
            padding: 1rem 1.25rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
        }

        .alert-item:last-child {
            border-bottom: none;
        }

        .alert-icon {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .alert-icon.warning { background: rgba(210, 153, 34, 0.2); color: var(--accent-yellow); }
        .alert-icon.success { background: rgba(63, 185, 80, 0.2); color: var(--accent-green); }
        .alert-icon.error { background: rgba(248, 81, 73, 0.2); color: var(--accent-red); }

        .alert-content {
            flex: 1;
        }

        .alert-title {
            font-weight: 500;
            margin-bottom: 0.25rem;
        }

        .alert-time {
            font-size: 0.75rem;
            color: var(--text-secondary);
        }

        /* Buttons */
        .btn {
            padding: 0.5rem 1rem;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.2s;
        }

        .btn-primary {
            background: var(--accent-blue);
            color: white;
        }

        .btn-primary:hover {
            filter: brightness(1.1);
        }

        /* Tab navigation */
        .tabs {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
        }

        .tab {
            padding: 0.5rem 1rem;
            background: transparent;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            border-radius: 6px;
            transition: all 0.2s;
        }

        .tab:hover, .tab.active {
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }

        /* Loading spinner */
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid var(--border-color);
            border-top-color: var(--accent-blue);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Page sections */
        .page { display: none; }
        .page.active { display: block; }

        /* Responsive */
        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
            }
            .sidebar {
                display: none;
            }
            .card-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <!-- Sidebar -->
        <nav class="sidebar">
            <div class="logo">Crypto<span>Portfolio</span></div>
            <a class="nav-item active" data-page="overview">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="7" height="7"></rect>
                    <rect x="14" y="3" width="7" height="7"></rect>
                    <rect x="14" y="14" width="7" height="7"></rect>
                    <rect x="3" y="14" width="7" height="7"></rect>
                </svg>
                Overview
            </a>
            <a class="nav-item" data-page="holdings">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M12 6v6l4 2"></path>
                </svg>
                Holdings
            </a>
            <a class="nav-item" data-page="analysis">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="22,12 18,12 15,21 9,3 6,12 2,12"></polyline>
                </svg>
                Analysis
            </a>
            <a class="nav-item" data-page="tax">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14,2 14,8 20,8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                </svg>
                Tax Tools
            </a>
            <a class="nav-item" data-page="alerts">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                    <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                </svg>
                Alerts
            </a>
            <a class="nav-item" data-page="settings">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="3"></circle>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                </svg>
                Settings
            </a>
        </nav>

        <!-- Main Content -->
        <main class="main-content">
            <header class="header">
                <h1 id="page-title">Portfolio Overview</h1>
                <div class="connection-status">
                    <span class="status-dot" id="ws-status"></span>
                    <span id="ws-status-text">Connecting...</span>
                </div>
            </header>

            <!-- Overview Page -->
            <div id="page-overview" class="page active">
                <div class="card-grid">
                    <div class="card">
                        <div class="card-title">Total Portfolio Value</div>
                        <div class="card-value" id="total-value">$0.00</div>
                        <div class="card-change" id="total-change">--</div>
                    </div>
                    <div class="card">
                        <div class="card-title">24h Change</div>
                        <div class="card-value" id="daily-change">$0.00</div>
                        <div class="card-change" id="daily-change-pct">--</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Unrealized P&L</div>
                        <div class="card-value" id="unrealized-pnl">$0.00</div>
                        <div class="card-change" id="unrealized-pnl-pct">--</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Today's Realized P&L</div>
                        <div class="card-value" id="realized-pnl">$0.00</div>
                        <div class="card-change">Realized gains/losses</div>
                    </div>
                </div>

                <div class="holdings-section">
                    <div class="section-header">Holdings</div>
                    <table class="holdings-table">
                        <thead>
                            <tr>
                                <th>Asset</th>
                                <th>Amount</th>
                                <th>Price</th>
                                <th>Value</th>
                                <th>24h</th>
                                <th>P&L</th>
                            </tr>
                        </thead>
                        <tbody id="holdings-body">
                            <tr>
                                <td colspan="6" style="text-align: center; color: var(--text-secondary);">
                                    <div class="loading"></div> Loading holdings...
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="alerts-panel">
                    <div class="section-header">Recent Activity</div>
                    <div id="alerts-list">
                        <div class="alert-item">
                            <div class="alert-icon warning">⚡</div>
                            <div class="alert-content">
                                <div class="alert-title">Connecting to server...</div>
                                <div class="alert-time">Just now</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Holdings Page -->
            <div id="page-holdings" class="page">
                <div class="tabs">
                    <button class="tab active">All Assets</button>
                    <button class="tab">Staking</button>
                    <button class="tab">DeFi</button>
                </div>
                <div class="holdings-section">
                    <table class="holdings-table">
                        <thead>
                            <tr>
                                <th>Asset</th>
                                <th>Amount</th>
                                <th>Avg Cost</th>
                                <th>Current Price</th>
                                <th>Value</th>
                                <th>Cost Basis</th>
                                <th>P&L</th>
                                <th>P&L %</th>
                            </tr>
                        </thead>
                        <tbody id="detailed-holdings-body">
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Analysis Page -->
            <div id="page-analysis" class="page">
                <div class="card-grid">
                    <div class="card">
                        <div class="card-title">Portfolio Health Score</div>
                        <div class="card-value" id="health-score">--</div>
                        <div class="card-change">Based on diversification & risk</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Sharpe Ratio</div>
                        <div class="card-value" id="sharpe-ratio">--</div>
                        <div class="card-change">Risk-adjusted return</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Max Drawdown</div>
                        <div class="card-value" id="max-drawdown">--</div>
                        <div class="card-change">Largest peak-to-trough decline</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Volatility (30d)</div>
                        <div class="card-value" id="volatility">--</div>
                        <div class="card-change">Annualized standard deviation</div>
                    </div>
                </div>

                <div class="chart-container">
                    <div>📊 Portfolio allocation chart will appear here</div>
                </div>

                <div class="card" style="margin-top: 1rem;">
                    <div class="card-title">AI Recommendations</div>
                    <div id="ai-recommendations" style="margin-top: 0.5rem; color: var(--text-secondary);">
                        Loading AI analysis...
                    </div>
                </div>
            </div>

            <!-- Tax Page -->
            <div id="page-tax" class="page">
                <div class="card-grid">
                    <div class="card">
                        <div class="card-title">YTD Realized Gains</div>
                        <div class="card-value" id="ytd-gains">$0.00</div>
                        <div class="card-change">Taxable gains this year</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Harvestable Losses</div>
                        <div class="card-value" id="harvestable-losses">$0.00</div>
                        <div class="card-change">Potential tax savings</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Est. Tax Savings</div>
                        <div class="card-value" id="tax-savings">$0.00</div>
                        <div class="card-change">If losses harvested</div>
                    </div>
                </div>

                <div class="holdings-section">
                    <div class="section-header">Tax Loss Harvesting Opportunities</div>
                    <table class="holdings-table">
                        <thead>
                            <tr>
                                <th>Asset</th>
                                <th>Unrealized Loss</th>
                                <th>Loss %</th>
                                <th>Strategy</th>
                                <th>Est. Savings</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody id="tlh-body">
                            <tr>
                                <td colspan="6" style="text-align: center; color: var(--text-secondary);">
                                    No tax loss harvesting opportunities found
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Alerts Page -->
            <div id="page-alerts" class="page">
                <div class="card-grid">
                    <div class="card">
                        <div class="card-title">Active Alerts</div>
                        <div class="card-value" id="active-alerts-count">0</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Triggered Today</div>
                        <div class="card-value" id="triggered-today">0</div>
                    </div>
                </div>

                <div class="alerts-panel">
                    <div class="section-header">
                        All Alerts
                        <button class="btn btn-primary" style="float: right;">+ New Alert</button>
                    </div>
                    <div id="all-alerts-list">
                        <div class="alert-item">
                            <div class="alert-content">
                                <div class="alert-title">No alerts configured</div>
                                <div class="alert-time">Create price alerts to get notified</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Settings Page -->
            <div id="page-settings" class="page">
                <div class="card">
                    <h3 style="margin-bottom: 1rem;">Dashboard Settings</h3>
                    <p style="color: var(--text-secondary);">Settings will be available here.</p>
                </div>
            </div>
        </main>
    </div>

    <script>
        // Dashboard application
        const Dashboard = {
            ws: null,
            reconnectAttempts: 0,
            maxReconnectAttempts: 5,
            data: {
                portfolio: null,
                holdings: {},
                prices: {},
                alerts: []
            },

            init() {
                this.setupNavigation();
                this.connectWebSocket();
                this.loadInitialData();
            },

            setupNavigation() {
                document.querySelectorAll('.nav-item').forEach(item => {
                    item.addEventListener('click', (e) => {
                        const page = e.currentTarget.dataset.page;
                        this.showPage(page);

                        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
                        e.currentTarget.classList.add('active');
                    });
                });
            },

            showPage(pageId) {
                document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
                document.getElementById(`page-${pageId}`).classList.add('active');

                const titles = {
                    overview: 'Portfolio Overview',
                    holdings: 'Holdings',
                    analysis: 'Portfolio Analysis',
                    tax: 'Tax Tools',
                    alerts: 'Alerts',
                    settings: 'Settings'
                };
                document.getElementById('page-title').textContent = titles[pageId] || pageId;
            },

            connectWebSocket() {
                const wsUrl = `ws://${window.location.host}/ws/portfolio`;

                try {
                    this.ws = new WebSocket(wsUrl);

                    this.ws.onopen = () => {
                        console.log('WebSocket connected');
                        this.setConnectionStatus(true);
                        this.reconnectAttempts = 0;
                        this.addAlert('success', 'Connected', 'Real-time updates enabled');
                    };

                    this.ws.onmessage = (event) => {
                        const message = JSON.parse(event.data);
                        this.handleMessage(message);
                    };

                    this.ws.onclose = () => {
                        console.log('WebSocket disconnected');
                        this.setConnectionStatus(false);
                        this.attemptReconnect();
                    };

                    this.ws.onerror = (error) => {
                        console.error('WebSocket error:', error);
                        this.setConnectionStatus(false);
                    };
                } catch (e) {
                    console.error('Failed to connect WebSocket:', e);
                    this.setConnectionStatus(false);
                }
            },

            attemptReconnect() {
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
                    console.log(`Reconnecting in ${delay}ms...`);
                    setTimeout(() => this.connectWebSocket(), delay);
                }
            },

            setConnectionStatus(connected) {
                const dot = document.getElementById('ws-status');
                const text = document.getElementById('ws-status-text');

                if (connected) {
                    dot.classList.add('connected');
                    text.textContent = 'Live';
                } else {
                    dot.classList.remove('connected');
                    text.textContent = 'Disconnected';
                }
            },

            handleMessage(message) {
                switch (message.type) {
                    case 'initial_snapshot':
                    case 'portfolio_update':
                        this.updatePortfolio(message.data);
                        break;
                    case 'price_update':
                        this.updatePrice(message.data);
                        break;
                    case 'pnl_update':
                        this.updatePnL(message.data);
                        break;
                    case 'alert':
                        this.handleAlert(message.data);
                        break;
                    case 'trade_executed':
                        this.handleTrade(message.data);
                        break;
                }
            },

            updatePortfolio(data) {
                this.data.portfolio = data;

                // Update overview cards
                document.getElementById('total-value').textContent = this.formatCurrency(data.total_value);

                const pnl = parseFloat(data.total_unrealized_pnl);
                const pnlPct = data.total_unrealized_pnl_pct;

                document.getElementById('unrealized-pnl').textContent = this.formatCurrency(data.total_unrealized_pnl);
                document.getElementById('unrealized-pnl').className = `card-value ${pnl >= 0 ? 'positive' : 'negative'}`;
                document.getElementById('unrealized-pnl-pct').textContent = `${pnl >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%`;
                document.getElementById('unrealized-pnl-pct').className = `card-change ${pnl >= 0 ? 'positive' : 'negative'}`;

                document.getElementById('realized-pnl').textContent = this.formatCurrency(data.total_realized_pnl_today);

                // Update holdings table
                this.updateHoldingsTable(data.holdings);
            },

            updateHoldingsTable(holdings) {
                const tbody = document.getElementById('holdings-body');
                const detailedTbody = document.getElementById('detailed-holdings-body');

                if (!holdings || Object.keys(holdings).length === 0) {
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="6" style="text-align: center; color: var(--text-secondary);">
                                No holdings found
                            </td>
                        </tr>
                    `;
                    return;
                }

                // Sort by value
                const sorted = Object.entries(holdings).sort((a, b) =>
                    parseFloat(b[1].current_value) - parseFloat(a[1].current_value)
                );

                tbody.innerHTML = sorted.map(([asset, data]) => {
                    const pnl = parseFloat(data.unrealized_pnl);
                    const pnlPct = data.unrealized_pnl_pct;
                    const pnlClass = pnl >= 0 ? 'positive' : 'negative';

                    return `
                        <tr>
                            <td>
                                <div class="asset-info">
                                    <div class="asset-icon">${asset.substring(0, 2)}</div>
                                    <div>${asset}</div>
                                </div>
                            </td>
                            <td>${parseFloat(data.amount).toFixed(6)}</td>
                            <td>${this.formatCurrency(data.price)}</td>
                            <td>${this.formatCurrency(data.current_value)}</td>
                            <td class="${pnlClass}">--</td>
                            <td class="${pnlClass}">${pnl >= 0 ? '+' : ''}${this.formatCurrency(data.unrealized_pnl)} (${pnlPct.toFixed(2)}%)</td>
                        </tr>
                    `;
                }).join('');

                // Update detailed table too
                detailedTbody.innerHTML = sorted.map(([asset, data]) => {
                    const pnl = parseFloat(data.unrealized_pnl);
                    const pnlPct = data.unrealized_pnl_pct;
                    const pnlClass = pnl >= 0 ? 'positive' : 'negative';
                    const avgCost = parseFloat(data.cost_basis) / parseFloat(data.amount);

                    return `
                        <tr>
                            <td>
                                <div class="asset-info">
                                    <div class="asset-icon">${asset.substring(0, 2)}</div>
                                    <div>${asset}</div>
                                </div>
                            </td>
                            <td>${parseFloat(data.amount).toFixed(6)}</td>
                            <td>${this.formatCurrency(avgCost)}</td>
                            <td>${this.formatCurrency(data.price)}</td>
                            <td>${this.formatCurrency(data.current_value)}</td>
                            <td>${this.formatCurrency(data.cost_basis)}</td>
                            <td class="${pnlClass}">${pnl >= 0 ? '+' : ''}${this.formatCurrency(data.unrealized_pnl)}</td>
                            <td class="${pnlClass}">${pnl >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%</td>
                        </tr>
                    `;
                }).join('');
            },

            updatePrice(data) {
                this.data.prices[data.asset] = data;
            },

            updatePnL(data) {
                // Individual asset PnL updates handled here
            },

            handleAlert(data) {
                this.addAlert(data.alert_type || 'warning', data.message, data.data?.details || '');
            },

            handleTrade(data) {
                this.addAlert('success', 'Trade Executed',
                    `${data.side} ${data.amount} ${data.asset} @ ${data.price}`);
            },

            addAlert(type, title, description) {
                const alertsList = document.getElementById('alerts-list');
                const alertHtml = `
                    <div class="alert-item">
                        <div class="alert-icon ${type}">${type === 'success' ? '✓' : type === 'error' ? '✕' : '⚡'}</div>
                        <div class="alert-content">
                            <div class="alert-title">${title}</div>
                            <div class="alert-time">${description || 'Just now'}</div>
                        </div>
                    </div>
                `;
                alertsList.insertAdjacentHTML('afterbegin', alertHtml);

                // Keep only last 10 alerts
                while (alertsList.children.length > 10) {
                    alertsList.removeChild(alertsList.lastChild);
                }
            },

            async loadInitialData() {
                try {
                    // Load portfolio data via REST API
                    const response = await fetch('/api/portfolio');
                    if (response.ok) {
                        const data = await response.json();
                        this.updatePortfolio(data);
                    }
                } catch (e) {
                    console.error('Failed to load initial data:', e);
                }

                try {
                    // Load analysis data
                    const analysisResponse = await fetch('/api/analysis');
                    if (analysisResponse.ok) {
                        const analysis = await analysisResponse.json();
                        this.updateAnalysis(analysis);
                    }
                } catch (e) {
                    console.error('Failed to load analysis:', e);
                }
            },

            updateAnalysis(data) {
                if (data.health_score) {
                    document.getElementById('health-score').textContent = data.health_score + '/100';
                }
                if (data.sharpe_ratio) {
                    document.getElementById('sharpe-ratio').textContent = data.sharpe_ratio.toFixed(2);
                }
                if (data.max_drawdown) {
                    document.getElementById('max-drawdown').textContent = data.max_drawdown + '%';
                }
                if (data.volatility) {
                    document.getElementById('volatility').textContent = data.volatility + '%';
                }
                if (data.recommendations) {
                    document.getElementById('ai-recommendations').innerHTML =
                        data.recommendations.map(r => `<p style="margin-bottom: 0.5rem;">• ${r}</p>`).join('');
                }
            },

            formatCurrency(value) {
                const num = typeof value === 'string' ? parseFloat(value) : value;
                return new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD',
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }).format(num);
            }
        };

        // Initialize on load
        document.addEventListener('DOMContentLoaded', () => Dashboard.init());
    </script>
</body>
</html>
"""


# Request/Response models
if FASTAPI_AVAILABLE:
    class PortfolioResponse(BaseModel):
        total_value: str
        total_cost_basis: str
        total_unrealized_pnl: str
        total_unrealized_pnl_pct: float
        total_realized_pnl_today: str
        holdings: Dict[str, Dict]

    class AnalysisResponse(BaseModel):
        health_score: int
        sharpe_ratio: float
        max_drawdown: float
        volatility: float
        recommendations: List[str]

    class AlertCreate(BaseModel):
        asset: str
        condition: str  # "above", "below"
        price: float
        notification_channels: List[str] = ["email"]


def create_dashboard_app(
    portfolio_manager=None,
    stream_manager=None,
) -> "FastAPI":
    """
    Create the FastAPI dashboard application.

    Args:
        portfolio_manager: Optional portfolio manager instance
        stream_manager: Optional real-time stream manager

    Returns:
        FastAPI application instance
    """
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI is required. Install with: pip install fastapi uvicorn")

    app = FastAPI(
        title="Crypto Portfolio Dashboard",
        description="Real-time cryptocurrency portfolio management dashboard",
        version="1.0.0",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Store references
    app.state.portfolio_manager = portfolio_manager
    app.state.stream_manager = stream_manager
    app.state.connected_clients = set()

    # Routes
    @app.get("/", response_class=HTMLResponse)
    async def dashboard_home():
        """Serve the main dashboard page."""
        return HTMLResponse(content=DASHBOARD_HTML)

    @app.get("/api/portfolio")
    async def get_portfolio():
        """Get current portfolio data."""
        # Return mock data if no portfolio manager
        if app.state.portfolio_manager is None:
            return {
                "total_value": "127834.56",
                "total_cost_basis": "100000.00",
                "total_unrealized_pnl": "27834.56",
                "total_unrealized_pnl_pct": 27.83,
                "total_realized_pnl_today": "1234.56",
                "holdings": {
                    "BTC": {
                        "amount": "1.5",
                        "price": "45000.00",
                        "current_value": "67500.00",
                        "cost_basis": "50000.00",
                        "unrealized_pnl": "17500.00",
                        "unrealized_pnl_pct": 35.0,
                    },
                    "ETH": {
                        "amount": "20.0",
                        "price": "2500.00",
                        "current_value": "50000.00",
                        "cost_basis": "40000.00",
                        "unrealized_pnl": "10000.00",
                        "unrealized_pnl_pct": 25.0,
                    },
                    "SOL": {
                        "amount": "100.0",
                        "price": "103.35",
                        "current_value": "10334.56",
                        "cost_basis": "10000.00",
                        "unrealized_pnl": "334.56",
                        "unrealized_pnl_pct": 3.35,
                    },
                },
            }

        # Get real data from portfolio manager
        try:
            portfolio = await app.state.portfolio_manager.get_portfolio_summary()
            return portfolio
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/analysis")
    async def get_analysis():
        """Get portfolio analysis."""
        return {
            "health_score": 78,
            "sharpe_ratio": 1.45,
            "max_drawdown": 18.5,
            "volatility": 42.3,
            "recommendations": [
                "Consider rebalancing - BTC allocation is above target",
                "Tax loss harvesting opportunity in SOL (-5% unrealized)",
                "Portfolio correlation is high - consider diversification",
            ],
        }

    @app.get("/api/tax/opportunities")
    async def get_tax_opportunities():
        """Get tax loss harvesting opportunities."""
        return {
            "ytd_realized_gains": "5000.00",
            "harvestable_losses": "2500.00",
            "estimated_tax_savings": "875.00",
            "opportunities": [],
        }

    @app.get("/api/alerts")
    async def get_alerts():
        """Get configured alerts."""
        return {
            "active_count": 3,
            "triggered_today": 1,
            "alerts": [
                {
                    "id": "1",
                    "asset": "BTC",
                    "condition": "above",
                    "price": 50000,
                    "active": True,
                },
            ],
        }

    @app.post("/api/alerts")
    async def create_alert(alert: AlertCreate):
        """Create a new price alert."""
        return {"id": "new_alert_id", "status": "created"}

    @app.websocket("/ws/portfolio")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates."""
        await websocket.accept()
        client_id = str(id(websocket))
        app.state.connected_clients.add(websocket)

        try:
            # Send initial snapshot
            portfolio_data = await get_portfolio()
            await websocket.send_json({
                "type": "initial_snapshot",
                "data": portfolio_data,
            })

            # Keep connection alive and handle messages
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    # Handle subscription changes
                    if message.get("action") == "ping":
                        await websocket.send_json({"type": "pong"})

                except Exception:
                    break

        except WebSocketDisconnect:
            pass
        finally:
            app.state.connected_clients.discard(websocket)

    @app.on_event("startup")
    async def startup():
        """Start background tasks."""
        # Start price update broadcast loop
        asyncio.create_task(broadcast_updates(app))

    return app


async def broadcast_updates(app: "FastAPI"):
    """Periodically broadcast updates to all connected clients."""
    import random

    while True:
        await asyncio.sleep(5)  # Update every 5 seconds

        if not app.state.connected_clients:
            continue

        # Generate mock portfolio update
        update = {
            "type": "portfolio_update",
            "data": {
                "total_value": str(127834.56 + random.uniform(-500, 500)),
                "total_cost_basis": "100000.00",
                "total_unrealized_pnl": str(27834.56 + random.uniform(-500, 500)),
                "total_unrealized_pnl_pct": 27.83 + random.uniform(-1, 1),
                "total_realized_pnl_today": "1234.56",
                "holdings": {
                    "BTC": {
                        "amount": "1.5",
                        "price": str(45000 + random.uniform(-200, 200)),
                        "current_value": str(67500 + random.uniform(-300, 300)),
                        "cost_basis": "50000.00",
                        "unrealized_pnl": str(17500 + random.uniform(-300, 300)),
                        "unrealized_pnl_pct": 35.0 + random.uniform(-1, 1),
                    },
                    "ETH": {
                        "amount": "20.0",
                        "price": str(2500 + random.uniform(-20, 20)),
                        "current_value": str(50000 + random.uniform(-400, 400)),
                        "cost_basis": "40000.00",
                        "unrealized_pnl": str(10000 + random.uniform(-400, 400)),
                        "unrealized_pnl_pct": 25.0 + random.uniform(-1, 1),
                    },
                    "SOL": {
                        "amount": "100.0",
                        "price": str(103.35 + random.uniform(-2, 2)),
                        "current_value": str(10334.56 + random.uniform(-200, 200)),
                        "cost_basis": "10000.00",
                        "unrealized_pnl": str(334.56 + random.uniform(-200, 200)),
                        "unrealized_pnl_pct": 3.35 + random.uniform(-2, 2),
                    },
                },
                "timestamp": datetime.now().isoformat(),
            },
        }

        # Broadcast to all clients
        disconnected = set()
        for client in app.state.connected_clients:
            try:
                await client.send_json(update)
            except Exception:
                disconnected.add(client)

        # Remove disconnected clients
        app.state.connected_clients -= disconnected


def run_dashboard(
    host: str = "0.0.0.0",
    port: int = 8080,
    portfolio_manager=None,
):
    """
    Run the dashboard server.

    Args:
        host: Host to bind to
        port: Port to listen on
        portfolio_manager: Optional portfolio manager instance
    """
    import uvicorn

    app = create_dashboard_app(portfolio_manager)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_dashboard()
