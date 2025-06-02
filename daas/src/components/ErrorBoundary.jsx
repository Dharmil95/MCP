import { Component } from 'react';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error to an error reporting service
    console.error("Error caught by boundary:", error, errorInfo);
    this.setState({
      error,
      errorInfo
    });
  }

  render() {
    if (this.state.hasError) {
      // You can render any custom fallback UI
      return (
        <div className="error-boundary p-4 border rounded bg-light">
          <h2 className="text-danger">Something went wrong</h2>
          <p>We apologize for the inconvenience. Please try refreshing the page.</p>
          <div className="mt-3">
            <button 
              className="btn btn-primary me-2" 
              onClick={() => window.location.reload()}
            >
              Refresh Page
            </button>
            <button 
              className="btn btn-outline-secondary" 
              onClick={() => this.setState({ hasError: false, error: null, errorInfo: null })}
            >
              Try to recover
            </button>
          </div>
          {process.env.NODE_ENV !== 'production' && (
            <details className="mt-4">
              <summary className="text-muted">Technical Details</summary>
              <pre className="mt-2 bg-dark text-light p-3 rounded">
                <code>
                  {this.state.error?.toString()}
                  {"\n\n"}
                  {this.state.errorInfo?.componentStack}
                </code>
              </pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
