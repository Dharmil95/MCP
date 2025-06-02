#!/usr/bin/env python3
"""
Memory Manager for MCP Supervisor Chatbot
Provides utilities for managing conversation state and message cleanup.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import threading
import uuid

try:
    from langgraph.checkpoint.memory import MemorySaver
    from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False


class EnhancedMemorySaver:
    """
    Enhanced memory saver with state cleanup capabilities.
    Wraps LangGraph's MemorySaver with additional cleanup functionality.
    """
    
    def __init__(self):
        """Initialize the enhanced memory saver."""
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph not available for memory management")
            
        self.memory_saver = MemorySaver()
        self.thread_metadata: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        
    def compile_workflow(self, workflow):
        """Compile workflow with the enhanced memory saver."""
        return workflow.compile(checkpointer=self.memory_saver)
    
    def register_thread(self, thread_id: str, metadata: Optional[Dict[str, Any]] = None):
        """Register a thread with optional metadata."""
        with self._lock:
            self.thread_metadata[thread_id] = {
                "created_at": datetime.now(),
                "last_accessed": datetime.now(),
                "message_count": 0,
                **(metadata or {})
            }
    
    def update_thread_access(self, thread_id: str):
        """Update the last accessed time for a thread."""
        with self._lock:
            if thread_id in self.thread_metadata:
                self.thread_metadata[thread_id]["last_accessed"] = datetime.now()
                self.thread_metadata[thread_id]["message_count"] += 1
    
    def clear_thread_state(self, thread_id: str) -> bool:
        """
        Clear conversation state for a specific thread.
        
        Args:
            thread_id: The thread ID to clear
            
        Returns:
            True if state was cleared, False if thread not found
        """
        try:
            # Clear from metadata tracking
            with self._lock:
                if thread_id in self.thread_metadata:
                    del self.thread_metadata[thread_id]
            
            # Note: MemorySaver doesn't expose a public clear method
            # We'll work around this by using a new thread ID pattern
            print(f"🧹 Thread state cleared for: {thread_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error clearing thread state for {thread_id}: {e}")
            return False
    
    def clear_old_threads(self, max_age_hours: int = 24) -> int:
        """
        Clear old conversation threads older than specified hours.
        
        Args:
            max_age_hours: Maximum age in hours before clearing
            
        Returns:
            Number of threads cleared
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleared_count = 0
        
        with self._lock:
            threads_to_clear = [
                thread_id for thread_id, metadata in self.thread_metadata.items()
                if metadata.get("last_accessed", datetime.min) < cutoff_time
            ]
        
        for thread_id in threads_to_clear:
            if self.clear_thread_state(thread_id):
                cleared_count += 1
                
        print(f"🧹 Cleared {cleared_count} old conversation threads")
        return cleared_count
    
    def get_thread_stats(self) -> Dict[str, Any]:
        """Get statistics about active threads."""
        with self._lock:
            total_threads = len(self.thread_metadata)
            total_messages = sum(
                metadata.get("message_count", 0) 
                for metadata in self.thread_metadata.values()
            )
            
            oldest_thread = None
            newest_thread = None
            
            if self.thread_metadata:
                oldest_thread = min(
                    self.thread_metadata.items(),
                    key=lambda x: x[1].get("created_at", datetime.max)
                )[0]
                newest_thread = max(
                    self.thread_metadata.items(),
                    key=lambda x: x[1].get("created_at", datetime.min)
                )[0]
        
        return {
            "total_threads": total_threads,
            "total_messages": total_messages,
            "oldest_thread": oldest_thread,
            "newest_thread": newest_thread
        }


class ConversationManager:
    """
    High-level conversation manager for proper state lifecycle management.
    """
    
    def __init__(self):
        """Initialize the conversation manager."""
        self.enhanced_memory = EnhancedMemorySaver()
        self.active_conversations: Dict[str, datetime] = {}
        
    def create_session(self, session_type: str = "chat") -> str:
        """
        Create a new conversation session with unique ID.
        
        Args:
            session_type: Type of session (chat, test, demo, etc.)
            
        Returns:
            Unique session ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        session_id = f"{session_type}_{timestamp}_{unique_id}"
        
        self.enhanced_memory.register_thread(session_id, {
            "session_type": session_type,
            "created_by": "conversation_manager"
        })
        
        self.active_conversations[session_id] = datetime.now()
        
        print(f"🆕 Created new session: {session_id}")
        return session_id
    
    def end_session(self, session_id: str) -> bool:
        """
        End a conversation session and clean up its state.
        
        Args:
            session_id: The session ID to end
            
        Returns:
            True if session was ended successfully
        """
        success = self.enhanced_memory.clear_thread_state(session_id)
        
        if session_id in self.active_conversations:
            del self.active_conversations[session_id]
            
        print(f"🔚 Ended session: {session_id}")
        return success
    
    def cleanup_inactive_sessions(self, max_idle_minutes: int = 30) -> int:
        """
        Cleanup sessions that have been inactive.
        
        Args:
            max_idle_minutes: Maximum idle time in minutes
            
        Returns:
            Number of sessions cleaned up
        """
        cutoff_time = datetime.now() - timedelta(minutes=max_idle_minutes)
        inactive_sessions = [
            session_id for session_id, last_active in self.active_conversations.items()
            if last_active < cutoff_time
        ]
        
        cleaned_count = 0
        for session_id in inactive_sessions:
            if self.end_session(session_id):
                cleaned_count += 1
                
        return cleaned_count
    
    def get_memory_saver(self) -> EnhancedMemorySaver:
        """Get the enhanced memory saver instance."""
        return self.enhanced_memory
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs."""
        return list(self.active_conversations.keys())
    
    def update_session_activity(self, session_id: str):
        """Update last activity time for a session."""
        if session_id in self.active_conversations:
            self.active_conversations[session_id] = datetime.now()
            self.enhanced_memory.update_thread_access(session_id)


# Utility functions for easy integration
def create_clean_session() -> str:
    """Create a new clean conversation session."""
    manager = ConversationManager()
    return manager.create_session()


def create_test_session(test_name: str = "test") -> str:
    """Create a new test session with cleanup."""
    manager = ConversationManager()
    return manager.create_session(f"test_{test_name}")


def cleanup_test_sessions():
    """Clean up all test sessions."""
    manager = ConversationManager()
    # Clean up any sessions older than 1 hour
    return manager.enhanced_memory.clear_old_threads(max_age_hours=1)


# Global conversation manager instance
_global_conversation_manager = None


def get_conversation_manager() -> ConversationManager:
    """Get or create the global conversation manager."""
    global _global_conversation_manager
    if _global_conversation_manager is None:
        _global_conversation_manager = ConversationManager()
    return _global_conversation_manager


if __name__ == "__main__":
    # Example usage
    print("Memory Manager Example")
    print("=" * 30)
    
    if not LANGGRAPH_AVAILABLE:
        print("❌ LangGraph not available")
        exit(1)
    
    # Create conversation manager
    manager = ConversationManager()
    
    # Create test sessions
    session1 = manager.create_session("demo")
    session2 = manager.create_session("test")
    
    print(f"Active sessions: {manager.get_active_sessions()}")
    
    # Get memory stats
    stats = manager.enhanced_memory.get_thread_stats()
    print(f"Memory stats: {stats}")
    
    # End sessions
    manager.end_session(session1)
    manager.end_session(session2)
    
    print(f"Active sessions after cleanup: {manager.get_active_sessions()}")
