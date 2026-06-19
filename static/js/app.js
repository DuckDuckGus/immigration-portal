let currentView = 'cases';
let caseDataMap = new Map(); // To store full case data by case_key
let navigationStack = []; // For smart back button
let currentLanguage = localStorage.getItem('lang') || 'en';
let currentPage = 1;
const pageSize = 20;

const translations = {
    en: {
        all_cases: "All Cases",
        team: "Team",
        sort_by: "Sort By:",
        high_urgency_first: "High Urgency First",
        least_complete_first: "Least Complete First",
        alphabetical: "Alphabetical",
        all_states: "All States",
        all_lawyers: "All Lawyers",
        all_engagements: "All Engagements",
        urgency: "Urgency",
        completeness: "Completeness",
        ask_lex: "Ask Lex the Robot a question...",
        lex_thinking: "Lex the Robot is checking the vault...",
        search_placeholder: "Search by case ID or client name...",
        lex_greeting: "Hello! I am Lex the Robot. How can I help you today?",
        // Dynamic Content
        "Student Visa": "Student Visa",
        "Non-Lucrative Residency": "Non-Lucrative Residency",
        "EU Family Members": "EU Family Members",
        "Work Permit (Employee)": "Work Permit (Employee)",
        "Highly Skilled Professional": "Highly Skilled Professional",
        "EU Blue Card": "EU Blue Card",
        "Digital Nomad": "Digital Nomad",
        "Work Permit (Self-Employed)": "Work Permit (Self-Employed)",
        "HIGH_URGENCY": "High Urgency",
        "GATHERING": "Gathering",
        "READY_TO_FILE": "Ready to File",
        "Total Active Cases": "Total Active Cases",
        "Average Urgency": "Average Urgency",
        "Average Completeness": "Average Completeness",
        "Assigned Case Files": "Assigned Case Files",
        "Caseload by Engagement Type": "Caseload by Engagement Type",
        // Document Types
        "Passport": "Passport",
        "Police Certificate": "Police Certificate",
        "Medical Certificate": "Medical Certificate",
        "Official Medical Certificate": "Official Medical Certificate",
        "Bank Statements": "Bank Statements",
        "Proof of Income": "Proof of Income",
        "Health Insurance": "Health Insurance",
        "Private Spanish Health Insurance": "Private Spanish Health Insurance",
        "Work Contract": "Work Contract",
        "Job Offer": "Job Offer",
        "Business Plan": "Business Plan",
        "University Degree": "University Degree",
        "Marriage/Partner Certificate": "Marriage/Partner Certificate",
        "Empadronamiento": "Empadronamiento",
        "Form 790-052": "Form 790-052",
        "Company CIF": "Company CIF",
        "Letter of Acceptance": "Letter of Acceptance",
        "Social Security Cert": "Social Security Cert",
        "Work Experience Proof": "Work Experience Proof",
        "Financial Feasibility": "Financial Feasibility",
        "Professional Licenses": "Professional Licenses",
        // Detail View Labels
        "clients": "Clients",
        "assigned_lawyer": "Assigned Lawyer",
        "documents": "Documents",
        "date_of_birth": "Date of Birth",
        "nationality": "Nationality",
        "email": "Email",
        "address": "Address",
        "spouse": "Spouse",
        "metrics": "Metrics",
        "back": "Back"
    },
    es: {
        all_cases: "Todos los Casos",
        team: "Equipo",
        sort_by: "Ordenar por:",
        high_urgency_first: "Mayor Urgencia",
        least_complete_first: "Menos Completo",
        alphabetical: "Alfabético",
        all_states: "Todos los Estados",
        all_lawyers: "Todos los Abogados",
        all_engagements: "Todos los Tipos",
        urgency: "Urgencia",
        completeness: "Completitud",
        ask_lex: "Pregúntale a Lex el Robot...",
        lex_thinking: "Lex el Robot está consultando la bóveda...",
        search_placeholder: "Buscar por ID de caso o nombre...",
        lex_greeting: "¡Hola! Soy Lex el Robot. ¿En qué puedo ayudarte hoy?",
        // Dynamic Content
        "Student Visa": "Visado de Estudiante",
        "Non-Lucrative Residency": "Residencia No Lucrativa",
        "EU Family Members": "Familiares de la UE",
        "Work Permit (Employee)": "Permiso de Trabajo (Cuenta Ajena)",
        "Highly Skilled Professional": "Profesional Altamente Cualificado",
        "EU Blue Card": "Tarjeta Azul UE",
        "Digital Nomad": "Nómada Digital",
        "Work Permit (Self-Employed)": "Permiso de Trabajo (Cuenta Propia)",
        "HIGH_URGENCY": "Urgencia Alta",
        "GATHERING": "Recopilando",
        "READY_TO_FILE": "Listo para Presentar",
        "Total Active Cases": "Total de Casos Activos",
        "Average Urgency": "Urgencia Promedio",
        "Average Completeness": "Completitud Promedio",
        "Assigned Case Files": "Casos Asignados",
        "Caseload by Engagement Type": "Carga de Casos por Tipo",
        // Document Types
        "Passport": "Pasaporte",
        "Police Certificate": "Certificado de Antecedentes Penales",
        "Medical Certificate": "Certificado Médico",
        "Official Medical Certificate": "Certificado Médico Oficial",
        "Bank Statements": "Extractos Bancarios",
        "Proof of Income": "Prueba de Ingresos",
        "Health Insurance": "Seguro de Salud",
        "Private Spanish Health Insurance": "Seguro de Salud Privado Español",
        "Work Contract": "Contrato de Trabajo",
        "Job Offer": "Oferta de Empleo",
        "Business Plan": "Plan de Negocios",
        "University Degree": "Título Universitario",
        "Marriage/Partner Certificate": "Certificado de Matrimonio/Pareja",
        "Empadronamiento": "Empadronamiento",
        "Form 790-052": "Formulario 790-052",
        "Company CIF": "CIF de la Empresa",
        "Letter of Acceptance": "Carta de Aceptación",
        "Social Security Cert": "Certificado de la Seguridad Social",
        "Work Experience Proof": "Prueba de Experiencia Laboral",
        "Financial Feasibility": "Viabilidad Financiera",
        "Professional Licenses": "Licencias Profesionales",
        // Detail View Labels
        "clients": "Clientes",
        "assigned_lawyer": "Abogado Asignado",
        "documents": "Documentos",
        "date_of_birth": "Fecha de Nacimiento",
        "nationality": "Nacionalidad",
        "email": "Correo Electrónico",
        "address": "Dirección",
        "spouse": "Cónyuge",
        "metrics": "Métricas",
        "back": "Volver"
    }
};

