import React, { useState } from 'react';
import {
  AlertTriangle, Upload, CheckCircle2, XCircle, ArrowRight,
  Database, Sparkles, X, ShieldAlert, FileText, SkipForward
} from 'lucide-react';

const API = 'http://127.0.0.1:5050';

export default function DataGapModal({ gap, sessionId, isOpen, onClose, onDataProvided, onSkipped }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [skipping, setSkipping] = useState(false);

  if (!isOpen || !gap) return null;

  const isCritical = gap.priority === 'CRITICAL';
  const expectedCols = gap.example_csv_columns || [];

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.name.endsWith('.csv')) {
      setFile(droppedFile);
      setValidationResult(null);
    }
  };

  const handleFileInput = (e) => {
    const selected = e.target.files[0];
    if (selected && selected.name.endsWith('.csv')) {
      setFile(selected);
      setValidationResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setValidationResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API}/api/provide-data/${sessionId}`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();

      if (data.success) {
        setValidationResult({ success: true, message: data.message });
        setTimeout(() => {
          onDataProvided && onDataProvided(data);
          onClose();
        }, 1200);
      } else {
        setValidationResult({
          success: false,
          message: data.message || 'Validation failed. The CSV does not contain the required columns.',
        });
      }
    } catch (err) {
      setValidationResult({ success: false, message: 'Upload error: ' + err.message });
    } finally {
      setUploading(false);
    }
  };

  const handleSkip = async () => {
    if (isCritical) return; // Cannot skip critical gaps
    setSkipping(true);
    try {
      const res = await fetch(`${API}/api/skip-data-request/${sessionId}`);
      const data = await res.json();
      onSkipped && onSkipped(data);
      onClose();
    } catch (err) {
      alert('Could not skip gap: ' + err.message);
    } finally {
      setSkipping(false);
    }
  };

  return (
    <div className="modal-backdrop fade-in">
      <div className={`data-gap-modal card ${isCritical ? 'critical' : 'important'}`}>
        {/* Header */}
        <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-4)' }}>
          <div className="flex items-center gap-2">
            {isCritical ? (
              <ShieldAlert size={20} color="var(--accent-rose)" />
            ) : (
              <AlertTriangle size={20} color="var(--accent-amber)" />
            )}
            <span style={{ fontSize: 16, fontWeight: 800 }}>
              {isCritical ? 'Critical Data Request' : 'Supplemental Data Request'}
            </span>
            <span className={`pill ${isCritical ? 'pill-rose' : 'pill-amber'}`}>
              {gap.priority}
            </span>
          </div>

          {!isCritical && (
            <button className="btn btn-ghost" onClick={onClose} style={{ padding: 4 }}>
              <X size={16} />
            </button>
          )}
        </div>

        {/* Gap Description */}
        <div style={{ marginBottom: 'var(--space-4)' }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6 }}>
            {gap.title}
          </div>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 8 }}>
            <strong>Why it matters:</strong> {gap.why_it_matters}
          </p>
          <div className="impact-box" style={{
            background: isCritical ? 'rgba(244,63,94,0.1)' : 'rgba(245,158,11,0.1)',
            borderLeft: `3px solid ${isCritical ? 'var(--accent-rose)' : 'var(--accent-amber)'}`,
            padding: '8px 12px',
            borderRadius: '0 6px 6px 0',
            fontSize: 11,
            color: 'var(--text-secondary)'
          }}>
            <strong>Impact if absent:</strong> {gap.impact_if_absent}
          </div>
        </div>

        {/* Expected Schema */}
        {expectedCols.length > 0 && (
          <div style={{ marginBottom: 'var(--space-4)' }}>
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-secondary)', marginBottom: 6 }}>
              Expected CSV Columns:
            </div>
            <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
              {expectedCols.map((col) => (
                <span key={col} className="pill pill-cyan" style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>
                  {col}
                </span>
              ))}
            </div>
            {gap.example_description && (
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>
                {gap.example_description}
              </div>
            )}
          </div>
        )}

        {/* Upload Zone */}
        <div
          className={`drop-zone ${isDragOver ? 'drag-over' : ''}`}
          style={{ minHeight: 110, padding: 'var(--space-3)', marginBottom: 'var(--space-4)' }}
          onDrop={handleDrop}
          onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
          onClick={() => document.getElementById('supplemental-file-input').click()}
        >
          <input
            id="supplemental-file-input"
            type="file"
            accept=".csv"
            style={{ display: 'none' }}
            onChange={handleFileInput}
          />
          <Upload size={22} color={isDragOver ? 'var(--accent-violet)' : 'var(--text-secondary)'} />
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>
            {file ? file.name : 'Drop supplemental CSV here or click to browse'}
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>
            Must contain matching keys (e.g. state, year, id) to join with original data
          </div>
        </div>

        {/* Validation Feedback */}
        {validationResult && (
          <div style={{
            padding: '10px 14px',
            borderRadius: 'var(--radius-md)',
            marginBottom: 'var(--space-4)',
            fontSize: 12,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            background: validationResult.success ? 'var(--accent-green-dim)' : 'var(--accent-rose-dim)',
            border: `1px solid ${validationResult.success ? 'var(--accent-green-mid)' : 'rgba(244,63,94,0.3)'}`,
            color: validationResult.success ? 'var(--accent-green)' : 'var(--accent-rose)',
          }}>
            {validationResult.success ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
            <span>{validationResult.message}</span>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between" style={{ marginTop: 'var(--space-4)' }}>
          <div>
            {!isCritical ? (
              <button
                className="btn btn-secondary"
                onClick={handleSkip}
                disabled={skipping || uploading}
                style={{ fontSize: 12 }}
              >
                <SkipForward size={14} />
                {skipping ? 'Skipping...' : 'Skip this request'}
              </button>
            ) : (
              <span style={{ fontSize: 10, color: 'var(--accent-rose)', fontWeight: 600 }}>
                * Critical gaps must be provided or waited out
              </span>
            )}
          </div>

          <div className="flex gap-2">
            <button
              className="btn btn-primary"
              onClick={handleUpload}
              disabled={!file || uploading}
              style={{ fontSize: 12 }}
            >
              {uploading ? (
                <>
                  <span className="spin" style={{ width: 12, height: 12, border: '2px solid #fff', borderTopColor: 'transparent', borderRadius: '50%' }} />
                  Validating & Merging...
                </>
              ) : (
                <>
                  <Sparkles size={14} />
                  Validate & Merge Data
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
