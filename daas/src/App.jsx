import { useState } from 'react'
import UploadTab from './components/UploadTab'
import DocumentsTab from './components/DocumentsTab'
import SearchTab from './components/SearchTab'
import ChatTab from './components/ChatTab'
import ApiStatus from './components/ApiStatus'
import ErrorBoundary from './components/ErrorBoundary'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('upload')
  const [documents, setDocuments] = useState([])

  const handleDocumentsChange = (newDocuments) => {
    setDocuments(newDocuments);
  };

  return (
    <div className="container">
      <div className="d-flex justify-content-between align-items-center">
        <h1 className="mb-4">PDF Document Management with Milvus</h1>
        <ApiStatus />
      </div>
      
      <ul className="nav nav-tabs mb-4">
        <li className="nav-item">
          <button 
            className={`nav-link ${activeTab === 'upload' ? 'active' : ''}`} 
            onClick={() => setActiveTab('upload')}
          >
            Upload
          </button>
        </li>
        <li className="nav-item">
          <button 
            className={`nav-link ${activeTab === 'documents' ? 'active' : ''}`}
            onClick={() => setActiveTab('documents')}
          >
            Documents
          </button>
        </li>
        <li className="nav-item">
          <button 
            className={`nav-link ${activeTab === 'search' ? 'active' : ''}`}
            onClick={() => setActiveTab('search')}
          >
            Search
          </button>
        </li>
        <li className="nav-item">
          <button 
            className={`nav-link ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            Chat
          </button>
        </li>
      </ul>
      
      <div className="tab-content">
        <ErrorBoundary>
          {activeTab === 'upload' && <UploadTab />}
          {activeTab === 'documents' && <DocumentsTab onDocumentsChange={handleDocumentsChange} />}
          {activeTab === 'search' && <SearchTab documents={documents} />}
          {activeTab === 'chat' && <ChatTab />}
        </ErrorBoundary>
      </div>
    </div>
  )
}

export default App
