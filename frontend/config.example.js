// Example configuration file
// Copy this to config.js and update with your actual values

const config = {
    // Azure AD (Entra ID) configuration
    // Get these values from your Azure AD App Registration
    auth: {
        clientId: 'YOUR_CLIENT_ID', // Application (client) ID from Azure AD
        authority: 'https://login.microsoftonline.com/YOUR_TENANT_ID', // Replace YOUR_TENANT_ID
        redirectUri: window.location.origin // Current origin
    },
    
    // API endpoint - your Azure Function App URL
    // After deployment: https://func-foundry-demo-UNIQUE.azurewebsites.net
    // For local development: http://localhost:7071
    apiEndpoint: 'YOUR_FUNCTION_APP_URL',
    
    // Scopes for accessing the API
    // Use the scope you created in "Expose an API" section
    // Format: api://YOUR_CLIENT_ID/scope_name
    apiScopes: ['api://YOUR_CLIENT_ID/access_as_user']
};

// Environment-specific configuration
// Automatically use local backend when running locally
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    config.apiEndpoint = 'http://localhost:7071';
    config.auth.redirectUri = 'http://localhost:8080';
}
