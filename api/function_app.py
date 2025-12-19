"""
Azure Functions app for foundry-observability-demo.
Provides stateless chat API with OpenTelemetry instrumentation.
"""
import azure.functions as func
import logging
import os

# Import function blueprints
from health import bp as health_bp
from chat import bp as chat_bp

# Initialize the function app
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Register blueprints
app.register_functions(health_bp)
app.register_functions(chat_bp)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
