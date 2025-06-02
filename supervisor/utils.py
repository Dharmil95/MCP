#!/usr/bin/env python3
"""
Status and Help utilities for the MCP Supervisor Chatbot.
"""

from typing import Dict, Any
from .mcp_clients import MCPClientManager
from .agents import AgentManager
from .workflow import SupervisorWorkflow


class StatusManager:
    """Manages status reporting for the supervisor chatbot."""
    
    def __init__(self, mcp_manager: MCPClientManager, agent_manager: AgentManager, workflow: SupervisorWorkflow):
        """Initialize status manager."""
        self.mcp_manager = mcp_manager
        self.agent_manager = agent_manager
        self.workflow = workflow
    
    async def get_status_message(self) -> str:
        """Get comprehensive system status."""
        status = "🔍 MCP Supervisor Chatbot Status:\n\n"
        
        # LLM status
        llm = self.agent_manager.get_llm()
        if llm:
            model_name = getattr(llm, 'model_name', 'Unknown')
            status += f"✅ Supervisor LLM: {model_name} (Active)\n"
        else:
            status += "❌ Supervisor LLM: Not available\n"
        
        # Document agent status
        document_agent = self.agent_manager.get_document_agent()
        if document_agent and self.mcp_manager.fastmcp_client:
            if await self.mcp_manager.check_fastmcp_health():
                status += "✅ Document Agent: Connected (FastMCP)\n"
            else:
                status += "❌ Document Agent: Connection failed\n"
        else:
            status += "❌ Document Agent: Not available\n"
        
        # Math agent status
        math_agent = self.agent_manager.get_math_agent()
        if math_agent and self.mcp_manager.langgraph_client:
            if await self.mcp_manager.check_langgraph_health():
                tools = await self.mcp_manager.get_langgraph_tools()
                status += f"✅ Math Agent: Connected ({len(tools)} tools)\n"
            else:
                status += "❌ Math Agent: Connection failed\n"
        else:
            status += "❌ Math Agent: Not available\n"
        
        # Workflow status
        if self.workflow.is_available():
            status += "✅ Supervisor Workflow: Active\n"
        else:
            status += "❌ Supervisor Workflow: Not available\n"
        
        # Tool summary
        available_tools = self.mcp_manager.get_available_tools()
        status += f"\n📊 Total tools across agents: {len(available_tools)}"
        status += f"\n🎯 Multi-agent coordination: {'Active' if self.workflow.is_available() else 'Inactive'}"
        
        return status


class HelpManager:
    """Manages help messages for the supervisor chatbot."""
    
    def __init__(self, agent_manager: AgentManager):
        """Initialize help manager."""
        self.agent_manager = agent_manager
    
    def get_help_message(self) -> str:
        """Get comprehensive help message."""
        help_text = "🤖 MCP Supervisor Chatbot - Multi-Agent System\n\n"
        help_text += "🎯 **Supervisor Intelligence:**\n"
        help_text += "  I automatically route your requests to specialized agents:\n\n"
        
        # Document agent help
        if self.agent_manager.get_document_agent():
            help_text += "📄 **Document Agent** (FastMCP):\n"
            help_text += "  • List documents\n"
            help_text += "  • Search documents\n"
            help_text += "  • Document management\n\n"
        
        # Math agent help
        if self.agent_manager.get_math_agent():
            help_text += "🧮 **Math Agent** (LangGraph):\n"
            help_text += "  • Addition, subtraction\n"
            help_text += "  • Multiplication, division\n"
            help_text += "  • Mathematical calculations\n\n"
        
        # Example queries
        help_text += "💬 **Example Queries:**\n"
        if self.agent_manager.get_document_agent() and self.agent_manager.get_math_agent():
            help_text += "  • 'List all documents and then calculate 15 + 23'\n"
            help_text += "  • 'Find documents about AI and multiply 7 by 8'\n"
        
        if self.agent_manager.get_document_agent():
            help_text += "  • 'Search for machine learning documents'\n"
            help_text += "  • 'List all available documents'\n"
        
        if self.agent_manager.get_math_agent():
            help_text += "  • 'What's the result of 45 divided by 9?'\n"
            help_text += "  • 'Calculate 123 plus 456'\n"
        
        help_text += "\n🔧 **Commands:**\n"
        help_text += "  • 'help' - Show this message\n"
        help_text += "  • 'status' - Check system status\n"
        help_text += "  • 'quit' - Exit chatbot\n\n"
        
        if self.agent_manager.get_document_agent() and self.agent_manager.get_math_agent():
            help_text += "✨ **Multi-step workflows supported!**"
        else:
            help_text += "⚠️  Limited functionality - some agents unavailable"
        
        return help_text
