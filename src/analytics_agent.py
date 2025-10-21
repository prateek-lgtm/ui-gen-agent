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
    
    def _retrieve_relevant_data(self, user_query: str, intent: Dict) -> str:
        """
        Use RAG tools to retrieve relevant data from vector database based on user query and intent.
        
        Args:
            user_query (str): Original user query
            intent (Dict): Analyzed intent containing app, timeframe, metric_type, etc.
        
        Returns:
            str: Relevant data retrieved from vector database through RAG tools
        """
        # If no tools available, return empty data
        if not self.tools:
            return "No relevant data found - RAG tools not available."
        
        # Create a more specific query based on intent analysis
        app = intent.get('app', '')
        timeframe = intent.get('timeframe', 'today')
        metric_type = intent.get('metric_type', 'overview')
        data_points = intent.get('data_points', [])
        
        # Build enhanced query for RAG system
        enhanced_queries = []
        
        # Add the original query
        enhanced_queries.append(user_query)
        
        # Special handling for casual conversational queries
        casual_indicators = [
            "what's going", "what's hot", "what's happening", "what's up", 
            "anything interesting", "what's new", "what's on", "what's coming",
            "show me what's active", "what's available", "what can I do",
            "what's current", "what's trending", "what's popular"
        ]
        is_casual_query = any(indicator in user_query.lower() for indicator in casual_indicators)
        
        if is_casual_query:
            # For casual queries, focus on events and current activities
            enhanced_queries.extend([
                "current events and activities",
                "upcoming events this month",
                "active events October November December",
                "events happening now",
                "recent events and activities"
            ])
        
        # Add intent-based queries for better retrieval
        if app:
            enhanced_queries.append(f"{app} data information")
            
            # If app is events, add more event-specific queries
            if app == "events":
                enhanced_queries.extend([
                    "all events October November December 2025",
                    "event details dates locations guests",
                    "upcoming events with prices and locations"
                ])
        
        if metric_type != 'overview':
            enhanced_queries.append(f"{metric_type} metrics data")
        
        # Add data point specific queries
        for data_point in data_points:
            enhanced_queries.append(f"{data_point} information")
        
        # Execute RAG tool queries
        all_relevant_data = []
        
        for tool in self.tools:
            if hasattr(tool, '_run') or hasattr(tool, 'run'):
                try:
                    for query in enhanced_queries:
                        # Try both _run and run methods for compatibility
                        if hasattr(tool, '_run'):
                            result = tool._run(query)
                        else:
                            result = tool.run(query)
                        
                        if result and result.strip():
                            all_relevant_data.append(f"Query: {query}\nData: {result}")
                except Exception as e:
                    # Log error but continue with other tools/queries
                    all_relevant_data.append(f"Error retrieving data for '{query}': {str(e)}")
        
        # Combine all retrieved data
        if all_relevant_data:
            return "\n\n---\n\n".join(all_relevant_data)
        else:
            return f"No relevant data found for query: {user_query}"
        
    def analyze_intent(self, query: str, user_data: Dict = None) -> Dict:
        """
        Analyze user query using LLM to determine the type of analytics and data source.
        
        This method uses the LLM to intelligently understand user queries and map them
        to available data sources dynamically, without hardcoded keyword mappings.
        
        Args:
            query (str): Natural language query from the user.
            user_data (Dict, optional): Available user data to help with intent analysis.
        
        Returns:
            Dict: Intent analysis results containing:
                - app (str|None): Target data source
                - timeframe (str): Time period 
                - metric_type (str): Type of metrics
                - data_points (List[str]): Specific data points
                - ui_request_type (str): 'data_visualization' or 'simple_ui' or 'unclear'
        """
        # Default intent structure
        intent = {
            'app': None,
            'timeframe': 'today',
            'metric_type': 'overview',
            'data_points': [],
            'ui_request_type': 'data_visualization'
        }
        
        # If no LLM available, return unclear intent
        if not self._custom_llm or not hasattr(self._custom_llm, '_call'):
            intent['ui_request_type'] = 'unclear'
            return intent
        
        # Get available data sources from user_data
        available_data_sources = []
        if user_data:
            available_data_sources = list(user_data.keys())
        
        # Create LLM prompt for intent analysis
        prompt = f"""Analyze the following user query and determine the intent. The user has access to the following data sources: {available_data_sources}

USER QUERY: "{query}"

Your task is to analyze this query and return a JSON object with the following structure:
{{
    "app": "data_source_name or null",
    "timeframe": "today|yesterday|week|month|year",
    "metric_type": "overview|usage|messages|content|performance|plans|budget",
    "data_points": ["list", "of", "specific", "metrics"],
    "ui_request_type": "data_visualization|simple_ui|unclear"
}}

Rules:
1. If the query asks for simple UI elements (login, signup, settings), set ui_request_type to "simple_ui" and app to null
2. If the query is about data/analytics, set ui_request_type to "data_visualization"
3. If you cannot understand what the user wants, set ui_request_type to "unclear"
4. For app field, choose the most relevant data source from the available list, or null if none match
5. Analyze the query semantically - understand the intent, don't just look for keywords
6. For timeframe, determine what time period the user is asking about
7. For metric_type, determine what kind of metrics/data they want to see
8. For data_points, list specific metrics mentioned in the query
9. IMPORTANT: Casual conversational queries like "what's going?", "what's hot?", "what's happening?", "what's up?" should be interpreted as requests to show current/upcoming events and activities

CASUAL QUERY MAPPING:
- "what's going?" / "what's going on?" → Show current events and activities (app: "events", metric_type: "content")
- "what's hot?" / "what's trending?" → Show popular/upcoming events (app: "events", metric_type: "content") 
- "what's happening?" / "what's up?" → Show current events and activities (app: "events", metric_type: "content")
- "anything interesting?" / "what's new?" → Show events and activities (app: "events", metric_type: "content")
- "show me what's active" / "what's on?" → Show current events (app: "events", metric_type: "content")
- "what's available?" / "what can I do?" → Show available events (app: "events", metric_type: "content")
- "what's current?" / "what's popular?" → Show current popular events (app: "events", metric_type: "content")

Examples:
- "show me business plans" → app: "business_plans", ui_request_type: "data_visualization"
- "display my youtube usage" → app: "youtube", ui_request_type: "data_visualization" 
- "create a login page" → app: null, ui_request_type: "simple_ui"
- "social media budget" → app: "social_media_budget", ui_request_type: "data_visualization"
- "what's going?" → app: "events", metric_type: "content", ui_request_type: "data_visualization"
- "what's hot?" → app: "events", metric_type: "content", ui_request_type: "data_visualization"
- "what's happening?" → app: "events", metric_type: "content", ui_request_type: "data_visualization"
- "what's new?" → app: "events", metric_type: "content", ui_request_type: "data_visualization"
- "what's on?" → app: "events", metric_type: "content", ui_request_type: "data_visualization"
- "what can I do?" → app: "events", metric_type: "content", ui_request_type: "data_visualization"
- "xyz abc 123" → ui_request_type: "unclear"

Return ONLY the JSON object, no explanation or markdown."""

        try:
            # Call LLM for intent analysis
            response = self._custom_llm._call(prompt)
            
            # Extract JSON from response
            result_str = str(response)
            json_start = result_str.find('{')
            json_end = result_str.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = result_str[json_start:json_end]
                llm_intent = json.loads(json_str)
                
                # Merge with default intent, ensuring all required fields exist
                for key in intent:
                    if key in llm_intent:
                        intent[key] = llm_intent[key]
                
                return intent
            else:
                # LLM didn't return valid JSON - mark as unclear
                intent['ui_request_type'] = 'unclear'
                return intent
                
        except Exception as e:
            # LLM failed - mark as unclear
            intent['ui_request_type'] = 'unclear'
            return intent
    
    def _generate_unclear_intent_ui(self, user_query: str) -> Dict:
        """
        Generate a UI when the agent cannot understand user intent.
        """
        return {
            "type": "Screen",
            "title": "Could Not Understand",
            "content": {
                "type": "Column",
                "modifier": {"fillMaxSize": True, "padding": 16},
                "children": [
                    {
                        "type": "Card",
                        "modifier": {"fillMaxWidth": True, "padding": 16},
                        "elevation": 4,
                        "backgroundColor": "#FFF8E1",
                        "content": {
                            "type": "Column",
                            "children": [
                                {
                                    "type": "Text",
                                    "text": "I cannot understand what you want",
                                    "fontSize": 20,
                                    "fontWeight": "bold",
                                    "color": "#F57C00"
                                },
                                {
                                    "type": "Spacer",
                                    "height": 12
                                },
                                {
                                    "type": "Text",
                                    "text": "Can you please specify more clearly what you would like to see?",
                                    "fontSize": 16,
                                    "color": "#666666"
                                },
                                {
                                    "type": "Spacer",
                                    "height": 8
                                },
                                {
                                    "type": "Text",
                                    "text": f"Your request: \"{user_query}\"",
                                    "fontSize": 14,
                                    "color": "#888888"
                                },
                                {
                                    "type": "Spacer",
                                    "height": 16
                                },
                                {
                                    "type": "Text",
                                    "text": "Try asking for:",
                                    "fontSize": 16,
                                    "fontWeight": "bold",
                                    "color": "#424242"
                                },
                                {
                                    "type": "Spacer",
                                    "height": 8
                                },
                                {
                                    "type": "Text",
                                    "text": "• Business plans\n• Social media budget\n• WhatsApp usage\n• YouTube activity\n• Battery performance\n• Create a login page",
                                    "fontSize": 14,
                                    "color": "#666666"
                                }
                            ]
                        }
                    }
                ]
            }
        }
    
    def detect_modification_request(self, query: str, session_id: Optional[str] = None) -> bool:
        """
        Use LLM to detect if the user is asking to modify an existing UI rather than create a new one.
        
        Args:
            query (str): User query to analyze
            session_id (Optional[str]): Session ID to check if there's previous UI context
            
        Returns:
            bool: True if this is a modification request, False if it's a new UI request
        """
        # If no LLM available, assume it's a new request
        if not self._custom_llm or not hasattr(self._custom_llm, '_call'):
            return False
        
        # If no session or memory, can't be a modification
        if not session_id or not self._memory:
            return False
        
        # Check if there's a previous UI in the conversation
        last_ui = self._memory.get_last_ui_generated(session_id)
        if not last_ui:
            return False
        
        # Use LLM to determine if this is a modification request
        prompt = f"""Analyze the following user query to determine if they want to modify an existing UI or create a completely new one.

USER QUERY: "{query}"

Context: The user previously generated a UI in this conversation session.

Your task is to determine if this query is asking to:
1. MODIFY the existing UI (change colors, styling, layout, etc.)
2. CREATE a completely new UI (different data, different purpose)

Return ONLY "true" if this is a modification request, or "false" if this is a new UI request.

Examples:
- "make the background darker" → true (modification)
- "change the text color to blue" → true (modification) 
- "show me business plans" → false (new UI)
- "display youtube data" → false (new UI)
- "make it bigger" → true (modification)
- "use different colors" → true (modification)

Return ONLY: true or false"""

        try:
            response = self._custom_llm._call(prompt)
            result_str = str(response).strip().lower()
            return "true" in result_str
        except Exception as e:
            # If LLM fails, assume it's a new request
            return False

    def generate_ui(self, user_query: str, user_data: Dict, session_id: Optional[str] = None) -> Dict:
        """Generate UI based on user query and data using AI agent - 100% dynamic via Claude with conversation context"""
        # Analyze user intent using LLM with available data sources
        intent = self.analyze_intent(user_query, user_data)
        
        # Handle unclear intent
        if intent.get('ui_request_type') == 'unclear':
            return self._generate_unclear_intent_ui(user_query)
        
        # Use RAG tools to retrieve relevant data based on query intent
        app = intent.get('app', 'general')
        relevant_data = self._retrieve_relevant_data(user_query, intent)
        
        # Fallback to direct JSON access if RAG doesn't return sufficient data
        if not relevant_data or "No relevant data found" in relevant_data or "Error retrieving data" in relevant_data:
            # Fallback to structured data from JSON
            app_data = user_data.get(app, {}) if app else {}
            if app_data:
                relevant_data = f"Fallback data for {app}:\n{json.dumps(app_data, indent=2)}"
            else:
                # Try to get any available data
                available_apps = list(user_data.keys()) if user_data else []
                if available_apps:
                    sample_app = available_apps[0]
                    sample_data = user_data.get(sample_app, {})
                    relevant_data = f"Available data sources: {available_apps}\nSample data from {sample_app}:\n{json.dumps(sample_data, indent=2)}"
                else:
                    relevant_data = "No user data available."
        
        # Check if this is a modification request
        is_modification = self.detect_modification_request(user_query, session_id)
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

