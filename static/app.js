// DOM Elements
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
setupAutoRefresh();