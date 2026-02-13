/**
 * Admin Dashboard - LinkedIn AI Commenter
 * Logique JavaScript pour le dashboard d'administration
 * Plan 03-03: Refonte complete avec 2 onglets, KPIs et drill-down
 */

// =============================================================================
// 1. API Configuration
// =============================================================================

const USERS_API_URL = '__USERS_API_URL__';
const AI_SERVICE_URL = '__AI_API_URL__';

// =============================================================================
// 2. State
// =============================================================================

let authToken = null;
let isLoading = false;
let GOOGLE_CLIENT_ID = null;
let tokenClient = null;

// New state for dashboard navigation
let currentPeriod = '30d';
let currentTab = 'overview';
let currentExpandedUserId = null;
let usersData = [];
let sortColumn = null;
let sortDirection = 'asc';
let usageDataLoaded = false;
let pieChart = null;
let featuresChart = null;
let distributionsData = {};
let trendsChart = null;
let rolesChart = null;
const ROLE_COLORS = { FREE: '#9E9E9E', MEDIUM: '#2196F3', PREMIUM: '#FFC107' };

// =============================================================================
// 3. DOM Elements
// =============================================================================

const loginSection = document.getElementById('login-section');
const dashboardSection = document.getElementById('dashboard-section');
const errorSection = document.getElementById('error-section');
const authStatus = document.getElementById('auth-status');
const logoutBtn = document.getElementById('logout-btn');

// New DOM elements for tabs and data display
let tabButtons;
let tabPanels;
let periodButtons;

// =============================================================================
// 4. Init and Event Listeners
// =============================================================================

document.addEventListener('DOMContentLoaded', init);

/**
 * Initialise le dashboard
 */
async function init() {
    authToken = localStorage.getItem('admin_jwt');

    // Init tabs/period/sort BEFORE loading dashboard (switchTab needs tabButtons)
    initTabs();
    initPeriodSelector();
    initTableSort();

    if (authToken) {
        await loadDashboard();
    } else {
        showLoginSection();
        initGoogleSignIn();
    }

    setupEventListeners();
}

/**
 * Configure les event listeners
 */
function setupEventListeners() {
    // JWT manual link (fallback)
    const jwtManualLink = document.getElementById('jwt-manual-link');
    if (jwtManualLink) {
        jwtManualLink.addEventListener('click', (e) => {
            e.preventDefault();
            handleManualJwtLogin();
        });
    }

    // Logout button
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }

    // Retry button
    const retryBtn = document.getElementById('retry-btn');
    if (retryBtn) {
        retryBtn.addEventListener('click', () => {
            if (isLoading) return;
            if (authToken) {
                loadDashboard();
            } else {
                showLoginSection();
                initGoogleSignIn();
            }
        });
    }

    // Initialize tabs and period selector after dashboard is shown
    initTabs();
    initPeriodSelector();
    initTableSort();
}

// =============================================================================
// 5. Auth Functions (PRESERVED FROM ORIGINAL)
// =============================================================================

/**
 * Affiche la section login
 */
function showLoginSection() {
    loginSection.style.display = 'block';
    dashboardSection.style.display = 'none';
    errorSection.style.display = 'none';
    authStatus.textContent = '';
    logoutBtn.style.display = 'none';
    const loginMsg = document.getElementById('login-message');
    if (loginMsg) loginMsg.style.display = 'none';
}

/**
 * Affiche le dashboard
 */
function showDashboard() {
    loginSection.style.display = 'none';
    dashboardSection.style.display = 'block';
    errorSection.style.display = 'none';
    authStatus.textContent = 'Connecte en tant qu\'admin';
    logoutBtn.style.display = 'inline-block';
}

/**
 * Affiche un message d'erreur
 */
function showError(message) {
    loginSection.style.display = 'none';
    dashboardSection.style.display = 'none';
    errorSection.style.display = 'block';
    document.getElementById('error-message').textContent = message;
    logoutBtn.style.display = authToken ? 'inline-block' : 'none';
}

/**
 * Charge les donnees du dashboard
 */
async function loadDashboard() {
    if (isLoading) return;
    isLoading = true;

    try {
        showLoadingState();

        // Initialize tabs and load default active tab (overview with 30d)
        showDashboard();

        // Load the default tab data
        await switchTab(currentTab);

    } catch (error) {
        handleApiError(error);
    } finally {
        isLoading = false;
        hideLoadingState();
    }
}

/**
 * Affiche l'etat de chargement avec spinner
 */
function showLoadingState() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) spinner.style.display = 'flex';
    dashboardSection.classList.add('loading');
}

/**
 * Cache l'etat de chargement
 */
function hideLoadingState() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) spinner.style.display = 'none';
    dashboardSection.classList.remove('loading');
}

/**
 * Effectue une requete authentifiee
 */
