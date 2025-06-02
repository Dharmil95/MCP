#!/usr/bin/env python3
"""
Agent Manager
Creates and manages specialized agents for different tasks.
"""

import os
from typing import Optional, Any

# LangGraph imports
try:
    from langgraph.prebuilt import create_react_agent
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False

from .config import LLMConfig
from .mcp_clients import MCPClientManager
try:
    from .config import DOCUMENT_AGENT_PROMPT, MATH_AGENT_PROMPT
except ImportError:
    DOCUMENT_AGENT_PROMPT = None
    MATH_AGENT_PROMPT = None


class AgentManager:
    """Manages specialized agents for document and math operations."""
    
    def __init__(self, mcp_manager: MCPClientManager):
        """Initialize agent manager with MCP client manager."""
        self.mcp_manager = mcp_manager
        self.llm = None
        self.document_agent = None
        self.math_agent = None
        
    async def initialize_llm(self) -> bool:
        """Initialize the LLM for agents."""
        if not AGENT_AVAILABLE:
            print("❌ Agent dependencies not available")
            return False
            
        try:
            if os.getenv("OPENAI_API_KEY"):
                self.llm = ChatOpenAI(
                    model=LLMConfig.DEFAULT_MODEL,
                    temperature=LLMConfig.DEFAULT_TEMPERATURE
                )
                print(f"✓ Using OpenAI {LLMConfig.DEFAULT_MODEL} for agent reasoning")
                return True
            else:
                print("❌ No OPENAI_API_KEY found. Set your OpenAI API key.")
                return False
                
        except Exception as e:
            print(f"❌ LLM initialization failed: {e}")
            return False
    
    async def create_document_agent(self) -> bool:
        """Create specialized document management agent."""
        if not self.llm:
            print("⚠️  Cannot create document agent - LLM not available")
            return False
            
        if not self.mcp_manager.fastmcp_client:
            print("⚠️  Cannot create document agent - FastMCP client not available")
            return False
            
        try:
            document_tools = await self.mcp_manager.get_fastmcp_tools()
            
            if document_tools:
                # Create the agent with the system message if available
                if DOCUMENT_AGENT_PROMPT:
                    system_message = SystemMessage(content=DOCUMENT_AGENT_PROMPT)
                    self.document_agent = create_react_agent(
                        self.llm,
                        document_tools,
                        system_message=system_message
                    )
                else:
                    self.document_agent = create_react_agent(
                        self.llm,
                        document_tools
                    )
                
                print("✓ Document agent created with FastMCP tools")
                return True
            else:
                print("⚠️  No document tools available")
                return False
                
        except Exception as e:
            print(f"❌ Document agent creation failed: {e}")
            return False
    
    async def create_math_agent(self) -> bool:
        """Create specialized math operations agent."""
        if not self.llm:
            print("⚠️  Cannot create math agent - LLM not available")
            return False
            
        if not self.mcp_manager.langgraph_client:
            print("⚠️  Cannot create math agent - LangGraph client not available")
            return False
            
        try:
            math_tools = await self.mcp_manager.get_langgraph_tools()
            
            if math_tools:
                self.math_agent = create_react_agent(
                    self.llm,
                    math_tools
                )
                print("✓ Math agent created with LangGraph tools")
                return True
            else:
                print("⚠️  No math tools available")
                return False
                
        except Exception as e:
            print(f"❌ Math agent creation failed: {e}")
            return False
    
    async def create_all_agents(self) -> dict:
        """Create all available agents."""
        results = {}
        
        # Initialize LLM first
        llm_ready = await self.initialize_llm()
        if not llm_ready:
            return {"llm": False, "document_agent": False, "math_agent": False}
        
        results["llm"] = True
        results["document_agent"] = await self.create_document_agent()
        results["math_agent"] = await self.create_math_agent()
        
        return results
    
    def get_llm(self) -> Optional[Any]:
        """Get the initialized LLM."""
        return self.llm
    
    def get_document_agent(self) -> Optional[Any]:
        """Get the document agent."""
        return self.document_agent
    
    def get_math_agent(self) -> Optional[Any]:
        """Get the math agent."""
        return self.math_agent
    
    def has_agents(self) -> bool:
        """Check if any agents are available."""
        return self.document_agent is not None or self.math_agent is not None
