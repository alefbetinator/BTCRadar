#!/usr/bin/env python3
"""
Bitcoin News Scanner Web UI

A simple web interface that displays recent opportunities
and allows clicking on them to open in the browser.
"""

import os
import sys
import json
from datetime import datetime
import threading
import time
import webbrowser
import signal
import subprocess
import argparse

from flask import Flask, render_template, jsonify, send_from_directory, url_for

from utils.db_manager import DatabaseManager
import config

DEFAULT_PORT = 7777

app = Flask(
    __name__, 
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
)

db_manager = DatabaseManager(config.DB_FILE)

scanner_process = None

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'), exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/opportunities')
def get_opportunities():
    opportunities = db_manager.get_recent_opportunities(24)
    
    for opp in opportunities:
        timestamp = opp.get('timestamp', '')
        try:
            date_obj = datetime.fromisoformat(timestamp)
            opp['formatted_time'] = date_obj.strftime("%m/%d %H:%M")
        except:
            opp['formatted_time'] = ""
    
    return jsonify({
        'opportunities': opportunities,
        'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'count': len(opportunities)
    })


@app.route('/api/refresh', methods=['GET'])
def refresh_data():
    try:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting refresh data...")
        
        main_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.py')
        
        cmd = [sys.executable, main_script, '--once']
        print(f"Running command: {' '.join(cmd)}")
        
        process = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            check=False  
        )
        
        print(f"Command stdout: {process.stdout}")
        print(f"Command stderr: {process.stderr}")
        print(f"Return code: {process.returncode}")
        
        if process.returncode != 0:
            print(f"WARNING: Refresh returned non-zero exit code: {process.returncode}")
            return jsonify({
                'status': 'error',
                'message': f"Refresh failed with exit code {process.returncode}. Check logs.",
                'stdout': process.stdout,
                'stderr': process.stderr,
                'return_code': process.returncode
            })
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Refresh completed successfully")
        
        return jsonify({
            'status': 'success',
            'message': 'Refresh completed successfully',
            'stdout': process.stdout,
            'stderr': process.stderr,
            'return_code': process.returncode
        })
        
    except Exception as e:
        print(f"ERROR during refresh: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        })


@app.route('/api/force_rescan', methods=['GET'])
def force_rescan():
    try:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting force rescan...")
        
        main_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.py')
        
        cmd = [sys.executable, main_script, '--once', '--force-rescan']
        print(f"Running command: {' '.join(cmd)}")
        
        process = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            check=False  
        )
        
        print(f"Command stdout: {process.stdout}")
        print(f"Command stderr: {process.stderr}")
        print(f"Return code: {process.returncode}")
        
        if process.returncode != 0:
            print(f"WARNING: Force rescan returned non-zero exit code: {process.returncode}")
            return jsonify({
                'status': 'error',
                'message': f"Force rescan failed with exit code {process.returncode}. Check logs.",
                'stdout': process.stdout,
                'stderr': process.stderr,
                'return_code': process.returncode
            })
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Force rescan completed successfully")
        
        return jsonify({
            'status': 'success',
            'message': 'Force rescan completed successfully',
            'stdout': process.stdout,
            'stderr': process.stderr,
            'return_code': process.returncode
        })
        
    except Exception as e:
        print(f"ERROR during force rescan: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        })


@app.route('/api/toggle_scanner', methods=['POST'])
def toggle_scanner():
    global scanner_process
    
    if scanner_process is None or scanner_process.poll() is not None:
        try:
            scanner_process = subprocess.Popen([
                sys.executable,
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.py')
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return jsonify({
                'status': 'success', 
                'running': True,
                'message': 'Scanner started'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f"Failed to start scanner: {str(e)}"
            })
    else:
        try:
            scanner_process.terminate()
            scanner_process = None
            return jsonify({
                'status': 'success',
                'running': False,
                'message': 'Scanner stopped'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f"Failed to stop scanner: {str(e)}"
            })


@app.route('/api/debug', methods=['GET'])
def debug():
    try:
        debug_info = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'environment': {},
            'database': {},
            'system': {}
        }
        
        debug_info['environment']['python_version'] = sys.version
        debug_info['environment']['python_path'] = sys.executable
        debug_info['environment']['working_directory'] = os.getcwd()
        
        main_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.py')
        debug_info['system']['main_script_exists'] = os.path.exists(main_script)
        debug_info['system']['main_script_path'] = main_script
        
        if os.path.exists(config.DB_FILE):
            db_size = os.path.getsize(config.DB_FILE)
            debug_info['database']['exists'] = True
            debug_info['database']['path'] = config.DB_FILE
            debug_info['database']['size'] = f"{db_size} bytes"
            
            with DatabaseManager(config.DB_FILE) as db:
                articles_count = len(db.get_all_articles())
                opportunities_count = len(db.get_opportunities(hours=24))
            debug_info['database']['articles_count'] = articles_count
            debug_info['database']['opportunities_count'] = opportunities_count
            debug_info['database']['status'] = 'ok'
        else:
            debug_info['database']['exists'] = False
            
        try:
            result = subprocess.run(
                [sys.executable, main_script, '--help'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=5  
            )
            debug_info['system']['main_script_executable'] = result.returncode == 0
            debug_info['system']['main_script_return_code'] = result.returncode
            debug_info['system']['main_script_error'] = result.stderr if result.stderr else None
        except Exception as e:
            debug_info['system']['main_script_executable'] = False
            debug_info['system']['main_script_error'] = str(e)
            
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })


def create_template_files():
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bitcoin News Scanner</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="container">
        <header>
            <h1>Bitcoin Investment Opportunities</h1>
            <div class="controls">
                <button id="refreshBtn">Refresh Data</button>
                <button id="forceRescanBtn">Force Rescan</button>
                <button id="scannerBtn">Start Scanner</button>
            </div>
        </header>
        
        <div class="status-bar">
            <span id="lastUpdated">Last updated: Never</span>
            <span id="opportunityCount">0 opportunities found</span>
            <span class="debug-link"><a href="/api/debug" target="_blank">Debug Info</a></span>
        </div>
        
        <div id="statusMessage" class="status-message hidden"></div>
        
        <div id="opportunitiesList" class="opportunities-list">
            <div class="loading">Loading opportunities...</div>
        </div>
        
        <footer>
            <p>Bitcoin News Scanner | Click on an opportunity to open in browser</p>
        </footer>
    </div>
    
    <script src="{{ url_for('static', filename='app.js') }}"></script>
</body>
</html>
"""
    
    with open(os.path.join(app.template_folder, 'index.html'), 'w') as f:
        f.write(index_html)
    
    css = """body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
    color: #333;
}

