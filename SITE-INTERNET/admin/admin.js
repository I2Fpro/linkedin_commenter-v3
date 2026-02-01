/**
 * Admin Dashboard - LinkedIn AI Commenter
 * Logique JavaScript pour le dashboard d'administration
 */

// Configuration API - PLACEHOLDER remplace par apply-env.sh au deploy
const USERS_API_URL = '__USERS_API_URL__';
const AI_SERVICE_URL = '__AI_API_URL__'; // Story 4-3: Pour charger Google Client ID

// State
let authToken = null;
let isLoading = false; // Fix M3: Prevent spam
let GOOGLE_CLIENT_ID = null; // Story 4-3
let tokenClient = null; // Story 4-3: OAuth token client

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
        // Story 4-3: Initialiser Google Sign-In
        initGoogleSignIn();
    }

    // Event listeners
    setupEventListeners();
}

/**
 * Configure les event listeners
 */
function setupEventListeners() {
    // Story 4-3: JWT manual link (fallback)
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

    // Retry button - Fix M3: Debounce to prevent spam
    const retryBtn = document.getElementById('retry-btn');
    if (retryBtn) {
        retryBtn.addEventListener('click', () => {
            if (isLoading) return; // Prevent spam
            if (authToken) {
                loadDashboard();
            } else {
                showLoginSection();
                initGoogleSignIn();
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

// =============================================================================
// Story 4-3: Google OAuth Functions
// =============================================================================

/**
 * Story 4-3: Charge la configuration Google OAuth depuis le backend
 * @returns {Promise<boolean>} True si config chargee avec succes
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
 * Story 4-3: Initialise Google Sign-In
 */
async function initGoogleSignIn() {
    const configLoaded = await loadGoogleConfig();
    if (!configLoaded || !GOOGLE_CLIENT_ID) {
        return;
    }

    // Attendre que le SDK Google soit charge
    if (typeof google === 'undefined') {
        console.log('En attente du chargement du SDK Google...');
        setTimeout(initGoogleSignIn, 100);
        return;
    }

    // Initialiser le client OAuth 2.0
    tokenClient = google.accounts.oauth2.initTokenClient({
        client_id: GOOGLE_CLIENT_ID,
        scope: 'https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile',
        callback: handleGoogleCallback,
    });

    // Attacher le bouton Google
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
 * Story 4-3: Gere la reponse de Google OAuth
 * @param {Object} response - Reponse OAuth de Google
 */
async function handleGoogleCallback(response) {
    const googleBtn = document.getElementById('google-signin-btn');

    try {
        if (response.error) {
            throw new Error(response.error);
        }

        // Desactiver le bouton pendant le traitement
        if (googleBtn) {
            googleBtn.disabled = true;
            googleBtn.innerHTML = '<span>Connexion en cours...</span>';
        }

        const googleAccessToken = response.access_token;
        console.log('Google access token recu');

        // Echanger le token Google contre un JWT backend
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
            // Stocker temporairement le token
            const tempToken = data.access_token;

            // Verifier que l'utilisateur est admin en appelant un endpoint admin
            authToken = tempToken;
            const isAdmin = await verifyAdminAccess();

            if (isAdmin) {
                // Stocker definitivement le token
                localStorage.setItem('admin_jwt', authToken);
                await loadDashboard();
            } else {
                // Pas admin - ne pas stocker le token
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
        // Reactiver le bouton
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
 * Story 4-3: Verifie que l'utilisateur a acces admin
 * @returns {Promise<boolean>} True si l'utilisateur est admin
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
 * Story 4-3: Gere le login JWT manuel (fallback)
 * Ancien handleLogin renomme
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
    // Story 4-3: Reinitialiser Google Sign-In apres deconnexion
    initGoogleSignIn();
}
