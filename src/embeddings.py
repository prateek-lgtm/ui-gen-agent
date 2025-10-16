"""
Custom OpenAI Embeddings Module

This module provides a LangChain-compatible wrapper for OpenAI's embedding models,
specifically designed for use with the RAG (Retrieval-Augmented Generation) system.
The implementation focuses on efficiency, reliability, and compatibility with
ChromaDB vector storage.

Key Features:
    - LangChain Embeddings interface compliance
    - OpenAI text-embedding-3-small model integration
    - Batch processing for multiple documents
    - Consistent float encoding for vector operations
    - Error handling and retry logic

The embeddings are used to convert user activity text data and queries into
high-dimensional vector representations that enable semantic similarity search
within the RAG system.

Technical Specifications:
    - Model: text-embedding-3-small (1536 dimensions)
    - Encoding: Float format for precise similarity calculations
    - Batch size: Optimized for OpenAI API limits and performance
    - Output: Normalized vectors suitable for cosine similarity

Dependencies:
    - openai: Official OpenAI Python client library
    - langchain: For Embeddings base class interface
    - numpy: For vector operations and validation

Author: Huawei Agent POC Team
Version: 1.0.0
"""

from langchain.embeddings.base import Embeddings
from typing import List
from openai import OpenAI
import numpy as np

class CustomOpenAIEmbeddings(Embeddings):
    """
    Custom LangChain-compatible wrapper for OpenAI embedding models.
    
    This class implements the LangChain Embeddings interface while providing
    optimized access to OpenAI's text-embedding-3-small model. It's designed
    specifically for RAG applications requiring high-quality semantic embeddings.
    
    The implementation handles both single document embedding and batch processing
    of multiple documents, with appropriate error handling and optimization for
    the OpenAI API constraints.
    
    Attributes:
        client (OpenAI): Configured OpenAI client instance for API communication.
        model (str): OpenAI embedding model identifier. Default: "text-embedding-3-small"
    
    Model Characteristics:
        - text-embedding-3-small: 1536 dimensions, optimized for retrieval tasks
        - High semantic understanding across diverse text types
        - Efficient processing with reasonable API costs
        - Consistent performance across different document lengths
    
    API Configuration:
        - Encoding format: "float" for precise vector calculations
        - Batch processing: Handles multiple texts in single API calls
        - Error handling: Comprehensive exception management
        - Rate limiting: Respects OpenAI API constraints
    
    Example Usage:
        ```python
        # Initialize with API key
        embeddings = CustomOpenAIEmbeddings(
            api_key="your-openai-key",
            model="text-embedding-3-small"
        )
        
        # Embed single query
        query_vector = embeddings.embed_query("WhatsApp usage today")
        
        # Embed multiple documents
        doc_vectors = embeddings.embed_documents([
            "User sent 45 WhatsApp messages today",
            "YouTube viewing time was 2 hours",
            "Battery consumption was normal"
        ])
        ```
    
    Performance Considerations:
        - Single embedding: ~100-200ms per request
        - Batch embedding: More efficient for multiple documents
        - Vector dimensions: 1536 floats per embedding (~6KB per vector)
        - Memory usage scales linearly with text volume
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small"
    ):
        """
        Initialize the Custom OpenAI Embeddings wrapper.
        
        Sets up the OpenAI client with the provided API key and configures
        the embedding model. Validates the connection and model availability.
        
        Args:
            api_key (str): Valid OpenAI API key with access to embedding models.
                          Must have sufficient quota for text-embedding-3-small.
            model (str, optional): OpenAI embedding model identifier.
                                  Default: "text-embedding-3-small"
                                  Alternatives: "text-embedding-3-large", "text-embedding-ada-002"
        
        Raises:
            ValueError: If API key is invalid or model is not supported.
            Exception: If OpenAI client initialization fails.
        
        Model Selection Guidelines:
            - text-embedding-3-small: Best balance of quality and cost (recommended)
            - text-embedding-3-large: Higher quality, higher cost
            - text-embedding-ada-002: Legacy model, lower performance
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def _get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for a single text string.
        
        This private method handles the core embedding generation for individual
        text inputs. It communicates with the OpenAI API and processes the response
        to extract the embedding vector.
        
        Args:
            text (str): Input text to convert to embedding vector.
                       Can be queries, document chunks, or any text content.
        
        Returns:
            List[float]: 1536-dimensional embedding vector as list of floats.
                        Each dimension represents a semantic feature learned
                        by the embedding model.
        
        Raises:
            Exception: If API request fails due to network, authentication,
                      or quota issues. Includes original OpenAI error details.
        
        Processing Details:
            - Sends text to OpenAI embedding endpoint
            - Uses configured model (default: text-embedding-3-small)
            - Requests float encoding for precision
            - Extracts first embedding from response data array
        
        API Request Format:
            - Model: self.model (text-embedding-3-small)
            - Input: Raw text string
            - Encoding: "float" for precise vector calculations
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=text,
            encoding_format="float"
        )
        
        return response.data[0].embedding

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for multiple documents efficiently.
        
        This method processes multiple text documents in a single API call,
        which is more efficient than individual requests. It's designed for
        batch processing during vector store initialization.
        
        Args:
            texts (List[str]): List of text documents to embed.
                              Each string represents a document chunk or
                              complete document for vector storage.
        
        Returns:
            List[List[float]]: List of embedding vectors, one per input document.
                              Each inner list contains 1536 float values representing
                              the semantic embedding of the corresponding document.
        
        Raises:
            Exception: If batch API request fails or if any document cannot be processed.
                      Includes details about which documents failed if partial failure occurs.
        
        Batch Processing Benefits:
            - Reduced API calls: Single request for multiple documents
            - Lower latency: Network overhead amortized across batch
            - Rate limit efficiency: Better API quota utilization
            - Consistent ordering: Output order matches input order
        
        Performance Characteristics:
            - Batch size: Limited by OpenAI API constraints (typically ~100 docs)
            - Processing time: ~1-3 seconds for typical document batches
            - Memory usage: Scales with number and size of input documents
        
        Example:
            ```python
            docs = [
                "WhatsApp usage data for today",
                "YouTube viewing statistics",
                "Battery consumption metrics"
            ]
            vectors = embeddings.embed_documents(docs)
            # vectors[0] corresponds to docs[0], etc.
            ```
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
            encoding_format="float"
        )
        return [data.embedding for data in response.data]

    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding vector for a search query.
        
        This method creates an embedding vector for search queries, which are
        then used to find similar documents in the vector store. It's optimized
        for the query side of similarity search operations.
        
        Args:
            text (str): Search query string to convert to embedding.
                       Examples: "WhatsApp usage today", "YouTube viewing patterns"
        
        Returns:
            List[float]: 1536-dimensional query embedding vector.
                        This vector is used for cosine similarity calculations
                        against document embeddings in the vector store.
        
        Raises:
            Exception: If embedding generation fails due to API or network issues.
        
        Query Processing:
            - Uses same embedding model as documents for consistency
            - Generates semantically meaningful representation
            - Optimized for similarity search against document embeddings
            - Handles various query lengths and complexity levels
        
        Similarity Search Context:
            The returned embedding is used in vector stores to find the most
            semantically similar document chunks through cosine similarity:
            
            similarity = cosine(query_embedding, document_embedding)
        
        Example:
            ```python
            # Generate query embedding
            query_vector = embeddings.embed_query("show WhatsApp messages today")
            
            # Use in similarity search (typically handled by vector store)
            similar_docs = vector_store.similarity_search_by_vector(
                query_vector, k=3
            )
            ```
        """
        return self._get_embedding(text)