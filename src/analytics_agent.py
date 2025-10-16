"""
Analytics UI Agent Module

This module contains the core AI agent responsible for generating Jetpack Compose UI JSON
structures from natural language queries. The agent combines intent analysis, data retrieval,
and AI-powered UI generation to create contextually appropriate mobile interfaces.

Key Components:
    - AnalyticsUIAgent: Main CrewAI agent for UI generation
    - Intent analysis for query understanding
    - Dynamic UI generation with proper styling
    - Comprehensive error handling and fallback mechanisms

The agent is designed to handle both analytics-focused queries (displaying user activity data)
and general UI generation requests (login pages, settings screens, etc.).

Dependencies:
    - CrewAI: Agent framework for structured AI workflows
    - OpenRouter LLM: Integration with Claude 3.5 Sonnet
    - RAG tools: For retrieving relevant user activity data

Author: Huawei Agent POC Team
Version: 1.0.0
"""

from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from typing import List, Dict, Any, Optional
import json
import re
from datetime import datetime, timedelta
from .conversation_memory import ConversationMemory

class AnalyticsUIAgent(Agent):
    """
    AI Agent for generating Jetpack Compose UI JSON from natural language queries.
    
    This agent extends CrewAI's Agent class to provide specialized functionality for
    mobile UI generation. It analyzes user queries, retrieves relevant data through
    RAG tools, and generates appropriate UI structures using advanced language models.
    
    The agent is configured with specific role, goal, and backstory to optimize its
    performance for mobile UI generation tasks. It supports both analytics-focused
    queries and general UI creation requests.
    
    Attributes:
        rag_tools (List[BaseTool]): Tools for retrieving user activity data
        llm: Custom language model (typically OpenRouter with Claude 3.5 Sonnet)
        _custom_llm: Internal reference to avoid Pydantic conflicts
    
    Key Capabilities:
        - Intent analysis and query classification
        - Dynamic data retrieval based on query context
        - AI-powered UI structure generation
        - Adaptive styling based on app context and data sentiment
        - Comprehensive error handling with fallback UIs
    
    Supported UI Components:
        - Screen: Root container with title and content
        - Column/Row: Layout containers with children
        - Card: Material Design cards with elevation and styling
        - Text: Typography with font size, weight, and color options
        - Spacer: Layout spacing and weight distribution
        - Custom modifiers: Padding, margins, sizing, colors
    
    Example Usage:
        ```python
        # Initialize with RAG tools and custom LLM
        agent = AnalyticsUIAgent(rag_tools=[rag_tool], llm=custom_llm)
        
        # Generate UI from query
        ui_json = agent.generate_ui(
            "show me my whatsapp usage today", 
            user_data
        )
        ```
    """
    
    def __init__(self, rag_tools: List[BaseTool], llm=None, memory: Optional[ConversationMemory] = None):
        """
        Initialize the Analytics UI Agent.
        
        Args:
            rag_tools (List[BaseTool]): List of tools for data retrieval and processing.
                                       Typically includes QueryUIPatternsTool for user data access.
            llm: Custom language model instance. Should support _call() method for
                direct prompt execution. Typically OpenRouterLLM with Claude 3.5 Sonnet.
            memory (Optional[ConversationMemory]): Conversation memory instance for context-aware interactions.
        
        The initialization configures the agent with:
        - Specialized role as Jetpack Compose UI Generator
        - Clear goal for generating complete UI structures
        - Detailed backstory emphasizing design expertise
        - Tool integration for data access
        - Custom LLM configuration
        - Conversation memory for context awareness
        """
        super().__init__(
            role='Jetpack Compose UI Generator',
            goal='Generate complete Jetpack Compose UI JSON structures based on user queries and activity data',
            backstory="""You are an expert Jetpack Compose UI designer with years of experience 
            creating beautiful, modern mobile interfaces. You excel at:
            - Designing intuitive data visualizations
            - Choosing appropriate colors and layouts dynamically
            - Creating comprehensive UIs that display all relevant data
            - Writing clean, valid JSON structures for Jetpack Compose
            - Understanding conversation context and user intent
            - Providing contextually relevant responses based on previous interactions
            
            You always return ONLY valid JSON without any markdown formatting or extra text.""",
            tools=rag_tools,
            verbose=False,
            llm=llm,
            allow_delegation=False
        )
        # Store our custom LLM in a way that doesn't conflict with Pydantic
        object.__setattr__(self, '_custom_llm', llm)
        object.__setattr__(self, '_memory', memory)
        
    def analyze_intent(self, query: str) -> Dict:
        """
        Analyze user query to determine the type of analytics and timeframe.
        
        This method performs natural language processing on the user's query to extract
        key information that will guide the UI generation process. It identifies the
        target app, timeframe, metrics, and type of UI request.
        
        The intent analysis is crucial for determining whether to generate analytics
        dashboards with real user data or simple UI components like login screens.
        
        Args:
            query (str): Natural language query from the user.
                        Examples: "show me my whatsapp usage today",
                                 "create a login page",
                                 "display youtube activity this week"
        
        Returns:
            Dict: Intent analysis results containing:
                - app (str|None): Target app ('whatsapp', 'youtube', 'battery', etc.)
                - timeframe (str): Time period ('today', 'week', 'month', etc.)
                - metric_type (str): Type of metrics ('overview', 'usage', 'performance')
                - data_points (List[str]): Specific data points to display
                - ui_request_type (str): 'data_visualization' or 'simple_ui'
        
        Intent Classification:
            Simple UI Requests:
                - Triggered by keywords: login, signup, register, welcome, profile, settings
                - Results in standard UI components without user data
                
            Analytics Requests:
                - App-specific queries with time references
                - Requires data retrieval and visualization
        
        App Detection:
            - WhatsApp: messaging, chat, messages keywords
            - YouTube: youtube, video, watch keywords
            - Battery: battery, power, charging keywords
            - General: dashboard, apps, overview keywords
        
        Timeframe Detection:
            - Today: today, current day references
            - Week: week, weekly, past week references
            - Month: month, monthly references
            - Year: year, yearly references
        
        Example Usage:
            ```python
            intent = agent.analyze_intent("show me my whatsapp usage today")
            # Returns: {
            #     'app': 'whatsapp',
            #     'timeframe': 'today',
            #     'metric_type': 'overview',
            #     'data_points': ['messages', 'usage'],
            #     'ui_request_type': 'data_visualization'
            # }
            ```
        """
        intent = {
            'app': None,
            'timeframe': 'today',  # default
            'metric_type': 'overview',  # default
            'data_points': [],
            'ui_request_type': 'data_visualization'  # vs 'simple_ui'
        }
        
        query_lower = query.lower()
        
        # Check if it's a simple UI request (login page, etc.)
        simple_ui_keywords = ['login', 'signup', 'register', 'welcome', 'home', 'profile', 'settings']
        if any(keyword in query_lower for keyword in simple_ui_keywords):
            intent['ui_request_type'] = 'simple_ui'
            intent['app'] = 'general'
            return intent
        
        # App detection
        app_keywords = {
            'whatsapp': ['whatsapp', 'messaging', 'chat', 'messages'],
            'youtube': ['youtube', 'video', 'watch', 'viewing'],
            'battery': ['battery', 'power', 'charge', 'consumption']
        }
        
        for app, keywords in app_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                intent['app'] = app
                break
                
        # Timeframe detection
        timeframe_patterns = {
            'today': ['today', 'now'],
            'yesterday': ['yesterday'],
            'last_2_days': ['past 2 days', 'last 2 days', '2 days'],
            'last_week': ['week', 'weekly', 'past week', 'last week'],
            'last_month': ['month', 'monthly', 'past month', 'last month']
        }
        
        for timeframe, patterns in timeframe_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                intent['timeframe'] = timeframe
                break
            
        # Metric type detection
        if any(word in query_lower for word in ['usage', 'time', 'activity', 'spent']):
            intent['metric_type'] = 'usage'
        elif any(word in query_lower for word in ['messages', 'sent', 'received']):
            intent['metric_type'] = 'messages'
        elif any(word in query_lower for word in ['videos', 'watched', 'content']):
            intent['metric_type'] = 'content'
        elif any(word in query_lower for word in ['performance', 'cycles', 'charging']):
            intent['metric_type'] = 'performance'
            
        return intent
    def detect_modification_request(self, query: str) -> bool:
        """
        Detect if the user is asking to modify an existing UI rather than create a new one.
        
        Args:
            query (str): User query to analyze
            
        Returns:
            bool: True if this is a modification request, False if it's a new UI request
        """
        query_lower = query.lower()
        
        # Keywords that indicate modification requests
        modification_keywords = [
            'change', 'modify', 'update', 'alter', 'adjust', 'edit',
            'make it', 'make the', 'turn', 'switch', 'set',
            'different', 'another', 'new color', 'new background',
            'darker', 'lighter', 'bigger', 'smaller',
            'background', 'color', 'theme', 'style'
        ]
        
        return any(keyword in query_lower for keyword in modification_keywords)

    def generate_ui(self, user_query: str, user_data: Dict, session_id: Optional[str] = None) -> Dict:
        """Generate UI based on user query and data using AI agent - 100% dynamic via Claude with conversation context"""
        # Analyze user intent
        intent = self.analyze_intent(user_query)
        
        # Get the specific app data from the complete user_data
        app = intent.get('app', 'general')
        app_data = user_data.get(app, {})
        
        # Check if this is a modification request
        is_modification = self.detect_modification_request(user_query)
        last_ui = None
        
        # Get conversation context if memory is available and session_id provided
        conversation_context = ""
        if self._memory and session_id:
            conversation_context = self._memory.get_conversation_context(session_id)
            # Add the current user query to memory
            self._memory.add_message(session_id, "user", user_query)
            
            # If this is a modification request, get the last UI
            if is_modification:
                last_ui = self._memory.get_last_ui_generated(session_id)
        
        # Create different prompts based on whether this is a modification or new UI
        if is_modification and last_ui:
            # This is a modification request - provide the existing UI to modify
            prompt = f"""You are an expert Jetpack Compose UI designer. The user wants to MODIFY an existing UI.

USER REQUEST: "{user_query}"

EXISTING UI TO MODIFY:
{json.dumps(last_ui, indent=2)}

INSTRUCTIONS FOR MODIFICATION:
1. Take the existing UI structure above and modify ONLY what the user requested
2. Keep all the original data, layout, and components intact
3. Only change the specific elements mentioned in the user request
4. If they ask to change background color, modify the backgroundColor properties
5. If they ask to change text color, modify the text color properties
6. If they ask to change layout, adjust the layout components
7. Preserve all existing data values, text content, and structure
8. Maintain the same component hierarchy and organization
9. Keep all modifiers, padding, spacing, and other styling unless specifically asked to change

The user is asking to modify the existing UI, not create a new one. Respect their intent and preserve the existing structure while making only the requested changes.

Return ONLY a valid JSON object with the MODIFIED UI, no markdown, no explanation, just JSON."""

        else:
            # This is a new UI generation request
            context_section = f"\n\nCONVERSATION CONTEXT:\n{conversation_context}\n" if conversation_context else ""
            
            prompt = f"""You are an expert Jetpack Compose UI designer. Generate a complete Jetpack Compose UI in JSON format.

USER REQUEST: "{user_query}"

APP: {app}
TIMEFRAME: {intent.get('timeframe', 'today')}

COMPLETE DATA AVAILABLE:
{json.dumps(app_data, indent=2)}
{context_section}
REQUIREMENTS:
1. Create a beautiful, modern Jetpack Compose UI JSON structure
2. Display ALL relevant data from the data provided above
3. Consider the conversation context when designing the UI
4. Choose appropriate colors dynamically based on the app and data sentiment
5. Use Cards, Columns, Rows, Text, Spacer components creatively
6. Show daily stats, weekly summaries, peak hours, categories - everything available
7. Make the layout intuitive and visually appealing
8. Use proper typography sizes (14-24 for text)
9. Add appropriate padding and spacing
10. For simple UI requests (login, signup), create those UIs from scratch
11. Be creative and modern in your design choices

Return ONLY a valid JSON object, no markdown, no explanation, just JSON.

Example structure:
{{
  "type": "Screen",
  "title": "App Activity",
  "content": {{
    "type": "Column",
    "modifier": {{"fillMaxSize": true, "padding": 16}},
    "children": [
      {{"type": "Card", "content": {{...}}}}
    ]
  }}
}}"""
        
        try:
            # Check if we have our custom LLM
            if not self._custom_llm or not hasattr(self._custom_llm, '_call'):
                return self._generate_error_ui("LLM Error", "Custom OpenRouter LLM not properly configured")
            
            # Call the LLM directly with the prepared prompt
            response = self._custom_llm._call(prompt)
            
            # Parse the response
            result_str = str(response)
            
            # Try to extract JSON from the result
            json_start = result_str.find('{')
            json_end = result_str.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = result_str[json_start:json_end]
                ui_json = json.loads(json_str)
                
                # Add the assistant response to memory if available
                if self._memory and session_id:
                    ui_title = ui_json.get('title', 'Generated UI')
                    if is_modification and last_ui:
                        response_text = f"Modified UI: {ui_title} (changed: {user_query})"
                    else:
                        response_text = f"Generated UI: {ui_title}"
                    self._memory.add_message(session_id, "assistant", response_text, ui_generated=ui_json)
                
                return ui_json
            else:
                # Return failure message instead of fallback
                error_ui = {
                    "type": "Screen",
                    "title": "Generation Failed",
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
                                            "text": "UI Generation Failed",
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
                                            "text": "Claude could not generate valid JSON for this request.",
                                            "fontSize": 16,
                                            "color": "#666666"
                                        },
                                        {
                                            "type": "Text",
                                            "text": f"Query: {user_query}",
                                            "fontSize": 14,
                                            "color": "#888888"
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
                
                # Add error to memory if available
                if self._memory and session_id:
                    self._memory.add_message(session_id, "assistant", "UI generation failed - could not parse valid JSON", ui_generated=error_ui)
                
                return error_ui
                
        except json.JSONDecodeError as e:
            # JSON parsing failed
            error_ui = {
                "type": "Screen",
                "title": "JSON Parse Error",
                "content": {
                    "type": "Column",
                    "modifier": {"fillMaxSize": True, "padding": 16},
                    "children": [
                        {
                            "type": "Card",
                            "modifier": {"fillMaxWidth": True, "padding": 16},
                            "elevation": 4,
                            "backgroundColor": "#FFF3E0",
                            "content": {
                                "type": "Column",
                                "children": [
                                    {
                                        "type": "Text",
                                        "text": "JSON Parse Error",
                                        "fontSize": 20,
                                        "fontWeight": "bold",
                                        "color": "#F57C00"
                                    },
                                    {
                                        "type": "Spacer",
                                        "height": 8
                                    },
                                    {
                                        "type": "Text",
                                        "text": "Claude generated invalid JSON format.",
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
            
            # Add error to memory if available
            if self._memory and session_id:
                self._memory.add_message(session_id, "assistant", f"JSON parsing error: {str(e)}", ui_generated=error_ui)
            
            return error_ui
            
        except Exception as e:
            # General error
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
                                        "text": "Generation Error",
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
                                        "text": "An error occurred during UI generation.",
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
            
            # Add error to memory if available
            if self._memory and session_id:
                self._memory.add_message(session_id, "assistant", f"Generation error: {str(e)}", ui_generated=error_ui)
            
            return error_ui
    def _generate_error_ui(self, title: str, error_msg: str) -> Dict:
        """Generate a standardized error UI"""
        return {
            "type": "Screen",
            "title": title,
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
                                    "text": title,
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
                                    "text": "An error occurred during UI generation.",
                                    "fontSize": 16,
                                    "color": "#666666"
                                },
                                {
                                    "type": "Text",
                                    "text": f"Error: {error_msg}",
                                    "fontSize": 14,
                                    "color": "#888888"
                                }
                            ]
                        }
                    }
                ]
            }
        }
