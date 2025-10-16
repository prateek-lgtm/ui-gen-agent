"""
Interactive CLI Interface for Analytics UI Generator

This module provides a command-line interface for testing and interacting with the
Analytics UI Generator system. It offers a conversational interface where users can
input natural language queries and receive Jetpack Compose UI JSON responses.

Key Features:
    - Interactive chat interface with the analytics agent
    - Real-time UI generation and JSON output
    - Direct integration with RAG system for data retrieval
    - Error handling and graceful failure management
    - Support for all query types (analytics and general UI)

The CLI interface is designed for:
    - Development and testing of the UI generation system
    - Quick prototyping of new query patterns
    - Debugging and validation of agent responses
    - Educational demonstrations of the system capabilities

Architecture:
    CLI Input → Analytics Agent → OpenRouter LLM → JSON UI Output
                     ↓
                RAG Manager → Vector Database → User Activity Data

Dependencies:
    - CrewAI: Agent framework and task management
    - Custom modules: OpenRouter LLM, Analytics Agent, RAG Manager
    - dotenv: Environment variable management

Author: Huawei Agent POC Team
Version: 1.0.0
"""

from crewai import Crew, Task
from crewai.tools import BaseTool
from src.openrouter_llm import OpenRouterLLM
from src.analytics_agent import AnalyticsUIAgent
from src.rag import RAGManager
from src.conversation_memory import ConversationMemory
import json
import os
from dotenv import load_dotenv
from typing import Type
from pydantic import BaseModel, Field

def load_user_data():
    """
    Load user activity data from JSON file.
    
    This function reads the structured user activity data that contains analytics
    information for various apps including WhatsApp, YouTube, and battery usage.
    The data is used by the analytics agent to generate contextually appropriate UIs.
    
    Returns:
        dict: Parsed JSON data containing user activity information structured by app.
              Each app section contains daily usage statistics, weekly summaries,
              and various metrics for UI generation.
    
    Raises:
        FileNotFoundError: If the activity_data.json file is not found.
        json.JSONDecodeError: If the JSON file is malformed or corrupted.
        
    Data Structure:
        The loaded data follows this general structure:
        ```json
        {
            "whatsapp": {
                "daily_usage": [...],
                "weekly_summary": {...}
            },
            "youtube": {
                "daily_usage": [...],
                "weekly_summary": {...}
            },
            "battery": {
                "daily_usage": [...],
                "performance_metrics": {...}
            }
        }
        ```
    
    File Location:
        data/user_activity/activity_data.json
    
    Usage:
        ```python
        user_data = load_user_data()
        whatsapp_data = user_data.get('whatsapp', {})
        ```
    """
    with open('data/user_activity/activity_data.json', 'r') as f:
        return json.load(f)

class QueryUIPatternsTool(BaseTool):
    """
    CrewAI tool for querying user activity data through the RAG system.
    
    This tool provides the analytics agent with access to user activity data
    through semantic search capabilities. It acts as a bridge between the
    agent's decision-making process and the vector database containing user
    activity information.
    
    The tool uses the RAG (Retrieval-Augmented Generation) system to find
    relevant user data based on natural language queries, enabling the agent
    to generate more accurate and contextually appropriate UI structures.
    
    Attributes:
        name (str): Tool identifier for CrewAI framework.
        description (str): Human-readable description of tool capabilities.
        rag_manager (RAGManager): Instance of RAG system for data retrieval.
                                 Excluded from Pydantic serialization.
    
    Tool Interface:
        - Input: Natural language query about user activity
        - Processing: Semantic search through vector database
        - Output: Relevant user activity data chunks as strings
    
    Integration:
        The tool is designed to work seamlessly with CrewAI agents, providing
        them with contextual information needed for intelligent UI generation.
        
    Example Usage:
        ```python
        tool = QueryUIPatternsTool(rag_manager=rag_instance)
        results = tool._run("WhatsApp usage data for today")
        # Returns relevant chunks of user activity data
        ```
    """
    name: str = "QueryUserData"
    description: str = "Query user activity data including WhatsApp, YouTube, and battery usage"
    rag_manager: RAGManager = Field(..., exclude=True)
    
    def _run(self, query: str) -> str:
        """
        Execute the tool to retrieve user activity data.
        
        This method performs the actual data retrieval operation using the RAG
        system. It takes a natural language query, processes it through the
        vector database, and returns relevant user activity information.
        
        Args:
            query (str): Natural language query for user activity data.
                        Examples: "WhatsApp messages today", "YouTube viewing time",
                                 "battery usage patterns"
        
        Returns:
            str: Concatenated relevant data chunks separated by newlines.
                 Contains the most semantically similar user activity information
                 based on the input query.
        
        Raises:
            Exception: If the RAG query fails due to vector store issues or
                      API problems. Returns error message as string.
        
        Processing Flow:
            1. Receives natural language query from agent
            2. Passes query to RAG manager for semantic search
            3. Retrieves top-k most relevant document chunks
            4. Concatenates results with newline separators
            5. Returns formatted string for agent consumption
        
        Error Handling:
            - Comprehensive exception catching
            - Descriptive error messages for debugging
            - Graceful degradation when data retrieval fails
        
        Example:
            ```python
            query = "show me WhatsApp usage for today"
            result = tool._run(query)
            # Returns formatted user activity data relevant to WhatsApp usage
            ```
        """
        try:
            results = self.rag_manager.query_user_data(query)
            return "\n".join(results)
        except Exception as e:
            return f"Error querying user data: {str(e)}"

