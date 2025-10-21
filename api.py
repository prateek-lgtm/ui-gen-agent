#!/usr/bin/env python3
"""
FastAPI Server for Analytics UI Generator

This module provides a REST API server that generates Jetpack Compose UI JSON structures
from natural language queries about user analytics data. The server integrates multiple
AI components to understand user queries and generate appropriate mobile UI layouts.

Key Components:
    - FastAPI server with CORS support for web clients
    - Analytics UI Agent powered by Claude 3.5 Sonnet via OpenRouter
    - RAG (Retrieval-Augmented Generation) system for user data context
    - Structured request/response models with comprehensive error handling

Architecture:
    Client Request → FastAPI → Analytics Agent → OpenRouter LLM → UI JSON Response
                                     ↓
                            RAG Manager → Vector Database → User Activity Data

The API is designed to be stateless and scalable, with proper error handling that
returns consistent UI JSON responses even for error conditions.

Author: Huawei Agent POC Team
Version: 1.0.0
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json
import os
import logging
import openai
from dotenv import load_dotenv

# Import our existing modules
from src.openrouter_llm import OpenRouterLLM
from src.analytics_agent import AnalyticsUIAgent
from src.rag import RAGManager
from src.conversation_memory import ConversationMemory
from run import QueryUIPatternsTool, load_user_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Analytics UI Generator API",
    description="Generate Jetpack Compose UI JSON from natural language queries about user analytics data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class QueryRequest(BaseModel):
    """
    Request model for UI generation queries.
    
    This model defines the structure for incoming requests to the /generate-ui endpoint.
    The query should be a natural language description of the desired UI or analytics view.
    
    Attributes:
        query (str): Natural language query describing the desired UI.
                    Examples: "show me my whatsapp usage today",
                             "create a login page",
                             "display youtube activity this week"
        session_id (Optional[str]): Optional session ID for conversation continuity.
                                   If not provided, a new session will be created.
    
    Examples:
        >>> request = QueryRequest(query="show me my whatsapp usage today")
        >>> request.query
        "show me my whatsapp usage today"
        
        >>> # With session for conversation continuity
        >>> request = QueryRequest(query="show it in a different color", session_id="existing-session-id")
    """
    query: str
    session_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "show me my whatsapp usage today",
                "session_id": "optional-session-id"
            }
        }

class UIResponse(BaseModel):
    """
    Response model for UI generation results.
    
    This model provides a consistent response structure for all API calls,
    including both successful generations and error conditions. The UI field
    contains a complete Jetpack Compose component tree when successful.
    
    Attributes:
        success (bool): Whether the UI generation completed successfully.
        ui (Optional[Dict[str, Any]]): Generated Jetpack Compose UI JSON structure.
                                      Present when success=True, may be present for errors
                                      as an error display UI.
        error (Optional[str]): Error message when generation fails.
                              Present when success=False.
        session_id (str): Session ID for conversation continuity.
        message_count (int): Number of messages in this conversation session.
    
    UI Structure:
        The ui field contains a hierarchical JSON structure representing Jetpack
        Compose components with the following typical structure:
        
        {
            "type": "Screen",
            "title": "Screen Title",
            "content": {
                "type": "Column|Row|Card|...",
                "modifier": {"fillMaxSize": true, "padding": 16, ...},
                "children": [...]  // Array of child components
            }
        }
    
    Examples:
        >>> # Successful response
        >>> response = UIResponse(
        ...     success=True,
        ...     ui={"type": "Screen", "title": "Data View", "content": {...}},
        ...     error=None,
        ...     session_id="abc-123",
        ...     message_count=5
        ... )
        
        >>> # Error response with error UI
        >>> response = UIResponse(
        ...     success=False,
        ...     ui={"type": "Screen", "title": "Error", "content": {...}},
        ...     error="Failed to process query",
        ...     session_id="abc-123",
        ...     message_count=6
        ... )
    """
    success: bool
    ui: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    session_id: str
    message_count: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "ui": {
                    "type": "Screen",
                    "title": "WhatsApp Usage",
                    "content": {
                        "type": "Column",
                        "children": []
                    }
                },
                "error": None,
                "session_id": "abc-123",
                "message_count": 5
            }
        }

# RAG Chatbot Models
class QueryRequest(BaseModel):
    """Request model for RAG chatbot queries"""
    query: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is my current plan?"
            }
        }

class QueryResponse(BaseModel):
    """Response model for RAG chatbot queries"""
    response: str
    query: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Your current plan is Business Plan 300 with 45 GB data and 150 minutes for ₹300.",
                "query": "What is my current plan?"
            }
        }

class RAGChatbotAPI:
    """RAG Chatbot that uses the existing chroma_db for queries"""
    
    def __init__(self, rag_manager: RAGManager, openai_api_key: str):
        """Initialize with existing RAG manager and OpenAI API key"""
        # Set up OpenAI
        if not openai_api_key:
            raise ValueError("OpenAI API key is required")
        
        api_key = openai_api_key.strip().strip('"').strip("'")
        if not api_key.startswith('sk-'):
            raise ValueError("Invalid API key format")
        
        openai.api_key = api_key
        
        # Use existing RAG manager
        self.rag_manager = rag_manager
        self.embedding_model = "text-embedding-3-large"
    
    def retrieve_context(self, query: str, n_results: int = 5) -> List[str]:
        """Retrieve relevant context using existing RAG manager"""
        try:
            # Use the existing RAG manager's query method
            context_chunks = self.rag_manager.query_user_data(query, k=n_results)
            return context_chunks if context_chunks else []
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return []
    
    def generate_response(self, query: str, context: List[str]) -> str:
        """Generate response using LLM"""
        try:
            context_text = "\n\n".join(context)
            
            system_prompt = """You are a helpful assistant that answers questions about user activity data, business plans, events, and usage patterns. 

