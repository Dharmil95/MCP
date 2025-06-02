import { useState, useEffect } from 'react';
import { API_CONFIG } from '../utils/apiConfig';

const ApiStatus = () => {
  const [status, setStatus] = useState('checking');
  
  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        const response = await fetch(`${API_CONFIG.BASE_URL}/api/documents`, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          },
          signal: AbortSignal.timeout(3000) // Timeout after 3 seconds
        });
        
        if (response.ok) {
          setStatus('online');
        } else {
          setStatus('error');
        }
      } catch (error) {
        setStatus('offline');
      }
    };
    
    checkApiStatus();
    
    // Check every 30 seconds
    const intervalId = setInterval(checkApiStatus, 30000);
    
    return () => clearInterval(intervalId);
  }, []);
  
  const getStatusText = () => {
    switch (status) {
      case 'checking':
        return 'Checking API status...';
      case 'online':
        return 'API Connected';
      case 'error':
        return 'API Error';
      case 'offline':
        return 'API Offline';
      default:
        return 'Unknown Status';
    }
  };
  
  const getStatusClass = () => {
    switch (status) {
      case 'checking':
        return 'bg-secondary';
      case 'online':
        return 'bg-success';
      case 'error':
        return 'bg-warning';
      case 'offline':
        return 'bg-danger';
      default:
        return 'bg-secondary';
    }
  };
  
  return (
    <div className="api-status">
      <span className={`badge ${getStatusClass()}`}>
        <span className="status-indicator"></span>
        {getStatusText()}
      </span>
    </div>
  );
};

export default ApiStatus;
