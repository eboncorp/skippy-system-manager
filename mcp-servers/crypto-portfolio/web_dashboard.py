"""
Web Dashboard for Crypto Portfolio Manager.

A modern, responsive web interface built with FastAPI and vanilla JS.
Provides real-time portfolio monitoring, analysis tools, and trading interface.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# FastAPI and related imports
try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse
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

        /* Score gauge */
        .score-gauge {
            text-align: center;
            padding: 1rem;
        }

        .gauge-value {
            font-size: 3rem;
            font-weight: 700;
        }

        .gauge-label {
            color: var(--text-secondary);
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }

        /* Category bars */
        .category-bar {
            margin-bottom: 0.75rem;
        }

        .category-bar-header {
            display: flex;
            justify-content: space-between;
            font-size: 0.875rem;
            margin-bottom: 0.25rem;
        }

        .category-bar-track {
            height: 8px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            overflow: hidden;
        }

        .category-bar-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }

        /* Filter bar */
        .filter-bar {
            display: flex;
            gap: 0.75rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }

        .filter-bar select, .filter-bar input {
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 0.5rem 0.75rem;
            font-size: 0.875rem;
        }

        /* Pagination */
        .pagination {
            display: flex;
            justify-content: center;
            gap: 0.5rem;
            margin-top: 1rem;
        }

        .pagination button {
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 0.5rem 1rem;
            cursor: pointer;
        }

        .pagination button:disabled {
            opacity: 0.4;
            cursor: default;
        }

        .pagination .page-info {
            display: flex;
            align-items: center;
            color: var(--text-secondary);
            font-size: 0.875rem;
        }

        /* Chart canvas containers */
        .chart-wrapper {
            position: relative;
            height: 280px;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        }

        /* Recommendation card */
        .rec-card {
            background: var(--bg-tertiary);
            border-radius: 8px;
            padding: 1.25rem;
            margin-top: 1rem;
        }

        .rec-action {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }

        .rec-multiplier {
            font-size: 0.875rem;
            color: var(--text-secondary);
        }

        /* Two-column layout */
        .two-col {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }

        @media (max-width: 900px) {
            .two-col {
                grid-template-columns: 1fr;
            }
        }

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
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
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
            <a class="nav-item" data-page="signals">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M2 20h.01"></path>
                    <path d="M7 20v-4"></path>
                    <path d="M12 20v-8"></path>
                    <path d="M17 20V8"></path>
                    <path d="M22 4v16"></path>
                </svg>
                Signals
            </a>
            <a class="nav-item" data-page="history">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12,6 12,12 16,14"></polyline>
                </svg>
                History
            </a>
            <a class="nav-item" data-page="etf">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                </svg>
                ETF Manager
            </a>
            <a class="nav-item" data-page="trade">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="23,6 13.5,15.5 8.5,10.5 1,18"></polyline>
                    <polyline points="17,6 23,6 23,12"></polyline>
                </svg>
                Trade
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
            <a class="nav-item" data-page="system">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
                    <line x1="8" y1="21" x2="16" y2="21"></line>
                    <line x1="12" y1="17" x2="12" y2="21"></line>
                </svg>
                System
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

            <!-- Signals Page -->
            <div id="page-signals" class="page">
                <div class="filter-bar">
                    <select id="signal-asset-select" onchange="Dashboard.loadSignals()">
                        <option value="BTC">Bitcoin (BTC)</option>
                        <option value="ETH">Ethereum (ETH)</option>
                        <option value="SOL">Solana (SOL)</option>
                        <option value="AVAX">Avalanche (AVAX)</option>
                        <option value="LINK">Chainlink (LINK)</option>
                        <option value="DOT">Polkadot (DOT)</option>
                    </select>
                    <button class="btn btn-primary" onclick="Dashboard.loadSignals()">Analyze</button>
                </div>

                <div class="two-col">
                    <div class="card">
                        <div class="card-title">Composite Score</div>
                        <div class="score-gauge">
                            <div class="gauge-value" id="signal-score">--</div>
                            <div class="gauge-label" id="signal-score-label">Select an asset to analyze</div>
                        </div>
                    </div>
                    <div class="card">
                        <div class="card-title">Recommendation</div>
                        <div class="rec-card">
                            <div class="rec-action" id="signal-action">--</div>
                            <div class="rec-multiplier" id="signal-multiplier">DCA Multiplier: --</div>
                            <div style="margin-top: 0.75rem; color: var(--text-secondary); font-size: 0.875rem;" id="signal-reasoning">--</div>
                        </div>
                    </div>
                </div>

                <div class="card" style="margin-top: 1rem;">
                    <div class="card-title">Signal Categories (<span id="signal-count">0</span> signals)</div>
                    <div id="signal-categories" style="margin-top: 0.75rem;">
                        <p style="color: var(--text-secondary);">Click Analyze to load signal data</p>
                    </div>
                </div>
            </div>

            <!-- History Page -->
            <div id="page-history" class="page">
                <div class="filter-bar">
                    <select id="history-exchange-filter" onchange="Dashboard.loadHistory()">
                        <option value="">All Exchanges</option>
                    </select>
                    <select id="history-asset-filter" onchange="Dashboard.loadHistory()">
                        <option value="">All Assets</option>
                    </select>
                    <select id="history-type-filter" onchange="Dashboard.loadHistory()">
                        <option value="">All Types</option>
                        <option value="buy">Buy</option>
                        <option value="sell">Sell</option>
                        <option value="transfer">Transfer</option>
                        <option value="staking_reward">Staking Reward</option>
                    </select>
                </div>

                <div class="card-grid" style="grid-template-columns: repeat(3, 1fr);">
                    <div class="card">
                        <div class="card-title">Total Transactions</div>
                        <div class="card-value" id="history-total">0</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Total Volume</div>
                        <div class="card-value" id="history-volume">$0.00</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Showing</div>
                        <div class="card-value" id="history-showing">0</div>
                    </div>
                </div>

                <div class="holdings-section">
                    <div class="section-header">Transaction History</div>
                    <table class="holdings-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Exchange</th>
                                <th>Asset</th>
                                <th>Type</th>
                                <th>Amount</th>
                                <th>Price</th>
                                <th>Total</th>
                            </tr>
                        </thead>
                        <tbody id="history-body">
                            <tr><td colspan="7" style="text-align:center; color: var(--text-secondary);">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
                <div class="pagination">
                    <button id="history-prev" onclick="Dashboard.historyPrev()" disabled>Previous</button>
                    <span class="page-info" id="history-page-info">Page 1</span>
                    <button id="history-next" onclick="Dashboard.historyNext()">Next</button>
                </div>
            </div>

            <!-- ETF Manager Page -->
            <div id="page-etf" class="page">
                <div class="card-grid">
                    <div class="card">
                        <div class="card-title">ETF NAV</div>
                        <div class="card-value" id="etf-nav">$0.00</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Assets</div>
                        <div class="card-value" id="etf-assets-count">0</div>
                    </div>
                    <div class="card">
                        <div class="card-title">War Chest</div>
                        <div class="card-value" id="etf-war-chest">$0.00</div>
                        <div class="card-change" id="etf-war-chest-pct">0%</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Fear & Greed</div>
                        <div class="card-value" id="etf-fear-greed">--</div>
                        <div class="card-change" id="etf-fg-rule">--</div>
                    </div>
                </div>

                <div class="two-col">
                    <div class="chart-wrapper">
                        <canvas id="etf-allocation-chart"></canvas>
                    </div>
                    <div class="card">
                        <div class="card-title">Category Breakdown</div>
                        <div id="etf-categories" style="margin-top: 0.75rem;"></div>
                    </div>
                </div>

                <div class="holdings-section" style="margin-top: 1rem;">
                    <div class="section-header">Allocation Details</div>
                    <table class="holdings-table">
                        <thead>
                            <tr>
                                <th>Asset</th>
                                <th>Category</th>
                                <th>Target %</th>
                                <th>Current %</th>
                                <th>Drift</th>
                                <th>Value</th>
                            </tr>
                        </thead>
                        <tbody id="etf-alloc-body">
                            <tr><td colspan="6" style="text-align:center; color: var(--text-secondary);">Loading ETF data...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Trade Page -->
            <div id="page-trade" class="page">
                <div class="card-grid">
                    <div class="card">
                        <h3 style="margin-bottom: 1rem;">Paper Trade</h3>
                        <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                            <select id="trade-asset" style="background: var(--bg-tertiary); color: var(--text-primary); border: 1px solid var(--border-color); border-radius: 6px; padding: 0.5rem;">
                                <option value="BTC">BTC</option>
                                <option value="ETH">ETH</option>
                                <option value="SOL">SOL</option>
                            </select>
                            <input type="number" id="trade-amount" placeholder="Amount (USD)" style="background: var(--bg-tertiary); color: var(--text-primary); border: 1px solid var(--border-color); border-radius: 6px; padding: 0.5rem;">
                            <div style="display: flex; gap: 0.5rem;">
                                <button class="btn btn-primary" style="flex:1; background: var(--accent-green);" onclick="Dashboard.submitTrade('buy')">Buy</button>
                                <button class="btn btn-primary" style="flex:1; background: var(--accent-red);" onclick="Dashboard.submitTrade('sell')">Sell</button>
                            </div>
                        </div>
                        <p style="margin-top: 0.75rem; font-size: 0.75rem; color: var(--text-secondary);">Paper trading only - no real orders placed</p>
                    </div>
                    <div class="card">
                        <div class="card-title">DCA Status</div>
                        <div id="trade-dca-status" style="margin-top: 0.5rem; color: var(--text-secondary);">
                            No active DCA bots configured
                        </div>
                    </div>
                </div>

                <div class="holdings-section" style="margin-top: 1rem;">
                    <div class="section-header">Recent Paper Trades</div>
                    <table class="holdings-table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Asset</th>
                                <th>Side</th>
                                <th>Amount</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="trade-history-body">
                            <tr><td colspan="5" style="text-align:center; color: var(--text-secondary);">No paper trades yet</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Settings Page -->
            <div id="page-settings" class="page">
                <div class="card">
                    <h3 style="margin-bottom: 1rem;">Dashboard Settings</h3>
                    <p style="color: var(--text-secondary);">Settings will be available here.</p>
                </div>
            </div>

            <!-- System Page -->
            <div id="page-system" class="page">
                <div class="stats-grid">
                    <div class="card">
                        <div class="card-label">Cache Backend</div>
                        <div class="card-value" id="sys-cache-backend">--</div>
                        <div class="card-change" id="sys-cache-hit-rate">Hit rate: --</div>
                    </div>
                    <div class="card">
                        <div class="card-label">Active Jobs</div>
                        <div class="card-value" id="sys-active-jobs">--</div>
                        <div class="card-change" id="sys-jobs-success">Success rate: --</div>
                    </div>
                    <div class="card">
                        <div class="card-label">API Requests</div>
                        <div class="card-value" id="sys-api-requests">--</div>
                        <div class="card-change" id="sys-api-errors">Errors: --</div>
                    </div>
                    <div class="card">
                        <div class="card-label">Uptime</div>
                        <div class="card-value" id="sys-uptime">--</div>
                        <div class="card-change" id="sys-version">--</div>
                    </div>
                </div>

                <!-- Health Checks -->
                <div class="card" style="margin-bottom: 1rem;">
                    <h3 style="margin-bottom: 1rem;">Health Checks</h3>
                    <div id="sys-health-checks" style="display: grid; gap: 0.5rem;">
                        <p style="color: var(--text-secondary);">Loading health checks...</p>
                    </div>
                </div>

                <!-- Job Scheduler -->
                <div class="card" style="margin-bottom: 1rem;">
                    <h3 style="margin-bottom: 1rem;">Job Scheduler</h3>
                    <div style="overflow-x: auto;">
                        <table>
                            <thead>
                                <tr>
                                    <th>Job Name</th>
                                    <th>Interval</th>
                                    <th>Last Run</th>
                                    <th>Next Run</th>
                                    <th>Runs</th>
                                    <th>Failures</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody id="sys-jobs-body">
                                <tr><td colspan="7" style="text-align: center; color: var(--text-secondary);">Loading...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Notification Channels -->
                <div class="card" style="margin-bottom: 1rem;">
                    <h3 style="margin-bottom: 1rem;">Notification Channels</h3>
                    <div id="sys-notification-channels" style="display: grid; gap: 0.5rem;">
                        <p style="color: var(--text-secondary);">Loading channels...</p>
                    </div>
                </div>

                <!-- Cache Stats -->
                <div class="card">
                    <h3 style="margin-bottom: 1rem;">Cache Statistics</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;" id="sys-cache-details">
                        <p style="color: var(--text-secondary);">Loading cache stats...</p>
                    </div>
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
                    signals: 'Signal Analysis',
                    history: 'Transaction History',
                    etf: 'GTI Virtual ETF',
                    trade: 'Paper Trading',
                    alerts: 'Alerts',
                    settings: 'Settings',
                    system: 'System Status'
                };
                document.getElementById('page-title').textContent = titles[pageId] || pageId;

                // Load page-specific data on first visit
                if (pageId === 'history' && !this._historyLoaded) {
                    this.loadHistory();
                    this._historyLoaded = true;
                }
                if (pageId === 'etf' && !this._etfLoaded) {
                    this.loadETF();
                    this._etfLoaded = true;
                }
                if (pageId === 'tax' && !this._taxLoaded) {
                    this.loadTax();
                    this._taxLoaded = true;
                }
                if (pageId === 'system' && !this._systemLoaded) {
                    this.loadSystem();
                    this._systemLoaded = true;
                }
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

            // ---- Signals page ----

            async loadSignals() {
                const asset = document.getElementById('signal-asset-select').value;
                document.getElementById('signal-score').textContent = '...';
                document.getElementById('signal-score-label').textContent = 'Analyzing ' + asset + '...';

                try {
                    const res = await fetch('/api/signals/' + encodeURIComponent(asset));
                    if (!res.ok) throw new Error('Failed');
                    const data = await res.json();

                    if (data.error) {
                        document.getElementById('signal-score').textContent = 'N/A';
                        document.getElementById('signal-score-label').textContent = data.error;
                        return;
                    }

                    const score = data.composite_score;
                    const scoreEl = document.getElementById('signal-score');
                    scoreEl.textContent = score.toFixed(1);
                    scoreEl.className = 'gauge-value ' + (score > 20 ? 'negative' : score < -20 ? 'positive' : '');

                    let label = 'Neutral';
                    if (score <= -60) label = 'Extreme Fear';
                    else if (score <= -40) label = 'Fear';
                    else if (score <= -20) label = 'Mild Fear';
                    else if (score <= 0) label = 'Slight Fear';
                    else if (score <= 20) label = 'Neutral';
                    else if (score <= 40) label = 'Mild Greed';
                    else if (score <= 60) label = 'Greed';
                    else label = 'Extreme Greed';
                    document.getElementById('signal-score-label').textContent = label;

                    document.getElementById('signal-action').textContent = data.recommendation?.action || '--';
                    document.getElementById('signal-multiplier').textContent =
                        'DCA Multiplier: ' + (data.recommendation?.dca_multiplier?.toFixed(2) || '--') + 'x';
                    document.getElementById('signal-reasoning').textContent =
                        data.recommendation?.reasoning || '';
                    document.getElementById('signal-count').textContent = data.signal_count || 0;

                    // Render category bars (data is from our own API - safe numeric values)
                    const catDiv = document.getElementById('signal-categories');
                    this._renderCategoryBars(catDiv, data.categories);
                } catch (e) {
                    document.getElementById('signal-score').textContent = 'Error';
                    document.getElementById('signal-score-label').textContent = 'Failed to load signal data';
                    console.error('Signal load error:', e);
                }
            },

            _renderCategoryBars(container, categories) {
                while (container.firstChild) container.removeChild(container.firstChild);
                if (!categories) return;

                Object.entries(categories).forEach(([name, cat]) => {
                    const avg = cat.average_score || 0;
                    const pct = Math.min(100, Math.max(0, (avg + 100) / 2));
                    const color = avg < -20 ? 'var(--accent-green)' : avg > 20 ? 'var(--accent-red)' : 'var(--accent-blue)';

                    const bar = document.createElement('div');
                    bar.className = 'category-bar';

                    const header = document.createElement('div');
                    header.className = 'category-bar-header';
                    const nameSpan = document.createElement('span');
                    nameSpan.textContent = name + ' (' + cat.count + ')';
                    const valSpan = document.createElement('span');
                    valSpan.textContent = (avg > 0 ? '+' : '') + avg.toFixed(1);
                    header.appendChild(nameSpan);
                    header.appendChild(valSpan);

                    const track = document.createElement('div');
                    track.className = 'category-bar-track';
                    const fill = document.createElement('div');
                    fill.className = 'category-bar-fill';
                    fill.style.width = pct + '%';
                    fill.style.background = color;
                    track.appendChild(fill);

                    bar.appendChild(header);
                    bar.appendChild(track);
                    container.appendChild(bar);
                });
            },

            // ---- History page ----

            _historyOffset: 0,
            _historyLimit: 50,
            _historyTotal: 0,
            _historyLoaded: false,

            async loadHistory() {
                const exchange = document.getElementById('history-exchange-filter').value;
                const asset = document.getElementById('history-asset-filter').value;
                const txType = document.getElementById('history-type-filter').value;

                const params = new URLSearchParams({
                    limit: this._historyLimit,
                    offset: this._historyOffset,
                });
                if (exchange) params.set('exchange', exchange);
                if (asset) params.set('asset', asset);
                if (txType) params.set('tx_type', txType);

                try {
                    const res = await fetch('/api/history?' + params);
                    if (!res.ok) throw new Error('Failed');
                    const data = await res.json();

                    this._historyTotal = data.total;
                    document.getElementById('history-total').textContent = data.total;
                    document.getElementById('history-showing').textContent = data.transactions.length;

                    let volume = 0;
                    const tbody = document.getElementById('history-body');
                    while (tbody.firstChild) tbody.removeChild(tbody.firstChild);

                    if (data.transactions.length === 0) {
                        const row = tbody.insertRow();
                        const cell = row.insertCell();
                        cell.colSpan = 7;
                        cell.style.textAlign = 'center';
                        cell.style.color = 'var(--text-secondary)';
                        cell.textContent = 'No transactions found';
                    } else {
                        data.transactions.forEach(tx => {
                            const totalUsd = parseFloat(tx.total_usd) || 0;
                            volume += Math.abs(totalUsd);
                            const row = tbody.insertRow();
                            const cells = [
                                new Date(tx.timestamp).toLocaleDateString(),
                                tx.exchange,
                                tx.asset,
                                tx.tx_type,
                                parseFloat(tx.amount).toFixed(6),
                                this.formatCurrency(tx.price_usd),
                                this.formatCurrency(totalUsd),
                            ];
                            cells.forEach((text, i) => {
                                const cell = row.insertCell();
                                cell.textContent = text;
                                if (i === 3) {
                                    cell.className = tx.tx_type === 'buy' ? 'positive' : tx.tx_type === 'sell' ? 'negative' : '';
                                }
                            });
                        });
                    }
                    document.getElementById('history-volume').textContent = this.formatCurrency(volume);

                    const page = Math.floor(this._historyOffset / this._historyLimit) + 1;
                    const totalPages = Math.ceil(this._historyTotal / this._historyLimit) || 1;
                    document.getElementById('history-page-info').textContent = 'Page ' + page + ' of ' + totalPages;
                    document.getElementById('history-prev').disabled = this._historyOffset === 0;
                    document.getElementById('history-next').disabled = this._historyOffset + this._historyLimit >= this._historyTotal;
                } catch (e) {
                    console.error('History load error:', e);
                }
            },

            historyPrev() {
                this._historyOffset = Math.max(0, this._historyOffset - this._historyLimit);
                this.loadHistory();
            },

            historyNext() {
                this._historyOffset += this._historyLimit;
                this.loadHistory();
            },

            // ---- ETF page ----

            _etfLoaded: false,
            _etfChart: null,

            async loadETF() {
                try {
                    const res = await fetch('/api/etf/status');
                    if (!res.ok) throw new Error('Failed');
                    const data = await res.json();

                    if (!data.available) {
                        document.getElementById('etf-nav').textContent = 'N/A';
                        document.getElementById('etf-assets-count').textContent = data.error || 'Not available';
                        return;
                    }

                    document.getElementById('etf-nav').textContent = this.formatCurrency(data.nav_usd);
                    document.getElementById('etf-assets-count').textContent = data.assets_count;
                    document.getElementById('etf-war-chest').textContent = this.formatCurrency(data.war_chest_usd);
                    document.getElementById('etf-war-chest-pct').textContent = data.war_chest_pct.toFixed(1) + '%';
                    document.getElementById('etf-fear-greed').textContent = data.fear_greed;
                    document.getElementById('etf-fg-rule').textContent = data.war_chest_rule;

                    // Category breakdown bars
                    const catDiv = document.getElementById('etf-categories');
                    this._renderETFCategories(catDiv, data.categories);

                    // Allocation table
                    this._renderETFAllocTable(data.allocations);

                    // Donut chart
                    this.renderETFChart(data);
                } catch (e) {
                    console.error('ETF load error:', e);
                }
            },

            _renderETFCategories(container, categories) {
                while (container.firstChild) container.removeChild(container.firstChild);
                if (!categories) return;

                Object.entries(categories).forEach(([name, cat]) => {
                    const current = parseFloat(cat.current_pct) || 0;
                    const target = parseFloat(cat.target_pct) || 0;
                    const drift = parseFloat(cat.drift_pct) || 0;
                    const color = drift > 2 ? 'var(--accent-red)' : drift < -2 ? 'var(--accent-green)' : 'var(--accent-blue)';

                    const bar = document.createElement('div');
                    bar.className = 'category-bar';

                    const header = document.createElement('div');
                    header.className = 'category-bar-header';
                    const nameSpan = document.createElement('span');
                    nameSpan.textContent = name + ' (' + cat.assets + ')';
                    const valSpan = document.createElement('span');
                    valSpan.textContent = current.toFixed(1) + '% / ' + target + '% (' + (drift > 0 ? '+' : '') + drift.toFixed(1) + '%)';
                    header.appendChild(nameSpan);
                    header.appendChild(valSpan);

                    const track = document.createElement('div');
                    track.className = 'category-bar-track';
                    const fill = document.createElement('div');
                    fill.className = 'category-bar-fill';
                    fill.style.width = current + '%';
                    fill.style.background = color;
                    track.appendChild(fill);

                    bar.appendChild(header);
                    bar.appendChild(track);
                    container.appendChild(bar);
                });
            },

            _renderETFAllocTable(allocations) {
                const tbody = document.getElementById('etf-alloc-body');
                while (tbody.firstChild) tbody.removeChild(tbody.firstChild);

                if (!allocations || allocations.length === 0) {
                    const row = tbody.insertRow();
                    const cell = row.insertCell();
                    cell.colSpan = 6;
                    cell.style.textAlign = 'center';
                    cell.style.color = 'var(--text-secondary)';
                    cell.textContent = 'No allocation data';
                    return;
                }

                allocations
                    .sort((a, b) => Math.abs(b.drift_pct) - Math.abs(a.drift_pct))
                    .forEach(a => {
                        const row = tbody.insertRow();
                        const driftClass = a.drift_pct > 2 ? 'negative' : a.drift_pct < -2 ? 'positive' : '';
                        const cells = [
                            a.symbol + (a.is_locked ? ' (locked)' : ''),
                            a.category,
                            a.target_pct.toFixed(1) + '%',
                            a.current_pct.toFixed(1) + '%',
                            (a.drift_pct > 0 ? '+' : '') + a.drift_pct.toFixed(1) + '%',
                            this.formatCurrency(a.current_value_usd),
                        ];
                        cells.forEach((text, i) => {
                            const cell = row.insertCell();
                            cell.textContent = text;
                            if (i === 4) cell.className = driftClass;
                        });
                    });
            },

            renderETFChart(data) {
                if (typeof Chart === 'undefined' || !data.categories) return;

                const canvas = document.getElementById('etf-allocation-chart');
                if (!canvas) return;

                if (this._etfChart) this._etfChart.destroy();

                const labels = Object.keys(data.categories);
                const values = labels.map(k => parseFloat(data.categories[k].value_usd) || 0);
                const colors = [
                    '#58a6ff', '#3fb950', '#d29922', '#f85149',
                    '#bc8cff', '#f778ba', '#79c0ff', '#56d364',
                    '#e3b341', '#ff7b72', '#d2a8ff', '#db61a2'
                ];

                this._etfChart = new Chart(canvas, {
                    type: 'doughnut',
                    data: {
                        labels: labels,
                        datasets: [{
                            data: values,
                            backgroundColor: colors.slice(0, labels.length),
                            borderColor: '#161b22',
                            borderWidth: 2,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'right',
                                labels: { color: '#8b949e', font: { size: 11 } }
                            }
                        }
                    }
                });
            },

            // ---- Tax page ----

            _taxLoaded: false,

            async loadTax() {
                try {
                    const [summaryRes, lotsRes] = await Promise.all([
                        fetch('/api/tax/summary'),
                        fetch('/api/tax/lots'),
                    ]);

                    if (summaryRes.ok) {
                        const summary = await summaryRes.json();
                        const totalNet = summary.total_net || 0;

                        document.getElementById('ytd-gains').textContent = this.formatCurrency(totalNet);
                        document.getElementById('ytd-gains').className = 'card-value ' + (totalNet >= 0 ? 'positive' : 'negative');

                        const harvestable = Math.abs((summary.short_term?.losses || 0) + (summary.long_term?.losses || 0));
                        document.getElementById('harvestable-losses').textContent = this.formatCurrency(harvestable);
                        document.getElementById('tax-savings').textContent = this.formatCurrency(harvestable * 0.35);
                    }

                    if (lotsRes.ok) {
                        const lots = await lotsRes.json();
                        const tbody = document.getElementById('tlh-body');
                        if (lots.lots && lots.lots.length > 0) {
                            const losers = lots.lots.filter(l => l.unrealized_gain < 0);
                            if (losers.length > 0) {
                                while (tbody.firstChild) tbody.removeChild(tbody.firstChild);
                                losers.forEach(l => {
                                    const row = tbody.insertRow();
                                    const cells = [
                                        l.asset,
                                        this.formatCurrency(l.unrealized_gain),
                                        l.unrealized_percent.toFixed(1) + '%',
                                        'Harvest loss',
                                        this.formatCurrency(Math.abs(l.unrealized_gain) * 0.35),
                                        'Review',
                                    ];
                                    cells.forEach((text, i) => {
                                        const cell = row.insertCell();
                                        if (i === 5) {
                                            const btn = document.createElement('button');
                                            btn.className = 'btn btn-primary';
                                            btn.style.fontSize = '0.75rem';
                                            btn.style.padding = '0.25rem 0.5rem';
                                            btn.disabled = true;
                                            btn.textContent = text;
                                            cell.appendChild(btn);
                                        } else {
                                            cell.textContent = text;
                                        }
                                        if (i === 1 || i === 2) cell.className = 'negative';
                                    });
                                });
                            }
                        }
                    }
                } catch (e) {
                    console.error('Tax load error:', e);
                }
            },

            // ---- Trade page ----

            _paperTrades: [],

            submitTrade(side) {
                const asset = document.getElementById('trade-asset').value;
                const amount = document.getElementById('trade-amount').value;
                if (!amount || isNaN(amount) || parseFloat(amount) <= 0) return;

                const trade = {
                    time: new Date().toLocaleTimeString(),
                    asset: asset,
                    side: side,
                    amount: parseFloat(amount),
                    status: 'Filled (paper)',
                };
                this._paperTrades.unshift(trade);
                if (this._paperTrades.length > 20) this._paperTrades.pop();

                const tbody = document.getElementById('trade-history-body');
                while (tbody.firstChild) tbody.removeChild(tbody.firstChild);
                this._paperTrades.forEach(t => {
                    const row = tbody.insertRow();
                    const cells = [t.time, t.asset, t.side.toUpperCase(), this.formatCurrency(t.amount), t.status];
                    cells.forEach((text, i) => {
                        const cell = row.insertCell();
                        cell.textContent = text;
                        if (i === 2) cell.className = t.side === 'buy' ? 'positive' : 'negative';
                    });
                });

                document.getElementById('trade-amount').value = '';
                this.addAlert('success', 'Paper ' + side, side.toUpperCase() + ' $' + amount + ' ' + asset);
            },

            // ---- System page ----

            _systemLoaded: false,

            async loadSystem() {
                const [healthRes, cacheRes, jobsRes, notifRes, metricsRes] = await Promise.allSettled([
                    fetch('/api/health'),
                    fetch('/api/cache/stats'),
                    fetch('/api/jobs/status'),
                    fetch('/api/notifications/channels'),
                    fetch('/api/metrics'),
                ]);

                // Health checks
                if (healthRes.status === 'fulfilled' && healthRes.value.ok) {
                    const health = await healthRes.value.json();
                    const container = document.getElementById('sys-health-checks');
                    while (container.firstChild) container.removeChild(container.firstChild);

                    if (health.checks && Object.keys(health.checks).length > 0) {
                        Object.entries(health.checks).forEach(([name, check]) => {
                            const row = document.createElement('div');
                            row.style.cssText = 'display:flex;align-items:center;gap:0.75rem;padding:0.5rem 0;border-bottom:1px solid var(--border-color)';
                            const dot = document.createElement('span');
                            dot.style.cssText = 'width:10px;height:10px;border-radius:50%;flex-shrink:0;background:' +
                                (check.status === 'healthy' ? 'var(--accent-green)' : check.status === 'degraded' ? 'var(--accent-yellow)' : 'var(--accent-red)');
                            const label = document.createElement('span');
                            label.style.cssText = 'flex:1;color:var(--text-primary)';
                            label.textContent = name;
                            const status = document.createElement('span');
                            status.style.cssText = 'color:var(--text-secondary);font-size:0.85rem';
                            status.textContent = check.status + (check.response_time ? ' (' + check.response_time.toFixed(0) + 'ms)' : '');
                            row.appendChild(dot);
                            row.appendChild(label);
                            row.appendChild(status);
                            container.appendChild(row);
                        });
                    } else {
                        container.innerHTML = '<p style="color:var(--text-secondary)">No health checks configured</p>';
                    }
                    document.getElementById('sys-uptime').textContent = health.status === 'healthy' ? 'Healthy' : health.status || '--';
                }

                // Cache stats
                if (cacheRes.status === 'fulfilled' && cacheRes.value.ok) {
                    const cache = await cacheRes.value.json();
                    document.getElementById('sys-cache-backend').textContent = cache.backend || 'memory';
                    const hitRate = cache.hit_rate != null ? cache.hit_rate.toFixed(1) + '%' : '--';
                    document.getElementById('sys-cache-hit-rate').textContent = 'Hit rate: ' + hitRate;

                    const details = document.getElementById('sys-cache-details');
                    while (details.firstChild) details.removeChild(details.firstChild);
                    const stats = [
                        ['Keys', cache.keys || 0],
                        ['Hits', cache.hits || 0],
                        ['Misses', cache.misses || 0],
                        ['Backend', cache.backend || 'memory'],
                    ];
                    stats.forEach(([label, value]) => {
                        const div = document.createElement('div');
                        div.innerHTML = '<div style="color:var(--text-secondary);font-size:0.8rem">' + label +
                            '</div><div style="color:var(--text-primary);font-size:1.2rem;font-weight:600">' + value + '</div>';
                        details.appendChild(div);
                    });
                }

                // Job scheduler
                if (jobsRes.status === 'fulfilled' && jobsRes.value.ok) {
                    const jobs = await jobsRes.value.json();
                    const tbody = document.getElementById('sys-jobs-body');
                    while (tbody.firstChild) tbody.removeChild(tbody.firstChild);

                    const jobList = jobs.jobs || [];
                    document.getElementById('sys-active-jobs').textContent = jobList.length;
                    let totalRuns = 0, totalFails = 0;

                    if (jobList.length === 0) {
                        const row = tbody.insertRow();
                        const cell = row.insertCell();
                        cell.colSpan = 7;
                        cell.style.textAlign = 'center';
                        cell.style.color = 'var(--text-secondary)';
                        cell.textContent = 'No jobs registered';
                    } else {
                        jobList.forEach(j => {
                            totalRuns += j.run_count || 0;
                            totalFails += j.failure_count || 0;
                            const row = tbody.insertRow();
                            const interval = j.interval ? j.interval + 's' : j.cron || '--';
                            const lastRun = j.last_run ? new Date(j.last_run).toLocaleTimeString() : 'Never';
                            const nextRun = j.next_run ? new Date(j.next_run).toLocaleTimeString() : '--';
                            const cells = [
                                j.name,
                                interval,
                                lastRun,
                                nextRun,
                                j.run_count || 0,
                                j.failure_count || 0,
                                j.enabled !== false ? 'Active' : 'Disabled',
                            ];
                            cells.forEach((text, i) => {
                                const cell = row.insertCell();
                                cell.textContent = text;
                                if (i === 5 && (j.failure_count || 0) > 0) cell.className = 'negative';
                                if (i === 6) cell.className = j.enabled !== false ? 'positive' : 'negative';
                            });
                        });
                    }
                    const successRate = totalRuns > 0 ? ((totalRuns - totalFails) / totalRuns * 100).toFixed(1) + '%' : '--';
                    document.getElementById('sys-jobs-success').textContent = 'Success rate: ' + successRate;
                }

                // Notification channels
                if (notifRes.status === 'fulfilled' && notifRes.value.ok) {
                    const notif = await notifRes.value.json();
                    const container = document.getElementById('sys-notification-channels');
                    while (container.firstChild) container.removeChild(container.firstChild);

                    const channels = notif.channels || {};
                    if (Object.keys(channels).length === 0) {
                        container.innerHTML = '<p style="color:var(--text-secondary)">No notification channels configured</p>';
                    } else {
                        Object.entries(channels).forEach(([name, info]) => {
                            const row = document.createElement('div');
                            row.style.cssText = 'display:flex;align-items:center;gap:0.75rem;padding:0.5rem 0;border-bottom:1px solid var(--border-color)';
                            const dot = document.createElement('span');
                            dot.style.cssText = 'width:10px;height:10px;border-radius:50%;flex-shrink:0;background:' +
                                (info.configured ? 'var(--accent-green)' : 'var(--accent-red)');
                            const label = document.createElement('span');
                            label.style.cssText = 'flex:1;color:var(--text-primary);text-transform:capitalize';
                            label.textContent = name;
                            const status = document.createElement('span');
                            status.style.cssText = 'color:var(--text-secondary);font-size:0.85rem';
                            status.textContent = info.configured ? 'Configured' : 'Not configured';
                            row.appendChild(dot);
                            row.appendChild(label);
                            row.appendChild(status);
                            container.appendChild(row);
                        });
                    }
                }

                // Metrics summary
                if (metricsRes.status === 'fulfilled' && metricsRes.value.ok) {
                    const metrics = await metricsRes.value.json();
                    const counters = metrics.counters || {};
                    const requests = counters.api_requests || counters.requests || 0;
                    const errors = counters.api_errors || counters.errors || 0;
                    document.getElementById('sys-api-requests').textContent = requests;
                    document.getElementById('sys-api-errors').textContent = 'Errors: ' + errors;
                    document.getElementById('sys-version').textContent = metrics.version || '';
                }
            },

            formatCurrency(value) {
                const num = typeof value === 'string' ? parseFloat(value) : value;
                if (isNaN(num)) return '$0.00';
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
    transaction_history=None,
    etf_manager=None,
    notification_manager=None,
    cache_manager=None,
    metrics_collector=None,
    health_checker=None,
    job_scheduler=None,
    allowed_origins: Optional[List[str]] = None,
) -> "FastAPI":
    """
    Create the FastAPI dashboard application.

    Args:
        portfolio_manager: Optional PortfolioAggregator instance for real data
        stream_manager: Optional real-time stream manager
        transaction_history: Optional TransactionHistory instance
        etf_manager: Optional GTIVirtualETF instance
        notification_manager: Optional NotificationManager instance
        cache_manager: Optional CacheManager instance
        metrics_collector: Optional MetricsCollector instance
        health_checker: Optional HealthChecker instance
        job_scheduler: Optional JobScheduler instance
        allowed_origins: List of allowed CORS origins (defaults to localhost only)

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

    # CORS middleware - restrict to specified origins for security
    # SECURITY: Do not use allow_origins=["*"] with allow_credentials=True
    # This combination allows any site to make authenticated requests
    cors_origins = allowed_origins or [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Check if we should allow all origins (development mode only)
    allow_all_origins = os.getenv("DASHBOARD_ALLOW_ALL_ORIGINS", "false").lower() == "true"

    if allow_all_origins:
        # Development mode: allow all origins but WITHOUT credentials
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,  # SECURITY: Never combine * with credentials
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization"],
        )
    else:
        # Production mode: restrict origins
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization"],
        )

    # SECURITY: Add security headers middleware
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        """Add security headers to all HTTP responses."""
        response = await call_next(request)

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enable XSS filter
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy (allows inline scripts and Chart.js CDN)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline'; "
            "connect-src 'self' ws: wss:; "
            "img-src 'self' data:; "
            "frame-ancestors 'none';"
        )

        # Strict Transport Security (for HTTPS deployments)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response

    # Store references
    app.state.portfolio_manager = portfolio_manager
    app.state.stream_manager = stream_manager
    app.state.transaction_history = transaction_history
    app.state.etf_manager = etf_manager
    app.state.notification_manager = notification_manager
    app.state.cache_manager = cache_manager
    app.state.metrics_collector = metrics_collector
    app.state.health_checker = health_checker
    app.state.job_scheduler = job_scheduler
    app.state.connected_clients = set()

    # Include API router with real data and infrastructure endpoints
    from dashboard_api import create_api_router
    api_router = create_api_router(
        portfolio_manager=portfolio_manager,
        transaction_history=transaction_history,
        etf_manager=etf_manager,
        notification_manager=notification_manager,
        cache_manager=cache_manager,
        metrics_collector=metrics_collector,
        health_checker=health_checker,
        job_scheduler=job_scheduler,
    )
    app.include_router(api_router)

    # Routes
    @app.get("/", response_class=HTMLResponse)
    async def dashboard_home():
        """Serve the main dashboard page."""
        return HTMLResponse(content=DASHBOARD_HTML)

    async def _fetch_portfolio_snapshot():
        """Fetch portfolio data for WebSocket broadcast."""
        from dashboard_api import _mock_portfolio, _record_snapshot, _get_24h_change
        pm = app.state.portfolio_manager
        if pm is None:
            return _mock_portfolio()

        try:
            raw_data = await pm.get_combined_portfolio()
            total_value = raw_data.get('total_value_usd', 0)
            _record_snapshot(total_value)
            change_24h, change_24h_pct = _get_24h_change()

            holdings = {}
            for asset, data in raw_data.get('by_asset', {}).items():
                bal = data.get('total_balance', 0)
                val = data.get('total_value_usd', 0)
                price = val / bal if bal > 0 else 0
                holdings[asset] = {
                    "amount": str(bal),
                    "price": str(round(price, 6)),
                    "current_value": str(round(val, 2)),
                    "cost_basis": "0",
                    "unrealized_pnl": "0",
                    "unrealized_pnl_pct": 0,
                }

            total_cost = sum(float(h['cost_basis']) for h in holdings.values())
            total_unrealized = sum(float(h['unrealized_pnl']) for h in holdings.values())
            total_unrealized_pct = (total_unrealized / total_cost * 100) if total_cost > 0 else 0

            return {
                "total_value": str(round(total_value, 2)),
                "total_cost_basis": str(round(total_cost, 2)),
                "total_unrealized_pnl": str(round(total_unrealized, 2)),
                "total_unrealized_pnl_pct": round(total_unrealized_pct, 2),
                "total_realized_pnl_today": "0",
                "change_24h": str(round(change_24h, 2)),
                "change_24h_pct": round(change_24h_pct, 2),
                "holdings": holdings,
                "timestamp": raw_data.get('timestamp', datetime.now().isoformat()),
            }
        except Exception:
            return _mock_portfolio()

    @app.websocket("/ws/portfolio")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates."""
        await websocket.accept()
        app.state.connected_clients.add(websocket)

        try:
            portfolio_data = await _fetch_portfolio_snapshot()
            await websocket.send_json({
                "type": "initial_snapshot",
                "data": portfolio_data,
            })

            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)
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
        asyncio.create_task(broadcast_updates(app))

    return app


async def broadcast_updates(app: "FastAPI"):
    """Periodically broadcast real portfolio updates to connected clients."""
    _last_value = None

    while True:
        await asyncio.sleep(60)  # Real data refresh every 60 seconds

        if not app.state.connected_clients:
            continue

        # Fetch real portfolio data
        pm = app.state.portfolio_manager
        if pm is not None:
            try:
                from dashboard_api import _record_snapshot, _get_24h_change

                raw_data = await pm.get_combined_portfolio()
                total_value = raw_data.get('total_value_usd', 0)
                _record_snapshot(total_value)
                change_24h, change_24h_pct = _get_24h_change()

                # Skip broadcast if value unchanged (within 0.1%)
                if _last_value is not None and total_value > 0:
                    delta_pct = abs(total_value - _last_value) / total_value * 100
                    if delta_pct < 0.1:
                        continue
                _last_value = total_value

                holdings = {}
                for asset, data in raw_data.get('by_asset', {}).items():
                    bal = data.get('total_balance', 0)
                    val = data.get('total_value_usd', 0)
                    price = val / bal if bal > 0 else 0
                    holdings[asset] = {
                        "amount": str(bal),
                        "price": str(round(price, 6)),
                        "current_value": str(round(val, 2)),
                        "cost_basis": "0",
                        "unrealized_pnl": "0",
                        "unrealized_pnl_pct": 0,
                    }

                update = {
                    "type": "portfolio_update",
                    "data": {
                        "total_value": str(round(total_value, 2)),
                        "total_cost_basis": "0",
                        "total_unrealized_pnl": "0",
                        "total_unrealized_pnl_pct": 0,
                        "total_realized_pnl_today": "0",
                        "change_24h": str(round(change_24h, 2)),
                        "change_24h_pct": round(change_24h_pct, 2),
                        "holdings": holdings,
                        "timestamp": datetime.now().isoformat(),
                    },
                }
            except Exception:
                continue
        else:
            # No portfolio manager - send mock heartbeat
            import random
            update = {
                "type": "portfolio_update",
                "data": {
                    "total_value": str(127834.56 + random.uniform(-500, 500)),
                    "total_cost_basis": "100000.00",
                    "total_unrealized_pnl": str(27834.56 + random.uniform(-500, 500)),
                    "total_unrealized_pnl_pct": 27.83 + random.uniform(-1, 1),
                    "total_realized_pnl_today": "0",
                    "change_24h": "0",
                    "change_24h_pct": 0,
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

        app.state.connected_clients -= disconnected


def run_dashboard(
    host: str = "0.0.0.0",
    port: int = 8080,
    portfolio_manager=None,
    transaction_history=None,
    etf_manager=None,
):
    """
    Run the dashboard server.

    Args:
        host: Host to bind to
        port: Port to listen on
        portfolio_manager: Optional PortfolioAggregator instance
        transaction_history: Optional TransactionHistory instance
        etf_manager: Optional GTIVirtualETF instance
    """
    import uvicorn

    app = create_dashboard_app(
        portfolio_manager=portfolio_manager,
        transaction_history=transaction_history,
        etf_manager=etf_manager,
    )
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    # Standalone mode - creates own data sources
    _pm = None
    _tx = None
    _etf = None

    try:
        from portfolio_aggregator import PortfolioAggregator
        _pm = PortfolioAggregator()
        print(f"Portfolio aggregator initialized ({len(_pm.exchanges)} exchanges)")
    except Exception as e:
        print(f"Portfolio aggregator not available: {e}")

    try:
        from transaction_history import TransactionHistory
        _tx = TransactionHistory()
        if _tx.load():
            print(f"Transaction history loaded ({len(_tx.transactions)} transactions)")
        else:
            print("Transaction history: no saved data")
    except Exception as e:
        print(f"Transaction history not available: {e}")

    try:
        from etf_manager import GTIVirtualETF
        _etf = GTIVirtualETF()
        print("ETF manager initialized")
    except Exception as e:
        print(f"ETF manager not available: {e}")

    print("Starting dashboard at http://localhost:8080")
    run_dashboard(
        portfolio_manager=_pm,
        transaction_history=_tx,
        etf_manager=_etf,
    )
