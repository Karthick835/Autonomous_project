import React, { useState } from 'react';
import { GitCompare, Upload, Sparkles, CheckCircle, AlertCircle, ArrowRight } from 'lucide-react';

const API = 'http://127.0.0.1:5050';

export default function CompareUpload() {
  const [fileA, setFileA] = useState(null);
  const [fileB, setFileB] = useState(null);
  const [nameA, setNameA] = useState('');
  const [nameB, setNameB] = useState('');
  const [domainContext, setDomainContext] = useState('');
  const [llmModel, setLlmModel] = useState('gemini');
  const [loading, setLoading] = useState(false);
  const [comparison, setComparison] = useState(null);
  const [error, setError] = useState('');
  const [isDragA, setIsDragA] = useState(false);
  const [isDragB, setIsDragB] = useState(false);

  const uploadFile = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API}/api/upload`, { method: 'POST', body: formData });
    const data = await res.json();
    return data.filename;
  };

  const handleFileA = async (file) => {
    if (!file?.name.endsWith('.csv')) return;
    const fn = await uploadFile(file);
    setFileA(fn);
    setNameA(file.name);
  };

  const handleFileB = async (file) => {
    if (!file?.name.endsWith('.csv')) return;
    const fn = await uploadFile(file);
    setFileB(fn);
    setNameB(file.name);
  };

  const handleDropA = (e) => { e.preventDefault(); setIsDragA(false); handleFileA(e.dataTransfer.files[0]); };
  const handleDropB = (e) => { e.preventDefault(); setIsDragB(false); handleFileB(e.dataTransfer.files[0]); };

  const handleCompare = async () => {
    if (!fileA || !fileB) return setError('Please upload both datasets first.');
    setLoading(true);
    setError('');
    setComparison(null);

    try {
      // Start comparison
      const startRes = await fetch(`${API}/api/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          csv_filename_a: fileA,
          csv_filename_b: fileB,
          domain_context: domainContext,
          llm_model: llmModel,
        }),
      });
      const startData = await startRes.json();
      if (startData.detail) throw new Error(startData.detail);

      const sessionId = startData.session_id;

      // Stream events until COMPLETE
      const eventSource = new EventSource(`${API}/api/stream/${sessionId}`);
      await new Promise((resolve, reject) => {
        eventSource.onmessage = (e) => {
          const data = JSON.parse(e.data);
          if (data.stage === 'COMPLETE') { eventSource.close(); resolve(); }
          if (data.stage === 'ERROR') { eventSource.close(); reject(new Error(data.message)); }
        };
        eventSource.onerror = () => { eventSource.close(); reject(new Error('Stream error')); };
        setTimeout(() => { eventSource.close(); reject(new Error('Timeout')); }, 300000);
      });

      // Fetch results
      const resultsRes = await fetch(`${API}/api/results/${sessionId}`);
      const resultsData = await resultsRes.json();
      setComparison(resultsData.results?.comparison);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const DropZoneCard = ({ label, name, isDrag, onDrop, onDragOver, onDragLeave, inputId, onChange }) => (
    <div>
      <div className="label">{label}</div>
      <div
        className={`drop-zone ${isDrag ? 'drag-over' : ''}`}
        style={{ minHeight: 140 }}
        onDrop={onDrop}
        onDragOver={(e) => { e.preventDefault(); onDragOver(); }}
        onDragLeave={onDragLeave}
        onClick={() => document.getElementById(inputId).click()}
      >
        <input id={inputId} type="file" accept=".csv" style={{ display: 'none' }} onChange={e => onChange(e.target.files[0])} />
        {name ? (
          <>
            <CheckCircle size={24} color="var(--accent-green)" />
            <div style={{ fontWeight: 600, color: 'var(--accent-green)', fontSize: 13 }}>{name}</div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Click to replace</div>
          </>
        ) : (
          <>
            <Upload size={24} color={isDrag ? 'var(--accent-violet)' : 'var(--text-secondary)'} />
            <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>Drop {label} here</div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>.csv files only</div>
          </>
        )}
      </div>
    </div>
  );

  return (
    <div className="fade-in" style={{ maxWidth: 1080, margin: '0 auto' }}>
      <div className="card" style={{ padding: 'var(--space-6)', marginBottom: 'var(--space-5)' }}>
        <div className="section-header">
          <GitCompare size={16} color="var(--accent-violet)" />
          <span className="section-title">Multi-Dataset Comparison</span>
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 'var(--space-5)' }}>
          Upload two CSV datasets. The system runs the same hypothesis suite on both and cross-validates which findings replicate.
        </div>

        <div className="grid-2" style={{ marginBottom: 'var(--space-4)' }}>
          <DropZoneCard
            label="Dataset A"
            name={nameA}
            isDrag={isDragA}
            onDrop={handleDropA}
            onDragOver={() => setIsDragA(true)}
            onDragLeave={() => setIsDragA(false)}
            inputId="file-a"
            onChange={handleFileA}
          />
          <DropZoneCard
            label="Dataset B"
            name={nameB}
            isDrag={isDragB}
            onDrop={handleDropB}
            onDragOver={() => setIsDragB(true)}
            onDragLeave={() => setIsDragB(false)}
            inputId="file-b"
            onChange={handleFileB}
          />
        </div>

        <div className="grid-2" style={{ marginBottom: 'var(--space-4)' }}>
          <div>
            <div className="label">Investigation Focus</div>
            <input
              className="input"
              value={domainContext}
              onChange={e => setDomainContext(e.target.value)}
              placeholder="Optional: describe what you're comparing..."
            />
          </div>
          <div>
            <div className="label">LLM Model</div>
            <select className="select" value={llmModel} onChange={e => setLlmModel(e.target.value)}>
              <option value="gemini">Gemini 2.5 Flash</option>
              <option value="gpt4o">GPT-4o</option>
              <option value="claude">Claude 3.5 Sonnet</option>
            </select>
          </div>
        </div>

        {error && (
          <div style={{
            padding: 'var(--space-3)',
            background: 'var(--accent-rose-dim)',
            border: '1px solid var(--accent-rose-mid)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--accent-rose)',
            fontSize: 12,
            marginBottom: 'var(--space-4)',
          }}>
            <AlertCircle size={12} style={{ display: 'inline', marginRight: 6 }} />
            {error}
          </div>
        )}

        <div style={{ textAlign: 'right' }}>
          <button
            id="compare-btn"
            className={`btn btn-primary btn-lg ${loading ? 'investigating' : ''}`}
            onClick={handleCompare}
            disabled={!fileA || !fileB || loading}
          >
            {loading ? (
              <>
                <span className="spin" style={{ display: 'inline-block', width: 14, height: 14, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', borderRadius: '50%' }} />
                Comparing datasets...
              </>
            ) : (
              <><Sparkles size={16} /> Run Comparison</>
            )}
          </button>
        </div>
      </div>

      {/* Comparison Results */}
      {comparison && (
        <div className="fade-in stagger">
          {/* Cross-validated row */}
          <div className="grid-3" style={{ marginBottom: 'var(--space-5)' }}>
            <div className="stat-card">
              <div className="stat-card-label">Cross-Validated (Both)</div>
              <div className="stat-card-value confirmed">{comparison.total_replicated}</div>
            </div>
            <div className="stat-card">
              <div className="stat-card-label">Dataset A Only</div>
              <div className="stat-card-value cyan">{comparison.dataset_a_only?.length || 0}</div>
            </div>
            <div className="stat-card">
              <div className="stat-card-label">Dataset B Only</div>
              <div className="stat-card-value amber">{comparison.dataset_b_only?.length || 0}</div>
            </div>
          </div>

          {/* Cross-validated findings */}
          {comparison.cross_validated?.length > 0 && (
            <div className="card" style={{ padding: 'var(--space-5)', marginBottom: 'var(--space-4)' }}>
              <div className="section-header">
                <CheckCircle size={16} color="var(--accent-green)" />
                <span className="section-title">Cross-Validated Discoveries (Replicated in Both)</span>
              </div>
              {comparison.cross_validated.map((item, i) => (
                <div key={i} style={{
                  padding: 'var(--space-4)',
                  background: 'var(--accent-green-dim)',
                  border: '1px solid var(--accent-green-mid)',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: 'var(--space-3)',
                }}>
                  <div style={{ fontWeight: 600, color: 'var(--accent-green)', marginBottom: 'var(--space-2)' }}>
                    {item.title}
                  </div>
                  <div className="grid-2" style={{ fontSize: 12 }}>
                    <div style={{ color: 'var(--text-secondary)' }}>
                      Dataset A: p={item.dataset_a.p_value.toFixed(4)}, effect={item.dataset_a.effect_size.toFixed(3)}
                    </div>
                    <div style={{ color: 'var(--text-secondary)' }}>
                      Dataset B: p={item.dataset_b.p_value.toFixed(4)}, effect={item.dataset_b.effect_size.toFixed(3)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* A-only */}
          {comparison.dataset_a_only?.length > 0 && (
            <div className="card" style={{ padding: 'var(--space-5)', marginBottom: 'var(--space-4)' }}>
              <div className="section-header">
                <ArrowRight size={16} color="var(--accent-cyan)" />
                <span className="section-title">Dataset A Only</span>
              </div>
              {comparison.dataset_a_only.map((f, i) => (
                <div key={i} style={{
                  padding: 'var(--space-3)',
                  background: 'var(--accent-cyan-dim)',
                  border: '1px solid var(--accent-cyan-mid)',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: 'var(--space-2)',
                  fontSize: 13,
                }}>
                  {f.title} — p={f.p_value.toFixed(4)}, effect={f.effect_size.toFixed(3)}
                </div>
              ))}
            </div>
          )}

          {/* B-only */}
          {comparison.dataset_b_only?.length > 0 && (
            <div className="card" style={{ padding: 'var(--space-5)' }}>
              <div className="section-header">
                <ArrowRight size={16} color="var(--accent-amber)" />
                <span className="section-title">Dataset B Only</span>
              </div>
              {comparison.dataset_b_only.map((f, i) => (
                <div key={i} style={{
                  padding: 'var(--space-3)',
                  background: 'var(--accent-amber-dim)',
                  border: '1px solid rgba(245,158,11,0.3)',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: 'var(--space-2)',
                  fontSize: 13,
                }}>
                  {f.title} — p={f.p_value.toFixed(4)}, effect={f.effect_size.toFixed(3)}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