.container {
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
}

header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    background-color: #fff;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

h1 {
    margin: 0;
    font-size: 1.8rem;
    color: #2c3e50;
}

.controls {
    display: flex;
    gap: 10px;
}

button {
    padding: 8px 16px;
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
    transition: background-color 0.2s;
}

button:hover {
    background-color: #2980b9;
}

button:disabled {
    background-color: #95a5a6;
    cursor: not-allowed;
}

#scannerBtn.running {
    background-color: #e74c3c;
}

#scannerBtn.running:hover {
    background-color: #c0392b;
}

.status-bar {
    display: flex;
    justify-content: space-between;
    margin-bottom: 15px;
    font-size: 0.9rem;
    color: #7f8c8d;
    padding: 0 5px;
}

.debug-link a {
    color: #7f8c8d;
    text-decoration: none;
    font-size: 0.8rem;
}

.debug-link a:hover {
    text-decoration: underline;
    color: #3498db;
}

.status-message {
    background-color: #3498db;
    color: white;
    padding: 10px 15px;
    border-radius: 5px;
    margin-bottom: 15px;
    font-weight: bold;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.status-message.success {
    background-color: #2ecc71;
}

.status-message.error {
    background-color: #e74c3c;
}

.status-message.warning {
    background-color: #f39c12;
}

.status-message.hidden {
    display: none;
}

.status-message .spinner {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid rgba(255,255,255,0.3);
    border-radius: 50%;
    border-top-color: white;
    animation: spin 1s ease-in-out infinite;
}

.opportunities-list {
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    padding: 10px;
    min-height: 400px;
}

.loading {
    text-align: center;
    padding: 40px;
    color: #7f8c8d;
    font-style: italic;
}

.no-results {
    text-align: center;
    padding: 40px;
    color: #7f8c8d;
}

.opportunity-card {
    border-bottom: 1px solid #eee;
    padding: 15px 10px;
}

.opportunity-card:last-child {
    border-bottom: none;
}

.opportunity-title {
    font-weight: bold;
    font-size: 1.1rem;
    margin-bottom: 5px;
    color: #2980b9;
    cursor: pointer;
}

.opportunity-title:hover {
    text-decoration: underline;
}

.opportunity-meta {
    display: flex;
    justify-content: space-between;
    font-size: 0.8rem;
    color: #95a5a6;
    margin-bottom: 8px;
}

.opportunity-analysis {
    font-size: 0.95rem;
    line-height: 1.4;
    color: #555;
}

footer {
    margin-top: 20px;
    text-align: left;
    font-size: 0.8rem;
    color: #95a5a6;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}"""
    
    with open(os.path.join(app.static_folder, 'style.css'), 'w') as f:
        f.write(css)
    
    js = """// DOM Elements
const opportunitiesList = document.getElementById('opportunitiesList');
const lastUpdatedElement = document.getElementById('lastUpdated');
const opportunityCountElement = document.getElementById('opportunityCount');
const refreshBtn = document.getElementById('refreshBtn');
const forceRescanBtn = document.getElementById('forceRescanBtn');
const scannerBtn = document.getElementById('scannerBtn');
const statusMessage = document.getElementById('statusMessage');

// State
let isScanning = false;
let isRefreshing = false;
let autoRefreshInterval = null;

// Function to fetch opportunities
async function fetchOpportunities() {
    try {
        showStatus('Loading opportunities...', 'info');
        
        const response = await fetch('/api/opportunities');
        const data = await response.json();
        
        lastUpdatedElement.textContent = `Last updated: ${data.last_updated}`;
        opportunityCountElement.textContent = `${data.count} opportunities found`;
        
        opportunitiesList.innerHTML = '';
        
        if (data.opportunities.length === 0) {
            const noResults = document.createElement('div');
            noResults.className = 'no-results';
            noResults.textContent = 'No opportunities found in the last 24 hours.';
            opportunitiesList.appendChild(noResults);
            hideStatus();
            return;
        }
        
        // Sort opportunities by timestamp, newest first
        data.opportunities.sort((a, b) => {
            return new Date(b.timestamp) - new Date(a.timestamp);
        });
        
        data.opportunities.forEach((opp, index) => {
            const card = createOpportunityCard(opp, index + 1);
            opportunitiesList.appendChild(card);
        });
        
        hideStatus();
    } catch (error) {
        console.error('Error fetching opportunities:', error);
        opportunitiesList.innerHTML = `
            <div class="no-results">
                Error loading opportunities. Please try again.
            </div>
        `;
        showStatus('Error loading opportunities', 'error');
    }
}

// Show status message
function showStatus(message, type = 'info', showSpinner = true) {
    statusMessage.textContent = message;
    statusMessage.className = 'status-message';
    
    if (type) {
        statusMessage.classList.add(type);
    }
    
    if (showSpinner) {
        const spinner = document.createElement('span');
        spinner.className = 'spinner';
        statusMessage.appendChild(spinner);
    }
    
    statusMessage.classList.remove('hidden');
}

// Hide status message
function hideStatus() {
    statusMessage.classList.add('hidden');
}

// Function to create an opportunity card
function createOpportunityCard(opportunity, index) {
    const card = document.createElement('div');
    card.className = 'opportunity-card';
    
    const title = document.createElement('div');
    title.className = 'opportunity-title';
    title.textContent = `${index}. ${opportunity.article_title || 'Unnamed opportunity'}`;
    title.addEventListener('click', () => {
        window.open(opportunity.article_url, '_blank');
    });
    
    const meta = document.createElement('div');
    meta.className = 'opportunity-meta';
    
    const source = opportunity.article_source || 'Unknown';
    const formattedTime = opportunity.formatted_time || '';
    
    const sourceTime = document.createElement('span');
    sourceTime.textContent = `Source: ${source} | Found: ${formattedTime}`;
    
    const url = document.createElement('span');
    url.textContent = shortenUrl(opportunity.article_url || '#');
    
    meta.appendChild(sourceTime);
    meta.appendChild(url);
    
    const analysis = document.createElement('div');
    analysis.className = 'opportunity-analysis';
    analysis.textContent = opportunity.ai_analysis || '';
    
    card.appendChild(title);
    card.appendChild(meta);
    if (opportunity.ai_analysis) {
        card.appendChild(analysis);
    }
    
    return card;
}

// Function to shorten URL for display
function shortenUrl(url, maxLength = 60) {
    if (url.length <= maxLength) {
        return url;
    }
    
    if (url.includes('://')) {
        const [protocol, rest] = url.split('://', 2);
        if (rest.includes('/')) {
            const [domain, path] = rest.split('/', 2);
            const endPath = path.length > 20 ? `...${path.slice(-20)}` : path;
            return `${protocol}://${domain}/${endPath}`;
        }
    }
    
    return url.slice(0, maxLength - 3) + '...';
}

// Function to refresh data manually
async function refreshData() {
    if (isRefreshing) return;
    
    isRefreshing = true;
    disableButtons();
    showStatus('Refreshing data... This may take a moment.', 'info');
    
    try {
        const response = await fetch('/api/refresh');
        const data = await response.json();
        
        if (data.status === 'success') {
            showStatus('Data refreshed successfully!', 'success', false);
            setTimeout(hideStatus, 3000);
        } else {
            showStatus('Error refreshing data: ' + data.message, 'error', false);
        }
        
        await fetchOpportunities();
    } catch (error) {
        console.error('Error refreshing data:', error);
        showStatus('Error connecting to server', 'error', false);
    } finally {
        isRefreshing = false;
        enableButtons();
    }
}

// Function to force rescan
async function forceRescan() {
    if (isRefreshing) return;
    
    isRefreshing = true;
    disableButtons();
    showStatus('Running force rescan... This may take a few minutes.', 'warning');
    
    try {
        const response = await fetch('/api/force_rescan');
        const data = await response.json();
        
        if (data.status === 'success') {
            showStatus('Force rescan completed successfully!', 'success', false);
            setTimeout(hideStatus, 3000);
        } else {
            showStatus('Error during force rescan: ' + data.message, 'error', false);
        }
        
        await fetchOpportunities();
    } catch (error) {
        console.error('Error during force rescan:', error);
        showStatus('Error connecting to server', 'error', false);
    } finally {
        isRefreshing = false;
        enableButtons();
    }
}

// Disable all control buttons
function disableButtons() {
    refreshBtn.disabled = true;
    forceRescanBtn.disabled = true;
    scannerBtn.disabled = true;
}

// Enable all control buttons
function enableButtons() {
    refreshBtn.disabled = false;
    forceRescanBtn.disabled = false;
    scannerBtn.disabled = false;
    updateScannerButton();
}

// Function to toggle scanner
async function toggleScanner() {
    try {
        const response = await fetch('/api/toggle_scanner', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            isScanning = data.running;
            updateScannerButton();
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch (error) {
        console.error('Error toggling scanner:', error);
        alert('Failed to toggle scanner. Check console for details.');
    }
}

// Update scanner button text and style
function updateScannerButton() {
    if (isScanning) {
        scannerBtn.textContent = 'Stop Scanner';
        scannerBtn.classList.add('running');
    } else {
        scannerBtn.textContent = 'Start Scanner';
        scannerBtn.classList.remove('running');
    }
}

// Set up auto-refresh every 30 seconds
function setupAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    autoRefreshInterval = setInterval(fetchOpportunities, 30000);
}

// Event listeners
refreshBtn.addEventListener('click', refreshData);
forceRescanBtn.addEventListener('click', forceRescan);
scannerBtn.addEventListener('click', toggleScanner);

// Initial load
fetchOpportunities();
setupAutoRefresh();"""
    
    with open(os.path.join(app.static_folder, 'app.js'), 'w') as f:
        f.write(js)


def open_browser(port):
    time.sleep(1.5)
    webbrowser.open(f'http://127.0.0.1:{port}')


def signal_handler(sig, frame):
    global scanner_process
    if scanner_process:
        scanner_process.terminate()
    sys.exit(0)


def parse_args():
    parser = argparse.ArgumentParser(description='Bitcoin News Scanner Web UI')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                      help=f'Port to run the web server on (default: {DEFAULT_PORT})')
    return parser.parse_args()


def main():
    args = parse_args()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    create_template_files()
    
    print(f"\nBitcoin News Scanner Web UI starting on port {args.port}")
    print(f"Open your browser to: http://127.0.0.1:{args.port}")
    print("Press Ctrl+C to exit\n")
    
    threading.Thread(target=open_browser, args=(args.port,)).start()
    
    try:
        app.run(debug=False, port=args.port)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\nERROR: Port {args.port} is already in use.")
            print("Try running with a different port:")
            print(f"  python web_ui.py --port 9090\n")
        else:
            print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
