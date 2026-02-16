/**
 * Vintage Story RCon Web Client
 * Main JavaScript Application
 */

// Application state
const App = {
    socket: null,
    config: null,
    authenticated: false,
    connected: false,
    serverInfo: {},
    commandHistory: [],
    historyIndex: -1
};

// DOM Elements
const DOM = {
    loginPanel: null,
    connectionPanel: null,
    consolePanel: null,
    loginForm: null,
    connectionForm: null,
    commandForm: null,
    consoleOutput: null,
    commandInput: null,
    connectionStatus: null,
    userInfo: null,
    username: null,
    serverInfo: null,
    connectBtn: null,
    disconnectBtn: null,
    sendBtn: null,
    logoutBtn: null
};

// Initialize the application
function init() {
    // Get DOM elements
    DOM.loginPanel = document.getElementById('login-panel');
    DOM.connectionPanel = document.getElementById('connection-panel');
    DOM.consolePanel = document.getElementById('console-panel');
    DOM.loginForm = document.getElementById('login-form');
    DOM.connectionForm = document.getElementById('connection-form');
    DOM.commandForm = document.getElementById('command-form');
    DOM.consoleOutput = document.getElementById('console-output');
    DOM.commandInput = document.getElementById('command-input');
    DOM.connectionStatus = document.getElementById('connection-status');
    DOM.userInfo = document.getElementById('user-info');
    DOM.usernameDisplay = document.getElementById('username-display');
    DOM.serverInfo = document.getElementById('server-info');
    DOM.connectBtn = document.getElementById('connect-btn');
    DOM.disconnectBtn = document.getElementById('disconnect-btn');
    DOM.sendBtn = document.getElementById('send-btn');
    DOM.logoutBtn = document.getElementById('logout-btn');

    // Setup event listeners
    DOM.loginForm.addEventListener('submit', handleLogin);
    DOM.connectionForm.addEventListener('submit', handleConnect);
    DOM.commandForm.addEventListener('submit', handleCommand);
    DOM.logoutBtn.addEventListener('click', handleLogout);
    DOM.disconnectBtn.addEventListener('click', handleDisconnect);

    // Command history navigation
    DOM.commandInput.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowUp') {
            e.preventDefault();
            navigateHistory('up');
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            navigateHistory('down');
        }
    });

    // Load configuration
    loadConfig();

    // Initialize socket connection
    initSocket();
}

// Helper function to get cookie value
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

// Helper function to set cookie
function setCookie(name, value, days) {
    let expires = '';
    if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = '; expires=' + date.toUTCString();
    }
    document.cookie = name + '=' + (value || '') + expires + '; path=/; SameSite=Lax';
}

// Helper function to delete cookie
function deleteCookie(name) {
    document.cookie = name + '=; Max-Age=-99999999; path=/';
}

// Load configuration from server
function loadConfig() {
    fetch('/config')
        .then(response => response.json())
        .then(config => {
            App.config = config;

            // Set default values
            if (config.rcon) {
                document.getElementById('rcon-host').value = config.rcon.default_host || 'localhost';
                document.getElementById('rcon-port').value = config.rcon.default_port || 42425;

                // Lock address if configured
                if (config.rcon.locked_address) {
                    document.getElementById('rcon-host').disabled = true;
                    document.getElementById('rcon-port').disabled = true;
                    showMessage('connection-message', 'Server address is locked by administrator', 'info');
                }
            }

            // Setup OAuth buttons if enabled
            if (config.security && config.security.oauth_enabled && config.security.oauth_providers) {
                setupOAuthButtons(config.security.oauth_providers);
            }

            // Setup traditional login visibility
            if (config.security && config.security.traditional_login_enabled === false) {
                // Hide traditional login form
                const traditionalLoginSection = document.getElementById('traditional-login-section');
                if (traditionalLoginSection) {
                    traditionalLoginSection.style.display = 'none';
                }

                // Also hide the login form's submit handler won't interfere
                const loginForm = document.getElementById('login-form');
                if (loginForm) {
                    loginForm.style.display = config.security.oauth_enabled ? 'block' : 'none';
                }
            }

            // Check if authentication is required
            if (!config.security || !config.security.require_auth) {
                // Skip login if authentication is not required
                App.authenticated = true;
                showConnectionPanel();
            }
        })
        .catch(error => {
            console.error('Error loading configuration:', error);
            addConsoleMessage('Error loading configuration', 'error');
        });
}

