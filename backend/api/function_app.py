import os
import json
import logging
import time
import uuid
from typing import Dict, Any, Optional
import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI
from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode
from azure.monitor.opentelemetry import configure_azure_monitor

# Initialize OpenTelemetry with Application Insights
connection_string = os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING')
if connection_string:
    configure_azure_monitor(connection_string=connection_string)

# Get tracer and meter
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Create metrics
request_counter = meter.create_counter(
    "chat_requests_total",
    description="Total number of chat requests"
)
token_usage_counter = meter.create_counter(
    "openai_token_usage",
    description="Total token usage for OpenAI calls"
)
latency_histogram = meter.create_histogram(
    "chat_request_duration_seconds",
    description="Chat request duration in seconds"
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = func.FunctionApp()

def validate_token(req: func.HttpRequest) -> Optional[Dict[str, Any]]:
    """Validate Entra ID token from request headers."""
    try:
        auth_header = req.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.replace('Bearer ', '')
        # In production, validate the token using MSAL or Azure AD libraries
        # For demo purposes, we'll do basic validation
        if not token:
            return None
        
        # Return mock user info (in production, decode and validate JWT)
        return {
            'user_id': 'demo_user',
            'name': 'Demo User'
        }
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return None

def search_documents(query: str, search_endpoint: str, search_index: str = "documents") -> list:
    """Search for relevant documents using Azure AI Search."""
    try:
        credential = DefaultAzureCredential()
        search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=search_index,
            credential=credential
        )
        
        results = search_client.search(
            search_text=query,
            top=3,
            select=["content", "title"]
        )
        
        documents = []
        for result in results:
            documents.append({
                'title': result.get('title', ''),
                'content': result.get('content', '')
            })
        
        return documents
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return []

def generate_chat_response(
    messages: list,
    context_docs: list,
    openai_endpoint: str,
    deployment_name: str = "gpt-4"
) -> Dict[str, Any]:
    """Generate chat response using Azure OpenAI with RAG."""
    try:
        credential = DefaultAzureCredential()
        client = AzureOpenAI(
            azure_endpoint=openai_endpoint,
            api_version="2024-02-15-preview",
            azure_ad_token_provider=lambda: credential.get_token("https://cognitiveservices.azure.com/.default").token
        )
        
        # Build context from retrieved documents
        context = "\n\n".join([
            f"Document: {doc['title']}\n{doc['content']}"
            for doc in context_docs
        ])
        
        # Add system message with context
        system_message = {
            "role": "system",
            "content": f"You are a helpful assistant. Use the following context to answer questions:\n\n{context}" if context else "You are a helpful assistant."
        }
        
        full_messages = [system_message] + messages
        
        # Call OpenAI
        response = client.chat.completions.create(
            model=deployment_name,
            messages=full_messages,
            temperature=0.7,
            max_tokens=800
        )
        
        # Extract response and usage
        assistant_message = response.choices[0].message.content
        usage = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }
        
        # Check content filtering results
        content_filter_results = {}
        if hasattr(response.choices[0], 'content_filter_results'):
            content_filter_results = response.choices[0].content_filter_results
        
        return {
            'message': assistant_message,
            'usage': usage,
            'content_filter': content_filter_results,
            'finish_reason': response.choices[0].finish_reason
        }
    except Exception as e:
        logger.error(f"OpenAI error: {str(e)}")
        raise

