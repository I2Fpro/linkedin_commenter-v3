/**
 * Admin Dashboard - LinkedIn AI Commenter
 * Logique JavaScript pour le dashboard d'administration
 */

// Configuration API - PLACEHOLDER remplace par apply-env.sh au deploy
const USERS_API_URL = '__USERS_API_URL__';

// State
let authToken = null;

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

    // Retry button
    const retryBtn = document.getElementById('retry-btn');
    if (retryBtn) {
        retryBtn.addEventListener('click', () => {
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
 */
async function loadDashboard() {
    try {
        // Ajouter etat de chargement
        dashboardSection.classList.add('loading');

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
        dashboardSection.classList.remove('loading');
    }
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

    return response.json();
}

/**
 * Gere les erreurs API
 * @param {Error} error - Erreur capturee
 */
function handleApiError(error) {
    if (error.status === 401) {
        // Token invalide ou expire (AC #3)
        localStorage.removeItem('admin_jwt');
        authToken = null;
        showError('Session expiree. Veuillez vous reconnecter.');
        setTimeout(showLoginSection, 2000);
    } else if (error.status === 403) {
        // Non admin (AC #3)
        showError('Acces refuse. Vous n\'etes pas administrateur.');
    } else {
        showError(`Erreur: ${error.message}`);
    }
}

/**
 * Affiche le nombre d'utilisateurs premium (AC #1)
 * @param {Object} data - Donnees premium-count
 */
function displayPremiumCount(data) {
    document.getElementById('premium-count').textContent = data.count;

    const details = document.getElementById('premium-details');
    if (data.details && data.details.length > 0) {
        const list = data.details.map(u => {
            const dateStr = new Date(u.created_at).toLocaleDateString('fr-FR');
            // N'afficher que l'ID tronque (respect NFR5 donnees personnelles)
            return `<li>ID: ${u.id.substring(0, 8)}... - Inscription: ${dateStr}</li>`;
        }).join('');
        details.innerHTML = `<ul>${list}</ul>`;
    } else {
        details.textContent = 'Aucun utilisateur premium';
    }
}

/**
 * Affiche la consommation de tokens (AC #1)
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
            row.innerHTML = `
                <td title="${user.user_id}">${displayName}</td>
                <td>${user.total_tokens.toLocaleString('fr-FR')}</td>
                <td>${user.generation_count}</td>
                <td>${user.models_used.join(', ') || '-'}</td>
            `;
            tbody.appendChild(row);
        }
    } else {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="4" style="text-align: center; color: #6b7280;">Aucune donnee de consommation</td>';
        tbody.appendChild(row);
    }
}

/**
 * Affiche les signaux de conversion (AC #2)
 * Version MVP: Affiche les utilisateurs les plus actifs par generation_count
 * comme proxy des signaux de conversion (utilisateurs Free proches du quota)
 * @param {Object} tokenData - Donnees token-usage
 */
function displayConversionSignals(tokenData) {
    const signalsDiv = document.getElementById('conversion-signals');

    if (!tokenData.users || tokenData.users.length === 0) {
        signalsDiv.innerHTML = '<p>Aucun signal de conversion disponible.</p>';
        return;
    }

    // Trier par generation_count decroissant et prendre les 5 premiers
    const topUsers = [...tokenData.users]
        .sort((a, b) => b.generation_count - a.generation_count)
        .slice(0, 5);

    signalsDiv.innerHTML = `
        <p><strong>Utilisateurs les plus actifs</strong> (par generations):</p>
        <ol>
            ${topUsers.map(u =>
                `<li>ID: ${u.user_id.substring(0, 8)}... - ${u.generation_count} generations</li>`
            ).join('')}
        </ol>
        <p class="note">
            <strong>Note:</strong> Pour un suivi precis des quotas Free atteints
            plusieurs jours consecutifs, un endpoint dedie serait necessaire
            (evolution future).
        </p>
    `;
}

/**
 * Gere le login
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
        authToken = token.trim();
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
