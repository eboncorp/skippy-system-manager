#!/usr/bin/env python3
"""
Web Dashboard for Intelligent File Processor
Lightweight Flask-based monitoring interface
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add core directory to path
sys.path.insert(0, str(Path(__file__).parent / 'core'))

try:
    from flask import Flask, render_template_string, jsonify, request
    from database import Database
    from config_loader import ConfigLoader
    import logging
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask not installed. Install with: pip install flask")
    sys.exit(1)


# Initialize Flask app
app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Load config and database
config = ConfigLoader()
db_path = config.get('logging.database', '/home/dave/skippy/logs/file_processor.db')
db = Database(db_path, logger)


# HTML Templates
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Intelligent File Processor - Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 32px; margin-bottom: 5px; }
        .header p { opacity: 0.9; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            margin-top: 5px;
        }
        .stat-label {
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .section h2 {
            margin-bottom: 15px;
            color: #333;
            font-size: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #666;
            border-bottom: 2px solid #dee2e6;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #e9ecef;
        }
        .confidence-bar {
            display: inline-block;
            height: 6px;
            background: #667eea;
            border-radius: 3px;
        }
        .status-success { color: #28a745; }
        .status-error { color: #dc3545; }
        .category-tag {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            background: #e7f3ff;
            color: #0066cc;
        }
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .refresh-btn:hover { background: #5568d3; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Intelligent File Processor</h1>
            <p>Real-time monitoring dashboard</p>
        </div>

        <div class="stats" id="stats">
            <div class="stat-card">
                <div class="stat-label">Total Processed</div>
                <div class="stat-value" id="total">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Success Rate</div>
                <div class="stat-value" id="success-rate">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Confidence</div>
                <div class="stat-value" id="confidence">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Quarantined</div>
                <div class="stat-value" id="quarantined">-</div>
            </div>
        </div>

        <div class="section">
            <h2>Recent Files</h2>
            <button class="refresh-btn" onclick="loadData()">🔄 Refresh</button>
            <table id="recent-files">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>File</th>
                        <th>Category</th>
                        <th>Confidence</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="files-body">
                    <tr><td colspan="5">Loading...</td></tr>
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>Classification Distribution</h2>
            <div id="category-chart"></div>
        </div>
    </div>

    <script>
        function loadData() {
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('total').textContent = data.total_processed;
                    const successRate = (data.successful / Math.max(data.total_processed, 1) * 100).toFixed(1);
                    document.getElementById('success-rate').textContent = successRate + '%';
                    document.getElementById('confidence').textContent = data.avg_confidence ? data.avg_confidence.toFixed(1) + '%' : '-';

                    // Get quarantine count
                    fetch('/api/quarantine')
                        .then(r => r.json())
                        .then(q => {
                            document.getElementById('quarantined').textContent = q.count;
                        });

                    // Category distribution
                    let chartHTML = '<div style="padding: 10px;">';
                    if (data.by_category) {
                        const total = Object.values(data.by_category).reduce((a, b) => a + b, 0);
                        for (const [cat, count] of Object.entries(data.by_category)) {
                            const pct = (count / total * 100);
                            chartHTML += `
                                <div style="margin-bottom: 10px;">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                        <span style="font-weight: 600;">${cat}</span>
                                        <span>${count} (${pct.toFixed(1)}%)</span>
                                    </div>
                                    <div style="background: #e9ecef; height: 8px; border-radius: 4px;">
                                        <div style="background: #667eea; height: 100%; width: ${pct}%; border-radius: 4px;"></div>
                                    </div>
                                </div>
                            `;
                        }
                    } else {
                        chartHTML += '<p style="color: #999;">No data yet</p>';
                    }
                    chartHTML += '</div>';
                    document.getElementById('category-chart').innerHTML = chartHTML;
                });

            fetch('/api/recent')
                .then(r => r.json())
                .then(data => {
                    const tbody = document.getElementById('files-body');
                    if (data.files.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="5" style="color: #999;">No files processed yet</td></tr>';
                        return;
                    }

                    tbody.innerHTML = data.files.map(f => {
                        const time = new Date(f.processed_at).toLocaleString();
                        const confBar = Math.floor(f.confidence / 10);
                        const status = f.success ? '<span class="status-success">✓</span>' : '<span class="status-error">✗</span>';

                        return `
                            <tr>
                                <td>${time}</td>
                                <td>${f.original_name}</td>
                                <td><span class="category-tag">${f.classification}</span></td>
                                <td>
                                    ${f.confidence.toFixed(0)}%
                                    <div class="confidence-bar" style="width: ${confBar * 10}px;"></div>
                                </td>
                                <td>${status}</td>
                            </tr>
                        `;
                    }).join('');
                });
        }

        // Load data on page load
        loadData();

        // Auto-refresh every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>
"""


@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template_string(DASHBOARD_TEMPLATE)


@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    stats = db.get_statistics(days=7)
    return jsonify(stats)


@app.route('/api/recent')
def api_recent():
    """API endpoint for recent files"""
    limit = request.args.get('limit', 20, type=int)
    files = db.get_recent_files(limit=limit)
    return jsonify({'files': files})


@app.route('/api/quarantine')
def api_quarantine():
    """API endpoint for quarantine queue"""
    queue = db.get_quarantine_queue(reviewed=False)
    return jsonify({
        'count': len(queue),
        'files': queue
    })


@app.route('/api/search')
def api_search():
    """API endpoint for search"""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 50, type=int)

    if not query:
        return jsonify({'error': 'No query provided'}), 400

    results = db.search_files(query, limit=limit)
    return jsonify({'results': results})


def main():
    """Run web dashboard"""
    import argparse

    parser = argparse.ArgumentParser(description='Intelligent File Processor Web Dashboard')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8765, help='Port to bind to (default: 8765)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    print("=" * 70)
    print(" Intelligent File Processor - Web Dashboard")
    print("=" * 70)
    print(f"\n🌐 Starting web server...")
    print(f"   URL: http://{args.host}:{args.port}")
    print(f"\n💡 Open this URL in your browser to view the dashboard")
    print(f"   Press Ctrl+C to stop\n")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
