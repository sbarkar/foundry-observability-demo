// Configuration for the application
// Copy this file and update with your actual values
const config = {
    // Azure AD (Entra ID) configuration
    auth: {
        clientId: 'YOUR_CLIENT_ID', // Application (client) ID from Azure AD
        authority: 'https://login.microsoftonline.com/YOUR_TENANT_ID', // Tenant ID
        redirectUri: window.location.origin // Current origin
    },
    // API endpoint
    apiEndpoint: 'YOUR_FUNCTION_APP_URL', // e.g., https://func-foundry-demo.azurewebsites.net
    // Scopes for accessing the API
    apiScopes: ['api://YOUR_CLIENT_ID/access_as_user']
};

// For local development, you can use environment-specific config
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    config.apiEndpoint = 'http://localhost:7071';
}
