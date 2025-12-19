"""
RAG (Retrieval-Augmented Generation) module with OpenTelemetry instrumentation.
Simulates document retrieval and vector search with proper tracing.
"""

import time
from typing import List, Dict, Any
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode


class RAGClient:
    """Client for RAG operations with full observability."""
    
    def __init__(self, tracer: trace.Tracer):
        self.tracer = tracer
        # Simulated document store
        self.documents = [
            {"id": "doc1", "content": "Information about product features", "category": "product"},
            {"id": "doc2", "content": "Pricing and billing information", "category": "billing"},
            {"id": "doc3", "content": "Technical documentation", "category": "technical"},
            {"id": "doc4", "content": "Customer support guidelines", "category": "support"},
            {"id": "doc5", "content": "API reference documentation", "category": "technical"},
        ]
    
    def retrieve_documents(
        self, 
        query: str, 
        top_k: int = 3,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents using vector search with OpenTelemetry tracing.
        
        Args:
            query: Search query (not logged)
            top_k: Number of documents to retrieve
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of retrieved documents with metadata
        """
        with self.tracer.start_as_current_span("rag.retrieve") as span:
            start_time = time.time()
            
            # Set metadata attributes (no raw query)
            span.set_attributes({
                "rag.query_length": len(query),
                "rag.top_k": top_k,
                "rag.similarity_threshold": similarity_threshold,
                "rag.index_size": len(self.documents),
            })
            
            try:
                # Simulate vector search
                time.sleep(0.2)  # Simulate search latency
                
                # Simulated retrieval (in reality, this would use vector embeddings)
                import random
                retrieved_docs = random.sample(self.documents, min(top_k, len(self.documents)))
                
                # Add simulated similarity scores
                for doc in retrieved_docs:
                    doc["similarity_score"] = random.uniform(similarity_threshold, 1.0)
                
                # Sort by similarity
                retrieved_docs.sort(key=lambda x: x["similarity_score"], reverse=True)
                
                latency_ms = (time.time() - start_time) * 1000
                
                # Add RAG metrics event
                span.add_event("rag.retrieval_complete", attributes={
                    "rag.documents_retrieved": len(retrieved_docs),
                    "rag.avg_similarity": sum(d["similarity_score"] for d in retrieved_docs) / len(retrieved_docs) if retrieved_docs else 0,
                    "rag.latency_ms": latency_ms,
                })
                
                span.set_attributes({
                    "rag.documents_retrieved": len(retrieved_docs),
                    "rag.latency_ms": latency_ms,
                })
                
                span.set_status(Status(StatusCode.OK))
                
                return retrieved_docs
                
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.add_event("rag.error", attributes={
                    "error.type": type(e).__name__,
                    "error.message": str(e),
                })
                raise
    
    def build_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Build context string from retrieved documents.
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            Context string for LLM
        """
        with self.tracer.start_as_current_span("rag.build_context") as span:
            try:
                context_parts = []
                total_length = 0
                
                for doc in documents:
                    content = doc.get("content", "")
                    context_parts.append(f"[{doc.get('category', 'general')}] {content}")
                    total_length += len(content)
                
                context = "\n\n".join(context_parts)
                
                span.set_attributes({
                    "rag.context_documents": len(documents),
                    "rag.context_length": len(context),
                    "rag.avg_document_length": total_length // len(documents) if documents else 0,
                })
                
                span.set_status(Status(StatusCode.OK))
                
                return context
                
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
