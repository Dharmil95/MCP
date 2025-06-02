#!/usr/bin/env python3
"""Test the fixed modular supervisor chatbot."""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.append('.')

from supervisor import MCPClientManager, AgentManager, SupervisorWorkflow
from supervisor.config import LLMConfig

async def test_supervisor():
    """Test the modular supervisor system."""
    print("Testing Fixed Modular Supervisor...")
    
    try:
        # Initialize MCP client manager
        mcp_manager = MCPClientManager()
        results = await mcp_manager.initialize_all()
        print(f"MCP initialization: {results}")
        
        # Initialize agent manager
        agent_manager = AgentManager(mcp_manager)
        agent_results = await agent_manager.create_all_agents()
        print(f"Agent creation: {agent_results}")
        
        # Create supervisor workflow
        workflow = SupervisorWorkflow(agent_manager)
        workflow_success = await workflow.create_workflow()
        print(f"Workflow creation: {workflow_success}")
        
        if workflow_success:
            # Test document listing
            print("\n--- Testing document listing ---")
            response = await workflow.process_request("List all documents")
            print(f"Document response: {response}")
            
            # Test math calculation
            print("\n--- Testing math calculation ---")
            response = await workflow.process_request("15 + 23")
            print(f"Math response: {response}")
            
        else:
            print("Failed to create workflow")
            
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_supervisor())
