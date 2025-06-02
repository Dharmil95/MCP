"""
Chat API to interact with the supervisor system.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import asyncio
from typing import Optional, Dict, Any

import sys
sys.path.append('.')
from supervisor import MCPClientManager, AgentManager, SupervisorWorkflow

router = APIRouter()

# Global instances - initialized once and reused for all requests
mcp_manager = None
agent_manager = None
workflow = None
initialized = False

# Request and response models
class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    thread_id: Optional[str] = None

class StatusResponse(BaseModel):
    status: str
    message: Optional[str] = None
    agents: Optional[Dict[str, bool]] = None


async def ensure_initialized():
    """Initialize the supervisor system if not already done."""
    global mcp_manager, agent_manager, workflow, initialized
    
    if initialized:
        return True
    
    try:
        # Initialize MCP client manager
        mcp_manager = MCPClientManager()
        results = await mcp_manager.initialize_all()
        
        # Initialize agent manager
        agent_manager = AgentManager(mcp_manager)
        agent_results = await agent_manager.create_all_agents()
        
        # Create supervisor workflow
        workflow = SupervisorWorkflow(agent_manager)
        workflow_success = await workflow.create_workflow()
        
        if workflow_success:
            initialized = True
            return True
        else:
            return False
    except Exception as e:
        print(f"Initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False


@router.post("/", response_model=ChatResponse)
async def process_chat(request: ChatRequest):
    """
    Process a chat message through the supervisor workflow.
    """
    global workflow
    
    # Ensure the system is initialized
    if not initialized and not await ensure_initialized():
        raise HTTPException(status_code=500, detail="Failed to initialize the chat system")
    
    # Process the message
    try:
        response = await workflow.process_request(
            request.message,
            thread_id=request.thread_id
        )
        
        # Extract thread_id if available
        thread_id = request.thread_id
        if thread_id is None and isinstance(response, str) and "chat_" in response:
            # Try to extract session ID from the debug logs if present
            import re
            match = re.search(r'chat_\d+_\w+', response)
            if match:
                thread_id = match.group(0)
        
        # Clean up the response (remove emoji and debug prefixes)
        clean_response = response
        if isinstance(clean_response, str):
            clean_response = clean_response.replace("🤖 ", "")
        
        return ChatResponse(
            response=clean_response,
            thread_id=thread_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get the status of the chat system.
    """
    global agent_manager, initialized
    
    if not initialized:
        return StatusResponse(
            status="not_initialized",
            message="Chat system not yet initialized"
        )
    
    document_agent_available = agent_manager.document_agent is not None
    math_agent_available = agent_manager.math_agent is not None
    
    return StatusResponse(
        status="ready",
        agents={
            "document_agent": document_agent_available,
            "math_agent": math_agent_available
        }
    )


@router.post("/initialize", response_model=StatusResponse)
async def initialize_system():
    """
    Initialize the chat system explicitly.
    """
    success = await ensure_initialized()
    
    if success:
        return await get_status()
    else:
        raise HTTPException(status_code=500, detail="Failed to initialize the chat system")
