import React, { useState, useEffect, useRef } from 'react';
import {
  Award, CheckCircle2, XCircle, Download, BarChart3,
  ChevronDown, ChevronUp, FileCode, TrendingUp, AlertTriangle,
  ExternalLink, Database
} from 'lucide-react';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, Cell
} from 'recharts';
import ReactMarkdown from 'react-markdown';

const API = 'http://127.0.0.1:5050';

// Animated number counter
function CountUp({ target, decimals = 0, suffix = '' }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let start = 0;
    const steps = 40;
    const delta = target / steps;
    const timer = setInterval(() => {
      start = Math.min(start + delta, target);
      setVal(start);
      if (start >= target) clearInterval(timer);
    }, 20);
    return () => clearInterval(timer);
  }, [target]);
  return (
    <span className="count-up">
      {decimals > 0 ? val.toFixed(decimals) : Math.round(val)}{suffix}
    </span>
  );
}

// Discovery ceremony overlay
function DiscoveryCeremony({ count, onDismiss }) {
  const particles = Array.from({ length: 20 }, (_, i) => ({
    id: i,
    tx: `${(Math.random() - 0.5) * 400}px`,
    ty: `${(Math.random() - 0.5) * 400}px`,
    color: ['#7C3AED', '#06B6D4', '#10B981', '#F59E0B', '#EF4444'][i % 5],
    delay: `${Math.random() * 0.5}s`,
  }));

  return (
    <div className="ceremony-overlay" onClick={onDismiss}>
      <div className="ceremony-particles">
        {particles.map(p => (
          <div key={p.id} className="particle" style={{
            '--tx': p.tx,
            '--ty': p.ty,
            background: p.color,
            left: '50%',
            top: '50%',
            animationDelay: p.delay,
            animationDuration: `${0.8 + Math.random() * 0.6}s`,
          }} />
        ))}
      </div>
      <div className="card ceremony-card card-glow-border">
        <div className="ceremony-icon">🔬</div>
        <h2 style={{ fontSize: 26, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 'var(--space-2)' }}>
          Discovery Confirmed
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 'var(--space-6)', lineHeight: 1.6 }}>
          The Autonomous AI Scientist has identified <strong style={{ color: 'var(--accent-green)' }}>{count} statistically robust discovery(ies)</strong> that passed Benjamini-Hochberg FDR control and effect size guardrails.
        </p>
        <button className="btn btn-primary btn-lg" onClick={onDismiss}>
          View Findings →
        </button>
        <div style={{ marginTop: 'var(--space-3)', fontSize: 11, color: 'var(--text-tertiary)' }}>
          Click anywhere to dismiss
        </div>
      </div>
    </div>
  );
}