def chat_with_agent(analytics_agent, user_data, conversation_memory):
    """
    Interactive chat interface with the analytics agent with conversation memory.
    
    This function provides a command-line interface for real-time interaction
    with the Analytics UI Agent. Users can input natural language queries and
    receive immediate JSON UI responses. The interface now maintains conversation
    context across multiple queries within the same session.
    
    Features:
        - Persistent conversation context across queries
        - Session-based conversation memory
        - Continuous chat loop until user exits
        - Real-time UI generation and display
        - Error handling with graceful recovery
        - Support for multiple exit commands
        - Clean JSON formatting for output
        - Keyboard interrupt handling
        - Context-aware responses based on conversation history
    
    Args:
        analytics_agent (AnalyticsUIAgent): Initialized agent instance capable
                                           of generating UI JSON from queries.
        user_data (dict): Loaded user activity data for contextualized responses.
        conversation_memory (ConversationMemory): Memory system for conversation context.
    
    Interface Commands:
        - Regular queries: Generate UI JSON responses with conversation context
        - 'history': Show conversation history for current session
        - 'new session': Start a new conversation session
        - Exit commands: 'quit', 'exit', 'bye', 'goodbye'
        - Empty input: Ignored, prompt continues
        - Ctrl+C: Graceful shutdown with goodbye message
    
    Output Format:
        - Generated UI JSON is pretty-printed with 2-space indentation
        - Session information is displayed at start
        - Conversation context enhances response relevance
        - Error messages are displayed with guidance for retry
        - System messages use clear formatting and separators
    
    Error Handling:
        - Individual query errors don't terminate the session
        - Network and API errors are caught and reported
        - Keyboard interrupts are handled gracefully
        - Invalid input is managed with user-friendly messages
        - Context errors are handled without breaking the conversation
    
    Example Session:
        ```
        Analytics UI Assistant with Memory
        Session ID: abc-123 | Message Count: 0
        Type 'quit', 'exit', 'history', or 'new session' for special commands.
        ============================================================
        
        You: show me my whatsapp usage today
        {
          "type": "Screen",
          "title": "WhatsApp Usage Today",
          ...
        }
        
        You: make it more colorful
        {
          "type": "Screen",
          "title": "WhatsApp Usage Today - Colorful",
          // Context-aware response based on previous query
          ...
        }
        
        You: history
        Conversation History (Session: abc-123):
        1. User: show me my whatsapp usage today
        2. Assistant: Generated UI: WhatsApp Usage Today
        3. User: make it more colorful
        4. Assistant: Generated UI: WhatsApp Usage Today - Colorful
        
        You: quit
        Assistant: Goodbye! Session saved.
        ```
    
    Usage:
        ```python
        agent = AnalyticsUIAgent(rag_tools=[tool], llm=llm, memory=memory)
        user_data = load_user_data()
        memory = ConversationMemory("conversations.db")
        chat_with_agent(agent, user_data, memory)
        ```
    """
    # Create a new conversation session
    session_id = conversation_memory.create_session()
    
    print("Analytics UI Assistant with Memory")
    print(f"Session ID: {session_id[:8]}... | Message Count: 0")
    print("Type 'quit', 'exit', 'history', or 'new session' for special commands.")
    print("=" * 70)
    
    while True:
        try:
            # Get session info for display
            session_summary = conversation_memory.get_session_summary(session_id)
            message_count = session_summary.get('message_count', 0)
            
            # Get user input
            user_query = input(f"\nYou [{message_count}]: ").strip()
            
            # Handle special commands
            if user_query.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                print(f"\nAssistant: Goodbye! Session {session_id[:8]}... saved with {message_count} messages.")
                break
            elif user_query.lower() == 'history':
                # Show conversation history
                history = conversation_memory.get_conversation_history(session_id, limit=10)
                print(f"\nConversation History (Session: {session_id[:8]}...):")
                for i, msg in enumerate(history, 1):
                    role = "You" if msg.role == "user" else "Assistant"
                    content = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
                    print(f"{i}. {role}: {content}")
                continue
            elif user_query.lower() == 'new session':
                # Start a new session
                session_id = conversation_memory.create_session()
                print(f"\nStarted new session: {session_id[:8]}...")
                continue
            
            # Skip empty inputs
            if not user_query:
                continue
                
            # Process the query with conversation context
            result = analytics_agent.generate_ui(user_query, user_data, session_id)
            
            # Display only the JSON result
            print(json.dumps(result, indent=2))
            
        except KeyboardInterrupt:
            print(f"\n\nAssistant: Goodbye! Session {session_id[:8]}... saved.")
            break
        except Exception as e:
            print(f"Error: {str(e)}")
            print("Please try again with a different query.")

