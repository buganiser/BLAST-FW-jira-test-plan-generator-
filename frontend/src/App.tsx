import { useState, useCallback } from 'react';

// Types
interface TestPlanResponse {
  success: boolean;
  markdown?: string;
  json?: any;
  file_path?: string;
  error?: string;
}

interface TicketInfo {
  key: string;
  summary: string;
  priority: string;
  issue_type: string;
  acceptance_criteria: string;
}

// API base URL - will be proxied by Vite in dev
const API_BASE = '/api';

function App() {
  const [ticketKey, setTicketKey] = useState('SCRUM-10');
  const [status, setStatus] = useState<'idle' | 'generating' | 'success' | 'error'>('idle');
  const [result, setResult] = useState<TestPlanResponse | null>(null);
  const [ticketInfo, setTicketInfo] = useState<TicketInfo | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  const generateTestPlan = useCallback(async () => {
    if (!ticketKey.trim()) return;

    setStatus('generating');
    setResult(null);
    setTicketInfo(null);

    try {
      const response = await fetch(`${API_BASE}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticket_key: ticketKey.trim(), post_to_jira: true, save_json: true })
      });

      const data: TestPlanResponse = await response.json();

      if (data.success) {
        setStatus('success');
        setResult(data);
        // Try to fetch ticket info for display
        try {
          const ticketRes = await fetch(`${API_BASE}/ticket/${ticketKey.trim()}`);
          if (ticketRes.ok) {
            const ticketData = await ticketRes.json();
            setTicketInfo(ticketData);
          }
        } catch (e) {
          // Ignore ticket info fetch errors
        }
      } else {
        setStatus('error');
        setResult(data);
      }
    } catch (error) {
      setStatus('error');
      setResult({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      });
    }
  }, [ticketKey]);

  const fetchTicketInfo = useCallback(async () => {
    if (!ticketKey.trim()) return;
    try {
      const response = await fetch(`${API_BASE}/ticket/${ticketKey.trim()}`);
      if (response.ok) {
        const data = await response.json();
        setTicketInfo(data);
      }
    } catch (e) {
      // Ignore
    }
  }, [ticketKey]);

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div>
            <h1 className="header-title">Jira Test Plan Generator</h1>
            <p className="header-subtitle">Generate IEEE 829 compliant test plans from Jira tickets</p>
          </div>
        </div>
      </header>

      <main className="main">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Generate Test Plan</h2>
          </div>
          <div className="card-body">
            <div className="form-group">
              <label className="form-label" htmlFor="ticket-key">Jira Ticket Key</label>
              <input
                id="ticket-key"
                type="text"
                className="form-input"
                placeholder="e.g., SCRUM-10"
                value={ticketKey}
                onChange={(e) => setTicketKey(e.target.value.toUpperCase())}
                onKeyDown={(e) => e.key === 'Enter' && generateTestPlan()}
              />
            </div>

            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <button
                className="btn btn-primary"
                onClick={generateTestPlan}
                disabled={status === 'generating' || !ticketKey.trim()}
              >
                {status === 'generating' && <span className="spinner" />}
                {status === 'generating' ? 'Generating...' : 'Generate Test Plan'}
              </button>
              <button
                className="btn btn-secondary"
                onClick={fetchTicketInfo}
                disabled={status === 'generating'}
              >
                Preview Ticket
              </button>
            </div>

            {status === 'error' && result?.error && (
              <div className="alert alert-error" role="alert">
                <strong>Error:</strong> {result.error}
              </div>
            )}

            {status === 'success' && (
              <div className="alert alert-success" role="alert">
                <strong>Success!</strong> Test plan generated and saved.
                {result?.file_path && <span style={{marginLeft: 12}}>Saved to: <code>{result.file_path}</code></span>}
              </div>
            )}

            {ticketInfo && (
              <div style={{ marginTop: 16, padding: 16, background: '#fafbfc', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
                <h4 style={{fontSize: 14, fontWeight: 600, marginBottom: 8}}>Ticket: {ticketInfo.key}</h4>
                <p style={{fontSize: 14, marginBottom: 8, color: 'var(--color-text)'}}>{ticketInfo.summary}</p>
                <div style={{display: 'flex', gap: 12, flexWrap: 'wrap', fontSize: 12}}>
                  <span className={`status-badge ${ticketInfo.priority.toLowerCase()}`}>{ticketInfo.priority}</span>
                  <span className="status-badge pending">{ticketInfo.issue_type}</span>
                  {ticketInfo.acceptance_criteria && (
                    <span className="status-badge success">Has AC</span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {result?.success && result.markdown && (
          <div className="result-section">
            <div className="result-header">
              <h2 className="result-title">Generated Test Plan Preview</h2>
              <div style={{display: 'flex', gap: 8}}>
                <button
                  className={`btn ${showPreview ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setShowPreview(!showPreview)}
                >
                  {showPreview ? 'Hide Preview' : 'Show Preview'}
                </button>
                <a
                  href={`/api/download/${ticketKey}`}
                  className="btn btn-secondary"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Download .md
                </a>
              </div>
            </div>

            {showPreview && (
              <div className="markdown-preview">
                <div className="markdown-content" dangerouslySetInnerHTML={{ __html: markdownToHtml(result.markdown) }} />
              </div>
            )}
          </div>
        )}
      </main>

      <footer className="footer">
        Jira Test Plan Generator — IEEE 829 Compliant — Built with React + Python
      </footer>
    </div>
  );
}

// Simple markdown to HTML converter for preview
function markdownToHtml(markdown: string): string {
  return markdown
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/`(.*?)`/gim, '<code>$1</code>')
    .replace(/^\- (.*$)/gim, '<li>$1</li>')
    .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
    .replace(/\n\n/gim, '</p><p>')
    .replace(/\n/gim, '<br>')
    .replace(/^<p><\/p>/, '')
    .replace(/<p><\/p>$/, '')
    .replace(/<li>/g, '<ul><li>')
    .replace(/<\/li><br>/g, '</li></ul><br>')
    .replace(/<li>/g, '<ul><li>')
    .replace(/<\/li><br><\/ul>/g, '</li></ul>');
}

export default App;