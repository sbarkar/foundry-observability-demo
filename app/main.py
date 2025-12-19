"""
Main application demonstrating OpenTelemetry instrumentation for GenAI workflows.
Includes request handling, RAG, LLM calls, and response generation with full tracing.
"""

import time
from typing import Dict, Any
from opentelemetry.trace import Status, StatusCode

from app.observability import setup_telemetry
from app.rag import RAGClient
from app.llm import LLMClient


class GenAIApp:
    """GenAI application with comprehensive OpenTelemetry instrumentation."""
    
    def __init__(self):
        self.tracer, self.meter = setup_telemetry("foundry-genai-demo")
        self.rag_client = RAGClient(self.tracer)
        self.llm_client = LLMClient(self.tracer)
        
        # Create metrics
        self.request_counter = self.meter.create_counter(
            "genai.requests.total",
            description="Total number of GenAI requests"
        )
        self.error_counter = self.meter.create_counter(
            "genai.errors.total",
            description="Total number of errors"
        )
        self.token_counter = self.meter.create_counter(
            "genai.tokens.total",
            description="Total tokens used"
        )
    
    def process_request(self, user_query: str, use_rag: bool = True) -> Dict[str, Any]:
        """
        Process a GenAI request with full observability.
        
        Args:
            user_query: User's query (not logged in telemetry)
            use_rag: Whether to use RAG for context
            
        Returns:
            Dict containing response and metadata
        """
        # Create root span for the entire request
        with self.tracer.start_as_current_span("request.process") as span:
            request_start = time.time()
            
            # Set request metadata (no raw query)
            span.set_attributes({
                "request.query_length": len(user_query),
                "request.use_rag": use_rag,
                "request.timestamp": int(time.time()),
            })
            
            # Increment request counter
            self.request_counter.add(1, {"use_rag": str(use_rag)})
            
            try:
                context = None
                rag_metadata = {}
                
                # RAG retrieval if enabled
                if use_rag:
                    with self.tracer.start_as_current_span("request.rag_phase") as rag_span:
                        documents = self.rag_client.retrieve_documents(user_query, top_k=3)
                        context = self.rag_client.build_context(documents)
                        
                        rag_metadata = {
                            "documents_retrieved": len(documents),
                            "context_length": len(context),
                        }
                        
                        rag_span.set_attributes({
                            "rag.enabled": True,
                            "rag.documents_count": len(documents),
                        })
                
                # Safety check on user query
                with self.tracer.start_as_current_span("request.safety_check") as safety_span:
                    safety_result = self.llm_client.check_safety(user_query)
                    
                    if not safety_result["is_safe"]:
                        # Content blocked by safety filter
                        safety_span.add_event("request.blocked", attributes={
                            "blocked_categories": ",".join(safety_result["categories"]),
                        })
                        
                        span.set_status(Status(StatusCode.ERROR, "Content blocked by safety filter"))
                        span.set_attributes({
                            "request.blocked": True,
                            "request.blocked_reason": "safety_filter",
                        })
                        
                        self.error_counter.add(1, {"error_type": "safety_blocked"})
                        
                        return {
                            "blocked": True,
                            "reason": "Content blocked by safety filter",
                            "categories": safety_result["categories"],
                        }
                
                # LLM call
                with self.tracer.start_as_current_span("request.llm_phase") as llm_span:
                    llm_response = self.llm_client.call_llm(
                        prompt=user_query,
                        context=context,
                        model="gpt-4"
                    )
                    
                    # Record token usage
                    tokens = llm_response["tokens"]
                    self.token_counter.add(
                        tokens["total"],
                        {"token_type": "total", "model": llm_response["model"]}
                    )
                    self.token_counter.add(
                        tokens["prompt"],
                        {"token_type": "prompt", "model": llm_response["model"]}
                    )
                    self.token_counter.add(
                        tokens["completion"],
                        {"token_type": "completion", "model": llm_response["model"]}
                    )
                    
                    llm_span.set_attributes({
                        "llm.model": llm_response["model"],
                        "llm.tokens": tokens["total"],
                    })
                
                # Generate final response
                with self.tracer.start_as_current_span("request.response_generation") as response_span:
                    total_latency_ms = (time.time() - request_start) * 1000
                    
                    response_span.set_attributes({
                        "response.latency_ms": total_latency_ms,
                        "response.has_rag": use_rag,
                    })
                    
                    # Add final event with summary metrics
                    span.add_event("request.complete", attributes={
                        "request.total_latency_ms": total_latency_ms,
                        "request.llm_latency_ms": llm_response["latency_ms"],
                        "request.total_tokens": tokens["total"],
                        "request.success": True,
                    })
                    
                    span.set_status(Status(StatusCode.OK))
                    span.set_attributes({
                        "request.total_latency_ms": total_latency_ms,
                        "request.success": True,
                    })
                    
                    return {
                        "response": llm_response["response"],
                        "model": llm_response["model"],
                        "tokens": tokens,
                        "latency_ms": total_latency_ms,
                        "rag_used": use_rag,
                        "rag_metadata": rag_metadata if use_rag else None,
                    }
            
            except Exception as e:
                # Record error
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.add_event("request.error", attributes={
                    "error.type": type(e).__name__,
                    "error.message": str(e),
                })
                
                self.error_counter.add(1, {"error_type": type(e).__name__})
                
                raise


def main():
    """Run sample requests to demonstrate telemetry."""
    app = GenAIApp()
    
    print("Running GenAI demo with OpenTelemetry instrumentation...")
    print("=" * 70)
    
    # Example 1: Request with RAG
    print("\n1. Processing request WITH RAG:")
    try:
        result = app.process_request("What are the product features?", use_rag=True)
        print(f"   ✓ Success: {result['tokens']['total']} tokens, {result['latency_ms']:.2f}ms")
        print(f"   RAG: {result['rag_metadata']['documents_retrieved']} documents retrieved")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Example 2: Request without RAG
    print("\n2. Processing request WITHOUT RAG:")
    try:
        result = app.process_request("Tell me about pricing", use_rag=False)
        print(f"   ✓ Success: {result['tokens']['total']} tokens, {result['latency_ms']:.2f}ms")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Example 3: Multiple requests to generate metrics
    print("\n3. Processing multiple requests for metrics:")
    for i in range(3):
        try:
            result = app.process_request(f"Query {i+1}", use_rag=i % 2 == 0)
            print(f"   ✓ Request {i+1}: {result['latency_ms']:.2f}ms")
        except Exception as e:
            print(f"   ✗ Request {i+1} error: {e}")
    
    print("\n" + "=" * 70)
    print("Demo complete! Check Application Insights for telemetry data.")
    print("\nNote: Set APPLICATIONINSIGHTS_CONNECTION_STRING to export to Azure.")


if __name__ == "__main__":
    main()