// Initialize Socket.IO connection
function initSocket() {
    // Get JWT token from localStorage (for traditional login) or it will be in cookie (for OAuth)
    const token = localStorage.getItem('access_token') || getCookie('access_token');

    // Connect with token in query string if available
    const socketOptions = {};
    if (token) {
        socketOptions.query = { token: token };
    }

    App.socket = io(socketOptions);

    App.socket.on('connect', () => {
        console.log('Socket connected');
        console.log('Socket ID:', App.socket.id);
        addConsoleMessage('Connected to server', 'system');

        // Check if user is already authenticated (e.g., via OAuth or stored token)
        checkAuthStatus();
    });

    App.socket.on('disconnect', () => {
        console.log('Socket disconnected');
        App.connected = false;
        updateConnectionStatus(false);
        addConsoleMessage('Disconnected from server', 'error');
    });

    App.socket.on('connected', (data) => {
        console.log('Received connected event:', data);
        addConsoleMessage(data.message, 'system');
    });

    App.socket.on('login_response', (data) => {
        console.log('Received login_response:', data);
        handleLoginResponse(data);
    });

    App.socket.on('auth_status', (data) => {
        console.log('Received auth_status:', data);
        handleAuthStatus(data);
    });

    App.socket.on('logout_response', (data) => {
        console.log('Received logout_response:', data);
        handleLogoutResponse(data);
    });

    App.socket.on('rcon_response', (data) => {
        console.log('Received rcon_response:', data);
        handleRConResponse(data);
    });

    App.socket.on('command_response', (data) => {
        console.log('Received command_response:', data);
        handleCommandResponse(data);
    });

    App.socket.on('status_response', (data) => {
        console.log('Received status_response:', data);
        handleStatusResponse(data);
    });
}

// Setup OAuth buttons based on enabled providers
function setupOAuthButtons(providers) {
    if (!providers || providers.length === 0) {
        return;
    }

    // Show the OAuth buttons container
    const oauthContainer = document.getElementById('oauth-buttons');
    if (oauthContainer) {
        oauthContainer.style.display = 'block';

        // If traditional login is disabled, remove top margin and hide divider
        if (App.config && App.config.security && App.config.security.traditional_login_enabled === false) {
            oauthContainer.style.marginTop = '0';
            const divider = oauthContainer.querySelector('.divider');
            if (divider) {
                divider.style.display = 'none';
            }
        }
    }

    // Show individual provider buttons
    providers.forEach(provider => {
        const buttonId = provider + '-login-btn';
        const button = document.getElementById(buttonId);
        if (button) {
            button.style.display = 'inline-flex';
        }
    });
}

// Handle login form submission
function handleLogin(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    App.socket.emit('login', { username, password });
}

// Handle login response
function handleLoginResponse(data) {
    if (data.success) {
        App.authenticated = true;
        App.username = data.username;
        showMessage('login-message', data.message, 'success');

        // Store JWT token
        if (data.token) {
            localStorage.setItem('access_token', data.token);
            setCookie('access_token', data.token, 1); // 1 day expiration

            // Reconnect Socket.IO with token
            if (App.socket) {
                App.socket.disconnect();
                setTimeout(() => {
                    initSocket(); // Reconnect with token
                }, 100);
            }
        }
;

        setTimeout(() => {
            showConnectionPanel();
        }, 500);
    } else {
        showMessage('login-message', data.message, 'error');
    }
}

// Handle logout
function handleLogout() {
    // Clear JWT tokens
    localStorage.removeItem('access_token');
    deleteCookie('access_token');

    // Redirect to logout endpoint
    addConsoleMessage('Logging out...', 'system');
    window.location.href = '/logout';
}

