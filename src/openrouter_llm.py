"""
OpenRouter LLM Integration Module

This module provides a custom LangChain-compatible LLM implementation that routes
requests through OpenRouter's API to access Claude 3.5 Sonnet and other advanced
language models. The implementation is designed to work seamlessly with CrewAI
agents while bypassing potential model conflicts.

Key Features:
    - Direct integration with OpenRouter API
    - Support for multiple models (Claude, GPT-4, etc.)
    - Custom model name mapping to avoid CrewAI detection
    - Comprehensive error handling and timeout management
    - Compatible with LangChain LLM interface

The module is specifically configured to use Claude 3.5 Sonnet as the default model
for high-quality UI generation and reasoning tasks.

Dependencies:
    - requests: For HTTP API communication
    - langchain: For LLM base class compatibility
    - OpenRouter API: External service for model access

Environment Variables:
    OPENROUTER_API_KEY: Required API key for OpenRouter service

Author: Huawei Agent POC Team
Version: 1.0.0
"""
import requests
import json
import os
from typing import Any, Dict, List, Optional, Union
from langchain.llms.base import LLM
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.chat_models.base import BaseChatModel
from langchain.schema.messages import BaseMessage
from langchain.schema import ChatResult, ChatGeneration


class OpenRouterLLM(LLM):
    """
    Custom LangChain LLM implementation for OpenRouter API integration.
    
    This class provides a bridge between LangChain's LLM interface and OpenRouter's
    API, enabling access to advanced language models like Claude 3.5 Sonnet through
    a unified interface. The implementation includes custom model name mapping,
    comprehensive error handling, and timeout management.
    
    Key Design Features:
        - Uses custom model names to avoid CrewAI's automatic model detection
        - Maps internal names to actual OpenRouter model identifiers
        - Provides detailed error messages for debugging and monitoring
        - Supports configurable parameters (temperature, max_tokens, etc.)
        - Implements proper timeout handling for reliability
    
    Attributes:
        model (str): Internal model identifier. Defaults to "claude-sonnet-4"
                    which maps to "anthropic/claude-3.5-sonnet" in OpenRouter.
        api_key (str): OpenRouter API key for authentication.
        temperature (float): Sampling temperature (0.0-1.0). Default: 0.7
        max_tokens (Optional[int]): Maximum tokens to generate. Default: None (model default)
    
    Model Mapping:
        The class uses custom model names internally and maps them to actual
        OpenRouter model identifiers to avoid conflicts with CrewAI's model detection:
        
        - "claude-sonnet-4" → "anthropic/claude-3.5-sonnet"
        - Add more mappings as needed for other models
    
    Example Usage:
        ```python
        # Initialize with API key
        llm = OpenRouterLLM(
            model="claude-sonnet-4",
            temperature=0.7,
            api_key="your-openrouter-api-key"
        )
        
        # Generate response
        response = llm._call("Generate a UI for WhatsApp usage")
        print(response)
        ```
    
    Error Handling:
        The implementation provides specific error types for different failure modes:
        - API authentication errors
        - Network connectivity issues
        - Rate limiting and quota exceeded
        - Invalid request format
        - Unexpected response format
    
    Integration Notes:
        - Compatible with CrewAI agents through LangChain interface
        - Bypasses CrewAI's automatic model detection using custom names
        - Provides consistent interface for different OpenRouter models
        - Supports both synchronous and asynchronous usage patterns
    """
    
    # Model configuration with type hints for Pydantic validation
    model: str = "claude-sonnet-4"  # No provider prefix to avoid CrewAI detection
    api_key: str = ""
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    
    def __init__(self, **kwargs):
        """
        Initialize the OpenRouter LLM with configuration parameters.
        
        Args:
            **kwargs: Configuration parameters including:
                - model (str): Model identifier (default: "claude-sonnet-4")
                - api_key (str): OpenRouter API key (can also use env var)
                - temperature (float): Sampling temperature (default: 0.7)
                - max_tokens (int, optional): Maximum tokens to generate
        
        Raises:
            ValueError: If OPENROUTER_API_KEY is not provided via parameter or environment
        
        Environment Variables:
            OPENROUTER_API_KEY: Used as fallback if api_key not provided in kwargs
        """
        super().__init__(**kwargs)
        if not self.api_key:
            self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY must be provided")
    
    @property
    def _llm_type(self) -> str:
        """Return the LLM type for LangChain identification."""
        return "openrouter"
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        """
        Execute a chat completion request through OpenRouter API.
        
        This method handles the core functionality of sending prompts to OpenRouter
        and processing the responses. It includes model name mapping, request
        formatting, error handling, and response parsing.
        
        Args:
            prompt (str): The input prompt/query to send to the model.
            stop (Optional[List[str]]): Stop sequences for generation. Applied to
                                       the API request if provided.
            **kwargs: Additional parameters passed to the API (currently unused).
        
        Returns:
            str: The generated response text from the language model.
        
        Raises:
            Exception: Various exceptions for different failure modes:
                - "Request to OpenRouter failed": Network/connectivity issues
                - "OpenRouter API error": API-specific errors (auth, rate limits, etc.)
                - "Unexpected response format": Malformed API response
                - "Error calling OpenRouter API": Generic errors
        
        API Request Format:
            The method constructs a ChatML-style request with:
            - Model identifier (mapped from internal name)
            - Messages array with user role and content
            - Temperature and max_tokens parameters
            - Optional stop sequences
        
        Model Name Mapping:
            Internal names are mapped to actual OpenRouter model identifiers:
            - "claude-sonnet-4" → "anthropic/claude-3.5-sonnet"
            
        Response Processing:
            - Validates response structure and error conditions
            - Extracts message content from choices array
            - Provides detailed error information for debugging
        
        Timeout and Reliability:
            - 60-second timeout for all requests
            - Automatic HTTP status code validation
            - Comprehensive error message formatting
        
        Example:
            ```python
            response = llm._call(
                "Generate a JSON UI structure for WhatsApp analytics",
                stop=["```", "END"]
            )
            ```
        """
        # Map custom model names to actual OpenRouter model names
        actual_model = self.model
        if self.model == "claude-sonnet-4":
            actual_model = "anthropic/claude-3.5-sonnet"  # Use available model
        
        payload = {
            "model": actual_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.temperature,
        }
        
        if self.max_tokens:
            payload["max_tokens"] = self.max_tokens
            
        if stop:
            payload["stop"] = stop
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                data=json.dumps(payload),
                timeout=60
            )
            response.raise_for_status()
            
            response_data = response.json()
            
            if "error" in response_data:
                raise Exception(f"OpenRouter API error: {response_data['error']}")
            
            return response_data["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request to OpenRouter failed: {str(e)}")
        except KeyError as e:
            raise Exception(f"Unexpected response format from OpenRouter: {str(e)}")
        except Exception as e:
            raise Exception(f"Error calling OpenRouter API: {str(e)}")