RELEVANT DATA FROM DATABASE:
{relevant_data}
{context_section}
**DESIGN SYSTEM REQUIREMENTS (FINAL SIMPLIFIED VERSION)**

Use **modern soft-elevation design** optimized for **white backgrounds** with subtle shadows, light borders, and accent color contrast.
Output **only a valid JSON object** (no markdown, no explanation).
Use **Jetpack Compose–style structure** (components: Screen, Column, Row, Card, Text, Spacer, TextField, Button).
Use only **HEX colors** (no rgba/rgb).
Do not use any image or icon components (like AsyncImage, Image, or Icon).
Only use these component types: Screen, Column, Row, Card, Text, Spacer, TextField, Button, Box.
Use **integers** for sizes (no “dp” or “sp”).
No icons — focus on text, spacing, and clarity.

---

### 🎨 GUARDRAILS

Use these exact colors in your JSON:

* for background color use `#FFFFFF`
* for text primary use `#111827`
* for text secondary use `#374151`
* for text tertiary use `#4B5563`
* for border use `#E5E7EB`
* for accent (price or highlight) use `#6366F1`
* for light background sections (like usage boxes) use `#F9FAFB`
* for shadow use `#0000000D`

---

### 🧩 REQUIREMENTS

1. Output **only JSON** (no extra text or markdown).
2. Layout: Vertical card — title and price at top, data usage subcard below, followed by details (speed, validity, renewal).
3. Card uses soft elevation — white background, light border, smooth shadow, rounded corners.
4. Typography:

   * Title font size: 18, weight: 700, color: `#111827`
   * Price font size: 18, weight: 600, color: `#6366F1`
   * Section title font size: 16, weight: 600, color: `#111827`
   * Body text font size: 14, weight: 400–500, color: `#374151` to `#4B5563`