async function fetchWithAuth(endpoint) {
    const response = await fetch(`${USERS_API_URL}${endpoint}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        const error = new Error(`HTTP ${response.status}`);
        error.status = response.status;
        throw error;
    }

    try {
        return await response.json();
    } catch (parseError) {
        const error = new Error('Reponse API invalide (JSON attendu)');
        error.status = 500;
        throw error;
    }
}

/**
 * Gere les erreurs API
 */
function handleApiError(error) {
    if (error.status === 401) {
        localStorage.removeItem('admin_jwt');
        authToken = null;
        showLoginSectionWithMessage('Session expiree. Veuillez vous reconnecter.');
    } else if (error.status === 403) {
        showError('Acces refuse. Vous n\'etes pas administrateur.');
    } else {
        showError(`Erreur: ${error.message}`);
    }
}

/**
 * Affiche la section login avec un message contextuel
 */
function showLoginSectionWithMessage(message) {
    showLoginSection();
    const loginMsg = document.getElementById('login-message');
    if (loginMsg) {
        loginMsg.textContent = message;
        loginMsg.style.display = 'block';
    }
}

/**
 * Valide le format JWT basique
 */
function isValidJwtFormat(token) {
    if (!token || typeof token !== 'string') return false;
    const parts = token.split('.');
    if (parts.length !== 3) return false;
    const base64urlRegex = /^[A-Za-z0-9_-]+$/;
    return parts.every(part => part.length > 0 && base64urlRegex.test(part));
}

/**
 * Charge la configuration Google OAuth depuis le backend
 */
async function loadGoogleConfig() {
    try {
        const response = await fetch(`${AI_SERVICE_URL}/config`);
        if (!response.ok) {
            throw new Error('Impossible de charger la configuration Google OAuth');
        }
        const config = await response.json();
        GOOGLE_CLIENT_ID = config.google_client_id;
        console.log('Google Client ID charge');
        return true;
    } catch (error) {
        console.error('Erreur chargement config Google:', error);
        showLoginSectionWithMessage('Configuration Google OAuth non disponible. Utilisez le mode JWT manuel.');
        return false;
    }
}

/**
 * Initialise Google Sign-In
 */
async function initGoogleSignIn() {
    const configLoaded = await loadGoogleConfig();
    if (!configLoaded || !GOOGLE_CLIENT_ID) {
        return;
    }

    if (typeof google === 'undefined') {
        console.log('En attente du chargement du SDK Google...');
        setTimeout(initGoogleSignIn, 100);
        return;
    }

    tokenClient = google.accounts.oauth2.initTokenClient({
        client_id: GOOGLE_CLIENT_ID,
        scope: 'https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile',
        callback: handleGoogleCallback,
    });

    const googleBtn = document.getElementById('google-signin-btn');
    if (googleBtn) {
        googleBtn.addEventListener('click', () => {
            if (tokenClient) {
                tokenClient.requestAccessToken();
            } else {
                showLoginSectionWithMessage('Google OAuth non initialise. Utilisez le mode JWT manuel.');
            }
        });
    }
}

/**
 * Gere la reponse de Google OAuth
 */
async function handleGoogleCallback(response) {
    const googleBtn = document.getElementById('google-signin-btn');

    try {
        if (response.error) {
            throw new Error(response.error);
        }

        if (googleBtn) {
            googleBtn.disabled = true;
            googleBtn.innerHTML = '<span>Connexion en cours...</span>';
        }

        const googleAccessToken = response.access_token;
        console.log('Google access token recu');

        const loginResponse = await fetch(`${USERS_API_URL}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                google_token: googleAccessToken
            })
        });

        if (!loginResponse.ok) {
            const errorData = await loginResponse.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Erreur lors de la connexion avec Google');
        }

        const data = await loginResponse.json();

        if (data.access_token) {
            const tempToken = data.access_token;
            authToken = tempToken;
            const isAdmin = await verifyAdminAccess();

            if (isAdmin) {
                localStorage.setItem('admin_jwt', authToken);
                await loadDashboard();
            } else {
                authToken = null;
                showLoginSectionWithMessage('Acces refuse. Vous n\'etes pas administrateur.');
            }
        } else {
            throw new Error('Token non recu du serveur');
        }

    } catch (error) {
        console.error('Erreur de connexion Google:', error);
        showLoginSectionWithMessage(error.message);
        authToken = null;
    } finally {
        if (googleBtn) {
            googleBtn.disabled = false;
            googleBtn.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M19.6 10.227c0-.709-.064-1.39-.182-2.045H10v3.868h5.382a4.6 4.6 0 01-1.996 3.018v2.51h3.232c1.891-1.742 2.982-4.305 2.982-7.35z" fill="#4285F4"/>
                    <path d="M10 20c2.7 0 4.964-.895 6.618-2.423l-3.232-2.509c-.895.6-2.04.955-3.386.955-2.605 0-4.81-1.76-5.595-4.123H1.064v2.59A9.996 9.996 0 0010 20z" fill="#34A853"/>
                    <path d="M4.405 11.9c-.2-.6-.314-1.24-.314-1.9 0-.66.114-1.3.314-1.9V5.51H1.064A9.996 9.996 0 000 10c0 1.614.386 3.14 1.064 4.49l3.34-2.59z" fill="#FBBC05"/>
                    <path d="M10 3.977c1.468 0 2.786.505 3.823 1.496l2.868-2.868C14.959.99 12.695 0 10 0 6.09 0 2.71 2.24 1.064 5.51l3.34 2.59C5.19 5.736 7.395 3.977 10 3.977z" fill="#EA4335"/>
                </svg>
                <span>Se connecter avec Google</span>
            `;
        }
    }
}

/**
 * Verifie que l'utilisateur a acces admin
 */
async function verifyAdminAccess() {
    try {
        const response = await fetch(`${USERS_API_URL}/api/admin/premium-count`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.status === 403) {
            console.log('Utilisateur non admin (403)');
            return false;
        }

        if (response.status === 401) {
            console.log('Token invalide (401)');
            return false;
        }

        return response.ok;
    } catch (error) {
        console.error('Erreur verification admin:', error);
        return false;
    }
}

/**
 * Gere le login JWT manuel (fallback)
 */
function handleManualJwtLogin() {
    const token = prompt(
        'Mode avance - Entrez votre JWT admin:\n\n' +
        'Pour obtenir le JWT:\n' +
        '1. Connectez-vous avec l\'extension Chrome (compte admin)\n' +
        '2. DevTools → Application → Storage → chrome.storage.local\n' +
        '3. Copiez la valeur du JWT'
    );

    if (token && token.trim()) {
        const trimmedToken = token.trim();

        if (!isValidJwtFormat(trimmedToken)) {
            alert('Format JWT invalide. Le token doit avoir 3 parties separees par des points (xxx.yyy.zzz).');
            return;
        }

        authToken = trimmedToken;
        localStorage.setItem('admin_jwt', authToken);
        loadDashboard();
    }
}

/**
 * Gere la deconnexion
 */
function handleLogout() {
    localStorage.removeItem('admin_jwt');
    authToken = null;
    showLoginSection();
    initGoogleSignIn();
}

// =============================================================================
// 6. Tab Management
// =============================================================================

/**
 * Initialise les onglets
 */
function initTabs() {
    tabButtons = document.querySelectorAll('.tab-btn');
    tabPanels = document.querySelectorAll('[data-tab-panel]');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
}

/**
 * Change d'onglet et charge les donnees correspondantes
 */
async function switchTab(tabName) {
    currentTab = tabName;

    // Update UI
    tabButtons.forEach(btn => {
        const isActive = btn.getAttribute('data-tab') === tabName;
        btn.classList.toggle('active', isActive);
        btn.setAttribute('aria-selected', isActive);
    });

    tabPanels.forEach(panel => {
        const isActive = panel.getAttribute('data-tab-panel') === tabName;
        panel.classList.toggle('active', isActive);
    });

    // Cacher le selecteur de periode pour l'onglet Usage (independant)
    const periodSelector = document.getElementById('period-selector');
    if (periodSelector) {
        periodSelector.style.display = tabName === 'usage' ? 'none' : 'flex';
    }

    // Load data for active tab
    try {
        showLoadingState();

        if (tabName === 'overview') {
            await loadOverviewData(currentPeriod);
        } else if (tabName === 'users') {
            await loadUsersData(currentPeriod);
        } else if (tabName === 'usage') {
            await loadUsageData();
            // Resize les charts ECharts apres affichage (etaient caches donc dimensions = 0)
            if (typeof echarts !== 'undefined') {
                setTimeout(() => {
                    const containers = ['chart-features', 'chart-distributions', 'chart-trends', 'chart-roles'];
                    containers.forEach(id => {
                        const el = document.getElementById(id);
                        if (el) {
                            const instance = echarts.getInstanceByDom(el);
                            if (instance) instance.resize();
                        }
                    });
                }, 100);
            }
        }
    } catch (error) {
        console.error(`Erreur chargement donnees ${tabName}:`, error);
        // Show error in the relevant section instead of global error page
        if (tabName === 'overview') {
            document.getElementById('kpi-users-total').textContent = 'Erreur';
        } else if (tabName === 'users') {
            const tbody = document.querySelector('#users-consumption-table tbody');
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#ef4444;">Erreur de chargement des donnees</td></tr>';
        }

        // Handle auth errors globally
        if (error.status === 401 || error.status === 403) {
            handleApiError(error);
        }
    } finally {
        hideLoadingState();
    }
}

// =============================================================================
// 7. Period Selector
// =============================================================================

/**
 * Initialise le selecteur de periode
 */
function initPeriodSelector() {
    periodButtons = document.querySelectorAll('.period-btn');

    periodButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const period = btn.getAttribute('data-period');
            setPeriod(period);
        });
    });
}

/**
 * Change la periode et recharge les donnees
 */
async function setPeriod(period) {
    currentPeriod = period;

    // Update active classes
    periodButtons.forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-period') === period);
    });

    // Usage tab est independant du selecteur de periode
    if (currentTab === 'usage') {
        return;
    }

    // Reload current tab
    await switchTab(currentTab);
}

// =============================================================================
// 8. Overview Tab - KPIs
// =============================================================================

/**
 * Charge les donnees de l'onglet Overview
 */
async function loadOverviewData(period) {
    const data = await fetchWithAuth(`/api/admin/analytics/summary?period=${period}`);
    displayKPIs(data);
}

/**
 * Affiche les KPIs dans l'onglet Overview
 */
function displayKPIs(data) {
    // KPI 1: Utilisateurs
    const usersTotal = Object.values(data.users_by_role || {}).reduce((sum, count) => sum + count, 0);
    document.getElementById('kpi-users-total').textContent = usersTotal.toLocaleString('fr-FR');

    const usersByRole = data.users_by_role || {};
    const roleDetail = `FREE: ${usersByRole.FREE || 0} | MEDIUM: ${usersByRole.MEDIUM || 0} | PREMIUM: ${usersByRole.PREMIUM || 0}`;
    document.getElementById('kpi-users-detail').textContent = roleDetail;

    // KPI 2: Commentaires
    const commentsTotal = data.total_comments_generated || 0;
    document.getElementById('kpi-comments-total').textContent = commentsTotal.toLocaleString('fr-FR');

    const commentsTrendEl = document.getElementById('kpi-comments-trend');
    commentsTrendEl.innerHTML = '';
    if (data.trend_comments != null) {
        const trendSpan = document.createElement('span');
        trendSpan.className = 'kpi-trend';

        if (data.trend_comments > 0) {
            trendSpan.classList.add('up');
            trendSpan.textContent = `\u2191 +${data.trend_comments.toFixed(1)}%`;
        } else if (data.trend_comments < 0) {
            trendSpan.classList.add('down');
            trendSpan.textContent = `\u2193 ${data.trend_comments.toFixed(1)}%`;
        } else {
            trendSpan.classList.add('neutral');
            trendSpan.textContent = '=';
        }

        commentsTrendEl.appendChild(trendSpan);
    }

    // KPI 3: Cout estime
    const costTotal = parseFloat(data.total_cost_eur) || 0;
    document.getElementById('kpi-cost-total').textContent = `${costTotal.toFixed(2)} EUR`;

    const costTrendEl = document.getElementById('kpi-cost-trend');
    costTrendEl.innerHTML = '';
    if (data.trend_cost != null) {
        const trendSpan = document.createElement('span');
        trendSpan.className = 'kpi-trend';

        if (data.trend_cost > 0) {
            trendSpan.classList.add('up');
            trendSpan.textContent = `\u2191 +${data.trend_cost.toFixed(1)}%`;
        } else if (data.trend_cost < 0) {
            trendSpan.classList.add('down');
            trendSpan.textContent = `\u2193 ${data.trend_cost.toFixed(1)}%`;
        } else {
            trendSpan.classList.add('neutral');
            trendSpan.textContent = '=';
        }

        costTrendEl.appendChild(trendSpan);
    }

    // KPI 4: Trials actifs
    const trials = data.active_trials || 0;
    document.getElementById('kpi-trials').textContent = trials.toLocaleString('fr-FR');
}

// =============================================================================
// 9. Users Tab - Consumption Table
// =============================================================================

/**
 * Charge les donnees de consommation des utilisateurs
 */
async function loadUsersData(period) {
    const data = await fetchWithAuth(`/api/admin/users/consumption?period=${period}`);
    usersData = data.items || [];
    displayUsersTable(usersData);
}

/**
 * Affiche le tableau de consommation des utilisateurs
 */
function displayUsersTable(users) {
    const tbody = document.querySelector('#users-consumption-table tbody');
    const emptyMsg = document.getElementById('users-empty');

    tbody.innerHTML = '';

    if (!users || users.length === 0) {
        emptyMsg.style.display = 'block';
        return;
    }

    emptyMsg.style.display = 'none';

    users.forEach(user => {
        const row = document.createElement('tr');
        row.setAttribute('data-user-id', user.user_id);

        // Email
        const tdEmail = document.createElement('td');
        tdEmail.textContent = user.email || user.user_id.substring(0, 8) + '...';
        row.appendChild(tdEmail);

        // Role
        const tdRole = document.createElement('td');
        tdRole.textContent = user.role || '-';
        row.appendChild(tdRole);

        // Generations
        const tdGen = document.createElement('td');
        tdGen.textContent = (user.generation_count || 0).toLocaleString('fr-FR');
        row.appendChild(tdGen);

        // Tokens
        const tdTokens = document.createElement('td');
        tdTokens.textContent = (user.total_tokens || 0).toLocaleString('fr-FR');
        row.appendChild(tdTokens);

        // Cost EUR
        const tdCost = document.createElement('td');
        const cost = parseFloat(user.cost_eur) || 0;
        tdCost.textContent = cost.toFixed(4);
        row.appendChild(tdCost);

        // Last generation
        const tdLast = document.createElement('td');
        if (user.last_generation) {
            const date = new Date(user.last_generation);
            tdLast.textContent = date.toLocaleDateString('fr-FR');
        } else {
            tdLast.textContent = '-';
        }
        row.appendChild(tdLast);

        // Actions
        const tdActions = document.createElement('td');
        const editBtn = document.createElement('button');
        editBtn.className = 'edit-user-btn';
        editBtn.textContent = 'Editer';
        editBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            openUserModal(user.user_id);
        });
        tdActions.appendChild(editBtn);
        row.appendChild(tdActions);

        tbody.appendChild(row);
    });

    // Attach click handlers via event delegation
    tbody.addEventListener('click', handleTableClick);
}

/**
 * Gere les clics sur le tableau (event delegation)
 */
function handleTableClick(e) {
    const row = e.target.closest('tr[data-user-id]');
    if (!row) return;

    const userId = row.getAttribute('data-user-id');
    handleUserClick(userId, row);
}

// =============================================================================
// 10. Users Tab - Drill-down
// =============================================================================

/**
 * Gere le clic sur un utilisateur pour afficher/masquer le drill-down
 */
function handleUserClick(userId, rowElement) {
    // Toggle: si deja ouvert, fermer
    if (currentExpandedUserId === userId) {
        closeDrillDown();
        return;
    }

    // Si un autre drill-down est ouvert, le fermer d'abord
    if (currentExpandedUserId) {
        closeDrillDown();
    }

    // Creer la ligne de drill-down
    const drillDownRow = document.createElement('tr');
    drillDownRow.className = 'drill-down-row';
    drillDownRow.setAttribute('data-drill-user-id', userId);

    const td = document.createElement('td');
    td.colSpan = 6;

    const content = document.createElement('div');
    content.className = 'drill-down-content';
    content.id = `drill-${userId}`;
    content.innerHTML = '<p>Chargement des generations...</p>';

    td.appendChild(content);
    drillDownRow.appendChild(td);

    // Inserer apres la ligne cliquee
    rowElement.after(drillDownRow);
    rowElement.classList.add('expanded');

    currentExpandedUserId = userId;

    // Charger les generations
    loadGenerations(userId, 0);
}

/**
 * Charge les generations d'un utilisateur
 */
async function loadGenerations(userId, skip) {
    try {
        const data = await fetchWithAuth(`/api/admin/users/${userId}/generations?skip=${skip}&limit=20`);
        displayGenerations(userId, data, skip);
    } catch (error) {
        console.error('Erreur chargement generations:', error);
        const content = document.getElementById(`drill-${userId}`);
        if (content) {
            content.innerHTML = '<p style="color:#ef4444;">Erreur de chargement des generations</p>';
        }
    }
}

/**
 * Affiche les generations dans le drill-down
 */
function displayGenerations(userId, data, skip) {
    const content = document.getElementById(`drill-${userId}`);
    if (!content) return;

    content.innerHTML = '';

    if (!data.items || data.items.length === 0) {
        content.innerHTML = '<p>Aucune generation disponible.</p>';
        return;
    }

    // Creer le tableau des generations
    const table = document.createElement('table');
    table.className = 'generations-table';

    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th>Date</th>
            <th>Mode</th>
            <th>Langue</th>
            <th>Tokens In</th>
            <th>Tokens Out</th>
            <th>Cout EUR</th>
            <th>Apercu</th>
        </tr>
    `;
    table.appendChild(thead);

    const tbody = document.createElement('tbody');

    data.items.forEach(gen => {
        const row = document.createElement('tr');

        // Date
        const tdDate = document.createElement('td');
        const date = new Date(gen.created_at);
        tdDate.textContent = date.toLocaleString('fr-FR');
        row.appendChild(tdDate);

        // Mode
        const tdMode = document.createElement('td');
        tdMode.textContent = gen.mode || '-';
        row.appendChild(tdMode);

        // Langue
        const tdLang = document.createElement('td');
        tdLang.textContent = gen.language || '-';
        row.appendChild(tdLang);

        // Tokens In
        const tdTokensIn = document.createElement('td');
        tdTokensIn.textContent = (gen.tokens_used_input || 0).toLocaleString('fr-FR');
        row.appendChild(tdTokensIn);

        // Tokens Out
        const tdTokensOut = document.createElement('td');
        tdTokensOut.textContent = (gen.tokens_used_output || 0).toLocaleString('fr-FR');
        row.appendChild(tdTokensOut);

        // Cout EUR
        const tdCost = document.createElement('td');
        const cost = parseFloat(gen.cost_eur) || 0;
        tdCost.textContent = cost.toFixed(6);
        row.appendChild(tdCost);

        // Apercu
        const tdPreview = document.createElement('td');
        const preview = document.createElement('div');
        preview.className = 'comment-preview';
        preview.textContent = gen.generated_comment || '-';
        preview.title = gen.generated_comment || '';
        tdPreview.appendChild(preview);
        row.appendChild(tdPreview);

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    content.appendChild(table);

    // Bouton "Voir plus" si necessaire
    if (data.has_more) {
        const loadMoreBtn = document.createElement('button');
        loadMoreBtn.className = 'load-more-btn';
        loadMoreBtn.textContent = `Voir plus (${data.remaining} restantes)`;
        loadMoreBtn.addEventListener('click', () => {
            loadMoreGenerations(userId, skip + 20);
        });
        content.appendChild(loadMoreBtn);
    }
}

/**
 * Charge plus de generations (remplace le contenu)
 */
function loadMoreGenerations(userId, skip) {
    loadGenerations(userId, skip);
}

/**
 * Ferme le drill-down actuel
 */
function closeDrillDown() {
    if (!currentExpandedUserId) return;

    // Supprimer la ligne de drill-down
    const drillDownRow = document.querySelector(`.drill-down-row[data-drill-user-id="${currentExpandedUserId}"]`);
    if (drillDownRow) {
        drillDownRow.remove();
    }

    // Retirer la classe expanded de la ligne utilisateur
    const userRow = document.querySelector(`tr[data-user-id="${currentExpandedUserId}"]`);
    if (userRow) {
        userRow.classList.remove('expanded');
    }

    currentExpandedUserId = null;
}

// =============================================================================
// 11. Client-side Sort
// =============================================================================

/**
 * Initialise le tri du tableau
 */
function initTableSort() {
    const headers = document.querySelectorAll('#users-consumption-table th[data-sort]');

    headers.forEach(header => {
        header.addEventListener('click', () => {
            const column = header.getAttribute('data-sort');

            // Toggle direction if clicking same column
            if (sortColumn === column) {
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                sortColumn = column;
                sortDirection = 'asc';
            }

            sortUsers(column, sortDirection);
            updateSortIndicators(header);
        });
    });
}

/**
 * Trie les utilisateurs par colonne
 */
function sortUsers(column, direction) {
    usersData.sort((a, b) => {
        let valA, valB;

        switch (column) {
            case 'email':
                valA = (a.email || a.user_id).toLowerCase();
                valB = (b.email || b.user_id).toLowerCase();
                break;
            case 'role':
                valA = a.role || '';
                valB = b.role || '';
                break;
            case 'generation_count':
                valA = a.generation_count || 0;
                valB = b.generation_count || 0;
                break;
            case 'total_tokens':
                valA = a.total_tokens || 0;
                valB = b.total_tokens || 0;
                break;
            case 'cost_eur':
                valA = parseFloat(a.cost_eur) || 0;
                valB = parseFloat(b.cost_eur) || 0;
                break;
            case 'last_generation':
                valA = a.last_generation ? new Date(a.last_generation).getTime() : 0;
                valB = b.last_generation ? new Date(b.last_generation).getTime() : 0;
                break;
            default:
                return 0;
        }

        if (valA < valB) return direction === 'asc' ? -1 : 1;
        if (valA > valB) return direction === 'asc' ? 1 : -1;
        return 0;
    });

    displayUsersTable(usersData);
}

/**
 * Met a jour les indicateurs de tri dans les en-tetes
 */
function updateSortIndicators(activeHeader) {
    const headers = document.querySelectorAll('#users-consumption-table th[data-sort]');

    headers.forEach(header => {
        // Retirer les anciens indicateurs
        const text = header.textContent.replace(/\s*[\u2191\u2193]/, '');

        if (header === activeHeader) {
            const arrow = sortDirection === 'asc' ? '\u2191' : '\u2193';
            header.textContent = `${text} ${arrow}`;
        } else {
            header.textContent = text;
        }
    });
}

// =============================================================================
// 12. Usage Tab - Data Loading (stubs pour plans 07-03 et 07-04)
// =============================================================================

/**
 * Charge les donnees de l'onglet Usage.
 * Appele par switchTab('usage').
 * Les fonctions initXxxChart() seront implementees dans les plans 07-03 et 07-04.
 */
async function loadUsageData() {
    // Eviter rechargement si deja charge (donnees globales, pas de filtre temporel)
    if (usageDataLoaded) return;

    try {
        // Les fonctions de charts seront ajoutees par les plans 07-03 et 07-04
        if (typeof initFeaturesChart === 'function') await initFeaturesChart();
        if (typeof initDistributionsChart === 'function') await initDistributionsChart();
        if (typeof initTrendsChart === 'function') await initTrendsChart();
        if (typeof initRolesChart === 'function') await initRolesChart();

        usageDataLoaded = true;
    } catch (error) {
        console.error('Erreur chargement donnees Usage:', error);
        if (error.status === 401 || error.status === 403) {
            handleApiError(error);
        }
    }
}

// =============================================================================
// 13. Usage Tab - Distributions Pie Chart & Features Bar Chart
// =============================================================================

function showEmptyState(chart, message) {
    chart.setOption({
        title: {
            text: message,
            left: 'center',
            top: 'center',
            textStyle: { color: '#9ca3af', fontSize: 14, fontWeight: 'normal' }
        },
        series: []
    }, true);
}

async function initDistributionsChart() {
    if (pieChart) return;

    const container = document.getElementById('chart-distributions');
    pieChart = echarts.init(container);
    pieChart.showLoading();

    try {
        const response = await fetchWithAuth('/api/admin/usage/distributions');
        pieChart.hideLoading();

        // Group by dimension
        distributionsData = {};
        if (response.items && response.items.length > 0) {
            response.items.forEach(item => {
                if (!distributionsData[item.dimension]) distributionsData[item.dimension] = [];
                distributionsData[item.dimension].push({
                    name: item.value,
                    value: item.usage_count
                });
            });
            updateDistributionChart('tone');
        } else {
            showEmptyState(pieChart, 'Aucune donnee disponible');
        }

        // Selector listener
        const selector = document.getElementById('dimension-selector');
        if (selector) {
            selector.addEventListener('change', (e) => {
                updateDistributionChart(e.target.value);
            });
        }

        // Resize handler
        const resizeObserver = new ResizeObserver(() => pieChart.resize());
        resizeObserver.observe(container);
    } catch (error) {
        pieChart.hideLoading();
        console.error('Erreur chargement distributions:', error);
        showEmptyState(pieChart, 'Erreur de chargement');
    }
}

function updateDistributionChart(dimension) {
    const data = distributionsData[dimension] || [];

    if (data.length === 0) {
        showEmptyState(pieChart, 'Aucune donnee pour ' + dimension);
        return;
    }

    pieChart.setOption({
        title: { text: '', show: false },
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { orient: 'vertical', left: 'left', top: 'middle' },
        series: [{
            name: dimension,
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['60%', '50%'],
            data: data,
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowColor: 'rgba(0,0,0,0.5)'
                }
            },
            label: { formatter: '{b}: {d}%' }
        }]
    }, true);
}

async function initFeaturesChart() {
    if (featuresChart) return;

    const container = document.getElementById('chart-features');
    featuresChart = echarts.init(container);
    featuresChart.showLoading();

    try {
        const response = await fetchWithAuth('/api/admin/usage/feature-adoption');
        featuresChart.hideLoading();

        if (!response.items || response.items.length === 0) {
            showEmptyState(featuresChart, 'Aucune donnee disponible');
            return;
        }

        // Map feature names to readable labels
        const featureLabels = {
            'web_search_enabled': 'Web Search',
            'include_quote_enabled': 'Include Quote',
            'custom_prompt_used': 'Custom Prompt',
            'news_enrichment_enabled': 'News Enrichment'
        };

        const labels = [];
        const values = [];

        response.items.forEach(item => {
            if (featureLabels[item.feature_name]) {
                labels.push(featureLabels[item.feature_name]);
                values.push(parseFloat(item.adoption_rate));
            }
        });

        if (labels.length === 0) {
            showEmptyState(featuresChart, 'Aucune donnee disponible');
            return;
        }

        featuresChart.setOption({
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'shadow' },
                formatter: function(params) {
                    return params[0].name + ': ' + params[0].value + '% d\'adoption';
                }
            },
            grid: { left: '30%', right: '12%', top: '5%', bottom: '5%' },
            xAxis: {
                type: 'value',
                max: 100,
                axisLabel: { formatter: '{value}%' }
            },
            yAxis: {
                type: 'category',
                data: labels,
                axisLabel: { fontSize: 12 }
            },
            series: [{
                type: 'bar',
                data: values,
                label: {
                    show: true,
                    position: 'right',
                    formatter: '{c}%',
                    fontSize: 12,
                    color: '#333'
                },
                itemStyle: { color: '#0077B5' }
            }]
        });

        // Resize handler
        const resizeObserver = new ResizeObserver(() => featuresChart.resize());
        resizeObserver.observe(container);
    } catch (error) {
        featuresChart.hideLoading();
        console.error('Erreur chargement features:', error);
        showEmptyState(featuresChart, 'Erreur de chargement');
    }
}

