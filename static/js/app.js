let currentView = 'cases';

async function renderView(viewType) {
    currentView = viewType;
    const content = document.getElementById('main-content');
    const sortControls = document.getElementById('sort-controls');
    
    // Update UI tabs
    document.querySelectorAll('.tabs button').forEach(b => b.classList.remove('active'));
    document.getElementById(`btn-${viewType}`)?.classList.add('active');

    // Toggle sort visibility
    sortControls.style.visibility = viewType === 'cases' ? 'visible' : 'hidden';

    const query = document.getElementById('global-search').value;
    const sort = document.getElementById('sort-select').value;

    const endpoint = viewType === 'cases' 
        ? `/api/get_cases?q=${encodeURIComponent(query)}&sort=${sort}`
        : `/api/get_lawyers`;

    const response = await fetch(endpoint);
    const data = await response.json();
    
    // Clear and render the new data
    content.innerHTML = data.length > 0 
        ? data.map(item => viewType === 'cases' ? createCaseCard(item) : createLawyerCard(item)).join('')
        : `<div class="empty-state">No results found in the vault.</div>`;
}

function createCaseCard(c) {
    const riskClass = c.risk > 50 ? 'high-risk' : (c.completeness === 100 && c.risk < 20 ? 'ready' : '');
    const riskColor = c.risk > 50 ? 'val-red' : (c.risk < 20 ? 'val-green' : '');
    
    return `
        <div class="case-card ${riskClass}">
            <div class="case-header">
                <span class="case-key">${c.case_key}</span>
                <span class="status-badge">${c.status}</span>
            </div>
            <span class="client-names">${c.client_names}</span>
            <div class="eng-type">${c.engagement_name}</div>
            
            <div class="metrics">
                <div class="metric-box">
                    <span class="metric-label">Completeness</span>
                    <span class="metric-val">${c.completeness}%</span>
                </div>
                <div class="metric-box">
                    <span class="metric-label">Risk Level</span>
                    <span class="metric-val ${riskColor}">${c.risk}/100</span>
                </div>
            </div>

            <div class="progress-container">
                <div class="progress-bar" style="width: ${c.completeness}%"></div>
            </div>

            <div style="margin-top: 15px;">
                ${c.labels.map(l => `<span class="label-pill ${l}">${l.replace('_', ' ')}</span>`).join('')}
            </div>

            <div class="lawyer-footer">
                👤 Assigned: <strong>${c.assigned_lawyer}</strong>
            </div>
        </div>
    `;
}

function createLawyerCard(l) {
    return `
        <div class="lawyer-card">
            <div class="lawyer-avatar">${l.full_name.charAt(0)}</div>
            <div>
                <div style="font-weight: bold;">${l.full_name}</div>
                <div style="font-size: 0.8rem; color: #718096;">Lawyer ID: #${l.user_id}</div>
            </div>
        </div>
    `;
}

// Event Handlers
let searchTimeout;
function handleSearch(event) {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        renderView(currentView);
    }, 300); // Debounce to prevent server spam
}

function handleSortChange() {
    renderView('cases');
}