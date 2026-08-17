import React, { useState, useEffect } from 'react';
import { Database, Upload, Sparkles, FileText, CheckCircle2, Table, Eye, Layers } from 'lucide-react';

export default function DatasetUpload({ onStartInvestigation }) {
  const [samples, setSamples] = useState([]);
  const [selectedSample, setSelectedSample] = useState('');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [domainContext, setDomainContext] = useState('Explore key risk factors and predictive drivers');
  const [profile, setProfile] = useState(null);
  const [selectedTarget, setSelectedTarget] = useState('');
  const [taskType, setTaskType] = useState('auto');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch('http://127.0.0.1:5050/api/sample-datasets')
      .then(res => res.json())
      .then(data => {
        if (data.samples && data.samples.length > 0) {
          setSamples(data.samples);
          const firstSample = data.samples[0].name;
          setSelectedSample(firstSample);
          fetchPreview(firstSample);
        }
      })
      .catch(err => console.error("Failed loading samples:", err));
  }, []);

  const fetchPreview = (filename) => {
    fetch(`http://127.0.0.1:5050/api/dataset-preview/${filename}`)
      .then(res => res.json())
      .then(data => {
        if (data.profile) {
          setProfile(data.profile);
          if (data.profile.active_target) {
            setSelectedTarget(data.profile.active_target);
          }
          if (data.profile.active_task) {
            setTaskType(data.profile.active_task);
          }
        }
      })
      .catch(err => console.error("Failed loading dataset preview:", err));
  };

  const handleSelectSample = (sampleName) => {
    setSelectedSample(sampleName);
    setUploadedFile(null);
    fetchPreview(sampleName);
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file && file.name.endsWith('.csv')) {
      const formData = new FormData();
      formData.append('file', file);
      setLoading(true);
      fetch('http://127.0.0.1:5050/api/upload', {




        method: 'POST',
        body: formData
      })
        .then(res => res.json())
        .then(data => {
          setUploadedFile(data.filename);
          setSelectedSample('');
          if (data.profile) {
            setProfile(data.profile);
            if (data.profile.active_target) setSelectedTarget(data.profile.active_target);
            if (data.profile.active_task) setTaskType(data.profile.active_task);
          }
          setLoading(false);
        })
        .catch(err => {
          alert('Upload failed: ' + err);
          setLoading(false);
        });
    }
  };

  const handleLaunch = () => {
    const targetFile = uploadedFile || selectedSample;
    if (!targetFile) {
      alert("Please select or upload a dataset first.");
      return;
    }
    onStartInvestigation(targetFile, domainContext, selectedTarget, taskType);
  };

  const activeColumns = profile ? Object.keys(profile.column_profiles || {}) : [];

  return (
    <div className="glass-panel" style={{ padding: '28px', maxWidth: '1050px', margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
        <div style={{ padding: '10px', background: 'rgba(99, 102, 241, 0.15)', borderRadius: '10px', color: '#818cf8' }}>
          <Database size={24} />
        </div>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600 }}>1. Dataset Selection & Target Definition</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Upload your dataset, inspect data structure, and configure your target variable.</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
        {/* Preloaded Datasets */}
        <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <h3 style={{ fontSize: '0.9rem', marginBottom: '10px', color: 'var(--text-muted)' }}>Preloaded Datasets</h3>
          {samples.map(s => (
            <div
              key={s.name}
              onClick={() => handleSelectSample(s.name)}
              style={{
                padding: '10px 12px',
                borderRadius: '6px',
                cursor: 'pointer',
                background: selectedSample === s.name ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
                border: selectedSample === s.name ? '1px solid #6366f1' : '1px solid transparent',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '6px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FileText size={16} color="#38bdf8" />
                <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>{s.name}</span>
              </div>
              {selectedSample === s.name && <CheckCircle2 size={16} color="#10b981" />}
            </div>
          ))}
        </div>

        {/* Upload Custom CSV */}
        <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '16px', borderRadius: '8px', border: '1px dashed var(--border-color)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <Upload size={28} color="#9ca3af" style={{ marginBottom: '8px' }} />
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '10px' }}>Upload Custom `.csv` Dataset</p>
          <input type="file" accept=".csv" onChange={handleFileUpload} id="csv-upload" style={{ display: 'none' }} />
          <label htmlFor="csv-upload" className="btn-secondary" style={{ cursor: 'pointer' }}>
            {loading ? 'Uploading & Profiling...' : 'Browse CSV File'}
          </label>
          {uploadedFile && (
            <span style={{ fontSize: '0.75rem', color: '#10b981', marginTop: '8px' }}>Uploaded: {uploadedFile}</span>
          )}
        </div>
      </div>

      {/* Target Column & Task Configuration */}
      {profile && (
        <div style={{ background: '#090d16', padding: '18px', borderRadius: '8px', border: '1px solid var(--border-color)', marginBottom: '20px' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={18} color="#38bdf8" />
            Target Variable & Modeling Task Setup
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>Target Column (Dependent Variable)</label>
              <select
                value={selectedTarget}
                onChange={(e) => setSelectedTarget(e.target.value)}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: '6px',
                  background: '#111827',
                  border: '1px solid var(--border-color)',
                  color: '#fff',
                  fontSize: '0.85rem'
                }}
              >
                {activeColumns.map(col => (
                  <option key={col} value={col}>
                    {col} ({profile.column_profiles[col]?.dtype}, {profile.column_profiles[col]?.unique_count} unique)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>Task Type</label>
              <select
                value={taskType}
                onChange={(e) => setTaskType(e.target.value)}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: '6px',
                  background: '#111827',
                  border: '1px solid var(--border-color)',
                  color: '#fff',
                  fontSize: '0.85rem'
                }}
              >
                <option value="classification">Classification (Binary / Multi-class)</option>
                <option value="regression">Continuous Regression (Numeric target)</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>Dataset Dimensions</label>
              <div style={{ padding: '9px 12px', background: '#111827', borderRadius: '6px', fontSize: '0.85rem', color: '#10b981', fontWeight: 600 }}>
                {profile.num_rows} Rows × {profile.num_cols} Columns
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Dataset Table Preview */}
      {profile && profile.preview_rows && profile.preview_rows.length > 0 && (
        <div style={{ background: '#090d16', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Table size={18} color="#a855f7" />
            <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>Dataset Table Preview (First 5 Rows)</span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ background: 'rgba(255,255,255,0.05)', borderBottom: '1px solid var(--border-color)' }}>
                  {activeColumns.map(col => (
                    <th key={col} style={{ padding: '8px 10px', color: col === selectedTarget ? '#10b981' : 'var(--text-muted)' }}>
                      {col} {col === selectedTarget && '(Target)'}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {profile.preview_rows.slice(0, 5).map((row, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    {activeColumns.map(col => (
                      <td key={col} style={{ padding: '8px 10px', whiteSpace: 'nowrap' }}>
                        {String(row[col] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Domain Context Input */}
      <div style={{ marginBottom: '24px' }}>
        <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '6px' }}>Domain Context / Scientific Question (Optional)</label>
        <input
          type="text"
          value={domainContext}
          onChange={(e) => setDomainContext(e.target.value)}
          placeholder="e.g. Find key risk factors predicting disease progression or customer churn..."
          style={{
            width: '100%',
            padding: '10px 14px',
            borderRadius: '8px',
            background: '#090d16',
            border: '1px solid var(--border-color)',
            color: '#fff',
            fontFamily: 'inherit',
            fontSize: '0.9rem'
          }}
        />
      </div>

      <div style={{ textAlign: 'right' }}>
        <button onClick={handleLaunch} className="btn-primary">
          <Sparkles size={18} />
          Run Autonomous AI Scientist
        </button>
      </div>
    </div>
  );
}

