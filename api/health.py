"""
Health check endpoint for monitoring and readiness probes.
"""
import azure.functions as func
import json
import logging
from correlation import generate_correlation_id

logger = logging.getLogger(__name__)

# Create blueprint for health function
bp = func.Blueprint()


@bp.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint.
    Returns 200 OK with status information.
    No authentication required.
    """
    correlation_id = generate_correlation_id()
    
    logger.info(f"Health check requested - correlationId: {correlation_id}")
    
    response_body = {
        "status": "healthy",
        "service": "foundry-observability-demo-api",
        "correlationId": correlation_id
    }
    
    return func.HttpResponse(
        body=json.dumps(response_body),
        status_code=200,
        mimetype="application/json",
        headers={
            "X-Correlation-ID": correlation_id
        }
    )
