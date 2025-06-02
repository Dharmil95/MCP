import { useState, useEffect } from 'react';
import { apiRequest } from '../utils/apiConfig';

const DocumentViewer = ({ documentId, filename, onClose }) => {
  const [content, setContent] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchDocumentContent = async () => {
      setIsLoading(true);
      try {
        // This is a mock request since we don't have a direct endpoint to get document content
        // You'll need to implement an appropriate API endpoint for this
        const queryParams = new URLSearchParams({
          document_id: documentId,
          limit: 50
        });
        
        const data = await apiRequest(`/api/documents/search?${queryParams.toString()}`);
        setContent(data.results);
      } catch (err) {
        setError(`Failed to load document content: ${err.message}`);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchDocumentContent();
  }, [documentId]);
  
  return (
    <div className="modal d-block" tabIndex="-1" role="dialog" style={{backgroundColor: 'rgba(0,0,0,0.5)'}}>
      <div className="modal-dialog modal-lg" role="document">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">Document: {filename}</h5>
            <button type="button" className="btn-close" onClick={onClose} aria-label="Close"></button>
          </div>
          <div className="modal-body">
            {isLoading ? (
              <div className="text-center py-5">
                <div className="spinner-border" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
                <p className="mt-3">Loading document content...</p>
              </div>
            ) : error ? (
              <div className="alert alert-danger">{error}</div>
            ) : content && content.length > 0 ? (
              <div className="document-content">
                {content.map((chunk, index) => (
                  <div key={index} className="content-chunk mb-3 p-2 border-bottom">
                    <p>{chunk.content}</p>
                    <small className="text-muted">
                      Page: {chunk.metadata.page || 'Unknown'}, 
                      Location: {chunk.metadata.location || 'Unknown'}
                    </small>
                  </div>
                ))}
              </div>
            ) : (
              <div className="alert alert-info">No content available for this document.</div>
            )}
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentViewer;