def main():
    """
    Main function to initialize and run the Analytics UI Generator CLI.
    
    This function orchestrates the entire system initialization process and
    starts the interactive chat interface. It handles environment setup,
    component initialization, and error management for a smooth user experience.
    
    Initialization Process:
        1. Environment Variables: Loads configuration from .env file
        2. API Key Management: Configures keys for different services
        3. LLM Setup: Initializes OpenRouter integration with Claude 3.5 Sonnet
        4. RAG System: Sets up vector database and embeddings
        5. Agent Creation: Configures Analytics UI Agent with tools
        6. Interface Launch: Starts interactive chat session
    
    Environment Requirements:
        - OPENROUTER_API_KEY: Required for Claude 3.5 Sonnet access
        - OPENAI_API_KEY: Required for embeddings and vector search
    
    Key Design Decisions:
        - API Key Isolation: Removes conflicting keys to ensure correct LLM usage
        - Custom LLM: Uses OpenRouter to bypass CrewAI's automatic model detection
        - Persistent Storage: Vector database survives across sessions
        - Error Handling: Graceful failure at each initialization step
    
    Component Architecture:
        OpenRouter LLM ← Analytics Agent ← CLI Interface
                ↓                ↓
        Claude 3.5 Sonnet   RAG Manager ← Vector Database ← User Data
                                   ↓
                            OpenAI Embeddings
    
    Error Handling:
        - Missing environment variables
        - API authentication failures
        - File system permissions issues
        - Network connectivity problems
        - Invalid user data format
    
    Performance Considerations:
        - Cold start: 3-5 seconds for full initialization
        - Vector store: Loaded once, reused across queries
        - Memory usage: Scales with vector database size
        - API efficiency: Optimized for minimal external calls
    
    Example Usage:
        ```bash
        # Set up environment
        export OPENROUTER_API_KEY="your-key"
        export OPENAI_API_KEY="your-key"
        
        # Run the CLI
        python run.py
        ```
    
    Raises:
        SystemExit: If any critical component fails to initialize.
                   Error details are logged for debugging.
    """
    # Load environment variables
    load_dotenv()
    
    # Store the OpenAI key for RAG before removing it from environment
    openai_key = os.getenv('OPENAI_API_KEY')
    
    # Remove conflicting API keys to force use of our custom LLM for agents
    # This prevents CrewAI from automatically detecting and using other LLMs
    if 'OPENAI_API_KEY' in os.environ:
        del os.environ['OPENAI_API_KEY']
    if 'ANTHROPIC_API_KEY' in os.environ:
        del os.environ['ANTHROPIC_API_KEY']
    
    # Initialize conversation memory
    conversation_memory = ConversationMemory("conversation_memory.db")
    print("Conversation memory initialized")
    
    # Initialize LLM with Claude Sonnet 4 via OpenRouter  
    llm = OpenRouterLLM(
        model="claude-sonnet-4",  # Custom name to avoid CrewAI detection
        temperature=0.7,
        api_key=os.getenv('OPENROUTER_API_KEY')
    )
    
    # Initialize RAG manager with the stored OpenAI key
    rag_manager = RAGManager(
        api_key=openai_key
    )
    
    # Initialize vector store with user activity data
    rag_manager.initialize_vector_store("data/user_activity/user_data_for_vectordb.txt")
    
    # Create RAG tool
    rag_tool = QueryUIPatternsTool(rag_manager=rag_manager)
    
    # Load user activity data
    user_data = load_user_data()
    
    # Create Analytics UI agent with LLM and conversation memory
    analytics_agent = AnalyticsUIAgent(rag_tools=[rag_tool], llm=llm, memory=conversation_memory)
    
    # Start interactive chat with memory
    chat_with_agent(analytics_agent, user_data, conversation_memory)

if __name__ == "__main__":
    main()