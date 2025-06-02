import { useState, useEffect, useRef } from 'react';
import { apiRequest } from '../utils/apiConfig';
import './ChatTab.css';

/**
 * ChatTab Component
 * A chat interface that connects to the supervisor workflow backend
 * Allows users to send messages and receive responses from document and math agents
 */
const ChatTab = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [threadId, setThreadId] = useState(null);
  const [error, setError] = useState(null);
  const [systemStatus, setSystemStatus] = useState({
    status: 'unknown',
    agents: {}
  });
  const messagesEndRef = useRef(null);
  
  // Scroll to bottom of messages when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch chat system status on component mount
  useEffect(() => {
    const checkSystemStatus = async () => {
      try {
        const status = await apiRequest('/api/chat/status');
        setSystemStatus(status);
        
        // If system is not initialized, try initializing it
        if (status.status === 'not_initialized') {
          await apiRequest('/api/chat/initialize', { 
            method: 'POST' 
          });
          // Check status again after initialization
          const updatedStatus = await apiRequest('/api/chat/status');
          setSystemStatus(updatedStatus);
        }
      } catch (err) {
        console.error('Failed to check chat system status:', err);
        setError(`Failed to connect to chat system: ${err.message}`);
      }
    };
    
    checkSystemStatus();
  }, []);

  // Handle form submission (sending a message)
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    
    const userMessage = input;
    setInput('');
    
    // Add user message to chat
    setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
    setIsProcessing(true);
    setError(null);
    
    try {
      const response = await apiRequest('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: userMessage,
          thread_id: threadId
        })
      });
      
      // Store thread ID for continued conversation
      if (response.thread_id) {
        setThreadId(response.thread_id);
      }
      
      // Add response to chat
      setMessages(prev => [...prev, { 
        type: 'assistant', 
        content: response.response
      }]);
    } catch (err) {
      console.error('Chat request failed:', err);
      setError(`Failed to send message: ${err.message}`);
      setMessages(prev => [...prev, { 
        type: 'error', 
        content: `Error: ${err.message}` 
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  // Render chat messages
  const renderMessage = (msg, index) => {
    const messageClass = msg.type === 'user' 
      ? 'bg-primary text-white' 
      : msg.type === 'error' 
        ? 'bg-danger text-white'
        : 'bg-light';
    
    const messageLabel = msg.type === 'user' 
      ? 'You'
      : msg.type === 'error'
        ? 'Error'
        : 'Assistant';
        
    return (
      <div key={index} className={`message ${msg.type} mb-2`}>
        <div className={`p-2 rounded ${messageClass}`}>
          <strong>{messageLabel}: </strong>
          <span className="message-content">{msg.content}</span>
        </div>
      </div>
    );
  };

  const renderAgentStatus = (agents) => {
    if (!agents) return null;
    
    return (
      <div className="agent-status mt-2 small text-muted">
        <span className="me-3">
          📄 Document Agent: {agents.document_agent 
            ? <span className="text-success">Available</span> 
            : <span className="text-danger">Unavailable</span>}
        </span>
        <span>
          🔢 Math Agent: {agents.math_agent 
            ? <span className="text-success">Available</span> 
            : <span className="text-danger">Unavailable</span>}
        </span>
      </div>
    );
  };

  return (
    <div className="chat-container">
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h5 className="mb-0">Multi-Agent Chat</h5>
          <span className={`badge ${
            systemStatus.status === 'ready' ? 'bg-success' : 'bg-warning'
          }`}>
            {systemStatus.status === 'ready' ? 'System Ready' : 'Initializing...'}
          </span>
        </div>
        
        <div className="card-body">
          <div className="chat-messages p-3 mb-3 border rounded" style={{ height: '400px', overflowY: 'auto' }}>
            {messages.length === 0 && (
              <div className="text-center text-muted p-4">
                <p>👋 Hello! I'm a multi-agent chatbot.</p>
                <p>I can help with:</p>
                <ul className="text-start">
                  <li>Document operations (try "list documents" or "search for...")</li>
                  <li>Math calculations (try "15 + 23" or "what is 45 * 12?")</li>
                </ul>
                <p>What would you like to know?</p>
              </div>
            )}
            
            {messages.map(renderMessage)}
            
            {isProcessing && (
              <div className="message assistant mb-2">
                <div className="p-2 rounded bg-light">
                  <em>Assistant is thinking...</em>
                  <div className="spinner-border spinner-border-sm ms-2" role="status">
                    <span className="visually-hidden">Loading...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
          
          {renderAgentStatus(systemStatus.agents)}
          
          <form onSubmit={handleSubmit}>
            <div className="input-group">
              <input
                type="text"
                className="form-control"
                placeholder="Type your message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={isProcessing || systemStatus.status !== 'ready'}
              />
              <button
                className="btn btn-primary"
                type="submit"
                disabled={isProcessing || !input.trim() || systemStatus.status !== 'ready'}
              >
                Send
              </button>
            </div>
            {error && <div className="text-danger mt-2">{error}</div>}
          </form>
          
          <div className="mt-3 small text-muted">
            <strong>Hint:</strong> Try document operations like "list documents" 
            or math calculations like "what's 15 + 23?"
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatTab;