// =============================================================================
// 14. Usage Tab - Trends Line Chart
// =============================================================================

async function initTrendsChart() {
    if (trendsChart) return;

    const container = document.getElementById('chart-trends');
    trendsChart = echarts.init(container);
    trendsChart.showLoading();

    try {
        const response = await fetchWithAuth('/api/admin/usage/trends');
        trendsChart.hideLoading();

        if (!response.items || response.items.length === 0) {
            showEmptyState(trendsChart, 'Aucune donnee disponible');
            return;
        }

        // Transform data: group by dimension, extract weeks
        const seriesMap = {
            'feature_web_search': { name: 'Web Search', data: {} },
            'feature_include_quote': { name: 'Include Quote', data: {} },
            'feature_custom_prompt': { name: 'Custom Prompt', data: {} },
            'feature_news_enrichment': { name: 'News Enrichment', data: {} }
        };

        const weeks = new Set();

        response.items.forEach(item => {
            if (seriesMap[item.dimension]) {
                weeks.add(item.week_start_date);
                seriesMap[item.dimension].data[item.week_start_date] = item.usage_count;
            }
        });

        const sortedWeeks = Array.from(weeks).sort();

        // Format dates DD/MM
        const xAxisLabels = sortedWeeks.map(week => {
            const date = new Date(week);
            return String(date.getDate()).padStart(2, '0') + '/' + String(date.getMonth() + 1).padStart(2, '0');
        });

        // Build series
        const series = Object.values(seriesMap).map(s => ({
            name: s.name,
            type: 'line',
            data: sortedWeeks.map(week => s.data[week] || 0),
            smooth: true,
            emphasis: { focus: 'series' }
        }));

        trendsChart.setOption({
            tooltip: {
                trigger: 'axis',
                valueFormatter: (value) => value + ' generations'
            },
            legend: {
                data: Object.values(seriesMap).map(s => s.name),
                bottom: 0
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: xAxisLabels,
                boundaryGap: false
            },
            yAxis: {
                type: 'value',
                name: 'Generations'
            },
            series: series
        });

        // Resize handler
        const resizeObserver = new ResizeObserver(() => trendsChart.resize());
        resizeObserver.observe(container);
    } catch (error) {
        trendsChart.hideLoading();
        console.error('Erreur chargement trends:', error);
        showEmptyState(trendsChart, 'Erreur de chargement');
    }
}

