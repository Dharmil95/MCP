#!/usr/bin/env python3
"""
MCP Supervisor Package
A modular multi-agent supervisor system for MCP tools.
"""

from .config import MCPConfig, LLMConfig
from .mcp_clients import MCPClientManager
from .agents import AgentManager
from .workflow import SupervisorWorkflow
from .utils import StatusManager, HelpManager
from .memory_manager import ConversationManager, get_conversation_manager

__version__ = "1.0.0"
__all__ = [
    "MCPConfig",
    "LLMConfig", 
    "MCPClientManager",
    "AgentManager",
    "SupervisorWorkflow",
    "StatusManager",
    "HelpManager",
    "ConversationManager",
    "get_conversation_manager"
]
