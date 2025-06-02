import { useState, useEffect } from 'react';
import { apiRequest } from '../utils/apiConfig';

const SearchTab = ({ documents = [] }) => {
  const [query, setQuery] = useState('');
  const [fileFilter, setFileFilter] = useState('');
  const [numResults, setNumResults] = useState(5);
  const [results, setResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState(null);
  
  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) {
      alert('Please enter a search query');
      return;
    }
    
    setIsSearching(true);
    setError(null);
    setResults(null);
    
    try {
      const queryParams = new URLSearchParams({
        query: query.trim(),
        limit: numResults
      });
      
      if (fileFilter) {
        queryParams.append('document_id', fileFilter);
      }
      
      const url = `/api/documents/search?${queryParams.toString()}`;
      const data = await apiRequest(url);
      setResults(data.results);
    } catch (err) {
      setError(`Error searching documents: ${err.message}`);
    } finally {
      setIsSearching(false);
    }
  };
  
  return (
    <div className="card">
      <div className="card-body">
        <h5 className="card-title">Search Documents</h5>
        <form onSubmit={handleSearch}>
          <div className="mb-3">
            <label htmlFor="searchQuery" className="form-label">Search Query</label>
            <input 
              type="text" 
              className="form-control" 
              id="searchQuery" 
              placeholder="Enter your search query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          
          <div className="mb-3">
            <label htmlFor="fileFilter" className="form-label">Filter by Document (Optional)</label>
            <select 
              className="form-select" 
              id="fileFilter"
              value={fileFilter}
              onChange={(e) => setFileFilter(e.target.value)}
            >
              <option value="">All Documents</option>
              {documents.map(doc => (
                <option key={doc.document_id} value={doc.document_id}>{doc.filename}</option>
              ))}
            </select>
          </div>
          
          <div className="mb-3">
            <label htmlFor="numResults" className="form-label">Number of Results</label>
            <input 
              type="number" 
              className="form-control" 
              id="numResults" 
              min="1" 
              max="20"
              value={numResults}
              onChange={(e) => setNumResults(parseInt(e.target.value))}
            />
          </div>
          
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={isSearching || !query.trim()}
          >
            {isSearching ? 'Searching...' : 'Search'}
          </button>
        </form>
        
        {isSearching && (
          <div className="mt-3">Searching...</div>
        )}
        
        {error && (
          <div className="alert alert-danger mt-3">{error}</div>
        )}
        
        {results && (
          <div id="searchResults" className="result mt-3">
            <h5>{results.length} results found:</h5>
            
            {results.length === 0 ? (
              <p>No matching documents found.</p>
            ) : (
              results.map((item, index) => (
                <div className="card mb-3" key={index}>
                  <div className="card-header">
                    <strong>Result {index + 1}</strong> | Source: {item.metadata.source || 'Unknown'}
                  </div>
                  <div className="card-body">
                    <p>{item.content}</p>
                  </div>
                  <div className="card-footer text-muted">
                    Document ID: {item.metadata.document_id}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchTab;
