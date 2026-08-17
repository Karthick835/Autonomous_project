import React, { useState } from 'react';
import { Activity, FileText, Database, FlaskConical } from 'lucide-react';
import DatasetUpload from './components/DatasetUpload';
import LiveLoopMonitor from './components/LiveLoopMonitor';
import ReportViewer from './components/ReportViewer';

export default function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [sessionId, setSessionId] = useState(null);
  const [results, setResults] = useState(null);

  const handleStartInvestigation = (csvFilename, domainContext, targetColumn, taskType) => {
    fetch('http://127.0.0.1:5050/api/investigate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        csv_filename: csvFilename,
        domain_context: domainContext,
        target_column: targetColumn,
        task_type: taskType
      })
    })
      .then(res => res.json())
      .then(data => {
        setSessionId(data.session_id);
        setResults(null);
        setActiveTab('monitor');
      })
      .catch(err => alert("Error starting investigation: " + err));
  };

  const handleInvestigationComplete = (sid) => {
    fetch(`http://127.0.0.1:5050/api/results/${sid}`)




      .then(res => res.json())
      .then(data => {
        if (data.results) {
          setResults(data.results);
          setActiveTab('results');
        }
      })
      .catch(err => console.error("Error fetching final results:", err));
  };

  return (
    <div style={{ padding: '30px 20px', minHeight: '100vh' }}>
      {/* Top Header */}
      <header style={{ maxWidth: '1100px', margin: '0 auto 30px auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'linear-gradient(135deg, #6366f1, #06b6d4)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 15px rgba(99, 102, 241, 0.4)' }}>
            <FlaskConical size={26} color="#ffffff" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.45rem', fontWeight: 700, letterSpacing: '-0.02em' }}>Autonomous AI Scientist</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Multi-Agent Hypothesis Generation, FDR Guardrails, Regression & Classification Engines</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="glass-panel" style={{ padding: '4px', display: 'flex', gap: '4px' }}>
          <button
            onClick={() => setActiveTab('upload')}
            className="btn-secondary"
            style={{ border: 'none', background: activeTab === 'upload' ? 'rgba(99, 102, 241, 0.25)' : 'transparent', color: activeTab === 'upload' ? '#fff' : 'var(--text-muted)' }}
          >
            <Database size={16} /> Dataset Setup
          </button>

          <button
            onClick={() => setActiveTab('monitor')}
            disabled={!sessionId}
            className="btn-secondary"
            style={{ border: 'none', background: activeTab === 'monitor' ? 'rgba(99, 102, 241, 0.25)' : 'transparent', color: activeTab === 'monitor' ? '#fff' : 'var(--text-muted)', opacity: !sessionId ? 0.4 : 1 }}
          >
            <Activity size={16} /> Live Loop Monitor
          </button>

          <button
            onClick={() => setActiveTab('results')}
            disabled={!results}
            className="btn-secondary"
            style={{ border: 'none', background: activeTab === 'results' ? 'rgba(99, 102, 241, 0.25)' : 'transparent', color: activeTab === 'results' ? '#fff' : 'var(--text-muted)', opacity: !results ? 0.4 : 1 }}
          >
            <FileText size={16} /> Scientific Findings
          </button>
        </div>
      </header>

      {/* Main Tab Content */}
      <main>
        {activeTab === 'upload' && (
          <DatasetUpload onStartInvestigation={handleStartInvestigation} />
        )}

        {activeTab === 'monitor' && (
          <LiveLoopMonitor sessionId={sessionId} onComplete={handleInvestigationComplete} />
        )}

        {activeTab === 'results' && (
          <ReportViewer results={results} sessionId={sessionId} />
        )}
      </main>
    </div>
  );
}

