"""
Chat endpoint with Azure OpenAI integration and optional RAG.
"""
import azure.functions as func
import json
import logging
import os
from typing import Dict, List, Optional
from azure.identity import DefaultAzureCredential
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.search.documents import SearchClient
from correlation import generate_correlation_id
from auth import validate_jwt_token, extract_bearer_token
from telemetry import get_tracer, add_span_attributes
import jwt

logger = logging.getLogger(__name__)

# Constants
MAX_MESSAGE_LENGTH = 4000

# Create blueprint for chat function
bp = func.Blueprint()

# Global clients (initialized lazily)
_openai_client = None
_search_client = None
_credential = None


def get_credential():
    """Get or create DefaultAzureCredential instance."""
    global _credential
    if _credential is None:
        _credential = DefaultAzureCredential()
    return _credential


def get_openai_client():
    """Get or create Azure OpenAI client with managed identity."""
    global _openai_client
    if _openai_client is None:
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if not endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT not configured")
        
        credential = get_credential()
        _openai_client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=credential
        )
        logger.info("Initialized Azure OpenAI client")
    
    return _openai_client


def get_search_client():
    """Get or create Azure AI Search client with managed identity."""
    global _search_client
    if _search_client is None:
        endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
        
        if not endpoint or not index_name:
            raise ValueError("Azure Search not configured")
        
        credential = get_credential()
        _search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=credential
        )
        logger.info("Initialized Azure AI Search client")
    
    return _search_client


def perform_rag_search(query: str, top_k: int = 3) -> List[Dict]:
    """
    Perform RAG search using Azure AI Search.
    Returns top-k relevant documents without logging content.
    
    Args:
        query: User query for semantic search
        top_k: Number of top results to return
        
    Returns:
        List of search results with metadata only
    """
    try:
        search_client = get_search_client()
        
        # Perform semantic search
        results = search_client.search(
            search_text=query,
            top=top_k,
            select=["id", "content"]  # Only select needed fields
        )
        
        documents = []
        for result in results:
            # Extract only metadata, never log actual content
            doc_metadata = {
                "id": result.get("id", "unknown"),
                "score": result.get("@search.score", 0.0)
            }
            documents.append({
                "metadata": doc_metadata,
                "content": result.get("content", "")  # Used in prompt but not logged
            })
        
        logger.info(f"RAG search returned {len(documents)} documents")
        return documents
    
    except Exception as e:
        logger.error(f"RAG search failed: {str(e)}")
        return []


def create_chat_completion(user_message: str, rag_context: Optional[List[Dict]] = None, correlation_id: str = "") -> Dict:
    """
    Create chat completion with Azure OpenAI.
    
    Args:
        user_message: User's chat message
        rag_context: Optional RAG documents to inject into prompt
        correlation_id: Correlation ID for tracking
        
    Returns:
        Response dictionary with answer and metadata
    """
    tracer = get_tracer(__name__)
    
    with tracer.start_as_current_span("openai_chat_completion") as span:
        add_span_attributes(span, {
            "correlation_id": correlation_id,
            "rag_enabled": rag_context is not None,
            "rag_doc_count": len(rag_context) if rag_context else 0
        })
        
        try:
            client = get_openai_client()
            deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
            
            # Build messages
            messages = []
            
            # System message
            system_content = "You are a helpful AI assistant."
            if rag_context:
                # Inject RAG context into system prompt
                context_snippets = [doc["content"] for doc in rag_context]
                context_text = "\n\n".join([f"[Document {i+1}]\n{snippet}" for i, snippet in enumerate(context_snippets)])
                system_content = f"{system_content}\n\nUse the following context to answer the user's question:\n\n{context_text}"
            
            messages.append(SystemMessage(content=system_content))
            messages.append(UserMessage(content=user_message))
            
            # Call Azure OpenAI
            response = client.complete(
                model=deployment_name,
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )
            
            # Extract response
            answer = response.choices[0].message.content
            
            # Log metadata only
            add_span_attributes(span, {
                "model": deployment_name,
                "finish_reason": response.choices[0].finish_reason,
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0
            })
            
            logger.info(f"Chat completion successful - correlationId: {correlation_id}")
            
            return {
                "answer": answer,
                "model": deployment_name,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }
            }
        
        except Exception as e:
            logger.error(f"Chat completion failed: {str(e)} - correlationId: {correlation_id}")
            raise


