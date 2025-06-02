import { useState, useEffect } from 'react';
import DocumentViewer from './DocumentViewer';
import { apiRequest } from '../utils/apiConfig';

const DocumentsTab = ({ onDocumentsChange }) => {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDocument, setSelectedDocument] = useState(null);

  const loadDocumentsList = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await apiRequest('/api/documents');
      setDocuments(data.documents);
      
      // Notify parent component about document changes
      if (onDocumentsChange) {
        onDocumentsChange(data.documents);
      }
    } catch (err) {
      console.error("Document loading error:", err);
      setError(`Failed to load documents: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDocumentsList();
  }, []);

  const handleDeleteDocument = async (documentId) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await apiRequest(`/api/documents/${documentId}`, {
          method: 'DELETE',
        });

        alert('Document deleted successfully');
        loadDocumentsList();
      } catch (err) {
        console.error("Document deletion error:", err);
        alert(`Error deleting document: ${err.message}`);
      }
    }
  };

  return (
    <div className="card">
      <div className="card-body">
        <h5 className="card-title">Documents List</h5>
        <button 
          className="btn btn-outline-primary mb-3"
          onClick={loadDocumentsList}
          disabled={isLoading}
        >
          {isLoading ? 'Loading...' : 'Refresh List'}
        </button>
        
        {error && (
          <div className="alert alert-danger">{error}</div>
        )}
        
        <div className="table-responsive">
          <table className="table">
            <thead>
              <tr>
                <th>Filename</th>
                <th>Document ID</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan="3" className="text-center">Loading...</td>
                </tr>
              ) : documents.length === 0 ? (
                <tr>
                  <td colSpan="3" className="text-center">No documents found</td>
                </tr>
              ) : (
                documents.map((doc) => (
                  <tr key={doc.document_id}>
                    <td>{doc.filename}</td>
                    <td>{doc.document_id}</td>
                    <td>
                      <div className="btn-group" role="group" aria-label="Document actions">
                        <button 
                          className="btn btn-sm btn-info me-1"
                          onClick={() => setSelectedDocument(doc)}
                        >
                          View
                        </button>
                        <button 
                          className="btn btn-sm btn-danger"
                          onClick={() => handleDeleteDocument(doc.document_id)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {selectedDocument && (
          <DocumentViewer 
            documentId={selectedDocument.document_id}
            filename={selectedDocument.filename}
            onClose={() => setSelectedDocument(null)}
          />
        )}
      </div>
    </div>
  );
};

export default DocumentsTab;