// =============================================================================
// 15. Usage Tab - Roles Grouped Bar Chart
// =============================================================================

async function initRolesChart() {
    if (rolesChart) return;

    const container = document.getElementById('chart-roles');
    rolesChart = echarts.init(container);
    rolesChart.showLoading();

    try {
        const response = await fetchWithAuth('/api/admin/usage/by-role');
        rolesChart.hideLoading();

        if (!response.items || response.items.length === 0) {
            showEmptyState(rolesChart, 'Aucune donnee disponible');
            return;
        }

        // Build lookup: { role: { metricKey: count } }
        const roleLookup = {};
        response.items.forEach(item => {
            if (!roleLookup[item.role]) roleLookup[item.role] = {};
            const key = item.metric_type === 'total_generations' && item.dimension === 'all'
                ? 'generations'
                : item.metric_type === 'feature' ? item.dimension : null;
            if (key) {
                roleLookup[item.role][key] = item.count;
            }
        });

        // X-axis metrics
        const metrics = [
            { key: 'generations', label: 'Generations' },
            { key: 'web_search_enabled', label: 'Web Search' },
            { key: 'include_quote_enabled', label: 'Quote' },
            { key: 'custom_prompt_used', label: 'Custom Prompt' },
            { key: 'news_enrichment_enabled', label: 'News' }
        ];

        const xAxisLabels = metrics.map(m => m.label);
        const roles = ['FREE', 'MEDIUM', 'PREMIUM'];

        const series = roles.map(role => ({
            name: role,
            type: 'bar',
            data: metrics.map(m => (roleLookup[role] && roleLookup[role][m.key]) || 0),
            itemStyle: { color: ROLE_COLORS[role] }
        }));

        rolesChart.setOption({
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'shadow' }
            },
            legend: {
                data: roles
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '10%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: xAxisLabels
            },
            yAxis: {
                type: 'value',
                name: 'Count'
            },
            series: series
        });

        // Resize handler
        const resizeObserver = new ResizeObserver(() => rolesChart.resize());
        resizeObserver.observe(container);
    } catch (error) {
        rolesChart.hideLoading();
        console.error('Erreur chargement roles:', error);
        showEmptyState(rolesChart, 'Erreur de chargement');
    }
}


