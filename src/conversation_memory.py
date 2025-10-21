"""
Conversation Memory Management Module

This module implements persistent conversation memory for the Analytics UI Agent,
enabling context-aware interactions across multiple queries within a session.
The system maintains conversation history, session management, and context
retrieval for enhanced user experience.

Key Components:
    - ConversationMemory: Main class for managing conversation history
    - Session management with unique session IDs
    - SQLite-based persistent storage for conversation data
    - Context summarization for efficient memory usage
    - Query context integration for better AI responses

Features:
    - Persistent conversation storage across sessions
    - Automatic context summarization to prevent token overflow
    - Session-based isolation for multiple users
    - Efficient retrieval of relevant conversation context
    - Memory cleanup and optimization

Database Schema:
    - conversations: Main conversation history table
    - sessions: Session metadata and configuration
    - context_summaries: Compressed conversation summaries

Author: Huawei Agent POC Team
Version: 1.0.0
"""

import sqlite3
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConversationMessage:
    """
    Represents a single message in a conversation.
    
    Attributes:
        session_id (str): Unique identifier for the conversation session
        timestamp (datetime): When the message was created
        role (str): 'user' or 'assistant' to identify the speaker
        content (str): The actual message content
        ui_generated (Optional[Dict]): UI JSON if this was a UI generation response
        metadata (Optional[Dict]): Additional metadata about the message
    """
    session_id: str
    timestamp: datetime
    role: str  # 'user' or 'assistant'
    content: str
    ui_generated: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class ConversationMemory:
    """
    Manages conversation history and context for the Analytics UI Agent.
    
    This class provides persistent storage and retrieval of conversation history,
    enabling context-aware interactions. It handles session management, memory
    optimization, and context summarization to maintain efficient performance
    while preserving important conversation context.
    
    Key Features:
        - Session-based conversation isolation
        - Persistent SQLite storage for conversation history
        - Automatic context summarization for long conversations
        - Efficient context retrieval for AI query enhancement
        - Memory cleanup and session management
    
    Database Structure:
        - conversations: Individual messages with metadata
        - sessions: Session information and settings
        - context_summaries: Compressed conversation history
    
    Usage:
        ```python
        memory = ConversationMemory("conversations.db")
        session_id = memory.create_session()
        
        # Add user message
        memory.add_message(session_id, "user", "Show me WhatsApp usage")
        
        # Add assistant response with UI
        memory.add_message(session_id, "assistant", "Here's your WhatsApp usage", 
                          ui_generated=ui_json)
        
        # Get conversation context for next query
        context = memory.get_conversation_context(session_id)
        ```
    """
    
    def __init__(self, db_path: str = "conversation_memory.db"):
        """
        Initialize the conversation memory system.
        
        Args:
            db_path (str): Path to the SQLite database file for storing conversations.
                          Will be created if it doesn't exist.
        """
        self.db_path = db_path
        self.max_retries = 3
        self.retry_delay = 0.1  # 100ms
        self._init_database()
    
    @contextmanager
    def _get_db_connection(self):
        """
        Context manager for database connections with proper error handling and timeouts.
        
        Yields:
            tuple: (connection, cursor) ready for database operations
        """
        conn = None
        retries = 0
        
        while retries < self.max_retries:
            try:
                # Configure SQLite connection with timeout and optimizations
                conn = sqlite3.connect(
                    self.db_path, 
                    timeout=30.0,  # 30 second timeout
                    check_same_thread=False
                )
                
                # Configure SQLite for better concurrency
                conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
                conn.execute("PRAGMA synchronous=NORMAL")  # Balance safety and performance
                conn.execute("PRAGMA cache_size=10000")  # Increase cache
                conn.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp storage
                conn.execute("PRAGMA busy_timeout=30000")  # 30 second busy timeout
                
                cursor = conn.cursor()
                yield conn, cursor
                break
                
            except sqlite3.OperationalError as e:
                retries += 1
                if "database is locked" in str(e).lower() and retries < self.max_retries:
                    logger.warning(f"Database locked, retrying ({retries}/{self.max_retries}) after {self.retry_delay}s")
                    time.sleep(self.retry_delay)
                    self.retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    logger.error(f"Database error after {retries} retries: {e}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected database error: {e}")
                raise
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception as e:
                        logger.error(f"Error closing database connection: {e}")
    
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        with self._get_db_connection() as (conn, cursor):
            # Create conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    ui_generated TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    context_summary TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_timestamp ON conversations(session_id, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_activity ON sessions(last_activity)")
            
            conn.commit()
    
    def create_session(self) -> str:
        """
        Create a new conversation session.
        
        Returns:
            str: Unique session ID for the new conversation session.
        """
        session_id = str(uuid.uuid4())
        
        with self._get_db_connection() as (conn, cursor):
            cursor.execute("""
                INSERT INTO sessions (session_id, created_at, last_activity)
                VALUES (?, ?, ?)
            """, (session_id, datetime.now().isoformat(), datetime.now().isoformat()))
            
            conn.commit()
        
        logger.info(f"Created new conversation session: {session_id}")
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str, 
                   ui_generated: Optional[Dict[str, Any]] = None,
                   metadata: Optional[Dict[str, Any]] = None):
        """
        Add a message to the conversation history.
        
        Args:
            session_id (str): Session identifier for this conversation
            role (str): 'user' or 'assistant' to identify the speaker
            content (str): The message content
            ui_generated (Optional[Dict]): UI JSON if this was a UI generation response
            metadata (Optional[Dict]): Additional metadata about the message
        """
        with self._get_db_connection() as (conn, cursor):
            # Add the message
            cursor.execute("""
                INSERT INTO conversations (session_id, timestamp, role, content, ui_generated, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                datetime.now().isoformat(),
                role,
                content,
                json.dumps(ui_generated) if ui_generated else None,
                json.dumps(metadata) if metadata else None
            ))
            
            # Update session activity
            cursor.execute("""
                UPDATE sessions 
                SET last_activity = ?, message_count = message_count + 1
                WHERE session_id = ?
            """, (datetime.now().isoformat(), session_id))
            
            conn.commit()
        
        logger.debug(f"Added {role} message to session {session_id}: {content[:100]}...")
    
    def get_conversation_history(self, session_id: str, limit: int = 20) -> List[ConversationMessage]:
        """
        Retrieve conversation history for a session.
        
        Args:
            session_id (str): Session identifier
            limit (int): Maximum number of recent messages to retrieve
            
        Returns:
            List[ConversationMessage]: List of conversation messages, ordered by timestamp
        """
        with self._get_db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT session_id, timestamp, role, content, ui_generated, metadata
                FROM conversations
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (session_id, limit))
            
            rows = cursor.fetchall()
        
        messages = []
        for row in rows:
            session_id, timestamp, role, content, ui_generated, metadata = row
            messages.append(ConversationMessage(
                session_id=session_id,
                timestamp=datetime.fromisoformat(timestamp),
                role=role,
                content=content,
                ui_generated=json.loads(ui_generated) if ui_generated else None,
                metadata=json.loads(metadata) if metadata else None
            ))
        
        # Reverse to get chronological order
        return list(reversed(messages))
    
    def get_conversation_context(self, session_id: str, max_tokens: int = 2000) -> str:
        """
        Get formatted conversation context for AI query enhancement.
        
        This method retrieves recent conversation history and formats it as context
        that can be included in AI prompts to maintain conversation continuity.
        
        Args:
            session_id (str): Session identifier
            max_tokens (int): Approximate maximum tokens to include in context
            
        Returns:
            str: Formatted conversation context for AI prompt inclusion
        """
        messages = self.get_conversation_history(session_id, limit=10)
        
        if not messages:
            return ""
        
        context_parts = ["Previous conversation context:"]
        current_length = len(context_parts[0])
        
        for message in messages:
            # Format message with role and content
            if message.role == "user":
                msg_text = f"User: {message.content}"
            else:
                # For assistant messages, include summary of UI generated
                if message.ui_generated:
                    ui_type = message.ui_generated.get('type', 'UI')
                    ui_title = message.ui_generated.get('title', 'Generated UI')
                    msg_text = f"Assistant: {message.content} [Generated {ui_type}: {ui_title}]"
                else:
                    msg_text = f"Assistant: {message.content}"
            
            # Check if adding this message would exceed token limit
            if current_length + len(msg_text) > max_tokens:
                break
            
            context_parts.append(msg_text)
            current_length += len(msg_text)
        
        return "\n".join(context_parts)
    
    def get_last_ui_generated(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent UI JSON that was generated in this session.
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            Optional[Dict]: The last UI JSON generated, or None if no UI exists
        """
        messages = self.get_conversation_history(session_id, limit=20)
        
        # Look for the most recent assistant message with UI generated
        for message in messages:
            if message.role == "assistant" and message.ui_generated:
                return message.ui_generated
        
        return None
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Get summary information about a conversation session.
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            Dict: Session summary including message count, duration, topics, etc.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get session info
        cursor.execute("""
            SELECT created_at, last_activity, message_count, context_summary
            FROM sessions
            WHERE session_id = ?
        """, (session_id,))
        
        session_row = cursor.fetchone()
        if not session_row:
            return {}
        
        created_at, last_activity, message_count, context_summary = session_row
        
        # Get recent topics/apps mentioned
        cursor.execute("""
            SELECT content
            FROM conversations
            WHERE session_id = ? AND role = 'user'
            ORDER BY timestamp DESC
            LIMIT 5
        """, (session_id,))
        
        recent_queries = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return {
            "session_id": session_id,
            "created_at": created_at,
            "last_activity": last_activity,
            "message_count": message_count,
            "recent_queries": recent_queries,
            "context_summary": context_summary
        }
    
    def cleanup_old_sessions(self, days_old: int = 30):
        """
        Clean up old conversation sessions to manage database size.
        
        Args:
            days_old (int): Delete sessions older than this many days
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete old conversations
        cursor.execute("""
            DELETE FROM conversations
            WHERE session_id IN (
                SELECT session_id FROM sessions
                WHERE last_activity < ?
            )
        """, (cutoff_date.isoformat(),))
        
        # Delete old sessions
        cursor.execute("""
            DELETE FROM sessions
            WHERE last_activity < ?
        """, (cutoff_date.isoformat(),))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Cleaned up {deleted_count} old conversation sessions")
    
    def get_active_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get list of recently active conversation sessions.
        
        Args:
            limit (int): Maximum number of sessions to return
            
        Returns:
            List[Dict]: List of session summaries ordered by recent activity
        """
        with self._get_db_connection() as (conn, cursor):
            cursor.execute("""
                SELECT session_id, created_at, last_activity, message_count
                FROM sessions
                WHERE is_active = 1
                ORDER BY last_activity DESC
                LIMIT ?
            """, (limit,))
            
            sessions = []
            for row in cursor.fetchall():
                session_id, created_at, last_activity, message_count = row
                sessions.append({
                    "session_id": session_id,
                    "created_at": created_at,
                    "last_activity": last_activity,
                    "message_count": message_count
                })
            
            return sessions    
    def clear_session(self, session_id: str) -> bool:
        """
        Mark a session as inactive (clear/disable it).
        
        Args:
            session_id (str): Session identifier to clear
            
        Returns:
            bool: True if session was found and cleared, False if not found
        """
        with self._get_db_connection() as (conn, cursor):
            cursor.execute("""
                UPDATE sessions 
                SET is_active = 0
                WHERE session_id = ?
            """, (session_id,))
            
            conn.commit()
            return cursor.rowcount > 0