const metadataKeyTranslations = {
    en: {
        "issue_date": "Issue Date",
        "expiry_date": "Expiry Date",
        "has_apostille": "Has Apostille",
        "is_translated": "Is Translated",
        "passport_number": "Passport Number",
        "all_pages_scanned": "All Pages Scanned",
        "balance_eur": "Balance (EUR)",
        "currency": "Currency",
        "stamped_by_bank": "Stamped by Bank",
        "provider": "Provider",
        "no_copay": "No Co-pay",
        "repatriation": "Repatriation Included",
        "salary_annual": "Annual Salary",
        "duration": "Duration",
        "signed_by_company": "Signed by Company",
        "viable_by_upt": "Viable by UPT",
        "investment_amount": "Investment Amount",
        "homologated": "Homologated",
        "level": "Level",
        "members_listed": "Members Listed",
        "paid_status": "Paid Status",
        "active_status": "Active Status"
    },
    es: {
        "issue_date": "Fecha de Emisión",
        "expiry_date": "Fecha de Caducidad",
        "has_apostille": "Tiene Apostilla",
        "is_translated": "Está Traducido",
        "passport_number": "Número de Pasaporte",
        "all_pages_scanned": "Todas las Páginas Escaneadas",
        "balance_eur": "Saldo (EUR)",
        "currency": "Moneda",
        "stamped_by_bank": "Sellado por el Banco",
        "provider": "Proveedor",
        "no_copay": "Sin Copago",
        "repatriation": "Repatriación Incluida",
        "salary_annual": "Salario Anual",
        "duration": "Duración",
        "signed_by_company": "Firmado por la Empresa",
        "viable_by_upt": "Viable por UPT",
        "investment_amount": "Monto de Inversión",
        "homologated": "Homologado",
        "level": "Nivel",
        "members_listed": "Miembros Listados",
        "paid_status": "Estado del Pago",
        "active_status": "Estado Activo"
    }
};

