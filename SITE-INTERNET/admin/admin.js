/**
 * Admin Dashboard - LinkedIn AI Commenter
 * Logique JavaScript pour le dashboard d'administration
 */

// Configuration API - PLACEHOLDER remplace par apply-env.sh au deploy
const USERS_API_URL = '__USERS_API_URL__';

// State
let authToken = null;
let isLoading = false; // Fix M3: Prevent spam

// DOM Elements
const loginSection = document.getElementById('login-section');
const dashboardSection = document.getElementById('dashboard-section');
const errorSection = document.getElementById('error-section');
const authStatus = document.getElementById('auth-status');
const logoutBtn = document.getElementById('logout-btn');

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', init);

/**
 * Initialise le dashboard
 */
async function init() {
    // Verifier si un token est stocke (localStorage)
    authToken = localStorage.getItem('admin_jwt');

    if (authToken) {
        await loadDashboard();
    } else {
        showLoginSection();
    }

    // Event listeners
    setupEventListeners();
}

/**
 * Configure les event listeners
 */
function setupEventListeners() {
    // Login button
    const loginBtn = document.getElementById('login-btn');
    if (loginBtn) {
        loginBtn.addEventListener('click', handleLogin);
    }

    // Logout button
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }

    // Retry button - Fix M3: Debounce to prevent spam
    const retryBtn = document.getElementById('retry-btn');
    if (retryBtn) {
        retryBtn.addEventListener('click', () => {
            if (isLoading) return; // Prevent spam
            if (authToken) {
                loadDashboard();
            } else {
                showLoginSection();
            }
        });
    }
}

/**
 * Affiche la section login
 */
function showLoginSection() {
    loginSection.style.display = 'block';
    dashboardSection.style.display = 'none';
    errorSection.style.display = 'none';
    authStatus.textContent = '';
    logoutBtn.style.display = 'none';
    // Fix M4: Reset login message when showing section normally
    const loginMsg = document.getElementById('login-message');
    if (loginMsg) loginMsg.style.display = 'none';
}

/**
 * Affiche le dashboard
 */
function showDashboard() {
    loginSection.style.display = 'none';
    dashboardSection.style.display = 'grid';
    errorSection.style.display = 'none';
    authStatus.textContent = 'Connecte en tant qu\'admin';
    logoutBtn.style.display = 'inline-block';
}

/**
 * Affiche un message d'erreur
 * @param {string} message - Message d'erreur a afficher
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
 * Fix M3: Prevent concurrent calls with isLoading flag
 */
async function loadDashboard() {
    if (isLoading) return; // Fix M3: Prevent spam
    isLoading = true;

    try {
        // Fix L2: Show loading spinner
        showLoadingState();

        // Charger les deux endpoints en parallele
        const [premiumData, tokenData] = await Promise.all([
            fetchWithAuth('/api/admin/premium-count'),
            fetchWithAuth('/api/admin/token-usage')
        ]);

        // Afficher les donnees
        displayPremiumCount(premiumData);
        displayTokenUsage(tokenData);
        displayConversionSignals(tokenData);

        showDashboard();
    } catch (error) {
        handleApiError(error);
    } finally {
        isLoading = false;
        hideLoadingState();
    }
}

/**
 * Fix L2: Affiche l'etat de chargement avec spinner
 */
function showLoadingState() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) spinner.style.display = 'flex';
    dashboardSection.classList.add('loading');
}

/**
 * Fix L2: Cache l'etat de chargement
 */
function hideLoadingState() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) spinner.style.display = 'none';
    dashboardSection.classList.remove('loading');
}

/**
 * Effectue une requete authentifiee
 * @param {string} endpoint - Endpoint API (ex: /api/admin/premium-count)
 * @returns {Promise<Object>} Reponse JSON
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

    // Fix L1: Handle JSON parsing errors gracefully
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
 * Fix M4: UX coherente - pas de setTimeout confus
 * @param {Error} error - Erreur capturee
 */
function handleApiError(error) {
    if (error.status === 401) {
        // Token invalide ou expire (AC #3)
        // Fix M4: Redirection immediate vers login avec message
        localStorage.removeItem('admin_jwt');
        authToken = null;
        showLoginSectionWithMessage('Session expiree. Veuillez vous reconnecter.');
    } else if (error.status === 403) {
        // Non admin (AC #3)
        showError('Acces refuse. Vous n\'etes pas administrateur.');
    } else {
        showError(`Erreur: ${error.message}`);
    }
}

/**
 * Fix M4: Affiche la section login avec un message contextuel
 * @param {string} message - Message a afficher
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
 * Affiche le nombre d'utilisateurs premium (AC #1)
 * Fix M1: Utilise DOM methods au lieu de innerHTML
 * @param {Object} data - Donnees premium-count
 */
function displayPremiumCount(data) {
    document.getElementById('premium-count').textContent = data.count;

    const details = document.getElementById('premium-details');
    details.innerHTML = ''; // Clear previous content

    if (data.details && data.details.length > 0) {
        const ul = document.createElement('ul');
        data.details.forEach(u => {
            const li = document.createElement('li');
            const dateStr = new Date(u.created_at).toLocaleDateString('fr-FR');
            // N'afficher que l'ID tronque (respect NFR5 donnees personnelles)
            li.textContent = `ID: ${u.id.substring(0, 8)}... - Inscription: ${dateStr}`;
            ul.appendChild(li);
        });
        details.appendChild(ul);
    } else {
        details.textContent = 'Aucun utilisateur premium';
    }
}