5. Spacing:

   * Card padding: 16–20
   * Between lines: 6–8
   * Border radius: 16
6. Subcard (for Data Usage):

   * Background: `#F9FAFB`
   * Border: `#E5E7EB`
   * Padding: 10–14
   * Corner radius: 12
7. Interaction states: Include `"hover"` and `"active"` objects with slight shadow and elevation changes.
8. Accessibility: `"focusable": true`, `"ariaLabel"` describing the card purpose.
9. Always include `modifier` objects (`fillMaxWidth`, `padding`, etc.) as JSON fields.
10. Use **accent indigo (#6366F1)** only for highlights or progress elements.

Example Output Format
{{
  "type": "Screen",
  "title": "Smart Data Plan",
  "backgroundColor": "#FFFFFF",
  "content": {{
    "type": "Column",
    "modifier": {{ "fillMaxSize": true, "padding": 16 }},
    "horizontalAlignment": "centerHorizontally",
    "children": [
      {{
        "type": "Card",
        "modifier": {{
          "fillMaxWidth": true,
          "padding": 16
        }},
        "backgroundColor": "#FFFFFF",
        "borderColor": "#E5E7EB",
        "borderWidth": 1,
        "borderRadius": 16,
        "shadow": "0 4px 12px #0000000D",
        "content": {{
          "type": "Column",
          "spacing": 12,
          "children": [
            {{
              "type": "Row",
              "modifier": {{ "fillMaxWidth": true }},
              "horizontalArrangement": "spaceBetween",
              "children": [
                {{
                  "type": "Text",
                  "text": "Smart Data 499",
                  "fontSize": 18,
                  "fontWeight": "700",
                  "color": "#111827"
                }},
                {{
                  "type": "Text",
                  "text": "₱499",
                  "fontSize": 18,
                  "fontWeight": "600",
                  "color": "#6366F1"
                }}
              ]
            }},
            {{
              "type": "Card",
              "modifier": {{ "fillMaxWidth": true }},
              "backgroundColor": "#F9FAFB",
              "borderColor": "#E5E7EB",
              "borderWidth": 1,
              "borderRadius": 12,
              "padding": 12,
              "content": {{
                "type": "Column",
                "spacing": 4,
                "children": [
                  {{
                    "type": "Text",
                    "text": "Data Usage",
                    "fontSize": 16,
                    "fontWeight": "600",
                    "color": "#111827"
                  }},
                  {{
                    "type": "Text",
                    "text": "44GB used of 50GB",
                    "fontSize": 14,
                    "fontWeight": "500",
                    "color": "#374151"
                  }},
                  {{
                    "type": "Spacer",
                    "height": 8
                  }},
                  {{
                    "type": "Box",
                    "height": 4,
                    "borderRadius": 2,
                    "backgroundColor": "#E5E7EB",
                    "children": [
                      {{
                        "type": "Box",
                        "widthPercent": 88,
                        "height": 4,
                        "borderRadius": 2,
                        "backgroundColor": "#6366F1"
                      }}
                    ]
                  }}
                ]
              }}
            }},
            {{
              "type": "Text",
              "text": "Speed: 5G",
              "fontSize": 14,
              "fontWeight": "400",
              "color": "#4B5563"
            }},
            {{
              "type": "Text",
              "text": "Validity: 30 days",
              "fontSize": 14,
              "fontWeight": "400",
              "color": "#4B5563"
            }},
            {{
              "type": "Text",
              "text": "Renewal Date: Oct 30, 2025",
              "fontSize": 14,
              "fontWeight": "400",
              "color": "#4B5563"
            }}
          ]
        }},
        "interactionStates": {{
          "hover": {{
            "shadow": "0 6px 16px #0000001A",
            "transform": "translateY(-2)"
          }},
          "active": {{
            "shadow": "0 2px 8px #00000014",
            "transform": "translateY(0)"
          }}
        }},
        "focusable": true,
        "ariaLabel": "Smart Data 499 plan details card"
      }}
    ]
  }}
}}

"""
        
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