function getTranslation(key) {
    // Helper to get a translation, falling back to the key itself
    return translations[currentLanguage][key] || key;
}

async function renderView(viewType) {
    currentView = viewType;
    const content = document.getElementById('main-content');
    const filterControls = document.getElementById('filter-controls');

    // Only reset the navigation stack if we are not in the middle of a "back" operation.
    if (navigationStack.length <= 1) {
        navigationStack = [{ render: () => renderView(viewType), title: `Back to ${viewType} list` }];
    }

    // Update UI tabs
    document.querySelectorAll('.tabs button').forEach(b => b.classList.remove('active'));
    document.getElementById(`btn-${viewType}`)?.classList.add('active');

    // Toggle sort visibility
    filterControls.style.display = viewType === 'cases' ? 'flex' : 'none';
    document.querySelector('.control-bar').style.visibility = 'visible';

    // --- NEW: Toggle between List and Grid view ---
    if (viewType === 'cases') {
        content.className = 'list-view';
    } else {
        content.className = ''; // Resets to default grid view
    }

    // Combine search input with active filter pills
    const searchInput = document.getElementById('global-search').value;
    const stateFilter = document.getElementById('state-filter').value;
    const lawyerFilter = document.getElementById('lawyer-filter').value;
    const engagementFilter = document.getElementById('engagement-filter').value;

    const activeFilters = [stateFilter, lawyerFilter, engagementFilter].filter(f => f); // Removes empty strings
    const query = [searchInput, ...activeFilters].join(' ').trim();

    const sort = document.getElementById('sort-select').value;

    const endpoint = viewType === 'cases' 
        ? `/api/get_cases?q=${encodeURIComponent(query)}&sort=${sort}`
        : `/api/get_lawyers`;

    const response = await fetch(endpoint);
    const data = await response.json();
    
    // Store case data for modal access
    if (viewType === 'cases') data.forEach(c => caseDataMap.set(c.case_key, c));

    // --- PAGINATION LOGIC ---
    const totalPages = Math.ceil(data.length / pageSize);
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedData = data.slice(startIndex, endIndex);

    if (viewType === 'cases') {
        const caseListHtml = paginatedData.length > 0
            ? paginatedData.map(c => createCaseCard(c)).join('')
            : '<div class="empty-state">No results found in the vault.</div>';
        
        const paginationHtml = data.length > pageSize 
            ? createPaginationControls(totalPages) 
            : '';
        content.innerHTML = `<ol class="case-list-ol">${caseListHtml}</ol>${paginationHtml}`;
    } else {
        content.innerHTML = data.length > 0
            ? data.map(l => createLawyerCard(l)).join('')
            : '<div class="empty-state">No results found in the vault.</div>';
    }
}

function createCaseCard(c) {
    const urgencyClass = c.urgency > 50 ? 'high-urgency' : (c.completeness === 100 && c.urgency < 20 ? 'ready' : '');
    const urgencyColor = c.urgency > 50 ? 'val-red' : (c.urgency < 20 ? 'val-green' : '');
    
    // The card is now a list item with a horizontal layout
    return `
        <li class="case-card ${urgencyClass}" onclick="navigateTo(renderCaseDetailView, '${c.case_key}')" style="cursor: pointer;">
            <div>
                <strong class="case-key">${c.case_key}</strong>
                <div style="font-size: 0.9rem; margin: 0;">${c.client_names}</div>
            </div>
            <div class="eng-type">${getTranslation(c.engagement_name)}</div>
            <div class="lawyer-footer" style="border: none; padding: 0; margin: 0;">
                👤 <strong>${c.assigned_lawyer}</strong>
            </div>
            <div class="metric-box">
                <span class="metric-label">${getTranslation("urgency")}</span>
                <span class="metric-val ${urgencyColor}">${c.urgency}/100</span>
            </div>
            <div class="metric-box">
                <span class="metric-label">${getTranslation("completeness")}</span>
                <span class="metric-val">${c.completeness}%</span>
                <div class="progress-container" style="height: 5px;">
                    <div class="progress-bar" style="width: ${c.completeness}%"></div>
                </div>
            </div>
        </li>
    `;
}

