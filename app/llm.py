"""
LLM interaction module with OpenTelemetry instrumentation.
Simulates LLM calls with proper tracing and custom events.
"""

import random
import time
from typing import Optional, Dict, Any
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode


class LLMClient:
    """Client for interacting with LLM with full observability."""
    
    def __init__(self, tracer: trace.Tracer):
        self.tracer = tracer
        
    def call_llm(
        self, 
        prompt: str, 
        context: Optional[str] = None,
        model: str = "gpt-4",
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Make an LLM call with OpenTelemetry tracing.
        
        Args:
            prompt: User prompt (not logged)
            context: Additional context from RAG (not logged)
            model: Model name to use
            max_tokens: Maximum tokens in response
            
        Returns:
            Dict containing response metadata and content
        """
        with self.tracer.start_as_current_span("llm.call") as span:
            start_time = time.time()
            
            # Set metadata attributes (no raw prompt/response)
            span.set_attributes({
                "llm.model": model,
                "llm.max_tokens": max_tokens,
                "llm.has_context": context is not None,
                "llm.prompt_length": len(prompt),
                "llm.context_length": len(context) if context else 0,
            })
            
            try:
                # Simulate LLM call
                # In a real implementation, this would call Azure OpenAI or similar
                time.sleep(0.5)  # Simulate network latency
                
                # Simulated response
                response_text = f"Response to query (length: {len(prompt)} chars)"
                completion_tokens = 150
                prompt_tokens = len(prompt) // 4  # Rough token estimate
                total_tokens = prompt_tokens + completion_tokens
                
                latency_ms = (time.time() - start_time) * 1000
                
                # Add event with token usage
                span.add_event("llm.tokens", attributes={
                    "llm.usage.prompt_tokens": prompt_tokens,
                    "llm.usage.completion_tokens": completion_tokens,
                    "llm.usage.total_tokens": total_tokens,
                })
                
                # Add event with latency
                span.add_event("llm.latency", attributes={
                    "llm.latency_ms": latency_ms,
                })
                
                # Set success status
                span.set_status(Status(StatusCode.OK))
                span.set_attributes({
                    "llm.response_length": len(response_text),
                    "llm.latency_ms": latency_ms,
                })
                
                return {
                    "response": response_text,
                    "model": model,
                    "tokens": {
                        "prompt": prompt_tokens,
                        "completion": completion_tokens,
                        "total": total_tokens,
                    },
                    "latency_ms": latency_ms,
                }
                
            except Exception as e:
                # Record error
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.add_event("llm.error", attributes={
                    "error.type": type(e).__name__,
                    "error.message": str(e),
                })
                raise
    
    def check_safety(self, text: str) -> Dict[str, Any]:
        """
        Check content safety with OpenTelemetry tracing.
        
        Args:
            text: Text to check (not logged)
            
        Returns:
            Dict containing safety check results
        """
        with self.tracer.start_as_current_span("llm.safety_check") as span:
            span.set_attributes({
                "safety.text_length": len(text),
            })
            
            try:
                # Simulate safety check
                time.sleep(0.1)
                
                # Simulated safety results
                is_safe = True
                blocked_categories = []
                
                # Simulate occasional blocks (10% chance)
                if random.random() < 0.1:
                    is_safe = False
                    blocked_categories = ["hate", "violence"]
                
                # Add safety event
                span.add_event("safety.check_complete", attributes={
                    "safety.is_safe": is_safe,
                    "safety.blocked": not is_safe,
                    "safety.categories_blocked": ",".join(blocked_categories) if blocked_categories else "none",
                })
                
                span.set_attributes({
                    "safety.result": "blocked" if not is_safe else "passed",
                })
                
                if not is_safe:
                    span.set_status(Status(StatusCode.ERROR, "Content blocked by safety filter"))
                else:
                    span.set_status(Status(StatusCode.OK))
                
                return {
                    "is_safe": is_safe,
                    "blocked": not is_safe,
                    "categories": blocked_categories,
                }
                
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.add_event("safety.error", attributes={
                    "error.type": type(e).__name__,
                    "error.message": str(e),
                })
                raise