@app.route(route="chat", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def chat(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP-triggered Azure Function for chat with RAG and observability.
    Expects JSON body with: { "messages": [...], "use_rag": true }
    """
    start_time = time.time()
    correlation_id = str(uuid.uuid4())
    
    # Start tracing span
    with tracer.start_as_current_span("chat_request") as span:
        span.set_attribute("correlation_id", correlation_id)
        
        try:
            # Validate authentication
            user_info = validate_token(req)
            if not user_info:
                span.set_status(Status(StatusCode.ERROR, "Authentication failed"))
                return func.HttpResponse(
                    json.dumps({"error": "Unauthorized"}),
                    status_code=401,
                    mimetype="application/json"
                )
            
            span.set_attribute("user_id", user_info['user_id'])
            
            # Parse request body
            try:
                req_body = req.get_json()
            except ValueError:
                span.set_status(Status(StatusCode.ERROR, "Invalid JSON"))
                return func.HttpResponse(
                    json.dumps({"error": "Invalid JSON in request body"}),
                    status_code=400,
                    mimetype="application/json"
                )
            
            messages = req_body.get('messages', [])
            use_rag = req_body.get('use_rag', False)
            
            if not messages:
                span.set_status(Status(StatusCode.ERROR, "No messages provided"))
                return func.HttpResponse(
                    json.dumps({"error": "No messages provided"}),
                    status_code=400,
                    mimetype="application/json"
                )
            
            span.set_attribute("message_count", len(messages))
            span.set_attribute("use_rag", use_rag)
            
            # Get environment variables
            openai_endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
            search_endpoint = os.environ.get('AZURE_SEARCH_ENDPOINT')
            
            if not openai_endpoint:
                raise ValueError("AZURE_OPENAI_ENDPOINT not configured")
            
            # Perform RAG search if requested
            context_docs = []
            if use_rag and search_endpoint:
                with tracer.start_as_current_span("search_documents") as search_span:
                    last_user_message = next(
                        (m['content'] for m in reversed(messages) if m['role'] == 'user'),
                        ""
                    )
                    context_docs = search_documents(last_user_message, search_endpoint)
                    search_span.set_attribute("documents_found", len(context_docs))
            
            # Generate response using OpenAI
            with tracer.start_as_current_span("openai_chat_completion") as openai_span:
                response_data = generate_chat_response(
                    messages=messages,
                    context_docs=context_docs,
                    openai_endpoint=openai_endpoint
                )
                
                # Log token usage
                usage = response_data['usage']
                openai_span.set_attribute("prompt_tokens", usage['prompt_tokens'])
                openai_span.set_attribute("completion_tokens", usage['completion_tokens'])
                openai_span.set_attribute("total_tokens", usage['total_tokens'])
                
                # Record metrics
                token_usage_counter.add(usage['total_tokens'], {"type": "total"})
                token_usage_counter.add(usage['prompt_tokens'], {"type": "prompt"})
                token_usage_counter.add(usage['completion_tokens'], {"type": "completion"})
                
                # Log safety flags
                if response_data.get('content_filter'):
                    openai_span.set_attribute("content_filter_results", 
                                            json.dumps(response_data['content_filter']))
            
            # Calculate latency
            latency = time.time() - start_time
            latency_histogram.record(latency)
            span.set_attribute("latency_seconds", latency)
            
            # Increment request counter
            request_counter.add(1, {"status": "success"})
            
            # Build response
            response = {
                "correlation_id": correlation_id,
                "message": response_data['message'],
                "usage": response_data['usage'],
                "latency_ms": int(latency * 1000),
                "context_documents_used": len(context_docs),
                "finish_reason": response_data['finish_reason']
            }
            
            if response_data.get('content_filter'):
                response['content_filter'] = response_data['content_filter']
            
            span.set_status(Status(StatusCode.OK))
            
            return func.HttpResponse(
                json.dumps(response),
                status_code=200,
                mimetype="application/json",
                headers={
                    "X-Correlation-ID": correlation_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            
            # Increment error counter
            request_counter.add(1, {"status": "error"})
            
            return func.HttpResponse(
                json.dumps({
                    "error": "Internal server error",
                    "correlation_id": correlation_id
                }),
                status_code=500,
                mimetype="application/json",
                headers={
                    "X-Correlation-ID": correlation_id
                }
            )

@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint."""
    return func.HttpResponse(
        json.dumps({"status": "healthy"}),
        status_code=200,
        mimetype="application/json"
    )
