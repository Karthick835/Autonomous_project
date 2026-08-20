import React, { useState } from 'react';
import {
  Download, Award, AlertTriangle, XCircle, CheckCircle2,
  ChevronDown, ChevronUp, BarChart2, ShieldCheck, Scale,
  BookOpen, Sparkles, Layers, Search, Info
} from 'lucide-react';

const API = 'http://127.0.0.1:5050';

export default function ReportViewer({ results, sessionId }) {
  const [activeTab, setActiveTab] = useState('tiered'); // 'tiered' | 'raw_markdown'
  const [expandedTiers, setExpandedTiers] = useState({
    tier1: true,
    tier2: true,
    tier3: false, // collapsed by default as requested
  });
  const [expandedConditions, setExpandedConditions] = useState({});

  if (!results) {
    return (
      <div className="card" style={{ padding: 'var(--space-8)', textAlign: 'center' }}>
        <p className="text-muted">No investigation results to display. Run an investigation first.</p>
      </div>
    );
  }

  const {
    tier1_findings = [],
    tier2_findings = [],
    tier3_findings = [],
    profile = {},
    dataset_name = 'Dataset',
    markdown_report = '',
    adversarial_reviews = [],
    enrichment_info = null,
    skipped_gaps = [],
    optional_gaps = [],
  } = results;

  const reviewMap = {};
  (adversarial_reviews || []).forEach((r) => {
    reviewMap[r.hypothesis_id] = r;
  });

  const toggleTier = (t) => {
    setExpandedTiers((p) => ({ ...p, [t]: !p[t] }));
  };

  const toggleCondition = (hid) => {
    setExpandedConditions((p) => ({ ...p, [hid]: !p[hid] }));
  };

  const downloadMarkdown = () => {
    const blob = new Blob([markdown_report], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research_report_${dataset_name.replace('.csv', '')}.md`;
    a.click();
  };

  const downloadNotebook = () => {
    window.open(`${API}/api/download-notebook/${sessionId}`, '_blank');
  };

  return (
    <div className="fade-in" style={{ maxWidth: 1120, margin: '0 auto' }}>
      {/* ── Top Header & Actions ── */}
      <div className="card" style={{ padding: 'var(--space-6)', marginBottom: 'var(--space-5)' }}>
        <div className="flex items-center justify-between" style={{ flexWrap: 'wrap', gap: 'var(--space-3)' }}>
          <div>
            <div className="flex items-center gap-2">
              <Award size={20} color="var(--accent-green)" />
              <h2 style={{ fontSize: 18, fontWeight: 800 }}>Peer-Reviewed Scientific Report</h2>
              {enrichment_info?.success && (
                <span className="pill pill-green" style={{ fontSize: 11, gap: 4 }}>
                  <Sparkles size={11} /> Enriched Dataset
                </span>
              )}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
              Dataset: <code style={{ color: 'var(--accent-cyan)' }}>{dataset_name}</code> ·
              Target: <code style={{ color: 'var(--accent-green)' }}>{profile.active_target}</code> ({profile.active_task}) ·
              N={profile.num_rows} observations
            </div>
          </div>

          <div className="flex gap-2">
            <button className="btn btn-secondary" onClick={downloadMarkdown} style={{ fontSize: 12 }}>
              <Download size={13} />
              Markdown Report
            </button>
            <button className="btn btn-primary" onClick={downloadNotebook} style={{ fontSize: 12 }}>
              <BookOpen size={13} />
              Jupyter Notebook (.ipynb)
            </button>
          </div>
        </div>

        {/* Level 3 Enrichment Banner */}
        {enrichment_info?.success && (
          <div style={{
            marginTop: 'var(--space-4)',
            padding: '10px 14px',
            background: 'var(--accent-green-dim)',
            border: '1px solid var(--accent-green-mid)',
            borderRadius: 'var(--radius-md)',
            fontSize: 12,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            color: 'var(--accent-green)'
          }}>
            <Layers size={16} />
            <span>
              <strong>Active Data Acquisition:</strong> Integrated {enrichment_info.new_columns?.length || 0} supplemental variables
              ({enrichment_info.new_columns?.join(', ')}) via {enrichment_info.strategy} strategy on keys <code>{enrichment_info.merge_keys?.join(', ')}</code>.
            </span>
          </div>
        )}

        {/* Level 3 Skipped Data Limitations Banner */}
        {skipped_gaps?.length > 0 && (
          <div style={{
            marginTop: 'var(--space-3)',
            padding: '10px 14px',
            background: 'var(--accent-amber-dim)',
            border: '1px solid rgba(245,158,11,0.3)',
            borderRadius: 'var(--radius-md)',
            fontSize: 12,
            color: 'var(--text-secondary)'
          }}>
            <div style={{ color: 'var(--accent-amber)', fontWeight: 700, marginBottom: 4 }}>
              ⚠️ Active Data Sufficiency Limitations:
            </div>
            {skipped_gaps.map((g, i) => (
              <div key={i} style={{ fontSize: 11 }}>
                • <strong>{g.title}</strong>: {g.why_it_matters}
              </div>
            ))}
          </div>
        )}

        {/* Tier Scorecard Tabs */}
        <div className="flex gap-3" style={{ marginTop: 'var(--space-4)' }}>
          <div className="card" style={{ flex: 1, padding: 'var(--space-3)', border: '1px solid var(--accent-green-mid)', background: 'var(--accent-green-dim)' }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--accent-green)', textTransform: 'uppercase' }}>Tier 1: Validated</div>
            <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--accent-green)' }}>{tier1_findings.length}</div>
          </div>
          <div className="card" style={{ flex: 1, padding: 'var(--space-3)', border: '1px solid rgba(245, 158, 11, 0.4)', background: 'var(--accent-amber-dim)' }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--accent-amber)', textTransform: 'uppercase' }}>Tier 2: Conditional</div>
            <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--accent-amber)' }}>{tier2_findings.length}</div>
          </div>
          <div className="card" style={{ flex: 1, padding: 'var(--space-3)', border: '1px solid rgba(244, 63, 94, 0.4)', background: 'var(--accent-rose-dim)' }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--accent-rose)', textTransform: 'uppercase' }}>Tier 3: Invalidated</div>
            <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--accent-rose)' }}>{tier3_findings.length}</div>
          </div>
        </div>
      </div>

      {/* ── View Selector ── */}
      <div className="flex gap-2" style={{ marginBottom: 'var(--space-4)' }}>
        <button
          className={`btn ${activeTab === 'tiered' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('tiered')}
          style={{ fontSize: 12 }}
        >
          Structured Peer-Reviewed Tiers
        </button>
        <button
          className={`btn ${activeTab === 'raw_markdown' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('raw_markdown')}
          style={{ fontSize: 12 }}
        >
          Raw Markdown Document
        </button>
      </div>

      {/* ── Tab 1: Structured Tiers ── */}
      {activeTab === 'tiered' && (
        <div className="flex-col gap-4">
          {/* ── Tier 1: Validated Findings ── */}
          <div className="tier-section">
            <div className="tier-header" onClick={() => toggleTier('tier1')}>
              <div className="flex items-center gap-2">
                <CheckCircle2 size={18} color="var(--accent-green)" />
                <span style={{ fontWeight: 800, fontSize: 15 }}>
                  Tier 1 — Validated Findings (Highest Confidence)
                </span>
                <span className="pill pill-green">{tier1_findings.length}</span>
              </div>
              {expandedTiers.tier1 ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </div>

            {expandedTiers.tier1 && (
              <div className="tier-body">
                {tier1_findings.length === 0 ? (
                  <p className="text-muted" style={{ fontSize: 13 }}>No candidate hypotheses achieved unconditional Tier 1 validation.</p>
                ) : (
                  <div className="flex-col gap-3">
                    {tier1_findings.map((f) => {
                      const rev = reviewMap[f.hypothesis_id] || {};
                      const conf = rev.arbitration?.confidence_score || f.confidence_score || 90;
                      return (
                        <div key={f.hypothesis_id} className="finding-card tier1-card">
                          <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-2)' }}>
                            <div className="flex items-center gap-2">
                              <span className="pill pill-cyan" style={{ fontFamily: 'var(--font-mono)', fontSize: 10 }}>
                                {f.hypothesis_id}
                              </span>
                              <span style={{ fontWeight: 700, fontSize: 14 }}>{f.title}</span>
                              {f.from_enriched_data && (
                                <span className="pill pill-green" style={{ fontSize: 9 }}>Enriched Data</span>
                              )}
                            </div>
                            <span className="pill pill-green">✅ VALIDATED ({conf}%)</span>
                          </div>

                          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 'var(--space-3)', lineHeight: 1.5 }}>
                            {f.summary || f.statement}
                          </p>

                          <div className="flex gap-4" style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)' }}>
                            <span>Test: {f.test_type}</span>
                            <span>P-Value: {f.p_value?.toFixed(5)}</span>
                            <span>{f.effect_size_metric || 'Effect Size'}: {f.effect_size?.toFixed(3)}</span>
                          </div>

                          {/* Statistical Chart */}
                          {f.chart_file && (
                            <div className="finding-chart-box">
                              <img
                                src={`${API}/api/charts/${f.chart_file}`}
                                alt={`Chart for ${f.title}`}
                                className="finding-chart-img"
                              />
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ── Tier 2: Validated with Conditions ── */}
          <div className="tier-section">
            <div className="tier-header" onClick={() => toggleTier('tier2')}>
              <div className="flex items-center gap-2">
                <AlertTriangle size={18} color="var(--accent-amber)" />
                <span style={{ fontWeight: 800, fontSize: 15 }}>
                  Tier 2 — Validated with Conditions (Bounded Scope)
                </span>
                <span className="pill pill-amber">{tier2_findings.length}</span>
              </div>
              {expandedTiers.tier2 ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </div>

            {expandedTiers.tier2 && (
              <div className="tier-body">
                {tier2_findings.length === 0 ? (
                  <p className="text-muted" style={{ fontSize: 13 }}>No hypotheses classified into Tier 2.</p>
                ) : (
                  <div className="flex-col gap-3">
                    {tier2_findings.map((f) => {
                      const rev = reviewMap[f.hypothesis_id] || {};
                      const conf = rev.arbitration?.confidence_score || f.confidence_score || 80;
                      const conditions = rev.arbitration?.conditions || f.arbitration_conditions || [];
                      const isCondOpen = expandedConditions[f.hypothesis_id];

                      return (
                        <div key={f.hypothesis_id} className="finding-card tier2-card">
                          <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-2)' }}>
                            <div className="flex items-center gap-2">
                              <span className="pill pill-cyan" style={{ fontFamily: 'var(--font-mono)', fontSize: 10 }}>
                                {f.hypothesis_id}
                              </span>
                              <span style={{ fontWeight: 700, fontSize: 14 }}>{f.title}</span>
                              {f.from_enriched_data && (
                                <span className="pill pill-green" style={{ fontSize: 9 }}>Enriched Data</span>
                              )}
                            </div>
                            <span className="pill pill-amber">⚠️ CONDITIONAL ({conf}%)</span>
                          </div>

                          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 'var(--space-3)', lineHeight: 1.5 }}>
                            {f.summary || f.statement}
                          </p>

                          <div className="flex gap-4" style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 'var(--space-2)' }}>
                            <span>Test: {f.test_type}</span>
                            <span>P-Value: {f.p_value?.toFixed(5)}</span>
                            <span>{f.effect_size_metric || 'Effect Size'}: {f.effect_size?.toFixed(3)}</span>
                          </div>

                          {/* Expandable Conditions Drawer */}
                          {conditions.length > 0 && (
                            <div style={{ marginTop: 'var(--space-2)' }}>
                              <button
                                className="btn btn-ghost"
                                onClick={() => toggleCondition(f.hypothesis_id)}
                                style={{ fontSize: 11, color: 'var(--accent-amber)', gap: 4, padding: '4px 8px' }}
                              >
                                <AlertTriangle size={12} />
                                {isCondOpen ? 'Hide Stated Limitations' : `View ${conditions.length} Stated Limitations`}
                                {isCondOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                              </button>

                              {isCondOpen && (
                                <div className="conditions-drawer fade-in" style={{ marginTop: 'var(--space-2)' }}>
                                  <div className="conditions-drawer-title">
                                    Peer Review Stated Conditions & Scope Boundaries:
                                  </div>
                                  {conditions.map((c, ci) => (
                                    <div key={ci} style={{ marginBottom: 4 }}>• {c}</div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}

                          {/* Statistical Chart */}
                          {f.chart_file && (
                            <div className="finding-chart-box">
                              <img
                                src={`${API}/api/charts/${f.chart_file}`}
                                alt={`Chart for ${f.title}`}
                                className="finding-chart-img"
                              />
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ── Tier 3: Invalidated Hypotheses (Transparency Log) ── */}
          <div className="tier-section">
            <div className="tier-header" onClick={() => toggleTier('tier3')}>
              <div className="flex items-center gap-2">
                <XCircle size={18} color="var(--accent-rose)" />
                <span style={{ fontWeight: 800, fontSize: 15 }}>
                  Tier 3 — Invalidated Hypotheses (Transparency Log)
                </span>
                <span className="pill pill-rose">{tier3_findings.length}</span>
              </div>
              {expandedTiers.tier3 ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </div>

            {expandedTiers.tier3 && (
              <div className="tier-body">
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 'var(--space-3)', fontStyle: 'italic' }}>
                  Transparent science logs all tested hypotheses, including those invalidated during adversarial peer review or failing FDR thresholds.
                </div>
                {tier3_findings.length === 0 ? (
                  <p className="text-muted" style={{ fontSize: 13 }}>All candidate hypotheses survived peer review into Tier 1 or Tier 2.</p>
                ) : (
                  <div className="flex-col gap-3">
                    {tier3_findings.map((f) => {
                      const rev = reviewMap[f.hypothesis_id] || {};
                      const reason = rev.arbitration?.editorial_reasoning || f.rejection_reason || 'Did not survive adversarial peer review challenge.';
                      return (
                        <div key={f.hypothesis_id} className="finding-card tier3-card">
                          <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-2)' }}>
                            <div className="flex items-center gap-2">
                              <span className="pill pill-cyan" style={{ fontFamily: 'var(--font-mono)', fontSize: 10 }}>
                                {f.hypothesis_id}
                              </span>
                              <span style={{ fontWeight: 700, fontSize: 14, textDecoration: 'line-through', color: 'var(--text-secondary)' }}>
                                {f.title}
                              </span>
                            </div>
                            <span className="pill pill-rose">❌ INVALIDATED</span>
                          </div>
                          <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                            <strong>Reason for Rejection:</strong> {reason}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ── Level 3: Future Enhancement Opportunities Section ── */}
          {optional_gaps?.length > 0 && (
            <div className="card" style={{ padding: 'var(--space-5)', marginTop: 'var(--space-3)' }}>
              <div className="flex items-center gap-2" style={{ marginBottom: 'var(--space-3)' }}>
                <Search size={16} color="var(--accent-cyan)" />
                <span style={{ fontSize: 14, fontWeight: 800 }}>
                  Future Data Enhancement Opportunities (Level 3 Active Intelligence)
                </span>
              </div>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 'var(--space-3)' }}>
                The following data sources were identified by the Data Gap Analysis Agent as opportunities to further extend these findings in future runs:
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--space-3)' }}>
                {optional_gaps.map((og, i) => (
                  <div key={i} className="data-gap-card optional">
                    <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
                      {og.title}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 4 }}>
                      {og.what_is_missing}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--accent-cyan)' }}>
                      <strong>Potential Value:</strong> {og.why_it_matters}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Tab 2: Raw Markdown ── */}
      {activeTab === 'raw_markdown' && (
        <div className="card" style={{ padding: 'var(--space-6)' }}>
          <pre style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            color: 'var(--text-secondary)',
            whiteSpace: 'pre-wrap',
            lineHeight: 1.6,
            background: 'var(--bg-surface)',
            padding: 'var(--space-4)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--card-border)',
            overflowX: 'auto',
          }}>
            {markdown_report}
          </pre>
        </div>
      )}
    </div>
  );
}
