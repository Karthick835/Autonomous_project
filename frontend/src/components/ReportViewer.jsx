import React, { useState, useEffect, useRef } from 'react';
import {
  Award, CheckCircle2, XCircle, Download, BarChart3,
  ChevronDown, ChevronUp, FileCode, TrendingUp, AlertTriangle,
  ExternalLink, Database, Scale, ShieldAlert, Sparkles
} from 'lucide-react';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, Cell
} from 'recharts';
import ReactMarkdown from 'react-markdown';

const API = 'http://127.0.0.1:5050';

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
          Adversarial Peer Review Complete
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 'var(--space-6)', lineHeight: 1.6 }}>
          The Level 2 validation engine confirmed <strong style={{ color: 'var(--accent-green)' }}>{count} robust discovery(ies)</strong> that successfully survived Karl Popper falsification challenges and editorial arbitration.
        </p>
        <button className="btn btn-primary btn-lg" onClick={onDismiss}>
          View Peer-Reviewed Findings →
        </button>
        <div style={{ marginTop: 'var(--space-3)', fontSize: 11, color: 'var(--text-tertiary)' }}>
          Click anywhere to dismiss
        </div>
      </div>
    </div>
  );
}

function TieredHypothesisCard({ finding, tier, chartBase }) {
  const [expanded, setExpanded] = useState(false);

  const isTier1 = tier === 1 || finding.verdict === 'VALIDATED';
  const isTier2 = tier === 2 || finding.verdict === 'VALIDATED_WITH_CONDITIONS';
  const isTier3 = tier === 3 || finding.verdict === 'INVALIDATED' || finding.status === 'REJECTED';

  const statusClass = isTier1 ? 'confirmed' : isTier2 ? 'weak' : 'rejected';
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
            {isTier1 && <span className="tier-badge tier-badge-1">✅ Tier 1: Validated</span>}
            {isTier2 && <span className="tier-badge tier-badge-2">⚠️ Tier 2: Conditional</span>}
            {isTier3 && <span className="tier-badge tier-badge-3">❌ Tier 3: Invalidated</span>}
          </div>

          <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.4 }}>
            {finding.title}
          </h3>

          <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 'var(--space-1)', lineHeight: 1.5 }}>
            {finding.summary}
          </p>

          {/* Editorial reasoning citation */}
          {finding.editorial_reasoning && (
            <div style={{ fontSize: 11, color: 'var(--accent-cyan)', fontStyle: 'italic', marginTop: 'var(--space-2)' }}>
              Editorial Arbiter: "{finding.editorial_reasoning}"
            </div>
          )}

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
                  background: isTier1
                    ? 'linear-gradient(90deg, #059669, var(--accent-green))'
                    : isTier2
                    ? 'linear-gradient(90deg, #B45309, var(--accent-amber))'
                    : 'linear-gradient(90deg, #DC2626, var(--accent-rose))',
                }}
              />
            </div>
          </div>
        </div>

        <div className="flex-col items-center gap-2" style={{ minWidth: 120 }}>
          {finding.confidence_score && (
            <span className="pill pill-violet" style={{ fontSize: 10, fontFamily: 'var(--font-mono)' }}>
              {finding.confidence_score}% Conf.
            </span>
          )}

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
            {expanded ? 'Less' : 'Review Details'}
          </button>
        </div>
      </div>

      {/* Conditions for Tier 2 */}
      {isTier2 && finding.arbitration_conditions?.length > 0 && (
        <div className="conditions-drawer">
          <div className="conditions-drawer-title">
            <AlertTriangle size={12} /> Stated Peer Review Limitations:
          </div>
          {finding.arbitration_conditions.map((cond, i) => (
            <div key={i} style={{ marginBottom: 2 }}>• {cond}</div>
          ))}
        </div>
      )}

      {/* Expanded details */}
      {expanded && (
        <div className="fade-in" style={{
          marginTop: 'var(--space-4)',
          paddingTop: 'var(--space-4)',
          borderTop: '1px solid var(--card-border)',
        }}>
          <div className="flex gap-4" style={{ marginBottom: 'var(--space-4)', flexWrap: 'wrap' }}>
            {[
              { label: 'P-Value', value: finding.p_value.toFixed(5), color: finding.p_value < 0.05 ? 'var(--accent-green)' : 'var(--accent-rose)' },
              { label: 'Effect Size', value: `${finding.effect_size.toFixed(3)} (${finding.effect_size_metric})`, color: 'var(--accent-violet)' },
              { label: 'FDR Significant', value: finding.fdr_significant ? 'Yes' : 'No', color: finding.fdr_significant ? 'var(--accent-green)' : 'var(--accent-rose)' },
              { label: 'Editorial Verdict', value: finding.verdict || finding.status, color: isTier1 ? 'var(--accent-green)' : isTier2 ? 'var(--accent-amber)' : 'var(--accent-rose)' },
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
  const [tierFilter, setTierFilter] = useState('all');
  const ceremonyShownRef = useRef(false);

  const { validation, profile, dataset_name, markdown_report, global_charts, tier1_findings, tier2_findings, tier3_findings } = results || {};

  const allFindings = validation?.findings || [];
  const tier1 = tier1_findings || allFindings.filter(f => f.verdict === 'VALIDATED' || (f.status === 'CONFIRMED_DISCOVERY' && !f.verdict));
  const tier2 = tier2_findings || allFindings.filter(f => f.verdict === 'VALIDATED_WITH_CONDITIONS');
  const tier3 = tier3_findings || allFindings.filter(f => f.verdict === 'INVALIDATED' || f.status === 'REJECTED');

  useEffect(() => {
    if (!validation || ceremonyShownRef.current) return;
    if (tier1.length + tier2.length > 0) {
      ceremonyShownRef.current = true;
      setTimeout(() => setShowCeremony(true), 600);
    }
  }, [validation, tier1, tier2]);

  if (!results) return null;

  const maxEffect = Math.max(...allFindings.map(f => f.effect_size), 0.01);
  const radarData = allFindings.map(f => ({
    name: f.hypothesis_id,
    label: f.title.length > 18 ? f.title.slice(0, 16) + '…' : f.title,
    value: (f.effect_size / maxEffect) * 100,
    pValue: f.p_value,
    status: f.verdict || f.status,
    metric: f.effect_size_metric,
    rawEffect: f.effect_size,
  }));

  const handleDownload = () => {
    window.open(`${API}/api/download-notebook/${sessionId}`, '_blank');
  };

  const TABS = [
    { id: 'findings', label: 'Peer-Reviewed Findings', icon: <Scale size={14} /> },
    { id: 'charts',   label: 'Statistical Charts',    icon: <BarChart3 size={14} /> },
    { id: 'report',   label: 'Executive Report',      icon: <FileCode size={14} /> },
  ];

  return (
    <div className="fade-in" style={{ maxWidth: 1120, margin: '0 auto' }}>
      {showCeremony && (
        <DiscoveryCeremony
          count={tier1.length + tier2.length}
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
                Peer-Reviewed Discoveries: <span style={{ color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)', fontSize: 16 }}>{dataset_name}</span>
              </h1>
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              Target: <span style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>{profile.active_target}</span>
              &nbsp;·&nbsp;{profile.active_task}
              &nbsp;·&nbsp;FDR α = {validation.fdr_alpha_used}
              &nbsp;·&nbsp;{profile.num_rows?.toLocaleString()} rows
            </div>
          </div>
          <button id="download-notebook-btn" className="btn btn-primary" onClick={handleDownload}>
            <Download size={14} />
            Download Notebook
          </button>
        </div>

        {/* 3-Tier Stat Cards */}
        <div className="grid-4">
          <div className="stat-card">
            <div className="stat-card-label">Tier 1 (Validated)</div>
            <div className="stat-card-value confirmed">
              <CountUp target={tier1.length} />
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Tier 2 (Conditional)</div>
            <div className="stat-card-value amber">
              <CountUp target={tier2.length} />
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Tier 3 (Invalidated)</div>
            <div className="stat-card-value rose">
              <CountUp target={tier3.length} />
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Total Tested</div>
            <div className="stat-card-value cyan">
              <CountUp target={allFindings.length} />
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
          {/* Radar landscape */}
          <div className="card" style={{ padding: 'var(--space-6)', marginBottom: 'var(--space-5)' }}>
            <div className="section-header">
              <TrendingUp size={16} color="var(--accent-violet)" />
              <span className="section-title">Effect Size & Robustness Landscape</span>
            </div>
            <div className="grid-2" style={{ gap: 'var(--space-4)' }}>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 'var(--space-2)' }}>
                  Normalized effect size (higher = stronger empirical magnitude)
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

              <div>
                <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 'var(--space-2)' }}>
                  Tier Categorization Overview
                </div>
                <div className="flex-col gap-3" style={{ marginTop: 'var(--space-2)' }}>
                  <div style={{ padding: 'var(--space-3)', background: 'var(--accent-green-dim)', border: '1px solid var(--accent-green-mid)', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ fontWeight: 700, color: 'var(--accent-green)', fontSize: 12 }}>Tier 1: {tier1.length} Validated Discoveries</div>
                    <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Survived Popperian challenge without unaddressed vulnerabilities.</div>
                  </div>
                  <div style={{ padding: 'var(--space-3)', background: 'var(--accent-amber-dim)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ fontWeight: 700, color: 'var(--accent-amber)', fontSize: 12 }}>Tier 2: {tier2.length} Conditional Discoveries</div>
                    <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Empirically supported with explicit observational bounds.</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* ── Tier 1 Section ── */}
          <div style={{ marginBottom: 'var(--space-6)' }}>
            <div className="section-header">
              <Award size={16} color="var(--accent-green)" />
              <span className="section-title">Tier 1 — Validated Findings (Highest Confidence)</span>
              <span className="pill pill-green" style={{ marginLeft: 'auto' }}>
                {tier1.length} validated
              </span>
            </div>
            {tier1.length > 0 ? (
              tier1.map(f => (
                <TieredHypothesisCard key={f.hypothesis_id} finding={f} tier={1} chartBase={API} />
              ))
            ) : (
              <div className="card" style={{ padding: 'var(--space-4)', color: 'var(--text-secondary)', fontSize: 12 }}>
                No hypotheses achieved unconditional Tier 1 validation.
              </div>
            )}
          </div>

          {/* ── Tier 2 Section ── */}
          <div style={{ marginBottom: 'var(--space-6)' }}>
            <div className="section-header">
              <AlertTriangle size={16} color="var(--accent-amber)" />
              <span className="section-title">Tier 2 — Validated with Conditions (Bounded Scope)</span>
              <span className="pill pill-amber" style={{ marginLeft: 'auto' }}>
                {tier2.length} conditional
              </span>
            </div>
            {tier2.length > 0 ? (
              tier2.map(f => (
                <TieredHypothesisCard key={f.hypothesis_id} finding={f} tier={2} chartBase={API} />
              ))
            ) : (
              <div className="card" style={{ padding: 'var(--space-4)', color: 'var(--text-secondary)', fontSize: 12 }}>
                No hypotheses classified as Tier 2.
              </div>
            )}
          </div>

          {/* ── Tier 3 Section (Transparency Log) ── */}
          <div className="transparency-log-section">
            <div className="section-header">
              <ShieldAlert size={16} color="var(--accent-rose)" />
              <span className="section-title" style={{ color: 'var(--accent-rose)' }}>
                Tier 3 — Invalidated Hypotheses (Transparency Log)
              </span>
              <span className="pill pill-rose" style={{ marginLeft: 'auto' }}>
                {tier3.length} invalidated
              </span>
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 'var(--space-3)' }}>
              Open science principle: Every hypothesis that failed peer review or statistical thresholds is documented below.
            </div>
            {tier3.length > 0 ? (
              tier3.map(f => (
                <div key={f.hypothesis_id} className="transparency-item">
                  <div className="flex items-center justify-between" style={{ marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: 13 }}>
                      [{f.hypothesis_id}] {f.title}
                    </span>
                    <span className="pill pill-rose" style={{ fontSize: 10 }}>❌ Invalidated</span>
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--accent-rose)', marginBottom: 2 }}>
                    Reason: {f.editorial_reasoning || f.summary || 'Failed statistical significance threshold.'}
                  </div>
                  <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>
                    Observed: p={f.p_value.toFixed(4)}, {f.effect_size_metric}={f.effect_size.toFixed(3)}
                  </div>
                </div>
              ))
            ) : (
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                All tested hypotheses satisfied minimum peer review criteria.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── TAB: Charts ── */}
      {activeTab === 'charts' && (
        <div className="fade-in">
          {(!global_charts || Object.keys(global_charts).length === 0) && allFindings.every(f => !f.chart_file) ? (
            <div className="card" style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--text-secondary)' }}>
              <BarChart3 size={32} style={{ margin: '0 auto var(--space-3)', opacity: 0.4 }} />
              <div>No charts generated for this session.</div>
            </div>
          ) : (
            <div className="stagger" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
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
              {allFindings.filter(f => f.chart_file).map(f => (
                <div key={f.hypothesis_id} className="card chart-container">
                  <div className="chart-header">
                    <div>
                      <span className={`pill ${f.verdict === 'VALIDATED' ? 'pill-green' : f.verdict === 'VALIDATED_WITH_CONDITIONS' ? 'pill-amber' : 'pill-rose'}`} style={{ marginRight: 8 }}>
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
            <span className="section-title">Peer-Reviewed Executive Research Report</span>
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
