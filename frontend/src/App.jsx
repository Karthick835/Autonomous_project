import React, { useState, useEffect } from 'react';
import {
  FlaskConical, Database, Activity, FileText,
  ChevronRight, ChevronLeft, GitCompare, Brain,
  Circle, RotateCcw, PlusCircle
} from 'lucide-react';
import DatasetUpload from './components/DatasetUpload';
import LiveLoopMonitor from './components/LiveLoopMonitor';
import ReportViewer from './components/ReportViewer';
import CompareUpload from './components/CompareUpload';

const API = 'http://127.0.0.1:5050';

const NAV_ITEMS = [
  { id: 'upload',   label: 'Dataset Setup',       icon: Database,    alwaysEnabled: true },
  { id: 'monitor',  label: 'Live Loop Monitor',    icon: Activity,    requiresSession: true },
  { id: 'results',  label: 'Scientific Findings', icon: FileText,    requiresResults: true },
  { id: 'compare',  label: 'Multi-Dataset Compare', icon: GitCompare, alwaysEnabled: true },
];

// Aurora background component
function AuroraBackground({ active }) {
  return (
    <div className="aurora-bg">
      <div className={`aurora-orb aurora-orb-1 ${active ? 'active' : ''}`} />
      <div className={`aurora-orb aurora-orb-2 ${active ? 'active' : ''}`} />
      <div className={`aurora-orb aurora-orb-3 ${active ? 'active' : ''}`} />
    </div>
  );
}