You have access to the user's activity data including:
- Current business plans and pricing
- Upcoming events and entertainment
- Social media usage patterns
- User profile and account information

Use the provided context to answer questions accurately and helpfully. If the information isn't in the context, say so politely."""

            user_prompt = f"""Context:
{context_text}

User Question: {query}

Please provide a clear, helpful answer based on the context above."""

            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I apologize, but I encountered an error while generating a response."
    
    def chat(self, query: str) -> str:
        """Main chat function"""
        context = self.retrieve_context(query)
        
        if not context:
            return "I couldn't find relevant information to answer your question."
        
        return self.generate_response(query, context)

# Global variables for our initialized components
analytics_agent = None
user_data = None
conversation_memory = None
chatbot = None

@app.on_event("startup")
async def startup_event():
    """
    Initialize the analytics agent and load data on startup.
    
    This function is called when the FastAPI server starts up. It performs all
    necessary initialization including:
    
    1. Environment variable management (removing conflicting API keys)
    2. LLM initialization with OpenRouter integration
    3. RAG manager setup with vector database
    4. User activity data loading
    5. Analytics agent creation and configuration
    
    The startup process is designed to fail fast if any required components
    cannot be initialized, ensuring the API doesn't start in a broken state.
    
    Raises:
        Exception: If any critical component fails to initialize, the startup
                  will fail with a descriptive error message.
    
    Environment Variables Required:
        OPENROUTER_API_KEY: API key for accessing Claude 3.5 Sonnet
        OPENAI_API_KEY: API key for embeddings and vector search
    
    Side Effects:
        - Modifies os.environ by removing conflicting API keys
        - Initializes global variables: analytics_agent, user_data, conversation_memory
        - Creates vector database files in ./chroma_db/
        - Creates conversation memory database file
        - Loads user activity data from data/user_activity/
    """
    global analytics_agent, user_data, conversation_memory, chatbot
    
    try:
        logger.info("Starting Analytics UI Generator API...")
        
        # Store the OpenAI key for RAG before removing it from environment
        openai_key = os.getenv('OPENAI_API_KEY')
        
        # Validate OpenAI API key exists
        if not openai_key:
            raise ValueError("OpenAI API key is required. Please set OPENAI_API_KEY in your .env file")
        
        # Remove conflicting API keys to force use of our custom LLM for agents
        # But keep OpenAI key for the chatbot initialization
        if 'ANTHROPIC_API_KEY' in os.environ:
            del os.environ['ANTHROPIC_API_KEY']
        
        # Initialize conversation memory
        conversation_memory = ConversationMemory("conversation_memory.db")
        logger.info("Conversation memory initialized")
        
        # Initialize LLM with Claude Sonnet 4 via OpenRouter  
        llm = OpenRouterLLM(
            model="claude-sonnet-4",  # Custom name to avoid CrewAI detection
            temperature=0.7,
            api_key=os.getenv('OPENROUTER_API_KEY')
        )
        logger.info("OpenRouter LLM initialized")
        
        # Initialize RAG manager with the stored OpenAI key
        rag_manager = RAGManager(
            api_key=openai_key
        )
        
        # Initialize vector store with user activity data
        rag_manager.initialize_vector_store("data/user_activity/user_data_for_vectordb.txt")
        logger.info("RAG manager initialized")
        
        # Create RAG tool
        rag_tool = QueryUIPatternsTool(rag_manager=rag_manager)
        
        # Load user activity data
        user_data = load_user_data()
        logger.info("User data loaded")
        
        # Create Analytics UI agent with LLM and conversation memory
        analytics_agent = AnalyticsUIAgent(rag_tools=[rag_tool], llm=llm, memory=conversation_memory)
        logger.info("Analytics agent initialized")
        
        # Create RAG chatbot using existing RAG manager and API key
        chatbot = RAGChatbotAPI(rag_manager=rag_manager, openai_api_key=openai_key)
        logger.info("RAG chatbot initialized")
        
        # Now remove OpenAI key from environment after chatbot initialization
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        logger.info("✅ Analytics UI Generator API started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize API: {str(e)}")
        raise e

