#!/usr/bin/env python3
"""
Supervisor Workflow Management
Handles the workflow logic for the supervisor agent with enhanced memory management.
"""

import asyncio
from typing import Dict, Any, Optional

try:
    from langgraph.graph import StateGraph, MessagesState
    from langchain_core.messages import HumanMessage, AIMessage
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

from .config import SupervisorPrompts
from .agents import AgentManager
from .memory_manager import ConversationManager, get_conversation_manager


class SupervisorWorkflow:
    """Manages the supervisor workflow that coordinates specialized agents with enhanced memory management."""
    
    def __init__(self, agent_manager: AgentManager, conversation_manager: Optional[ConversationManager] = None):
        """Initialize supervisor workflow."""
        self.agent_manager = agent_manager
        self.conversation_manager = conversation_manager or get_conversation_manager()
        self.workflow = None
        self.supervisor_prompt = None
        
    def _create_supervisor_prompt(self):
        """Create the supervisor prompt template."""
        self.supervisor_prompt = ChatPromptTemplate.from_messages([
            ("system", SupervisorPrompts.SUPERVISOR_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "Given the above conversation, who should act next? Or should we FINISH?")
        ])
    
    def _supervisor_node(self, state: MessagesState) -> MessagesState:
        """Supervisor node that decides which agent to route to next."""
        try:
            llm = self.agent_manager.get_llm()
            if not llm or not self.supervisor_prompt:
                return {"messages": state["messages"] + [AIMessage(content="FINISH", name="supervisor")]}
            
            # Get the latest message
            messages = state["messages"]
            print(f"🎯 DEBUG: Supervisor processing {len(messages)} messages")
            
            # Show all messages for debugging
            for i, msg in enumerate(messages):
                msg_type = type(msg).__name__
                msg_name = getattr(msg, 'name', 'None')
                msg_content = getattr(msg, 'content', '')[:100]
                print(f"  Message {i}: {msg_type}, name={msg_name}")
                print(f"    content: {msg_content}...")
            
            # Find the latest user message for debugging
            latest_user_message = None
            for msg in reversed(messages):
                if hasattr(msg, '__class__') and msg.__class__.__name__ == 'HumanMessage':
                    latest_user_message = msg.content
                    break
            
            print(f"🎯 DEBUG: Latest user message: {latest_user_message or 'None'}")
            
            response = self.supervisor_prompt | llm
            result = response.invoke({"messages": messages})
            
            # Extract the decision
            decision = result.content.strip().upper()
            print(f"🎯 DEBUG: Raw supervisor decision: '{decision}'")
            
            # Validate decision
            valid_options = ["FINISH", "DOCUMENT_AGENT", "MATH_AGENT"]
            if decision not in valid_options:
                # Try to extract valid option from response
                for option in valid_options:
                    if option.lower().replace("_", "") in decision.lower().replace("_", ""):
                        decision = option
                        break
                else:
                    decision = "FINISH"  # Default fallback
            
            print(f"🎯 DEBUG: Final supervisor decision: '{decision}'")
            
            # Add supervisor decision to messages
            supervisor_message = AIMessage(
                content=f"Routing to: {decision}",
                name="supervisor"
            )
            
            return {"messages": messages + [supervisor_message]}
            
        except Exception as e:
            print(f"❌ Supervisor error: {e}")
            return {"messages": state["messages"] + [AIMessage(content="FINISH", name="supervisor")]}
    
    def _should_continue(self, state: MessagesState) -> str:
        """Determine next step based on supervisor decision."""
        try:
            last_message = state["messages"][-1]
            if hasattr(last_message, 'name') and last_message.name == "supervisor":
                content = last_message.content.upper()
                print(f"🎯 DEBUG: Supervisor decision: '{content}'")
                if "DOCUMENT_AGENT" in content and self.agent_manager.get_document_agent():
                    print("🎯 DEBUG: Routing to document_agent")
                    return "document_agent"
                elif "MATH_AGENT" in content and self.agent_manager.get_math_agent():
                    print("🎯 DEBUG: Routing to math_agent")
                    return "math_agent"
                else:
                    print("🎯 DEBUG: Routing to finish")
                    return "finish"
            print("🎯 DEBUG: No supervisor message found, routing to finish")
            return "finish"
        except Exception as e:
            print(f"🎯 DEBUG: Error in _should_continue: {e}")
            return "finish"
    
    async def create_workflow(self) -> bool:
        """Create the supervisor workflow with enhanced memory management."""
        if not LANGGRAPH_AVAILABLE:
            print("❌ LangGraph not available for workflow creation")
            return False
        
        if not self.agent_manager.has_agents():
            print("❌ Cannot create workflow without any agents")
            return False
        
        try:
            # Create supervisor prompt
            self._create_supervisor_prompt()
            
            # Create workflow
            workflow = StateGraph(MessagesState)
            
            # Add supervisor node
            workflow.add_node("supervisor", self._supervisor_node)
            
            # Add agent nodes
            document_agent = self.agent_manager.get_document_agent()
            math_agent = self.agent_manager.get_math_agent()
            
            if document_agent:
                workflow.add_node("document_agent", document_agent)
            
            if math_agent:
                workflow.add_node("math_agent", math_agent)
            
            # Set entry point
            workflow.set_entry_point("supervisor")
            
            # Add conditional edges from supervisor
            edge_mapping = {"finish": "__end__"}
            
            if document_agent:
                edge_mapping["document_agent"] = "document_agent"
                workflow.add_edge("document_agent", "supervisor")
            
            if math_agent:
                edge_mapping["math_agent"] = "math_agent"
                workflow.add_edge("math_agent", "supervisor")
            
            workflow.add_conditional_edges("supervisor", self._should_continue, edge_mapping)
            
            # Compile workflow with enhanced memory management
            self.workflow = self.conversation_manager.get_memory_saver().compile_workflow(workflow)
            
            print("✓ Supervisor workflow created with enhanced memory management")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create workflow: {e}")
            return False
    
    async def process_request(self, user_input: str, thread_id: Optional[str] = None, auto_cleanup: bool = True) -> str:
        """
        Process user input through the supervisor workflow with optional state management.
        
        Args:
            user_input: The user's input to process
            thread_id: Optional specific thread ID. If None, creates a new session
            auto_cleanup: Whether to automatically clean up the session after processing
            
        Returns:
            The response from the workflow
        """
        if not self.workflow:
            return "❌ Supervisor workflow not available. Please ensure system is properly initialized."
        
        user_input = user_input.strip()
        if not user_input:
            return "Please provide a message."
        
        # Handle session management
        session_id = thread_id
        created_new_session = False
        
        if session_id is None:
            session_id = self.conversation_manager.create_session("chat")
            created_new_session = True
        
        try:
            # Update session activity
            self.conversation_manager.update_session_activity(session_id)
            
            # Create initial state
            initial_state = {
                "messages": [HumanMessage(content=user_input)]
            }
            
            # Configuration for the workflow
            config = {"configurable": {"thread_id": session_id}}
            
            print(f"🎯 DEBUG: Processing request with session: {session_id}")
            
            # Run the workflow
            result = await asyncio.to_thread(
                self.workflow.invoke,
                initial_state,
                config
            )
            
            # Extract the final response
            messages = result.get("messages", [])
            
            # Find the last agent response (not supervisor routing messages)
            agent_responses = []
            for msg in messages:
                content = getattr(msg, 'content', '')
                if not content or content.startswith("Routing to:"):
                    continue
                    
                # Check if it's a supervisor message
                if hasattr(msg, 'name') and getattr(msg, 'name') == "supervisor":
                    continue
                    
                # Check if it's an agent response
                if (hasattr(msg, 'name') and 
                    getattr(msg, 'name') in ["document_agent", "math_agent"]):
                    agent_responses.append(content)
                elif isinstance(msg, AIMessage) and content:
                    # This might be an agent response without explicit name
                    agent_responses.append(content)
            
            # Prepare response
            if agent_responses:
                response = agent_responses[-1]
            else:
                # If no agent responses found, return the last non-supervisor message
                for msg in reversed(messages):
                    content = getattr(msg, 'content', '')
                    if (content and 
                        not content.startswith("Routing to:") and
                        not (hasattr(msg, 'name') and getattr(msg, 'name') == "supervisor")):
                        response = content
                        break
                else:
                    response = "I processed your request but couldn't generate a response."
            
            # Auto-cleanup for single-use sessions
            if auto_cleanup and created_new_session:
                self.conversation_manager.end_session(session_id)
                print(f"🧹 Auto-cleaned session: {session_id}")
            
            return f"🤖 {response}"
                
        except Exception as e:
            print(f"❌ Workflow error: {e}")
            
            # Cleanup on error if we created the session
            if auto_cleanup and created_new_session:
                self.conversation_manager.end_session(session_id)
                
            return f"❌ Error processing your request: {str(e)}"
    
    async def create_persistent_session(self, session_type: str = "chat") -> str:
        """
        Create a persistent conversation session that won't be auto-cleaned.
        
        Args:
            session_type: Type of session to create
            
        Returns:
            Session ID for continued conversation
        """
        return self.conversation_manager.create_session(session_type)
    
    async def end_session(self, session_id: str) -> bool:
        """
        Manually end a conversation session and clean up its state.
        
        Args:
            session_id: The session ID to end
            
        Returns:
            True if session was ended successfully
        """
        return self.conversation_manager.end_session(session_id)
    
    async def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up old conversation sessions.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
            
        Returns:
            Number of sessions cleaned up
        """
        return self.conversation_manager.enhanced_memory.clear_old_threads(max_age_hours)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about conversation sessions."""
        active_sessions = len(self.conversation_manager.get_active_sessions())
        memory_stats = self.conversation_manager.enhanced_memory.get_thread_stats()
        
        return {
            "active_sessions": active_sessions,
            "total_threads": memory_stats.get("total_threads", 0),
            "total_messages": memory_stats.get("total_messages", 0)
        }
    
    def is_available(self) -> bool:
        """Check if workflow is available."""
        return self.workflow is not None