@bp.route(route="chat", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def chat(req: func.HttpRequest) -> func.HttpResponse:
    """
    Chat endpoint with JWT authentication and Azure OpenAI integration.
    Supports optional RAG via Azure AI Search.
    
    Request body:
        {
            "message": "User's message",
            "enableRag": false  // optional
        }
    
    Response:
        {
            "answer": "AI response",
            "correlationId": "uuid",
            "model": "gpt-4",
            "usage": {...}
        }
    """
    correlation_id = generate_correlation_id()
    tracer = get_tracer(__name__)
    
    with tracer.start_as_current_span("chat_request") as span:
        add_span_attributes(span, {"correlation_id": correlation_id})
        
        try:
            # JWT validation
            auth_header = req.headers.get("Authorization")
            token = extract_bearer_token(auth_header)
            
            if not token and os.getenv("JWT_VALIDATION_ENABLED", "true").lower() == "true":
                logger.warning(f"Missing authorization token - correlationId: {correlation_id}")
                return func.HttpResponse(
                    body=json.dumps({
                        "error": "Unauthorized",
                        "message": "Missing or invalid authorization token",
                        "correlationId": correlation_id
                    }),
                    status_code=401,
                    mimetype="application/json",
                    headers={"X-Correlation-ID": correlation_id}
                )
            
            if token:
                try:
                    payload = validate_jwt_token(token)
                    add_span_attributes(span, {"user_id": payload.get("sub", "unknown")})
                except jwt.InvalidTokenError as e:
                    logger.warning(f"Invalid JWT token: {str(e)} - correlationId: {correlation_id}")
                    return func.HttpResponse(
                        body=json.dumps({
                            "error": "Unauthorized",
                            "message": "Invalid authorization token",
                            "correlationId": correlation_id
                        }),
                        status_code=401,
                        mimetype="application/json",
                        headers={"X-Correlation-ID": correlation_id}
                    )
            
            # Parse request body
            try:
                req_body = req.get_json()
            except ValueError:
                logger.warning(f"Invalid JSON in request body - correlationId: {correlation_id}")
                return func.HttpResponse(
                    body=json.dumps({
                        "error": "Bad Request",
                        "message": "Invalid JSON in request body",
                        "correlationId": correlation_id
                    }),
                    status_code=400,
                    mimetype="application/json",
                    headers={"X-Correlation-ID": correlation_id}
                )
            
            # Validate required fields
            user_message = req_body.get("message")
            if not user_message or not isinstance(user_message, str):
                logger.warning(f"Missing or invalid 'message' field - correlationId: {correlation_id}")
                return func.HttpResponse(
                    body=json.dumps({
                        "error": "Bad Request",
                        "message": "Missing or invalid 'message' field in request body",
                        "correlationId": correlation_id
                    }),
                    status_code=400,
                    mimetype="application/json",
                    headers={"X-Correlation-ID": correlation_id}
                )
            
            # Check if message is too long
            if len(user_message) > MAX_MESSAGE_LENGTH:
                logger.warning(f"Message too long - correlationId: {correlation_id}")
                return func.HttpResponse(
                    body=json.dumps({
                        "error": "Bad Request",
                        "message": f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters",
                        "correlationId": correlation_id
                    }),
                    status_code=400,
                    mimetype="application/json",
                    headers={"X-Correlation-ID": correlation_id}
                )
            
            # Log request metadata only (no user content)
            logger.info(f"Processing chat request - correlationId: {correlation_id}")
            
            # Optional RAG
            rag_context = None
            enable_rag = req_body.get("enableRag", False)
            rag_enabled_global = os.getenv("RAG_ENABLED", "false").lower() == "true"
            
            if enable_rag and rag_enabled_global:
                top_k = int(os.getenv("AZURE_SEARCH_TOP_K", "3"))
                rag_context = perform_rag_search(user_message, top_k=top_k)
            
            # Create chat completion
            result = create_chat_completion(
                user_message=user_message,
                rag_context=rag_context,
                correlation_id=correlation_id
            )
            
            # Build response
            response_body = {
                "answer": result["answer"],
                "correlationId": correlation_id,
                "model": result["model"],
                "usage": result["usage"]
            }
            
            return func.HttpResponse(
                body=json.dumps(response_body),
                status_code=200,
                mimetype="application/json",
                headers={"X-Correlation-ID": correlation_id}
            )
        
        except ValueError as e:
            # Configuration or validation errors
            logger.error(f"Configuration error: {str(e)} - correlationId: {correlation_id}")
            return func.HttpResponse(
                body=json.dumps({
                    "error": "Service Configuration Error",
                    "message": "Service is not properly configured",
                    "correlationId": correlation_id
                }),
                status_code=500,
                mimetype="application/json",
                headers={"X-Correlation-ID": correlation_id}
            )
        
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error: {str(e)} - correlationId: {correlation_id}", exc_info=True)
            return func.HttpResponse(
                body=json.dumps({
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                    "correlationId": correlation_id
                }),
                status_code=500,
                mimetype="application/json",
                headers={"X-Correlation-ID": correlation_id}
            )