// Single hypothesis card with expand/collapse
function HypothesisCard({ finding, chartBase }) {
  const [expanded, setExpanded] = useState(false);
  const statusClass = {
    CONFIRMED_DISCOVERY: 'confirmed',
    REJECTED: 'rejected',
    WEAK_EVIDENCE: 'weak',
    VALIDATED_CONTROL: 'confirmed',
    FAILED_CONTROL: 'rejected',
  }[finding.status] || 'rejected';

  const pillClass = {
    CONFIRMED_DISCOVERY: 'pill-green',
    REJECTED: 'pill-rose',
    WEAK_EVIDENCE: 'pill-amber',
    VALIDATED_CONTROL: 'pill-cyan',
    FAILED_CONTROL: 'pill-rose',
  }[finding.status] || 'pill-neutral';

  const effectPct = Math.min(finding.effect_size * 100, 100);

  return (
    <div
      id={`finding-${finding.hypothesis_id}`}
      className={`hypothesis-card ${statusClass}`}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start justify-between gap-4">
        <div style={{ flex: 1 }}>
          <div className="flex items-center gap-2" style={{ marginBottom: 'var(--space-1)' }}>
            <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)', fontWeight: 600 }}>
              {finding.hypothesis_id}
            </span>
            <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
              {finding.category}
            </span>
          </div>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.4 }}>
            {finding.title}
          </h3>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 'var(--space-1)', lineHeight: 1.5 }}>
            {finding.summary}
          </p>

          {/* Effect size bar */}
          <div style={{ marginTop: 'var(--space-2)' }}>
            <div className="flex justify-between" style={{ marginBottom: 3, fontSize: 10, color: 'var(--text-tertiary)' }}>
              <span>{finding.effect_size_metric}</span>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                {finding.effect_size.toFixed(3)}
              </span>
            </div>
            <div className="effect-bar">
              <div
                className={`effect-bar-fill ${statusClass}`}
                style={{
                  width: `${effectPct}%`,
                  background: statusClass === 'confirmed'
                    ? 'linear-gradient(90deg, #059669, var(--accent-green))'
                    : statusClass === 'rejected'
                    ? 'linear-gradient(90deg, #DC2626, var(--accent-rose))'
                    : 'linear-gradient(90deg, #B45309, var(--accent-amber))',
                }}
              />
            </div>
          </div>
        </div>

        <div className="flex-col items-center gap-2" style={{ minWidth: 110 }}>
          <span className={`pill ${pillClass}`}>
            {finding.status === 'CONFIRMED_DISCOVERY' ? '✓ Confirmed'
             : finding.status === 'REJECTED' ? '✗ Rejected'
             : finding.status === 'WEAK_EVIDENCE' ? '~ Weak'
             : finding.status}
          </span>

          {/* P-value pill */}
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            padding: '3px 8px',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--card-border)',
            borderRadius: 'var(--radius-full)',
            color: finding.p_value < 0.05 ? 'var(--accent-green)' : 'var(--accent-rose)',
          }}>
            p={finding.p_value.toFixed(4)}
          </div>

          <button className="btn btn-ghost" style={{ fontSize: 10, padding: '4px 8px', height: 'auto' }}>
            {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            {expanded ? 'Less' : 'Details'}
          </button>
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="fade-in" style={{
          marginTop: 'var(--space-4)',
          paddingTop: 'var(--space-4)',
          borderTop: '1px solid var(--card-border)',
        }}>
          {/* Stats row */}
          <div className="flex gap-4" style={{ marginBottom: 'var(--space-4)', flexWrap: 'wrap' }}>
            {[
              { label: 'P-Value', value: finding.p_value.toFixed(5), color: finding.p_value < 0.05 ? 'var(--accent-green)' : 'var(--accent-rose)' },
              { label: 'Effect Size', value: `${finding.effect_size.toFixed(3)} (${finding.effect_size_metric})`, color: 'var(--accent-violet)' },
              { label: 'FDR Significant', value: finding.fdr_significant ? 'Yes' : 'No', color: finding.fdr_significant ? 'var(--accent-green)' : 'var(--accent-rose)' },
              ...(finding.details?.group0_mean !== undefined ? [
                { label: 'Group 0 Mean', value: String(finding.details.group0_mean), color: 'var(--accent-cyan)' },
                { label: 'Group 1 Mean', value: String(finding.details.group1_mean), color: 'var(--accent-cyan)' },
                { label: 'Difference', value: String(finding.details.difference), color: 'var(--accent-amber)' },
              ] : []),
              ...(finding.details?.correlation !== undefined ? [
                { label: 'Correlation r', value: String(finding.details.correlation), color: 'var(--accent-violet)' },
              ] : []),
              ...(finding.details?.num_groups !== undefined ? [
                { label: 'Groups', value: String(finding.details.num_groups), color: 'var(--accent-cyan)' },
              ] : []),
            ].map((s, i) => (
              <div key={i} style={{
                padding: 'var(--space-2) var(--space-3)',
                background: 'var(--bg-elevated)',
                border: '1px solid var(--card-border)',
                borderRadius: 'var(--radius-md)',
                fontSize: 12,
              }}>
                <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 2 }}>{s.label}</div>
                <div style={{ fontFamily: 'var(--font-mono)', color: s.color, fontWeight: 600 }}>{s.value}</div>
              </div>
            ))}
          </div>

          {/* Top features (RF) */}
          {finding.details?.top_features && Object.keys(finding.details.top_features).length > 0 && (
            <div style={{ marginBottom: 'var(--space-3)' }}>
              <div className="label" style={{ marginBottom: 'var(--space-2)' }}>Top Feature Importances</div>
              {Object.entries(finding.details.top_features)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 5)
                .map(([feat, imp]) => (
                  <div key={feat} style={{ marginBottom: 'var(--space-1)' }}>
                    <div className="flex justify-between" style={{ fontSize: 11, marginBottom: 2 }}>
                      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{feat}</span>
                      <span style={{ color: 'var(--accent-violet)', fontFamily: 'var(--font-mono)' }}>{imp.toFixed(4)}</span>
                    </div>
                    <div className="progress-bar-track" style={{ height: 4 }}>
                      <div className="progress-bar-fill" style={{ width: `${imp * 100}%` }} />
                    </div>
                  </div>
                ))}
            </div>
          )}

          {/* Chart */}
          {finding.chart_file && (
            <div className="chart-container">
              <div className="chart-header">
                <span style={{ fontSize: 11, color: 'var(--text-secondary)', fontWeight: 600 }}>
                  Statistical Chart — {finding.hypothesis_id}
                </span>
                <a
                  href={`${API}/api/charts/${finding.chart_file}`}
                  download
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={e => e.stopPropagation()}
                  style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 4, fontSize: 11 }}
                >
                  <ExternalLink size={12} /> Download
                </a>
              </div>
              <img
                src={`${API}/api/charts/${finding.chart_file}`}
                alt={`Chart for ${finding.hypothesis_id}`}
                className="chart-img"
                onError={e => { e.target.style.display = 'none'; }}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ReportViewer({ results, sessionId }) {
  const [showCeremony, setShowCeremony] = useState(false);
  const [activeTab, setActiveTab] = useState('findings');
  const ceremonyShownRef = useRef(false);

  const { validation, profile, dataset_name, markdown_report, global_charts } = results || {};

  useEffect(() => {
    if (!validation || ceremonyShownRef.current) return;
    if (validation.confirmed_discoveries > 0) {
      ceremonyShownRef.current = true;
      setTimeout(() => setShowCeremony(true), 600);
    }
  }, [validation]);

  if (!results) return null;

  const confirmed = validation.findings.filter(f => f.status === 'CONFIRMED_DISCOVERY');
  const allFindings = validation.findings;

  // Radar chart data — normalize effect sizes 0-1
  const maxEffect = Math.max(...allFindings.map(f => f.effect_size), 0.01);
  const radarData = allFindings.map(f => ({
    name: f.hypothesis_id,
    label: f.title.length > 20 ? f.title.slice(0, 18) + '…' : f.title,
    value: (f.effect_size / maxEffect) * 100,
    pValue: f.p_value,
    status: f.status,
    metric: f.effect_size_metric,
    rawEffect: f.effect_size,
  }));

  const barData = allFindings.map(f => ({
    name: f.hypothesis_id,
    value: parseFloat(f.effect_size.toFixed(3)),
    isConfirmed: f.status === 'CONFIRMED_DISCOVERY',
    label: f.title.slice(0, 22),
  }));

  const handleDownload = () => {
    window.open(`${API}/api/download-notebook/${sessionId}`, '_blank');
  };

  const TABS = [
    { id: 'findings', label: 'Findings', icon: <CheckCircle2 size={14} /> },
    { id: 'charts',   label: 'Charts',   icon: <BarChart3 size={14} /> },
    { id: 'report',   label: 'Report',   icon: <FileCode size={14} /> },
  ];

  return (
    <div className="fade-in" style={{ maxWidth: 1080, margin: '0 auto' }}>

      {/* Discovery ceremony */}
      {showCeremony && (
        <DiscoveryCeremony
          count={validation.confirmed_discoveries}
          onDismiss={() => setShowCeremony(false)}
        />
      )}

      {/* ── Summary Header ── */}
      <div className="card" style={{ padding: 'var(--space-6)', marginBottom: 'var(--space-5)' }}>
        <div className="flex items-start justify-between" style={{ marginBottom: 'var(--space-5)' }}>
          <div>
            <div className="flex items-center gap-2" style={{ marginBottom: 'var(--space-2)' }}>
              <Award size={20} color="var(--accent-green)" />
              <h1 style={{ fontSize: 18, fontWeight: 800, letterSpacing: '-0.02em' }}>
                Scientific Findings: <span style={{ color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)', fontSize: 16 }}>{dataset_name}</span>
              </h1>
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              Target: <span style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>{profile.active_target}</span>
              &nbsp;·&nbsp;{profile.active_task}
              &nbsp;·&nbsp;BH FDR α = {validation.fdr_alpha_used}
              &nbsp;·&nbsp;{profile.num_rows?.toLocaleString()} rows
            </div>
          </div>
          <button id="download-notebook-btn" className="btn btn-primary" onClick={handleDownload}>
            <Download size={14} />
            Download Notebook
          </button>
        </div>

        {/* Stat cards */}
        <div className="grid-4">
          <div className="stat-card">
            <div className="stat-card-label">Confirmed</div>
            <div className="stat-card-value confirmed">
              <CountUp target={validation.confirmed_discoveries} />
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Total Tested</div>
            <div className="stat-card-value cyan">
              <CountUp target={validation.total_tested} />
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Rejected</div>
            <div className="stat-card-value rose">
              <CountUp target={validation.rejected_count} />
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">FDR Alpha</div>
            <div className="stat-card-value violet">
              <CountUp target={validation.fdr_alpha_used} decimals={2} />
            </div>
          </div>
        </div>
      </div>

      {/* ── Tab Navigation ── */}
      <div className="flex gap-1" style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--card-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 4,
        marginBottom: 'var(--space-4)',
      }}>
        {TABS.map(t => (
          <button
            key={t.id}
            id={`tab-${t.id}`}
            onClick={() => setActiveTab(t.id)}
            className="btn"
            style={{
              flex: 1,
              background: activeTab === t.id ? 'var(--accent-violet-dim)' : 'transparent',
              color: activeTab === t.id ? 'var(--accent-violet)' : 'var(--text-secondary)',
              border: activeTab === t.id ? '1px solid var(--accent-violet-mid)' : '1px solid transparent',
              height: 36,
              borderRadius: 'var(--radius-md)',
            }}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      {/* ── TAB: Findings ── */}
      {activeTab === 'findings' && (
        <div className="fade-in stagger">
          {/* Radar / bar chart */}
          <div className="card" style={{ padding: 'var(--space-6)', marginBottom: 'var(--space-5)' }}>
            <div className="section-header">
              <TrendingUp size={16} color="var(--accent-violet)" />
              <span className="section-title">Effect Size Landscape</span>
            </div>
            <div className="grid-2" style={{ gap: 'var(--space-4)' }}>
              {/* Radar */}
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 'var(--space-2)' }}>
                  Normalized effect size (higher = stronger)
                </div>
                <ResponsiveContainer width="100%" height={220}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="rgba(255,255,255,0.06)" />
                    <PolarAngleAxis dataKey="label" tick={{ fill: '#8B949E', fontSize: 10 }} />
                    <PolarRadiusAxis tick={false} axisLine={false} domain={[0, 100]} />
                    <Radar
                      dataKey="value"
                      stroke="var(--accent-violet)"
                      fill="var(--accent-violet)"
                      fillOpacity={0.25}
                      strokeWidth={2}
                    />
                    <Tooltip
                      contentStyle={{ background: '#161B22', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 11 }}
                      formatter={(val, _, props) => [`${props.payload.rawEffect.toFixed(3)} (${props.payload.metric})`, 'Effect Size']}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
              {/* Bar */}
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 'var(--space-2)' }}>
                  Absolute effect size per hypothesis
                </div>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={barData} margin={{ left: -20 }}>
                    <XAxis dataKey="name" tick={{ fill: '#8B949E', fontSize: 10 }} />
                    <YAxis tick={{ fill: '#8B949E', fontSize: 10 }} />
                    <Tooltip
                      contentStyle={{ background: '#161B22', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 11 }}
                    />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                      {barData.map((entry, i) => (
                        <Cell key={i} fill={entry.isConfirmed ? 'var(--accent-green)' : 'rgba(255,255,255,0.12)'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* All findings */}
          <div className="section-header">
            <Database size={16} color="var(--accent-cyan)" />
            <span className="section-title">All Hypothesis Results</span>
            <span className="pill pill-neutral" style={{ marginLeft: 'auto' }}>
              {allFindings.length} total
            </span>
          </div>
          {allFindings.map(f => (
            <HypothesisCard key={f.hypothesis_id} finding={f} chartBase={API} />
          ))}
        </div>
      )}

      {/* ── TAB: Charts ── */}
      {activeTab === 'charts' && (
        <div className="fade-in">
          {(!global_charts || Object.keys(global_charts).length === 0) && allFindings.every(f => !f.chart_file) ? (
            <div className="card" style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--text-secondary)' }}>
              <BarChart3 size={32} style={{ margin: '0 auto var(--space-3)', opacity: 0.4 }} />
              <div>No charts generated for this session.</div>
              <div style={{ fontSize: 12, marginTop: 4 }}>Charts require matplotlib to be installed in the backend.</div>
            </div>
          ) : (
            <div className="stagger" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {/* Global charts */}
              {global_charts?.correlation_heatmap && (
                <div className="card chart-container">
                  <div className="chart-header">
                    <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>
                      Correlation Heatmap — All Numerical Features
                    </span>
                    <a href={`${API}/api/charts/${global_charts.correlation_heatmap}`} download target="_blank" rel="noopener noreferrer">
                      <Download size={12} color="var(--text-secondary)" />
                    </a>
                  </div>
                  <img src={`${API}/api/charts/${global_charts.correlation_heatmap}`} alt="Correlation Heatmap" className="chart-img" />
                </div>
              )}
              {global_charts?.target_distribution && (
                <div className="card chart-container">
                  <div className="chart-header">
                    <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>
                      Target Variable Distribution — {profile.active_target}
                    </span>
                    <a href={`${API}/api/charts/${global_charts.target_distribution}`} download target="_blank" rel="noopener noreferrer">
                      <Download size={12} color="var(--text-secondary)" />
                    </a>
                  </div>
                  <img src={`${API}/api/charts/${global_charts.target_distribution}`} alt="Target Distribution" className="chart-img" />
                </div>
              )}
              {/* Per-hypothesis charts */}
              {allFindings.filter(f => f.chart_file).map(f => (
                <div key={f.hypothesis_id} className="card chart-container">
                  <div className="chart-header">
                    <div>
                      <span className={`pill ${f.status === 'CONFIRMED_DISCOVERY' ? 'pill-green' : 'pill-rose'}`} style={{ marginRight: 8 }}>
                        {f.hypothesis_id}
                      </span>
                      <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{f.title}</span>
                    </div>
                    <a href={`${API}/api/charts/${f.chart_file}`} download target="_blank" rel="noopener noreferrer">
                      <Download size={12} color="var(--text-secondary)" />
                    </a>
                  </div>
                  <img src={`${API}/api/charts/${f.chart_file}`} alt={f.title} className="chart-img" />
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── TAB: Report ── */}
      {activeTab === 'report' && (
        <div className="card fade-in" style={{ padding: 'var(--space-6)' }}>
          <div className="section-header" style={{ marginBottom: 'var(--space-5)' }}>
            <FileCode size={16} color="var(--accent-cyan)" />
            <span className="section-title">Executive Research Report</span>
            <button className="btn btn-secondary" style={{ marginLeft: 'auto' }} onClick={handleDownload}>
              <Download size={13} /> Download Notebook
            </button>
          </div>
          <div className="markdown-report">
            <ReactMarkdown>{markdown_report}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
