import { useState } from 'react';
import { API_CONFIG } from '../utils/apiConfig';

const UploadTab = () => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadResult, setUploadResult] = useState(null);
  const [progress, setProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  const handleFileChange = (e) => {
    setSelectedFiles(Array.from(e.target.files));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (selectedFiles.length === 0) {
      setUploadResult("Please select a file");
      return;
    }

    setIsUploading(true);
    setProgress(0);

    const formData = new FormData();
    
    for (let i = 0; i < selectedFiles.length; i++) {
      formData.append('files', selectedFiles[i]);
    }

    try {
      setUploadError(null);
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.UPLOAD}`);
      
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const percent = Math.round((event.loaded / event.total) * 100);
          setProgress(percent);
        }
      });

      xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) {
          const response = JSON.parse(xhr.responseText);
          setUploadResult(response);
          setSelectedFiles([]);
          document.getElementById("uploadForm").reset();
          // We would fetch document list here but that's handled by the parent component
        } else {
          try {
            const errorResponse = JSON.parse(xhr.responseText);
            const errorMessage = errorResponse.detail || `Upload failed with status ${xhr.status}`;
            setUploadError(errorMessage);
            setUploadResult(null);
          } catch (e) {
            setUploadError(`Error: Status ${xhr.status}`);
            setUploadResult(null);
          }
        }
        setIsUploading(false);
      };

      xhr.onerror = function() {
        setUploadError("Network error occurred. Please check if the API server is running.");
        setUploadResult(null);
        setIsUploading(false);
      };

      xhr.timeout = API_CONFIG.TIMEOUT;
      xhr.ontimeout = function() {
        setUploadError("Request timed out. Please try again.");
        setUploadResult(null);
        setIsUploading(false);
      };

      xhr.send(formData);
    } catch (error) {
      setUploadResult(`Error: ${error.message}`);
      setIsUploading(false);
    }
  };

  return (
    <div className="card">
      <div className="card-body">
        <h5 className="card-title">Upload PDF Documents</h5>
        <form id="uploadForm" onSubmit={handleSubmit}>
          <div className="mb-3">
            <label htmlFor="pdfFile" className="form-label">Select PDF File(s)</label>
            <input 
              type="file" 
              className="form-control" 
              id="pdfFile" 
              accept=".pdf" 
              multiple
              onChange={handleFileChange} 
            />
          </div>
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={isUploading || selectedFiles.length === 0}
          >
            {isUploading ? 'Uploading...' : 'Upload'}
          </button>
        </form>
        
        {uploadError && (
          <div className="alert alert-danger mt-3">
            {uploadError}
          </div>
        )}
        
        {uploadResult && (
          <div className="result mt-3">
            <div className="alert alert-success mb-2">Upload successful!</div>
            <pre>{typeof uploadResult === 'object' ? JSON.stringify(uploadResult, null, 2) : uploadResult}</pre>
          </div>
        )}
        
        {isUploading && (
          <div className="progress mt-3">
            <div 
              className="progress-bar" 
              role="progressbar" 
              style={{ width: `${progress}%` }}
              aria-valuenow={progress} 
              aria-valuemin="0" 
              aria-valuemax="100"
            >
              {progress}%
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadTab;