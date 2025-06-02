#!/usr/bin/env python3
"""
Configuration module for MCP Supervisor Chatbot
Contains all configuration settings and constants.
"""

from pathlib import Path
from typing import Dict, Any

class MCPConfig:
    """Configuration class for MCP services."""
    
    @staticmethod
    def get_fastmcp_config() -> Dict[str, Any]:
        """Get FastMCP configuration for document management."""
        return {
            "mcpServers": {
                "documents": {
                    "url": "http://localhost:8000/mcp",
                    "transport": "sse"
                }
            }
        }
    
    @staticmethod
    def get_langgraph_config() -> Dict[str, Any]:
        """Get LangGraph configuration for math tools."""
        return {
            "math": {
                "command": "python",
                "args": [str(Path(__file__).parent.parent / "math_server_example.py")],
                "transport": "stdio",
            }
        }

class LLMConfig:
    """Configuration for LLM settings."""
    
    DEFAULT_MODEL = "gpt-4o"
    DEFAULT_TEMPERATURE = 0
    
    SUPERVISOR_SYSTEM_PROMPT = (
        "You are a supervisor tasked with managing a conversation between the following workers: "
        "document_agent, math_agent. Given the following user request, respond with the worker to act next. "
        "Each worker will perform a task and respond with their results. When finished, respond with FINISH.\n\n"
        "Select carefully:\n"
        "- document_agent: For anything related to documents, files, searching, listing, uploading (including folder uploads), or document management\n"
        "- math_agent: For mathematical calculations, arithmetic operations, or numerical computations\n"
        "- FINISH: When the task is complete or no further agent action is needed\n\n"
        "Document agent capabilities include:\n"
        "- Uploading individual PDF files\n"
        "- Uploading entire folders containing PDF files (batch upload)\n"
        "- Searching through uploaded documents\n"
        "- Listing all available documents\n\n"
        "Respond with just the agent name or FINISH, nothing else."
    )


class SupervisorPrompts:
    """Prompt templates for the supervisor agent."""
    
    SUPERVISOR_SYSTEM_PROMPT = (
        "You are a supervisor tasked with managing a conversation between the following workers: "
        "document_agent, math_agent. Given the following user request, respond with the worker to act next. "
        "Each worker will perform a task and respond with their results. When finished, respond with FINISH.\n\n"
        "Select carefully:\n"
        "- document_agent: For anything related to documents, files, searching, listing, uploading (including folder uploads), "
        "or document management including DELETING documents. Any request involving document IDs should go to document_agent.\n"
        "- math_agent: For mathematical calculations, arithmetic operations, or numerical computations\n"
        "- FINISH: When the task is complete or no further agent action is needed\n\n"
        "Document agent capabilities include:\n"
        "- Uploading individual PDF files\n"
        "- Uploading entire folders containing PDF files (batch upload)\n"
        "- Searching through uploaded documents\n"
        "- Listing all available documents\n"
        "- Deleting documents using document IDs\n\n"
        "Respond with just the agent name or FINISH, nothing else."
    )
    
    SYSTEM_PROMPT = SUPERVISOR_SYSTEM_PROMPT
    
    @staticmethod
    def get_supervisor_prompt():
        """Get the supervisor prompt template."""
        return ChatPromptTemplate.from_messages([
            ("system", SupervisorPrompts.SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ])


# Import required for prompt templates
try:
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
except ImportError:
    # Fallback if LangChain is not available
    class ChatPromptTemplate:
        @staticmethod
        def from_messages(messages):
            return None
    
    class MessagesPlaceholder:
        def __init__(self, variable_name):
            pass
  