// Handle logout response (keeping for backward compatibility if needed)
function handleLogoutResponse(data) {
    console.log('Received logout_response:', data);

    // Clear JWT tokens
    localStorage.removeItem('access_token');
    deleteCookie('access_token');

    if (data.redirect) {
        // Redirect to logout route which will clear the session cookie
        addConsoleMessage('Logging out...', 'system');
        window.location.href = data.redirect;
    } else {
        // Fallback to manual logout
        App.authenticated = false;
        App.connected = false;
        App.username = null;

        // Reset UI
        DOM.loginPanel.style.display = 'block';
        DOM.connectionPanel.style.display = 'none';
        DOM.consolePanel.style.display = 'none';
        DOM.userInfo.style.display = 'none';

        updateConnectionStatus(false);

        // Clear forms
        DOM.loginForm.reset();
        DOM.connectionForm.reset();

        addConsoleMessage('Logged out', 'system');
    }
}

// Check authentication status (for OAuth sessions)
function checkAuthStatus() {
    App.socket.emit('check_auth');
}

// Handle authentication status response
function handleAuthStatus(data) {
    if (data.authenticated) {
        App.authenticated = true;
        App.username = data.username;

        // Show success message if we just logged in
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('login') === 'success') {
            showMessage('login-message', 'Login successful', 'success');
            // Clean up URL
            window.history.replaceState({}, document.title, window.location.pathname);
        }

        addConsoleMessage(`Authenticated as ${data.display_name || data.username}`, 'system');
        if (data.oauth_provider) {
            addConsoleMessage(`Logged in via ${data.oauth_provider}`, 'system');
        }

        showConnectionPanel();
    } else {
        // Check for OAuth error in URL
        const urlParams = new URLSearchParams(window.location.search);
        const error = urlParams.get('error');
        if (error) {
            let errorMessage = 'OAuth login failed';
            switch(error) {
                case 'no_email':
                    errorMessage = 'OAuth provider did not provide an email address';
                    break;
                case 'unauthorized':
                    errorMessage = 'Your email is not authorized to access this application';
                    break;
                case 'oauth_failed':
                    errorMessage = 'OAuth authentication failed';
                    break;
                case 'invalid_provider':
                    errorMessage = 'Invalid OAuth provider';
                    break;
            }
            showMessage('login-message', errorMessage, 'error');
            // Clean up URL
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }
}

// Show connection panel
function showConnectionPanel() {
    DOM.loginPanel.style.display = 'none';
    DOM.userInfo.style.display = 'flex';
    DOM.usernameDisplay.textContent = App.username || 'User';

    // Check if locked_address is enabled
    if (App.config && App.config.rcon && App.config.rcon.locked_address) {
        // Skip connection form and auto-connect
        DOM.connectionPanel.style.display = 'none';
        DOM.consolePanel.style.display = 'block';

        // Auto-connect to RCon server
        setTimeout(() => {
            autoConnectRCon();
        }, 500);
    } else {
        // Show connection form
        DOM.connectionPanel.style.display = 'block';
        DOM.consolePanel.style.display = 'block';
    }
}

// Auto-connect to RCon server (used when locked_address is true)
function autoConnectRCon() {
    if (!App.config || !App.config.rcon) {
        addConsoleMessage('Error: Configuration not loaded', 'error');
        return;
    }

    const host = App.config.rcon.default_host;
    const port = App.config.rcon.default_port;

    console.log('autoConnectRCon: Emitting rcon_connect event', { host, port });
    console.log('Socket connected:', App.socket.connected);
    console.log('Socket id:', App.socket.id);

    // Emit connection without password (server will use configured password)
    App.socket.emit('rcon_connect', { host, port });

    addConsoleMessage(`Auto-connecting to ${host}:${port}...`, 'system');
}

// Handle RCon connection
function handleConnect(e) {
    e.preventDefault();

    const host = document.getElementById('rcon-host').value;
    const port = document.getElementById('rcon-port').value;
    const password = document.getElementById('rcon-password').value;

    console.log('handleConnect: Emitting rcon_connect event', { host, port, password: '***' });
    console.log('Socket connected:', App.socket.connected);
    console.log('Socket id:', App.socket.id);

    App.socket.emit('rcon_connect', { host, port, password });

    addConsoleMessage(`Connecting to ${host}:${port}...`, 'system');
}

// Handle RCon disconnection
function handleDisconnect() {
    App.socket.emit('rcon_disconnect');
    addConsoleMessage('Disconnecting from RCon server...', 'system');
}