// ==================== USER DETAIL MODAL (CRUD) ====================

let currentModalUserId = null;

/**
 * Ouvre le modal de detail/edition d'un utilisateur
 */
async function openUserModal(userId) {
    const overlay = document.getElementById('user-modal-overlay');
    currentModalUserId = userId;

    try {
        const data = await fetchWithAuth(`/api/admin/users/${userId}`);

        // Remplir les champs du modal
        document.getElementById('modal-user-title').textContent = data.name || data.email || 'Utilisateur';
        document.getElementById('modal-email').textContent = data.email || '-';
        document.getElementById('modal-created').textContent = data.created_at
            ? new Date(data.created_at).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
            : '-';
        document.getElementById('modal-linkedin').textContent = data.linkedin_profile_captured ? 'Capture' : 'Non capture';

        // Toggle actif
        const toggleBtn = document.getElementById('modal-is-active');
        toggleBtn.classList.toggle('on', data.is_active);
        toggleBtn.onclick = () => toggleBtn.classList.toggle('on');

        // Role
        document.getElementById('modal-role').value = data.role;

        // Subscription status
        document.getElementById('modal-subscription-status').textContent = data.subscription_status || 'Aucun';

        // Trial dates
        const trialEndsInput = document.getElementById('modal-trial-ends');
        if (data.trial_ends_at) {
            trialEndsInput.value = new Date(data.trial_ends_at).toISOString().slice(0, 16);
        } else {
            trialEndsInput.value = '';
        }

        const trialRemaining = document.getElementById('modal-trial-remaining');
        if (data.trial_days_remaining !== null && data.trial_days_remaining !== undefined) {
            trialRemaining.textContent = `${data.trial_days_remaining}j restants`;
            trialRemaining.className = 'days-remaining';
        } else if (data.trial_ends_at && new Date(data.trial_ends_at) < new Date()) {
            trialRemaining.textContent = 'Expire';
            trialRemaining.className = 'days-remaining expired';
        } else {
            trialRemaining.textContent = '';
        }

        document.getElementById('modal-trial-started').textContent = data.trial_started_at
            ? new Date(data.trial_started_at).toLocaleDateString('fr-FR')
            : 'Jamais';

        // Grace dates
        const graceEndsInput = document.getElementById('modal-grace-ends');
        if (data.grace_ends_at) {
            graceEndsInput.value = new Date(data.grace_ends_at).toISOString().slice(0, 16);
        } else {
            graceEndsInput.value = '';
        }

        const graceRemaining = document.getElementById('modal-grace-remaining');
        if (data.grace_days_remaining !== null && data.grace_days_remaining !== undefined) {
            graceRemaining.textContent = `${data.grace_days_remaining}j restants`;
            graceRemaining.className = 'days-remaining';
        } else {
            graceRemaining.textContent = '';
        }

        // Historique des roles
        const historyTbody = document.querySelector('#modal-role-history tbody');
        historyTbody.innerHTML = '';

        if (data.role_history && data.role_history.length > 0) {
            data.role_history.forEach(entry => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${new Date(entry.changed_at).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })}</td>
                    <td>${entry.old_role ? `<span class="role-badge-modal ${entry.old_role}">${entry.old_role}</span> → ` : ''}<span class="role-badge-modal ${entry.new_role}">${entry.new_role}</span></td>
                    <td>${entry.changed_by || 'system'}</td>
                    <td>${entry.reason || '-'}</td>
                `;
                historyTbody.appendChild(tr);
            });
        } else {
            historyTbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#9ca3af;">Aucun historique</td></tr>';
        }

        overlay.classList.add('active');

    } catch (error) {
        console.error('Erreur chargement detail utilisateur:', error);
        alert('Erreur lors du chargement des details: ' + error.message);
    }
}

/**
 * Ferme le modal
 */
function closeUserModal() {
    document.getElementById('user-modal-overlay').classList.remove('active');
    currentModalUserId = null;
}

/**
 * Sauvegarde les modifications de l'utilisateur
 */
async function saveUserChanges() {
    if (!currentModalUserId) return;

    const saveBtn = document.getElementById('modal-save-btn');
    saveBtn.disabled = true;
    saveBtn.textContent = 'Sauvegarde...';

    try {
        const payload = {};

        // Role
        const roleSelect = document.getElementById('modal-role');
        payload.role = roleSelect.value;

        // Trial ends
        const trialEndsVal = document.getElementById('modal-trial-ends').value;
        if (trialEndsVal) {
            payload.trial_ends_at = new Date(trialEndsVal).toISOString();
        }

        // Grace ends
        const graceEndsVal = document.getElementById('modal-grace-ends').value;
        if (graceEndsVal) {
            payload.grace_ends_at = new Date(graceEndsVal).toISOString();
        }

        // Is active
        const isActive = document.getElementById('modal-is-active').classList.contains('on');
        payload.is_active = isActive;

        const response = await fetch(`${USERS_API_URL}/api/admin/users/${currentModalUserId}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || `Erreur ${response.status}`);
        }

        // Refresh le tableau
        await loadUsersData(currentPeriod);

        closeUserModal();
    } catch (error) {
        console.error('Erreur sauvegarde utilisateur:', error);
        alert('Erreur: ' + error.message);
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Sauvegarder';
    }
}

// Event listeners pour le modal
document.getElementById('modal-close-btn').addEventListener('click', closeUserModal);
document.getElementById('modal-cancel-btn').addEventListener('click', closeUserModal);
document.getElementById('modal-save-btn').addEventListener('click', saveUserChanges);
document.getElementById('user-modal-overlay').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeUserModal();
});
