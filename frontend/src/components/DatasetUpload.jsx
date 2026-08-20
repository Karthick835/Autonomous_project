import React, { useState, useEffect, useCallback } from 'react';
import {
  Database, Upload, Sparkles, FileText, CheckCircle2,
  Table, Eye, Zap, Search, X, ChevronDown, Info
} from 'lucide-react';
import LLMSelector from './LLMSelector';

const API = 'http://127.0.0.1:5050';

export default function DatasetUpload({ onStartInvestigation }) {
  const [samples, setSamples] = useState([]);
  const [selectedSample, setSelectedSample] = useState(() => {
    return localStorage.getItem('ai_selected_sample') || '';
  });
  const [uploadedFile, setUploadedFile] = useState(() => {
    return localStorage.getItem('ai_uploaded_file') || null;
  });
  const [uploadedOriginalName, setUploadedOriginalName] = useState(() => {
    return localStorage.getItem('ai_uploaded_orig_name') || '';
  });
  const [profile, setProfile] = useState(null);
  const [selectedTarget, setSelectedTarget] = useState(() => {
    return localStorage.getItem('ai_selected_target') || '';
  });
  const [taskType, setTaskType] = useState(() => {
    return localStorage.getItem('ai_task_type') || 'classification';
  });
  const [domainContext, setDomainContext] = useState(() => {
    return localStorage.getItem('ai_domain_context') || '';
  });
  const [nlQuery, setNlQuery] = useState(() => {
    return localStorage.getItem('ai_nl_query') || '';
  });
  const [nlMode, setNlMode] = useState(false);
  const [nlLoading, setNlLoading] = useState(false);
  const [nlResult, setNlResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedLLM, setSelectedLLM] = useState(() => {
    return localStorage.getItem('ai_selected_llm') || 'gemini';
  });
  const [uploadProgress, setUploadProgress] = useState(0);
  const [showAllColumns, setShowAllColumns] = useState(false);

  // Sync to localStorage
  useEffect(() => {
    if (selectedSample) localStorage.setItem('ai_selected_sample', selectedSample);
    else localStorage.removeItem('ai_selected_sample');
  }, [selectedSample]);

  useEffect(() => {
    if (uploadedFile) {
      localStorage.setItem('ai_uploaded_file', uploadedFile);
      localStorage.setItem('ai_uploaded_orig_name', uploadedOriginalName);
    } else {
      localStorage.removeItem('ai_uploaded_file');
      localStorage.removeItem('ai_uploaded_orig_name');
    }
  }, [uploadedFile, uploadedOriginalName]);

  useEffect(() => {
    if (selectedTarget) localStorage.setItem('ai_selected_target', selectedTarget);
  }, [selectedTarget]);

  useEffect(() => {
    if (taskType) localStorage.setItem('ai_task_type', taskType);
  }, [taskType]);

  useEffect(() => {
    localStorage.setItem('ai_domain_context', domainContext);
  }, [domainContext]);

  useEffect(() => {
    localStorage.setItem('ai_selected_llm', selectedLLM);
  }, [selectedLLM]);

  const fetchPreview = useCallback((filename, keepTarget = false) => {
    if (!filename) return;
    setLoading(true);
    fetch(`${API}/api/dataset-preview/${filename}`)
      .then(r => r.json())
      .then(d => {
        if (d.profile) {
          setProfile(d.profile);
          if (!keepTarget || !selectedTarget) {
            setSelectedTarget(d.profile.active_target || '');
            setTaskType(d.profile.active_task || 'classification');
          }
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [selectedTarget]);

  useEffect(() => {
    fetch(`${API}/api/sample-datasets`)
      .then(r => r.json())
      .then(d => {
        if (d.samples?.length) {
          setSamples(d.samples);
          const savedActive = localStorage.getItem('ai_uploaded_file') || localStorage.getItem('ai_selected_sample');
          if (savedActive) {
            fetchPreview(savedActive, true);
          } else {
            handleSelectSample(d.samples[0].name);
          }
        }
      })
      .catch(console.error);
  }, []);

  const handleSelectSample = (name) => {
    setSelectedSample(name);
    setUploadedFile(null);
    setUploadedOriginalName('');
    setProfile(null);
    setNlResult(null);
    fetchPreview(name, false);
  };

  const processFile = async (file) => {
    if (!file?.name.endsWith('.csv')) return;
    setUploading(true);
    setUploadProgress(10);

    const formData = new FormData();
    formData.append('file', file);

    // Fake progress ticks
    const ticker = setInterval(() => {
      setUploadProgress(p => Math.min(p + 15, 80));
    }, 200);

    try {
      const res = await fetch(`${API}/api/upload`, { method: 'POST', body: formData });
      const data = await res.json();
      clearInterval(ticker);
      setUploadProgress(100);
      setUploadedFile(data.filename);
      setUploadedOriginalName(data.original_name);
      setSelectedSample('');
      if (data.profile) {
        setProfile(data.profile);
        setSelectedTarget(data.profile.active_target || '');
        setTaskType(data.profile.active_task || 'classification');
      }
      setNlResult(null);
      setTimeout(() => setUploadProgress(0), 800);
    } catch (e) {
      clearInterval(ticker);
      setUploadProgress(0);
      alert('Upload failed: ' + e.message);
    } finally {
      setUploading(false);
    }
  };

  const handleFileInput = (e) => processFile(e.target.files[0]);
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    processFile(e.dataTransfer.files[0]);
  };
  const handleDragOver = (e) => { e.preventDefault(); setIsDragOver(true); };
  const handleDragLeave = () => setIsDragOver(false);

  const handleNLInterpret = async () => {
    if (!nlQuery.trim() || !activeFile) return;
    setNlLoading(true);
    try {
      const res = await fetch(`${API}/api/nl-interpret`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: nlQuery,
          csv_filename: activeFile,
          llm_model: selectedLLM,
        }),
      });
      const data = await res.json();
      if (data.detail) throw new Error(data.detail);
      setNlResult(data);
      setSelectedTarget(data.target_column);
      setTaskType(data.task_type);
      setDomainContext(data.domain_context);
    } catch (e) {
      alert('NL interpretation failed: ' + e.message);
    } finally {
      setNlLoading(false);
    }
  };

  const handleLaunch = () => {
    const targetFile = uploadedFile || selectedSample;
    if (!targetFile) return alert('Please select or upload a dataset first.');
    if (!selectedTarget) return alert('Please select a target variable.');
    onStartInvestigation(targetFile, domainContext, selectedTarget, taskType, selectedLLM);
  };

  const activeFile = uploadedFile || selectedSample;
  const activeColumns = profile ? Object.keys(profile.column_profiles || {}) : [];
  const visibleColumns = showAllColumns ? activeColumns : activeColumns.slice(0, 12);

  return (
    <div className="fade-in" style={{ maxWidth: 1080, margin: '0 auto' }}>

      {/* ── LLM Selector ── */}
      <div className="card" style={{ padding: 'var(--space-6)', marginBottom: 'var(--space-5)' }}>
        <div className="section-header">
          <Zap size={16} color="var(--accent-violet)" />
          <span className="section-title">LLM Engine Selection</span>
          <span className="pill pill-neutral" style={{ marginLeft: 'auto', fontSize: 10 }}>
            Drives hypothesis generation
          </span>
        </div>
        <LLMSelector selectedModel={selectedLLM} onSelect={setSelectedLLM} />
      </div>

      {/* ── Dataset Selection ── */}
      <div className="card" style={{ padding: 'var(--space-6)', marginBottom: 'var(--space-5)' }}>
        <div className="section-header">
          <Database size={16} color="var(--accent-cyan)" />
          <span className="section-title">Dataset Selection</span>
        </div>

        <div className="grid-2" style={{ gap: 'var(--space-4)' }}>
          {/* Preloaded samples */}
          <div>
            <div className="label">Preloaded Samples</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
              {samples.map(s => (
                <button
                  key={s.name}
                  id={`sample-${s.name}`}
                  onClick={() => handleSelectSample(s.name)}
                  style={{
                    padding: 'var(--space-3) var(--space-4)',
                    borderRadius: 'var(--radius-md)',
                    border: `1px solid ${selectedSample === s.name ? 'var(--accent-violet)' : 'var(--card-border)'}`,
                    background: selectedSample === s.name ? 'var(--accent-violet-dim)' : 'var(--bg-elevated)',
                    color: 'var(--text-primary)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    transition: 'all var(--transition-fast)',
                    fontFamily: 'var(--font-sans)',
                    fontSize: 13,
                  }}
                >
                  <div className="flex items-center gap-2">
                    <FileText size={14} color={selectedSample === s.name ? 'var(--accent-violet)' : 'var(--accent-cyan)'} />
                    <span style={{ fontWeight: 500 }}>{s.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted">
                      {(s.size_bytes / 1024).toFixed(0)} KB
                    </span>
                    {selectedSample === s.name && <CheckCircle2 size={14} color="var(--accent-green)" />}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Upload zone */}
          <div>
            <div className="label">Upload Your CSV</div>
            <div
              id="csv-drop-zone"
              className={`drop-zone ${isDragOver ? 'drag-over' : ''}`}
              style={{ minHeight: 140 }}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => document.getElementById('csv-file-input').click()}
            >
              <input
                id="csv-file-input"
                type="file"
                accept=".csv"
                style={{ display: 'none' }}
                onChange={handleFileInput}
              />
              <Upload size={28} color={isDragOver ? 'var(--accent-violet)' : 'var(--text-secondary)'} />
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>
                {uploading ? 'Uploading & profiling...' : 'Drop CSV here or click to browse'}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                Any .csv file — data is processed locally on your server
              </div>

              {uploadProgress > 0 && (
                <div style={{ width: '80%' }}>
                  <div className="progress-bar-track">
                    <div className="progress-bar-fill" style={{ width: `${uploadProgress}%` }} />
                  </div>
                </div>
              )}

              {uploadedFile && (
                <div className="pill pill-green">
                  <CheckCircle2 size={11} />
                  {uploadedOriginalName || uploadedFile}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── Natural Language Query ── */}
      {activeFile && (
        <div className="card" style={{ padding: 'var(--space-6)', marginBottom: 'var(--space-5)' }}>
          <div className="section-header">
            <Search size={16} color="var(--accent-amber)" />
            <span className="section-title">Natural Language Query</span>
            <button
              onClick={() => setNlMode(!nlMode)}
              className="btn btn-ghost"
              style={{ marginLeft: 'auto', gap: 'var(--space-1)', fontSize: 11 }}
            >
              {nlMode ? 'Use Manual Setup' : 'Use Natural Language'}
              <ChevronDown size={12} style={{ transform: nlMode ? 'rotate(180deg)' : 'none', transition: 'transform var(--transition-fast)' }} />
            </button>
          </div>

          {nlMode && (
            <div className="fade-in">
              <div style={{ marginBottom: 'var(--space-3)', fontSize: 12, color: 'var(--text-secondary)' }}>
                Describe what you want to investigate in plain English. The LLM will determine the target variable and investigation strategy.
              </div>
              <div className="flex gap-2">
                <input
                  id="nl-query-input"
                  className="input"
                  value={nlQuery}
                  onChange={e => setNlQuery(e.target.value)}
                  placeholder="e.g. 'find what causes customer churn' or 'which features predict crop yield best'"
                  onKeyDown={e => e.key === 'Enter' && handleNLInterpret()}
                  style={{ flex: 1 }}
                />
                <button
                  id="nl-interpret-btn"
                  className="btn btn-secondary"
                  onClick={handleNLInterpret}
                  disabled={nlLoading || !nlQuery.trim()}
                >
                  {nlLoading ? <span className="spin" style={{ display: 'inline-block', width: 14, height: 14, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'var(--accent-violet)', borderRadius: '50%' }} /> : <Sparkles size={14} />}
                  {nlLoading ? 'Interpreting...' : 'Interpret'}
                </button>
              </div>

              {nlResult && (
                <div className="fade-in" style={{
                  marginTop: 'var(--space-3)',
                  padding: 'var(--space-4)',
                  background: 'var(--accent-violet-dim)',
                  border: '1px solid var(--accent-violet-mid)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: 12,
                }}>
                  <div className="flex gap-4 items-center" style={{ marginBottom: 'var(--space-2)' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Target detected:</span>
                    <span className="pill pill-violet">{nlResult.target_column}</span>
                    <span className="pill pill-cyan">{nlResult.task_type}</span>
                    <span className={`pill ${nlResult.confidence === 'high' ? 'pill-green' : nlResult.confidence === 'medium' ? 'pill-amber' : 'pill-rose'}`}>
                      {nlResult.confidence} confidence
                    </span>
                  </div>
                  <div style={{ color: 'var(--text-secondary)' }}>
                    <Info size={12} style={{ display: 'inline', marginRight: 4 }} />
                    {nlResult.explanation}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── Target Configuration ── */}
      {profile && (
        <div className="card" style={{ padding: 'var(--space-6)', marginBottom: 'var(--space-5)' }}>
          <div className="section-header">
            <Eye size={16} color="var(--accent-green)" />
            <span className="section-title">Target Variable & Task Setup</span>
            <div className="flex gap-2" style={{ marginLeft: 'auto' }}>
              <span className="pill pill-cyan">{profile.num_rows?.toLocaleString()} rows</span>
              <span className="pill pill-neutral">{profile.num_cols} cols</span>
            </div>
          </div>

          <div className="grid-3" style={{ marginBottom: 'var(--space-5)' }}>
            {/* Target column selector */}
            <div>
              <div className="label">Target Column (Dependent Variable)</div>
              <select
                id="target-select"
                className="select"
                value={selectedTarget}
                onChange={e => {
                  setSelectedTarget(e.target.value);
                  const cp = profile.column_profiles[e.target.value];
                  setTaskType(cp?.is_numeric && cp?.unique_count > 10 ? 'regression' : 'classification');
                }}
              >
                {activeColumns.map(col => (
                  <option key={col} value={col}>
                    {col} ({profile.column_profiles[col]?.dtype}, {profile.column_profiles[col]?.unique_count} unique)
                  </option>
                ))}
              </select>
            </div>

            {/* Task type */}
            <div>
              <div className="label">Task Type</div>
              <select id="task-select" className="select" value={taskType} onChange={e => setTaskType(e.target.value)}>
                <option value="classification">Classification (Binary / Multi-class)</option>
                <option value="regression">Regression (Continuous Target)</option>
              </select>
            </div>

            {/* Domain context */}
            <div>
              <div className="label">Investigation Focus (Optional)</div>
              <input
                id="domain-input"
                className="input"
                value={domainContext}
                onChange={e => setDomainContext(e.target.value)}
                placeholder="e.g. key risk factors for churn..."
              />
            </div>
          </div>

          {/* ── Column Profile Cards ── */}
          <div className="label" style={{ marginBottom: 'var(--space-3)' }}>
            Column Profiles
            {activeColumns.length > 12 && (
              <button onClick={() => setShowAllColumns(!showAllColumns)} className="btn btn-ghost" style={{ marginLeft: 'var(--space-2)', fontSize: 10 }}>
                {showAllColumns ? `Show less` : `+${activeColumns.length - 12} more`}
              </button>
            )}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 'var(--space-2)' }}>
            {visibleColumns.map(col => {
              const cp = profile.column_profiles[col];
              const isTarget = col === selectedTarget;
              const isNum = cp?.is_numeric;
              const hist = cp?.histogram || [];
              const maxCount = hist.length ? Math.max(...hist.map(h => h.count), 1) : 1;
              const topCats = cp?.top_categories ? Object.entries(cp.top_categories) : [];

              return (
                <div
                  key={col}
                  id={`col-card-${col}`}
                  className={`col-card ${isTarget ? 'selected' : ''}`}
                  onClick={() => {
                    setSelectedTarget(col);
                    setTaskType(cp?.is_numeric && cp?.unique_count > 10 ? 'regression' : 'classification');
                  }}
                  title={`Click to set as target\n${cp?.dtype} | ${cp?.unique_count} unique | ${cp?.missing_pct}% missing`}
                >
                  {/* Target indicator */}
                  {isTarget && (
                    <div style={{ position: 'absolute', top: 6, right: 6 }}>
                      <CheckCircle2 size={12} color="var(--accent-violet)" />
                    </div>
                  )}

                  <div className="col-name" title={col}>{col}</div>

                  <div className="flex gap-1" style={{ marginTop: 'var(--space-1)', flexWrap: 'wrap' }}>
                    <span className={`col-type-pill ${isNum ? 'col-type-num' : 'col-type-cat'}`}>
                      {isNum ? 'num' : 'cat'}
                    </span>
                    <span style={{ fontSize: 9, color: 'var(--text-tertiary)' }}>
                      {cp?.unique_count}u
                    </span>
                  </div>

                  {/* Sparkline */}
                  {isNum && hist.length > 0 ? (
                    <div className="col-sparkline">
                      {hist.map((h, i) => (
                        <div
                          key={i}
                          className="col-sparkline-bar"
                          style={{
                            height: `${Math.max(10, (h.count / maxCount) * 100)}%`,
                            background: isTarget ? 'var(--accent-violet)' : 'var(--accent-cyan)',
                          }}
                        />
                      ))}
                    </div>
                  ) : topCats.length > 0 ? (
                    <div style={{ marginTop: 'var(--space-1)' }}>
                      {topCats.slice(0, 2).map(([k, v]) => (
                        <div key={k} style={{ fontSize: 9, color: 'var(--text-tertiary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {String(k).slice(0, 14)}: {v}
                        </div>
                      ))}
                    </div>
                  ) : null}

                  {cp?.missing_pct > 0 && (
                    <div style={{ fontSize: 9, color: 'var(--accent-amber)', marginTop: 2 }}>
                      {cp.missing_pct}% missing
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Leakage warnings */}
          {profile.leakage_warnings?.length > 0 && (
            <div style={{
              marginTop: 'var(--space-4)',
              padding: 'var(--space-3) var(--space-4)',
              background: 'var(--accent-amber-dim)',
              border: '1px solid rgba(245,158,11,0.3)',
              borderRadius: 'var(--radius-md)',
              fontSize: 12,
            }}>
              <div style={{ color: 'var(--accent-amber)', fontWeight: 600, marginBottom: 4 }}>⚠ Data Leakage Warnings</div>
              {profile.leakage_warnings.map((w, i) => (
                <div key={i} style={{ color: 'var(--text-secondary)', fontSize: 11 }}>• {w}</div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Data Preview Table ── */}
      {profile?.preview_rows?.length > 0 && (
        <div className="card" style={{ padding: 'var(--space-6)', marginBottom: 'var(--space-5)' }}>
          <div className="section-header">
            <Table size={16} color="var(--accent-purple)" />
            <span className="section-title">Dataset Preview (first 5 rows)</span>
            <span className="pill pill-neutral" style={{ marginLeft: 'auto', fontSize: 10 }}>
              {profile.num_rows?.toLocaleString()} total rows
            </span>
          </div>
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  {activeColumns.map(col => (
                    <th key={col} className={col === selectedTarget ? 'target-col' : ''}>
                      {col}{col === selectedTarget ? ' ▸' : ''}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {profile.preview_rows.slice(0, 5).map((row, i) => (
                  <tr key={i}>
                    {activeColumns.map(col => (
                      <td key={col}>{String(row[col] ?? '—')}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Loading skeleton when profiling ── */}
      {loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', marginBottom: 'var(--space-5)' }}>
          <div className="skeleton" style={{ height: 200 }} />
          <div className="skeleton" style={{ height: 120 }} />
        </div>
      )}

      {/* ── Launch Button ── */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
        {selectedTarget && profile && (
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', alignSelf: 'center' }}>
            Ready: targeting <span style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>{selectedTarget}</span> via <span style={{ color: 'var(--accent-violet)' }}>{selectedLLM}</span>
          </div>
        )}
        <button
          id="launch-btn"
          className="btn btn-primary btn-lg"
          onClick={handleLaunch}
          disabled={!activeFile || !selectedTarget || loading}
        >
          <Sparkles size={16} />
          Run Autonomous AI Scientist
        </button>
      </div>
    </div>
  );
}