// Handle RCon response
function handleRConResponse(data) {
    if (data.success) {
        App.connected = true;
        App.serverInfo = { host: data.host, port: data.port };

        updateConnectionStatus(true, `${data.host}:${data.port}`);
        showMessage('connection-message', data.message, 'success');

        // Enable command input
        DOM.commandInput.disabled = false;
        DOM.sendBtn.disabled = false;

        // Update UI
        DOM.connectBtn.style.display = 'none';
        DOM.disconnectBtn.style.display = 'inline-block';

        addConsoleMessage(`Connected to ${data.host}:${data.port}`, 'success');
    } else {
        App.connected = false;
        updateConnectionStatus(false);
        showMessage('connection-message', data.message, 'error');

        // Disable command input
        DOM.commandInput.disabled = true;
        DOM.sendBtn.disabled = true;

        // Update UI
        DOM.connectBtn.style.display = 'inline-block';
        DOM.disconnectBtn.style.display = 'none';

        addConsoleMessage(`Connection failed: ${data.message}`, 'error');
    }
}

// Handle command submission
function handleCommand(e) {
    e.preventDefault();

    const command = DOM.commandInput.value.trim();
    if (!command) return;

    // Add to history
    App.commandHistory.unshift(command);
    App.historyIndex = -1;

    // Show command in console
    addConsoleMessage(`> ${command}`, 'command');

    // Send command
    App.socket.emit('rcon_command', { command });

    // Clear input
    DOM.commandInput.value = '';
}

// Handle command response
function handleCommandResponse(data) {
    if (data.success) {
        const message = data.message || '(no output)';
        const isHtml = data.is_html || false;
        addConsoleMessage(message, 'response', isHtml);
    } else {
        addConsoleMessage(`Error: ${data.message}`, 'error');
    }
}

// Handle status response
function handleStatusResponse(data) {
    if (data.connected) {
        App.connected = true;
        App.serverInfo = { host: data.host, port: data.port };
        updateConnectionStatus(true, `${data.host}:${data.port}`);
    } else {
        App.connected = false;
        updateConnectionStatus(false);
    }
}

// Navigate command history
function navigateHistory(direction) {
    if (App.commandHistory.length === 0) return;

    if (direction === 'up') {
        if (App.historyIndex < App.commandHistory.length - 1) {
            App.historyIndex++;
            DOM.commandInput.value = App.commandHistory[App.historyIndex];
        }
    } else if (direction === 'down') {
        if (App.historyIndex > 0) {
            App.historyIndex--;
            DOM.commandInput.value = App.commandHistory[App.historyIndex];
        } else if (App.historyIndex === 0) {
            App.historyIndex = -1;
            DOM.commandInput.value = '';
        }
    }
}

// Update connection status
function updateConnectionStatus(connected, info = '') {
    if (connected) {
        DOM.connectionStatus.textContent = 'Connected';
        DOM.connectionStatus.className = 'status connected';
        if (info) {
            DOM.serverInfo.textContent = info;
        }
    } else {
        DOM.connectionStatus.textContent = 'Disconnected';
        DOM.connectionStatus.className = 'status disconnected';
        DOM.serverInfo.textContent = '';
    }
}

// Show message
function showMessage(elementId, message, type) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.textContent = message;
    element.className = `message ${type} show`;

    setTimeout(() => {
        element.classList.remove('show');
    }, 5000);
}

// Add message to console
function addConsoleMessage(message, type = 'response', isHtml = false) {
    const line = document.createElement('div');
    line.className = `console-line ${type}`;

    const timestamp = document.createElement('span');
    timestamp.className = 'timestamp';
    const now = new Date();
    timestamp.textContent = `[${now.toLocaleTimeString()}]`;

    const messageSpan = document.createElement('span');
    messageSpan.className = 'message';

    // Use innerHTML for HTML content, textContent for plain text
    if (isHtml) {
        messageSpan.innerHTML = message;
    } else {
        messageSpan.textContent = message;
    }

    line.appendChild(timestamp);
    line.appendChild(messageSpan);

    DOM.consoleOutput.appendChild(line);

    // Auto-scroll to bottom
    DOM.consoleOutput.scrollTop = DOM.consoleOutput.scrollHeight;
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