export default function App() {
  // Load state from localStorage on page refresh
  const [activeTab, setActiveTab] = useState(() => {
    return localStorage.getItem('ai_active_tab') || 'upload';
  });
  const [sessionId, setSessionId] = useState(() => {
    return localStorage.getItem('ai_session_id') || null;
  });
  const [results, setResults] = useState(() => {
    try {
      const saved = localStorage.getItem('ai_results');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [sidebarExpanded, setSidebarExpanded] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);
  const [currentLLM, setCurrentLLM] = useState(() => {
    return localStorage.getItem('ai_current_llm') || 'gemini';
  });
  const [isInvestigating, setIsInvestigating] = useState(false);

  // Sync to localStorage
  useEffect(() => {
    localStorage.setItem('ai_active_tab', activeTab);
  }, [activeTab]);

  useEffect(() => {
    if (sessionId) {
      localStorage.setItem('ai_session_id', sessionId);
    } else {
      localStorage.removeItem('ai_session_id');
    }
  }, [sessionId]);

  useEffect(() => {
    if (results) {
      try {
        localStorage.setItem('ai_results', JSON.stringify(results));
      } catch (e) {
        console.warn('Could not cache results in localStorage:', e);
      }
    } else {
      localStorage.removeItem('ai_results');
    }
  }, [results]);

  useEffect(() => {
    localStorage.setItem('ai_current_llm', currentLLM);
  }, [currentLLM]);

  // Initial load: Fetch system status and re-hydrate results if session exists but results missing
  useEffect(() => {
    fetch(`${API}/api/status`)
      .then(r => r.json())
      .then(setSystemStatus)
      .catch(() => {});

    const storedSessionId = localStorage.getItem('ai_session_id');
    if (storedSessionId && !results) {
      fetch(`${API}/api/results/${storedSessionId}`)
        .then(r => r.json())
        .then(data => {
          if (data.results) {
            setResults(data.results);
            if (activeTab === 'upload') setActiveTab('results');
          }
        })
        .catch(() => {});
    }
  }, []);

  const handleStartInvestigation = (csvFilename, domainContext, targetColumn, taskType, llmModel) => {
    setCurrentLLM(llmModel || 'gemini');
    setIsInvestigating(true);

    fetch(`${API}/api/investigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        csv_filename: csvFilename,
        domain_context: domainContext,
        target_column: targetColumn,
        task_type: taskType,
        llm_model: llmModel || 'gemini',
      }),
    })
      .then(r => r.json())
      .then(data => {
        if (data.detail) {
          alert('Error: ' + data.detail);
          setIsInvestigating(false);
          return;
        }
        setSessionId(data.session_id);
        setResults(null);
        setActiveTab('monitor');
      })
      .catch(err => {
        alert('Error starting investigation: ' + err.message);
        setIsInvestigating(false);
      });
  };

  const handleInvestigationComplete = (sid) => {
    setIsInvestigating(false);
    fetch(`${API}/api/results/${sid}`)
      .then(r => r.json())
      .then(data => {
        if (data.results) {
          setResults(data.results);
          setActiveTab('results');
        }
      })
      .catch(console.error);
  };

  const handleNewInvestigation = () => {
    setSessionId(null);
    setResults(null);
    setIsInvestigating(false);
    setActiveTab('upload');
    localStorage.removeItem('ai_session_id');
    localStorage.removeItem('ai_results');
  };

  const LLM_NAMES = { gemini: 'Gemini', gpt4o: 'GPT-4o', claude: 'Claude' };

  return (
    <>
      <AuroraBackground active={isInvestigating} />

      <div className="app-shell">
        {/* ── Sidebar ── */}
        <aside className={`sidebar ${sidebarExpanded ? 'expanded' : ''}`}>
          {/* Logo */}
          <div className="sidebar-logo">
            <div className="sidebar-logo-icon">
              <FlaskConical size={18} color="#fff" />
            </div>
            <span className="sidebar-logo-text">AI Scientist</span>
          </div>

          {/* Toggle button */}
          <button
            id="sidebar-toggle"
            className="sidebar-toggle"
            onClick={() => setSidebarExpanded(!sidebarExpanded)}
            aria-label={sidebarExpanded ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            {sidebarExpanded ? <ChevronLeft size={12} /> : <ChevronRight size={12} />}
          </button>

          {/* Navigation */}
          <nav className="sidebar-nav">
            <div className="sidebar-section-label">Workflow</div>

            {NAV_ITEMS.map(item => {
              const Icon = item.icon;
              const isDisabled = (item.requiresSession && !sessionId) || (item.requiresResults && !results);
              const isActive = activeTab === item.id;

              return (
                <button
                  key={item.id}
                  id={`nav-${item.id}`}
                  className={`sidebar-nav-item ${isActive ? 'active' : ''} ${isDisabled ? 'disabled' : ''}`}
                  onClick={() => !isDisabled && setActiveTab(item.id)}
                  title={sidebarExpanded ? '' : item.label}
                >
                  <span className="sidebar-nav-icon">
                    <Icon size={18} />
                  </span>
                  <span className="sidebar-nav-label">{item.label}</span>
                </button>
              );
            })}

            <div className="sidebar-section-label" style={{ marginTop: 'var(--space-4)' }}>Actions</div>

            <button
              id="nav-new-investigation"
              className="sidebar-nav-item"
              onClick={handleNewInvestigation}
              title="Start New Investigation"
            >
              <span className="sidebar-nav-icon"><PlusCircle size={18} color="var(--accent-cyan)" /></span>
              <span className="sidebar-nav-label" style={{ color: 'var(--accent-cyan)' }}>New Investigation</span>
            </button>

            <button
              id="nav-memory"
              className="sidebar-nav-item"
              onClick={() => window.open(`${API}/api/memory/stats`, '_blank')}
              title="Memory Stats"
            >
              <span className="sidebar-nav-icon"><Brain size={18} /></span>
              <span className="sidebar-nav-label">Memory Stats</span>
            </button>
          </nav>

          {/* Footer status */}
          <div style={{
            padding: 'var(--space-3) var(--space-4)',
            borderTop: '1px solid var(--card-border)',
            overflow: 'hidden',
          }}>
            <div className="flex items-center gap-2">
              <Circle
                size={7}
                fill={systemStatus?.status === 'online' ? 'var(--accent-green)' : 'var(--accent-rose)'}
                color="transparent"
              />
              <span className="sidebar-nav-label" style={{
                fontSize: 11,
                color: systemStatus?.status === 'online' ? 'var(--accent-green)' : 'var(--accent-rose)',
              }}>
                {systemStatus?.status === 'online' ? 'Backend Online' : 'Offline'}
              </span>
            </div>
          </div>
        </aside>

        {/* ── Main Content ── */}
        <div className={`main-content ${sidebarExpanded ? 'sidebar-expanded' : ''}`}>

          {/* ── Top Header ── */}
          <header className="top-header">
            <div>
              <div className="header-title">Autonomous AI Scientist</div>
              <div className="header-subtitle">
                Multi-agent hypothesis generation · FDR guardrails · Real chart generation
              </div>
            </div>

            <div className="header-pills">
              {/* New Investigation Button in Header */}
              {results && (
                <button
                  className="btn btn-secondary"
                  style={{ height: 28, fontSize: 11, padding: '0 10px', gap: 4 }}
                  onClick={handleNewInvestigation}
                  title="Start fresh investigation"
                >
                  <RotateCcw size={12} />
                  New Run
                </button>
              )}

              {/* Active LLM pill */}
              <span className="pill pill-violet" style={{ fontSize: 11 }}>
                <span className="pill-dot" />
                {LLM_NAMES[currentLLM] || currentLLM}
              </span>

              {/* Session pill */}
              {sessionId && (
                <span className="pill pill-cyan" style={{ fontSize: 10, fontFamily: 'var(--font-mono)' }}>
                  {sessionId}
                </span>
              )}

              {/* Investigating */}
              {isInvestigating && (
                <span className="pill pill-violet">
                  <span className="pill-dot-pulse" />
                  Investigating
                </span>
              )}

              {/* Memory */}
              {systemStatus?.memory?.total_records > 0 && (
                <span className="pill pill-neutral" style={{ fontSize: 10 }}>
                  <Brain size={10} />
                  {systemStatus.memory.total_records} memories
                </span>
              )}
            </div>
          </header>

          {/* ── Page Content ── */}
          <main className="page-content">
            {activeTab === 'upload' && (
              <DatasetUpload onStartInvestigation={handleStartInvestigation} />
            )}

            {activeTab === 'monitor' && sessionId && (
              <LiveLoopMonitor
                sessionId={sessionId}
                onComplete={handleInvestigationComplete}
              />
            )}

            {activeTab === 'results' && results && (
              <ReportViewer results={results} sessionId={sessionId} />
            )}

            {activeTab === 'compare' && (
              <CompareUpload />
            )}
          </main>
        </div>
      </div>
    </>
  );
}