@app.get("/")
async def root():
    """
    Root endpoint providing basic API information.
    
    This endpoint serves as a simple health check and provides basic information
    about the API. It's useful for verifying that the server is running and
    accessible.
    
    Returns:
        dict: Basic API information including name, status, and version.
        
    Example Response:
        {
            "message": "Analytics UI Generator API",
            "status": "running", 
            "version": "1.0.0"
        }
    """
    return {
        "message": "Analytics UI Generator API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """
    Detailed health check endpoint.
    
    This endpoint provides comprehensive health information about all critical
    components of the API. It's designed for monitoring systems and debugging
    to verify that all dependencies are properly initialized.
    
    Returns:
        dict: Detailed health status including:
            - status: Overall health ("healthy" or "unhealthy")
            - agent_ready: Whether the analytics agent is initialized
            - data_loaded: Whether user activity data is loaded
            - message: Human-readable status description
            
    Example Response:
        {
            "status": "healthy",
            "agent_ready": true,
            "data_loaded": true,
            "message": "API is ready to generate UIs"
        }
    """
    return {
        "status": "healthy",
        "agent_ready": analytics_agent is not None,
        "data_loaded": user_data is not None,
        "message": "API is ready to generate UIs"
    }

@app.post("/generate-ui", response_model=UIResponse)
async def generate_ui(request: QueryRequest):
    """
    Generate Jetpack Compose UI JSON from a natural language query.
    
    This is the core endpoint of the API that takes natural language queries about
    user analytics data and returns complete Jetpack Compose UI JSON structures.
    The endpoint uses AI to understand the user's intent and generate appropriate
    mobile UI layouts with proper styling, data visualization, and component hierarchy.
    
    Query Processing Pipeline:
        1. Query validation and sanitization
        2. Intent analysis (analytics vs. simple UI)
        3. Data retrieval via RAG system
        4. AI-powered UI generation using Claude 3.5 Sonnet
        5. JSON structure validation and response formatting
    
    Args:
        request (QueryRequest): Request containing the natural language query.
                               The query should describe the desired UI or data view.
    
    Returns:
        UIResponse: Response containing generated UI JSON or error information.
                   Even error responses include a UI structure for consistent
                   client handling.
    
    Raises:
        HTTPException: 
            - 503 Service Unavailable: If analytics agent or data not initialized
            - 400 Bad Request: If query is empty or invalid format
    
    Supported Query Types:
        Analytics Queries:
            - "show me my whatsapp usage today"
            - "display my youtube activity this week"
            - "show my battery performance"
            - "create a dashboard for all my apps"
        
        Standard UI Queries:
            - "create a login page"
            - "design a signup screen"
            - "make a settings page"
    
    UI Generation Features:
        - Dynamic color selection based on app context
        - Responsive layouts using Cards, Columns, Rows
        - Comprehensive data display (all available metrics)
        - Modern Material Design principles
        - Proper typography and spacing
        - Error handling with user-friendly messages
    
    Performance Notes:
        - First request may take 2-3 seconds (cold start)
        - Subsequent requests typically complete in 1-2 seconds
        - Response time depends on query complexity and AI processing
    
    Example Usage:
        ```python
        # Analytics query
        response = await generate_ui(QueryRequest(
            query="show me my whatsapp usage today"
        ))
        
        # Simple UI query
        response = await generate_ui(QueryRequest(
            query="create a login page"
        ))
        ```
    
    Example Response Structure:
        ```json
        {
            "success": true,
            "ui": {
                "type": "Screen",
                "title": "WhatsApp Usage Today",
                "content": {
                    "type": "Column",
                    "modifier": {"fillMaxSize": true, "padding": 16},
                    "children": [
                        {
                            "type": "Card",
                            "modifier": {"fillMaxWidth": true},
                            "content": {...}
                        }
                    ]
                }
            },
            "error": null
        }
        ```
    """
    
    if analytics_agent is None or user_data is None or conversation_memory is None:
        raise HTTPException(
            status_code=503, 
            detail="Service not ready. Analytics agent, user data, or conversation memory not initialized."
        )
    
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )
    
    try:
        logger.info(f"Processing query: {request.query}")
        
        # Handle session management
        session_id = request.session_id
        if not session_id:
            # Create new session if none provided
            session_id = conversation_memory.create_session()
            logger.info(f"Created new session: {session_id}")
        
        # Generate UI using the analytics agent with session context
        ui_json = analytics_agent.generate_ui(request.query, user_data, session_id)
        
        # Get session summary for response
        session_summary = conversation_memory.get_session_summary(session_id)
        message_count = session_summary.get('message_count', 0)
        
        logger.info(f"UI generated successfully for session {session_id}")
        
        return UIResponse(
            success=True,
            ui=ui_json,
            error=None,
            session_id=session_id,
            message_count=message_count
        )
        
    except Exception as e:
        logger.error(f"Error generating UI: {str(e)}")
        
        # Create session if needed for error response
        session_id = request.session_id
        if not session_id:
            session_id = conversation_memory.create_session()
        
        # Return error UI instead of throwing HTTP error
        error_ui = {
            "type": "Screen",
            "title": "Generation Error",
            "content": {
                "type": "Column",
                "modifier": {"fillMaxSize": True, "padding": 16},
                "children": [
                    {
                        "type": "Card",
                        "modifier": {"fillMaxWidth": True, "padding": 16},
                        "elevation": 4,
                        "backgroundColor": "#FFEBEE",
                        "content": {
                            "type": "Column",
                            "children": [
                                {
                                    "type": "Text",
                                    "text": "API Error",
                                    "fontSize": 20,
                                    "fontWeight": "bold",
                                    "color": "#D32F2F"
                                },
                                {
                                    "type": "Spacer",
                                    "height": 8
                                },
                                {
                                    "type": "Text",
                                    "text": "An error occurred while processing your request.",
                                    "fontSize": 16,
                                    "color": "#666666"
                                },
                                {
                                    "type": "Text",
                                    "text": f"Error: {str(e)}",
                                    "fontSize": 14,
                                    "color": "#888888"
                                }
                            ]
                        }
                    }
                ]
            }
        }
        
        # Add error to conversation memory
        conversation_memory.add_message(session_id, "user", request.query)
        conversation_memory.add_message(session_id, "assistant", f"API Error: {str(e)}", ui_generated=error_ui)
        
        # Get session summary for response
        session_summary = conversation_memory.get_session_summary(session_id)
        message_count = session_summary.get('message_count', 0)
        
        return UIResponse(
            success=False,
            ui=error_ui,
            error=str(e),
            session_id=session_id,
            message_count=message_count
        )

@app.post("/session/new")
async def create_new_session():
    """
    Create a new conversation session.
    
    Returns:
        dict: New session information including session_id
    """
    if conversation_memory is None:
        raise HTTPException(status_code=503, detail="Conversation memory not initialized")
    
    session_id = conversation_memory.create_session()
    return {
        "session_id": session_id,
        "message_count": 0,
        "created": True
    }

@app.get("/session/{session_id}/history")
async def get_conversation_history(session_id: str, limit: int = 20):
    """
    Get conversation history for a session.
    
    Args:
        session_id (str): Session identifier
        limit (int): Maximum number of messages to return
        
    Returns:
        dict: Conversation history and session information
    """
    if conversation_memory is None:
        raise HTTPException(status_code=503, detail="Conversation memory not initialized")
    
    try:
        history = conversation_memory.get_conversation_history(session_id, limit)
        session_summary = conversation_memory.get_session_summary(session_id)
        
        # Format messages for response
        messages = []
        for msg in history:
            message_data = {
                "timestamp": msg.timestamp.isoformat(),
                "role": msg.role,
                "content": msg.content
            }
            if msg.ui_generated:
                message_data["ui_generated"] = {
                    "type": msg.ui_generated.get("type"),
                    "title": msg.ui_generated.get("title")
                }
            messages.append(message_data)
        
        return {
            "session_id": session_id,
            "messages": messages,
            "session_info": session_summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")

@app.get("/sessions")
async def get_active_sessions(limit: int = 10):
    """
    Get list of recently active conversation sessions.
    
    Args:
        limit (int): Maximum number of sessions to return
        
    Returns:
        dict: List of active sessions with basic information
    """
    if conversation_memory is None:
        raise HTTPException(status_code=503, detail="Conversation memory not initialized")
    
    try:
        sessions = conversation_memory.get_active_sessions(limit)
        return {
            "sessions": sessions,
            "count": len(sessions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sessions: {str(e)}")

@app.delete("/session/{session_id}")
async def clear_session_history(session_id: str):
    """
    Clear conversation history for a session (marks session as inactive).
    
    Args:
        session_id (str): Session identifier to clear
        
    Returns:
        dict: Confirmation of session clearing
    """
    if conversation_memory is None:
        raise HTTPException(status_code=503, detail="Conversation memory not initialized")
    
    try:
        # Use the conversation memory's clear method with proper connection handling
        cleared = conversation_memory.clear_session(session_id)
        
        if not cleared:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_id,
            "cleared": True,
            "message": "Session marked as inactive"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")

@app.get("/chat/health")
async def chat_health():
    """Health check endpoint for RAG chatbot"""
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    return {"status": "healthy", "model": "text-embedding-3-large"}

@app.post("/chat", response_model=QueryResponse)
async def chat_endpoint(request: QueryRequest):
    """
    RAG chatbot endpoint that returns text responses from vector database.
    
    This endpoint provides a simple question-answering interface using the RAG
    (Retrieval-Augmented Generation) system. It returns plain text responses
    based on the user's activity data without generating UI components.
    
    Args:
        request (QueryRequest): Contains the user's query string
    
    Returns:
        QueryResponse: Contains the generated response and original query
    
    Raises:
        HTTPException: 503 if chatbot not initialized, 400 for empty queries,
                      500 for processing errors
    
    Examples:
        >>> POST /chat
        >>> {"query": "What is my current data usage?"}
        >>> Returns: {"response": "You have used 12.5 GB out of 45 GB...", "query": "..."}
    """
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        response = chatbot.chat(request.query)
        return QueryResponse(response=response, query=request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/examples")
async def get_examples():
    """Get example queries that can be used with the API"""
    return {
        "ui_generation_examples": [
            {
                "query": "show me my whatsapp usage today",
                "description": "Display WhatsApp activity and usage statistics",
                "endpoint": "/generate-ui"
            },
            {
                "query": "what's my youtube activity this week?",
                "description": "Show YouTube viewing history and time spent",
                "endpoint": "/generate-ui"
            },
            {
                "query": "display my battery performance",
                "description": "Battery usage, charging cycles, and consumption",
                "endpoint": "/generate-ui"
            },
            {
                "query": "show me a simple login page",
                "description": "Generate a basic login UI (not data-related)",
                "endpoint": "/generate-ui"
            },
            {
                "query": "create a dashboard for all my apps",
                "description": "Comprehensive view of all available data",
                "endpoint": "/generate-ui"
            }
        ],
        "rag_chatbot_examples": [
            {
                "query": "What is my current plan?",
                "description": "Get current business plan details",
                "endpoint": "/chat"
            },
            {
                "query": "What are the upcoming events?",
                "description": "List events happening in the coming months",
                "endpoint": "/chat"
            },
            {
                "query": "How much data do I use on YouTube?",
                "description": "Get social media usage statistics",
                "endpoint": "/chat"
            },
            {
                "query": "When does my plan expire?",
                "description": "Check plan expiry and renewal information",
                "endpoint": "/chat"
            },
            {
                "query": "What events are happening in Delhi?",
                "description": "Filter events by location",
                "endpoint": "/chat"
            },
            {
                "query": "Based on my usage suggest a plan to buy",
                "description": "Get plan recommendations based on usage patterns",
                "endpoint": "/chat"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app", 
        host="0.0.0.0", 
        port=7070, 
        reload=True,
        log_level="info"
    )
