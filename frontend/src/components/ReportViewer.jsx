import React from 'react';
import { Award, CheckCircle2, XCircle, Download, FileCode, BarChart3, Activity } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import ReactMarkdown from 'react-markdown';

export default function ReportViewer({ results, sessionId }) {
  if (!results) return null;

  const { validation, profile, dataset_name, markdown_report } = results;
  const confirmed = validation.findings.filter(f => f.status === 'CONFIRMED_DISCOVERY');

  const handleDownloadNotebook = () => {
    window.open(`http://127.0.0.1:5050/api/download-notebook/${sessionId}`, '_blank');
  };





  // Prepare chart data from tested hypotheses
  const chartData = validation.findings.map(f => ({
    name: f.hypothesis_id,
    title: f.title.length > 25 ? f.title.substring(0, 22) + '...' : f.title,
    effect_size: parseFloat(f.effect_size.toFixed(3)),
    p_value: parseFloat(f.p_value.toFixed(4)),
    metric: f.effect_size_metric || 'Effect',
    isConfirmed: f.status === 'CONFIRMED_DISCOVERY'
  }));

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
      {/* Header Bar */}
      <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <Award size={22} color="#10b981" />
            <h1 style={{ fontSize: '1.4rem', fontWeight: 700 }}>Scientific Research Findings: `{dataset_name}`</h1>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Target Outcome: <code style={{ color: '#10b981' }}>{profile.active_target}</code> ({profile.active_task}) | Validated via Benjamini-Hochberg FDR (α = {validation.fdr_alpha_used})
          </p>
        </div>

        <button onClick={handleDownloadNotebook} className="btn-primary" style={{ background: 'linear-gradient(135deg, #059669, #10b981)' }}>
          <Download size={18} />
          Download Executable Notebook (.ipynb)
        </button>
      </div>

      {/* Metric Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <div className="glass-panel" style={{ padding: '16px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>CONFIRMED DISCOVERIES</span>
          <span style={{ fontSize: '1.8rem', fontWeight: 800, color: '#10b981' }}>{validation.confirmed_discoveries}</span>
        </div>
        <div className="glass-panel" style={{ padding: '16px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>TOTAL HYPOTHESES TESTED</span>
          <span style={{ fontSize: '1.8rem', fontWeight: 800, color: '#38bdf8' }}>{validation.total_tested}</span>
        </div>
        <div className="glass-panel" style={{ padding: '16px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>REJECTED / INSUFFICIENT</span>
          <span style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f43f5e' }}>{validation.rejected_count}</span>
        </div>
        <div className="glass-panel" style={{ padding: '16px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>FDR GUARDRAIL ALPHA</span>
          <span style={{ fontSize: '1.8rem', fontWeight: 800, color: '#a855f7' }}>{validation.fdr_alpha_used}</span>
        </div>
      </div>

      {/* Interactive Recharts Visualization */}
      <div className="glass-panel" style={{ padding: '24px', marginBottom: '28px' }}>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <BarChart3 size={20} color="#6366f1" />
          Effect Size Comparison Across Tested Hypotheses
        </h2>

        <div style={{ width: '100%', height: 260 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
              <XAxis dataKey="title" stroke="#9ca3af" fontSize={11} interval={0} angle={-15} textAnchor="end" />
              <YAxis stroke="#9ca3af" fontSize={11} label={{ value: 'Effect Magnitude', angle: -90, position: 'insideLeft', fill: '#9ca3af', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#090d16', border: '1px solid #374151', borderRadius: '8px', color: '#fff', fontSize: '0.85rem' }}
                formatter={(val, name, props) => [`${val} (${props.payload.metric})`, 'Effect Size']}
              />
              <Bar dataKey="effect_size" radius={[6, 6, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.isConfirmed ? '#10b981' : '#64748b'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Confirmed Discoveries Section */}
      <div style={{ marginBottom: '28px' }}>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle2 size={20} color="#10b981" />
          Confirmed Scientific Discoveries
        </h2>

        {confirmed.length === 0 ? (
          <div className="glass-panel" style={{ padding: '20px', color: 'var(--text-muted)' }}>
            No hypotheses met both FDR significance and effect size cutoffs.
          </div>
        ) : (
          confirmed.map((f, i) => (
            <div key={i} className="glass-panel" style={{ padding: '18px', marginBottom: '14px', borderLeft: '4px solid #10b981' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', color: '#a855f7', fontWeight: 600 }}>{f.category}</span>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 600, marginTop: '2px' }}>{f.title}</h3>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <span className="badge confirmed">FDR Significance Passed</span>
                  <span className="badge confirmed">{f.effect_size_metric}: {f.effect_size.toFixed(3)}</span>
                </div>
              </div>

              <p style={{ color: 'var(--text-main)', fontSize: '0.9rem', marginBottom: '12px' }}>{f.summary}</p>

              <div style={{ background: '#090d16', padding: '10px 14px', borderRadius: '6px', fontSize: '0.8rem', display: 'flex', gap: '20px', color: 'var(--text-muted)' }}>
                <span>P-Value: <strong style={{ color: '#10b981' }}>{f.p_value.toFixed(5)}</strong></span>
                {f.details.group0_mean !== undefined && (
                  <>
                    <span>Group '{f.details.group0_label || '0'}': <strong>{f.details.group0_mean}</strong></span>
                    <span>Group '{f.details.group1_label || '1'}': <strong>{f.details.group1_mean}</strong></span>
                    <span>Difference: <strong style={{ color: '#38bdf8' }}>{f.details.difference}</strong></span>
                  </>
                )}
                {f.details.top_features && (
                  <span>Top Feature: <strong style={{ color: '#a855f7' }}>{Object.keys(f.details.top_features)[0]}</strong></span>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Formatted Markdown Executive Report */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileCode size={20} color="#38bdf8" />
          Full Executive Markdown Report
        </h2>
        <div className="markdown-body" style={{ lineHeight: '1.6', fontSize: '0.9rem', color: '#e5e7eb' }}>
          <ReactMarkdown>{markdown_report}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