/**
 * Affiche la consommation de tokens (AC #1)
 * Fix M1: Utilise DOM methods au lieu de innerHTML
 * @param {Object} data - Donnees token-usage
 */
function displayTokenUsage(data) {
    document.getElementById('total-tokens').textContent =
        `${data.total_tokens_all.toLocaleString('fr-FR')} tokens (${data.total_users} utilisateurs)`;

    const tbody = document.querySelector('#token-usage-table tbody');
    tbody.innerHTML = '';

    if (data.users && data.users.length > 0) {
        for (const user of data.users) {
            const row = document.createElement('tr');
            // Afficher le nom si disponible, sinon l'ID tronque
            const displayName = user.name || `${user.user_id.substring(0, 8)}...`;

            // Fix M1: Create cells with textContent instead of innerHTML
            const tdName = document.createElement('td');
            tdName.textContent = displayName;
            tdName.title = user.user_id;

            const tdTokens = document.createElement('td');
            tdTokens.textContent = user.total_tokens.toLocaleString('fr-FR');

            const tdGen = document.createElement('td');
            tdGen.textContent = user.generation_count;

            const tdModels = document.createElement('td');
            tdModels.textContent = user.models_used.join(', ') || '-';

            row.appendChild(tdName);
            row.appendChild(tdTokens);
            row.appendChild(tdGen);
            row.appendChild(tdModels);
            tbody.appendChild(row);
        }
    } else {
        const row = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = 4;
        td.style.textAlign = 'center';
        td.style.color = '#6b7280';
        td.textContent = 'Aucune donnee de consommation';
        row.appendChild(td);
        tbody.appendChild(row);
    }
}

/**
 * Affiche les signaux de conversion (AC #2 - Implementation partielle)
 *
 * LIMITATION CONNUE (Code Review 3.3):
 * AC #2 demande d'afficher les users Free ayant atteint leur quota plusieurs jours consecutifs.
 * L'implementation actuelle montre le top 5 par generation_count comme proxy MVP.
 * Un endpoint backend dedie serait necessaire pour l'implementation complete.
 *
 * Fix M1: Utilise DOM methods au lieu de innerHTML
 * @param {Object} tokenData - Donnees token-usage
 */
function displayConversionSignals(tokenData) {
    const signalsDiv = document.getElementById('conversion-signals');
    signalsDiv.innerHTML = ''; // Clear previous

    if (!tokenData.users || tokenData.users.length === 0) {
        const p = document.createElement('p');
        p.textContent = 'Aucun signal de conversion disponible.';
        signalsDiv.appendChild(p);
        return;
    }

    // Trier par generation_count decroissant et prendre les 5 premiers
    const topUsers = [...tokenData.users]
        .sort((a, b) => b.generation_count - a.generation_count)
        .slice(0, 5);

    // Fix M1: Build DOM elements instead of innerHTML
    const pTitle = document.createElement('p');
    const strong = document.createElement('strong');
    strong.textContent = 'Utilisateurs les plus actifs';
    pTitle.appendChild(strong);
    pTitle.appendChild(document.createTextNode(' (par generations):'));
    signalsDiv.appendChild(pTitle);

    const ol = document.createElement('ol');
    topUsers.forEach(u => {
        const li = document.createElement('li');
        li.textContent = `ID: ${u.user_id.substring(0, 8)}... - ${u.generation_count} generations`;
        ol.appendChild(li);
    });
    signalsDiv.appendChild(ol);

    const note = document.createElement('p');
    note.className = 'note';
    const noteStrong = document.createElement('strong');
    noteStrong.textContent = 'Note:';
    note.appendChild(noteStrong);
    note.appendChild(document.createTextNode(' Pour un suivi precis des quotas Free atteints plusieurs jours consecutifs, un endpoint dedie serait necessaire (evolution future).'));
    signalsDiv.appendChild(note);
}

/**
 * Fix M2: Valide le format JWT basique (xxx.yyy.zzz)
 * @param {string} token - Token a valider
 * @returns {boolean} True si format JWT valide
 */
function isValidJwtFormat(token) {
    if (!token || typeof token !== 'string') return false;
    const parts = token.split('.');
    if (parts.length !== 3) return false;
    // Verifier que chaque partie est du base64url valide
    const base64urlRegex = /^[A-Za-z0-9_-]+$/;
    return parts.every(part => part.length > 0 && base64urlRegex.test(part));
}

/**
 * Gere le login
 * Fix M2: Valide le format JWT avant stockage
 * Affiche des instructions pour obtenir le JWT depuis l'extension
 */
function handleLogin() {
    const token = prompt(
        'Entrez votre JWT admin:\n\n' +
        'Pour obtenir le JWT:\n' +
        '1. Connectez-vous avec l\'extension Chrome (compte admin)\n' +
        '2. DevTools → Application → Storage → chrome.storage.local\n' +
        '3. Copiez la valeur du JWT'
    );

    if (token && token.trim()) {
        const trimmedToken = token.trim();

        // Fix M2: Validate JWT format
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
}