function createLawyerCard(l) {
    return `
        <div class="lawyer-card" onclick="navigateTo(renderLawyerDetailView, ${l.user_id})" style="cursor: pointer;">
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
    currentPage = 1; // Reset to first page on sort
    }

async function setupFilterDropdowns() {
    const stateSelect = document.getElementById('state-filter');
    const lawyerSelect = document.getElementById('lawyer-filter');
    const engagementSelect = document.getElementById('engagement-filter');

    // Update sort options
    const sortSelect = document.getElementById('sort-select');
    sortSelect.options[0].text = translations[currentLanguage].high_urgency_first;
    sortSelect.options[1].text = translations[currentLanguage].least_complete_first;
    sortSelect.options[2].text = translations[currentLanguage].alphabetical;

    // 1. Populate State Filter (Static)
    const states = ['HIGH_URGENCY', 'GATHERING', 'READY_TO_FILE'];
    stateSelect.innerHTML = `<option value="">${translations[currentLanguage].all_states}</option>` + 
        states.map(s => `<option value="label:${s}">${getTranslation(s)}</option>`).join('');

    // 2. Populate Lawyer Filter (Dynamic)
    const lawyersRes = await fetch('/api/get_lawyers');
    const lawyers = await lawyersRes.json();
    lawyerSelect.innerHTML = `<option value="">${translations[currentLanguage].all_lawyers}</option>` + 
        lawyers.map(l => `<option value="lawyer:${l.full_name.replace(/ /g, '_')}">${l.full_name}</option>`).join('');

    // 3. Populate Engagement Filter (Dynamic)
    const engTypesRes = await fetch('/api/get_engagement_types');
    const engTypes = await engTypesRes.json();
    engagementSelect.innerHTML = `<option value="">${translations[currentLanguage].all_engagements}</option>` + 
        engTypes.map(name => `<option value="eng:${name.replace(/ /g, '_')}">${getTranslation(name)}</option>`).join('');

    // 4. Add event listeners to trigger re-render on change
    [stateSelect, lawyerSelect, engagementSelect].forEach(select => {
        select.addEventListener('change', () => {
            currentPage = 1; // Reset to first page on filter change
            renderView('cases');
        });
    });
}

    // Automatically load the 'cases' view so the dashboard isn't empty on arrival
    document.addEventListener('DOMContentLoaded', () => {
        // Initial render to show all cases
        renderView('cases');
        // Setup the dropdowns with data from the API
        setupFilterDropdowns();
        // Setup the document modal
        setupDocumentModal();
        // Setup language switcher
        setupLangSwitch();
        // Setup the chatbot functionality
        setupChatbot();
    });

function setupChatbot() {
    const launcher = document.getElementById('chat-launcher-btn');
    const closeBtn = document.getElementById('close-chat-btn');
    const chatWindow = document.getElementById('chat-window');
    const sendBtn = document.getElementById('send-chat-btn');
    const chatInput = document.getElementById('chat-input');

    launcher.addEventListener('click', () => {
        chatWindow.classList.add('open');
        launcher.style.display = 'none';
    });
    closeBtn.addEventListener('click', () => {
        chatWindow.classList.remove('open');
        launcher.style.display = 'block';
    });

    sendBtn.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });
}

async function sendChatMessage() {
    const chatInput = document.getElementById('chat-input');
    const chatBody = document.getElementById('chat-body');
    const prompt = chatInput.value.trim();

    if (!prompt) return;

    // 1. Display user's message
    addMessageToChat(prompt, 'user');
    chatInput.value = '';

    // 2. Show thinking indicator
    const thinkingIndicator = addMessageToChat(translations[currentLanguage].lex_thinking, 'lex thinking');

    // 3. Call the new API endpoint
    const response = await fetch('/api/ask_lex', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt, lang: currentLanguage })
    });
    const data = await response.json();

    // 4. Replace "thinking" with the actual answer
    thinkingIndicator.textContent = data.answer;
    thinkingIndicator.classList.remove('thinking');
}

function addMessageToChat(text, type) {
    const chatBody = document.getElementById('chat-body');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;
    messageDiv.textContent = text;
    chatBody.appendChild(messageDiv);
    chatBody.scrollTop = chatBody.scrollHeight; // Auto-scroll to the bottom
    return messageDiv;
}

function renderCaseDetailView(caseKey) {
    const caseData = caseDataMap.get(caseKey);
    if (!caseData) return;

    // Hide the main controls
    const backButtonHtml = createBackButton();

    document.getElementById('main-content').className = 'detail-mode';
    document.querySelector('.control-bar').style.visibility = 'hidden';

    const clientNamesHtml = caseData.client_names.split(', ').map(name => 
        `<span class="client-name-link" onclick="navigateTo(openClientModal, event, '${name}')">${name}</span>`
    ).join(', ');

    const lawyerNameHtml = caseData.lawyer_id
        ? `<span class="client-name-link" onclick="navigateTo(renderLawyerDetailView, ${caseData.lawyer_id})">${caseData.assigned_lawyer}</span>`
        : caseData.assigned_lawyer;

    const required = caseData.required_docs_list;
    const present = caseData.present_docs_list;
    const docListHtml = required.map(docName => {
        const isPresent = present.includes(docName);
        const statusClass = isPresent ? 'present' : 'missing';
        const icon = isPresent ? '✓' : '✗';
        const docIndex = caseData.documents.findIndex(d => d.doc_type === docName);
        return `<li class="${statusClass}" onclick="openDocumentModal(event, '${caseData.case_key}', ${docIndex})">${icon} ${getTranslation(docName)}</li>`;
    }).join('');

    const detailHtml = `
        <div class="detail-view-container">
            <div class="detail-header">
                <h2>${caseData.case_key}</h2>
                ${backButtonHtml}
            </div>
            <div class="detail-body">
                <p><strong>${getTranslation("clients")}:</strong> ${clientNamesHtml}</p>
                <p><strong>${getTranslation("assigned_lawyer")}:</strong> ${lawyerNameHtml}</p>
                <hr>
                <strong>${getTranslation("documents")}:</strong>
                <ul class="doc-list">${docListHtml}</ul>
            </div>
        </div>
    `;
    document.getElementById('main-content').innerHTML = detailHtml;
}

async function renderLawyerDetailView(lawyerId) {
    const response = await fetch(`/api/get_lawyer_details/${lawyerId}`);
    const data = await response.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    // Hide the main controls
    const backButtonHtml = createBackButton();

    document.getElementById('main-content').className = 'detail-mode';
    document.querySelector('.control-bar').style.visibility = 'hidden';

    // Generate the list of cases for this lawyer
    const caseListHtml = data.cases.length > 0
        ? data.cases.map(c => createCaseCard(c, true)).join('') // Pass true to indicate it's a sub-list
        : '<div class="empty-state">No active cases assigned.</div>';

    const detailHtml = `
        <div class="detail-view-container">
            <div class="detail-header">
                <h2>${data.full_name}</h2>
                ${backButtonHtml}
            </div>
            <div class="detail-body">
                <h3>${getTranslation("metrics")}</h3>
                <div class="lawyer-detail-metrics">
                    <div class="metric-box">
                        <span class="metric-label">${getTranslation("Total Active Cases")}</span>
                        <span class="metric-val">${data.total_cases}</span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">${getTranslation("Average Urgency")}</span>
                        <span class="metric-val ${data.avg_urgency > 40 ? 'val-red' : ''}">${data.avg_urgency}/100</span>
                    </div>
                    <div class="metric-box">
                        <span class="metric-label">${getTranslation("Average Completeness")}</span>
                        <span class="metric-val">${data.avg_completeness}%</span>
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="engagement-chart"></canvas>
                </div>
                <hr>
                <h3 data-translate-key="assigned_case_files">${getTranslation("Assigned Case Files")}</h3>
                <ol class="case-list-ol list-view">${caseListHtml}</ol>
            </div>
        </div>
    `;
    document.getElementById('main-content').innerHTML = detailHtml;

    // --- Render the Chart ---
    const ctx = document.getElementById('engagement-chart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.engagement_breakdown.labels.map(l => getTranslation(l)),
            datasets: [{
                label: 'Case Count',
                data: data.engagement_breakdown.data,
                backgroundColor: [
                    '#1a365d', '#3182ce', '#63b3ed', '#90cdf4',
                    '#2c5282', '#4299e1', '#bee3f8', '#a0aec0'
                ],
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top' },
                title: { display: true, text: getTranslation('Caseload by Engagement Type') }
            }
        }
    });
}

async function openClientModal(event, clientName) {
    event.stopPropagation(); // Prevent the case modal from opening

    const clientNameForApi = clientName.replace(/ /g, '_');
    const response = await fetch(`/api/get_client_details/${clientNameForApi}`);
    const data = await response.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    // Hide the main controls
    const backButtonHtml = createBackButton();

    document.getElementById('main-content').className = 'detail-mode';
    document.querySelector('.control-bar').style.visibility = 'hidden';

    const address = `${data.street_address}, ${data.city}, ${data.postal_code}, ${data.country}`;
    const spouseInfo = data.spouse_name ? `${data.spouse_name} (Married on: ${data.metadata.date_of_marriage})` : 'Not applicable';

    const detailHtml = `
        <div class="detail-view-container">
            <div class="detail-header">
                <h2>${data.full_name}</h2>
                ${backButtonHtml}
            </div>
            <div class="detail-body">
                <p><strong>${getTranslation("date_of_birth")}:</strong> ${data.dob}</p>
                <p><strong>${getTranslation("nationality")}:</strong> ${data.nationality}</p>
                <p><strong>${getTranslation("email")}:</strong> ${data.email}</p>
                <hr>
                <p><strong>${getTranslation("address")}:</strong> ${address}</p>
                <hr>
                <p><strong>${getTranslation("spouse")}:</strong> ${spouseInfo}</p>
            </div>
        </div>
    `;
    document.getElementById('main-content').innerHTML = detailHtml;
}

function navigateTo(viewFunction, ...args) {
    // This is the new central point for forward navigation.
    // It pushes the new view's render function onto the stack BEFORE executing it.
    navigationStack.push({ render: () => viewFunction(...args) });
    viewFunction(...args);
}

// We need to update the onclick handlers to use the new navigation function
function createCaseCard(c, isSubView = false) {
    const urgencyClass = c.urgency > 50 ? 'high-urgency' : (c.completeness === 100 && c.urgency < 20 ? 'ready' : '');
    const urgencyColor = c.urgency > 50 ? 'val-red' : (c.urgency < 20 ? 'val-green' : '');
    
    // The card is now a list item with a horizontal layout
    return `
        <li class="case-card ${urgencyClass}" onclick="navigateTo(renderCaseDetailView, '${c.case_key}')" style="cursor: pointer;">
            <div>
                <strong class="case-key">${c.case_key}</strong>
                <div style="font-size: 0.9rem; margin: 0;">${c.client_names}</div>
            </div>
            <div class="eng-type">${getTranslation(c.engagement_name)}</div>
            <div class="lawyer-footer" style="border: none; padding: 0; margin: 0;">
                👤 <strong>${c.assigned_lawyer}</strong>
            </div>
            <div class="metric-box">
                <span class="metric-label">${getTranslation("urgency")}</span>
                <span class="metric-val ${urgencyColor}">${c.urgency}/100</span>
            </div>
            <div class="metric-box">
                <span class="metric-label">${getTranslation("completeness")}</span>
                <span class="metric-val">${c.completeness}%</span>
                <div class="progress-container" style="height: 5px;">
                    <div class="progress-bar" style="width: ${c.completeness}%"></div>
                </div>
            </div>
        </li>
    `;
}

function createLawyerCard(l) {
    return `
        <div class="lawyer-card" onclick="navigateTo(renderLawyerDetailView, ${l.user_id})" style="cursor: pointer;">
            <div class="lawyer-avatar">${l.full_name.charAt(0)}</div>
            <div>
                <div style="font-weight: bold;">${l.full_name}</div>
                <div style="font-size: 0.8rem; color: #718096;">Lawyer ID: #${l.user_id}</div>
            </div>
        </div>
    `;
}

function goBack() {
    // Pop the current view
    if (navigationStack.length > 1) {
        navigationStack.pop();
    }
    // Render the view now at the top of the stack
    const previousView = navigationStack[navigationStack.length - 1];
    if (previousView && typeof previousView.render === 'function') {
        previousView.render();
    }
}

function createBackButton() {
    return `<button class="back-button" onclick="goBack()">← ${getTranslation("back")}</button>`;
}

function setupDocumentModal() {
    const modal = document.getElementById('document-modal');
    const closeBtn = document.getElementById('document-modal-close-btn');
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });
    closeBtn.addEventListener('click', () => modal.style.display = 'none');
}

function openDocumentModal(event, caseKey, docIndex) {
    event.stopPropagation(); // Prevent the case detail view from re-rendering

    const caseData = caseDataMap.get(caseKey);
    if (!caseData || docIndex === -1) return;

    const doc = caseData.documents[docIndex];
    if (!doc) return;

    document.getElementById('modal-doc-name').textContent = getTranslation(doc.doc_type.replace(/_/g, ' '));
    const modalBody = document.getElementById('document-modal-body');

    let metadataHtml = '<div class="metadata-grid">';
    for (const [key, value] of Object.entries(doc.metadata)) {
        const displayKey = metadataKeyTranslations[currentLanguage][key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        const displayValue = value === true ? 'Yes' : (value === false ? 'No' : (value || 'N/A'));
        metadataHtml += `<strong>${displayKey}:</strong> <span>${displayValue}</span>`;
    }
    metadataHtml += '</div>';

    modalBody.innerHTML = metadataHtml;
    document.getElementById('document-modal').style.display = 'flex';
}

function setLanguage(lang) {
    currentLanguage = lang;

    // Update active button visual state
    document.querySelectorAll('.lang-switch button').forEach(b => b.classList.remove('active'));
    document.getElementById(`lang-${lang}`).classList.add('active');

    localStorage.setItem('lang', lang);
    document.querySelectorAll('[data-translate-key]').forEach(el => {
        const key = el.dataset.translateKey;
        if (translations[lang][key]) {
            el.innerHTML = translations[lang][key];
        }
    });
    document.getElementById('global-search').placeholder = translations[lang].search_placeholder;
    document.getElementById('chat-input').placeholder = translations[lang].ask_lex;
    document.querySelector('.chat-message.lex').textContent = translations[lang].lex_greeting;

    // Re-render views to update dynamic text
    setupFilterDropdowns();
    renderView(currentView);
}

function setupLangSwitch() {
    document.getElementById('lang-en').addEventListener('click', () => setLanguage('en'));
    document.getElementById('lang-es').addEventListener('click', () => setLanguage('es'));
    setLanguage(currentLanguage); // Set initial language on load
}

function createPaginationControls(totalPages) {
    let buttonsHtml = '';
    for (let i = 1; i <= totalPages; i++) {
        buttonsHtml += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="changePage(${i})">${i}</button>`;
    }
    return `<div class="pagination-controls">${buttonsHtml}</div>`;
}

function changePage(page) {
    currentPage = page;
    renderView('cases');
}

function handleSearch(event) {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        currentPage = 1; // Reset to first page on search
        renderView(currentView);
    }, 300); // Debounce to prevent server spam
}