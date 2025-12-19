// MSAL instance
let msalInstance = null;
let accessToken = null;
let conversationHistory = [];

// Initialize MSAL
function initializeMsal() {
    const msalConfig = {
        auth: config.auth,
        cache: {
            cacheLocation: 'sessionStorage',
            storeAuthStateInCookie: false
        }
    };

    msalInstance = new msal.PublicClientApplication(msalConfig);
    
    // Handle redirect promise
    msalInstance.handleRedirectPromise().then(response => {
        if (response) {
            handleLoginResponse(response);
        } else {
            // Check if user is already logged in
            const accounts = msalInstance.getAllAccounts();
            if (accounts.length > 0) {
                msalInstance.setActiveAccount(accounts[0]);
                updateUI(accounts[0]);
            }
        }
    }).catch(error => {
        console.error('Error handling redirect:', error);
    });
}

// Login
async function login() {
    const loginRequest = {
        scopes: ['openid', 'profile', 'User.Read']
    };

    try {
        const response = await msalInstance.loginPopup(loginRequest);
        handleLoginResponse(response);
    } catch (error) {
        console.error('Login error:', error);
        alert('Login failed. Please try again.');
    }
}

// Logout
async function logout() {
    const logoutRequest = {
        account: msalInstance.getActiveAccount()
    };
    
    try {
        await msalInstance.logoutPopup(logoutRequest);
        updateUI(null);
        conversationHistory = [];
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Handle login response
function handleLoginResponse(response) {
    if (response && response.account) {
        msalInstance.setActiveAccount(response.account);
        updateUI(response.account);
    }
}

// Get access token
async function getAccessToken() {
    const account = msalInstance.getActiveAccount();
    if (!account) {
        throw new Error('No active account');
    }

    const tokenRequest = {
        scopes: config.apiScopes.length > 0 ? config.apiScopes : ['openid', 'profile'],
        account: account
    };

    try {
        const response = await msalInstance.acquireTokenSilent(tokenRequest);
        return response.accessToken;
    } catch (error) {
        console.warn('Silent token acquisition failed, trying popup:', error);
        try {
            const response = await msalInstance.acquireTokenPopup(tokenRequest);
            return response.accessToken;
        } catch (popupError) {
            console.error('Token acquisition error:', popupError);
            throw popupError;
        }
    }
}

// Update UI based on auth state
function updateUI(account) {
    const loginBtn = document.getElementById('login-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const userName = document.getElementById('user-name');
    const loginMessage = document.getElementById('login-message');
    const chatContainer = document.getElementById('chat-container');

    if (account) {
        loginBtn.style.display = 'none';
        logoutBtn.style.display = 'block';
        userName.style.display = 'block';
        userName.textContent = account.name || account.username;
        loginMessage.style.display = 'none';
        chatContainer.style.display = 'block';
    } else {
        loginBtn.style.display = 'block';
        logoutBtn.style.display = 'none';
        userName.style.display = 'none';
        loginMessage.style.display = 'block';
        chatContainer.style.display = 'none';
    }
}

// Add message to chat UI
function addMessage(role, content, metadata = {}) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const p = document.createElement('p');
    p.textContent = content;
    contentDiv.appendChild(p);
    
    messageDiv.appendChild(contentDiv);
    
    if (metadata.correlationId || metadata.latency || metadata.tokens) {
        const metadataDiv = document.createElement('div');
        metadataDiv.className = 'message-metadata';
        
        if (metadata.correlationId) {
            const span = document.createElement('span');
            span.textContent = `ID: ${metadata.correlationId}`;
            metadataDiv.appendChild(span);
        }
        
        if (metadata.latency) {
            const span = document.createElement('span');
            span.textContent = `⏱ ${metadata.latency}ms`;
            metadataDiv.appendChild(span);
        }
        
        if (metadata.tokens) {
            const span = document.createElement('span');
            span.textContent = `🎫 ${metadata.tokens} tokens`;
            metadataDiv.appendChild(span);
        }
        
        messageDiv.appendChild(metadataDiv);
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Update status bar
function updateStatusBar(data) {
    if (data.correlation_id) {
        document.getElementById('correlation-id').textContent = `Correlation ID: ${data.correlation_id}`;
    }
    if (data.latency_ms) {
        document.getElementById('latency').textContent = `Latency: ${data.latency_ms}ms`;
    }
    if (data.usage) {
        document.getElementById('tokens').textContent = 
            `Tokens: ${data.usage.total_tokens} (prompt: ${data.usage.prompt_tokens}, completion: ${data.usage.completion_tokens})`;
    }
}

// Send message
async function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const useRag = document.getElementById('use-rag').checked;
    
    const userMessage = messageInput.value.trim();
    if (!userMessage) return;
    
    // Disable input while processing
    messageInput.disabled = true;
    sendBtn.disabled = true;
    
    // Add user message to UI
    addMessage('user', userMessage);
    messageInput.value = '';
    
    // Add to conversation history
    conversationHistory.push({
        role: 'user',
        content: userMessage
    });
    
    try {
        // Get access token
        const token = await getAccessToken();
        
        // Show loading indicator
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant';
        loadingDiv.innerHTML = '<div class="message-content"><div class="loading"></div></div>';
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Call API
        const response = await fetch(`${config.apiEndpoint}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                messages: conversationHistory,
                use_rag: useRag
            })
        });
        
        // Remove loading indicator
        chatMessages.removeChild(loadingDiv);
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Add assistant response to UI
        addMessage('assistant', data.message, {
            correlationId: data.correlation_id,
            latency: data.latency_ms,
            tokens: data.usage?.total_tokens
        });
        
        // Add to conversation history
        conversationHistory.push({
            role: 'assistant',
            content: data.message
        });
        
        // Update status bar
        updateStatusBar(data);
        
    } catch (error) {
        console.error('Error sending message:', error);
        
        // Remove loading indicator if it exists
        const chatMessages = document.getElementById('chat-messages');
        const loadingDivs = chatMessages.querySelectorAll('.loading');
        loadingDivs.forEach(div => {
            const messageDiv = div.closest('.message');
            if (messageDiv) chatMessages.removeChild(messageDiv);
        });
        
        addMessage('assistant', 'Sorry, there was an error processing your request. Please try again.');
    } finally {
        // Re-enable input
        messageInput.disabled = false;
        sendBtn.disabled = false;
        messageInput.focus();
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    initializeMsal();
    
    document.getElementById('login-btn').addEventListener('click', login);
    document.getElementById('logout-btn').addEventListener('click', logout);
    
    document.getElementById('send-btn').addEventListener('click', sendMessage);
    
    document.getElementById('message-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});
