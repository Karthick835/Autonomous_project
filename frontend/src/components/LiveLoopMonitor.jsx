import React, { useEffect, useState, useRef } from 'react';
import {
  Terminal, Cpu, CheckCircle, XCircle, AlertTriangle, Clock,
  Microscope, Lightbulb, Code2, ShieldCheck, FileBarChart, Database,
  BarChart3, Scale, ShieldAlert, Sparkles, Award, Search, RefreshCw,
  Layers, ArrowUpRight
} from 'lucide-react';
import DataGapModal from './DataGapModal';

const API = 'http://127.0.0.1:5050';

const AGENT_CONFIG = {
  DataProfilerAgent: {
    label: 'Data Profiler',
    icon: <Microscope size={14} />,
    className: 'agent-profiler',
    logColor: 'var(--accent-cyan)',
  },
  DataGapAnalysisAgent: {
    label: 'Data Gap Agent',
    icon: <Search size={14} />,
    className: 'agent-hyp',
    logColor: 'var(--accent-violet)',
  },
  DataMergeEngine: {
    label: 'Merge Engine',
    icon: <Layers size={14} />,
    className: 'agent-validator',
    logColor: 'var(--accent-green)',
  },
  HypothesizerAgent: {
    label: 'Hypothesizer',
    icon: <Lightbulb size={14} />,
    className: 'agent-hyp',
    logColor: 'var(--accent-violet)',
  },
  CodeEngineerAgent: {
    label: 'Code Engineer',
    icon: <Code2 size={14} />,
    className: 'agent-engineer',
    logColor: 'var(--accent-amber)',
  },
  PythonSandbox: {
    label: 'Sandbox',
    icon: <Code2 size={14} />,
    className: 'agent-engineer',
    logColor: 'var(--accent-amber)',
  },
  StatisticalValidatorAgent: {
    label: 'Validator',
    icon: <ShieldCheck size={14} />,
    className: 'agent-validator',
    logColor: 'var(--accent-green)',
  },
  FalsificationAgent: {
    label: 'Falsifier 🔴',
    icon: <ShieldAlert size={14} />,
    className: 'agent-chart',
    logColor: 'var(--accent-rose)',
  },
  CorroborationAgent: {
    label: 'Corroborator 🟢',
    icon: <ShieldCheck size={14} />,
    className: 'agent-validator',
    logColor: 'var(--accent-green)',
  },
  ArbitrationAgent: {
    label: 'Arbiter 🟡',
    icon: <Scale size={14} />,
    className: 'agent-engineer',
    logColor: 'var(--accent-amber)',
  },
  ScienceWriterAgent: {
    label: 'Reporter',
    icon: <FileBarChart size={14} />,
    className: 'agent-reporter',
    logColor: '#A855F7',
  },
  AgentMemory: {
    label: 'Memory',
    icon: <Database size={14} />,
    className: 'agent-memory',
    logColor: '#8B5CF6',
  },
  ChartGeneratorAgent: {
    label: 'Chart Gen',
    icon: <BarChart3 size={14} />,
    className: 'agent-chart',
    logColor: 'var(--accent-rose)',
  },
  System: {
    label: 'System',
    icon: <Cpu size={14} />,
    className: 'agent-system',
    logColor: 'var(--text-secondary)',
  },
};

const STAGES = [
  { id: 'PROFILING',          label: 'Data Profiling' },
  { id: 'DATA_GAP_ANALYSIS',  label: 'Data Sufficiency' },
  { id: 'HYPOTHESIZING',      label: 'Hypothesizing' },
  { id: 'EXPERIMENTATION',    label: 'Experiments' },
  { id: 'VALIDATION',         label: 'Validation' },
  { id: 'ADVERSARIAL_REVIEW', label: 'Peer Review' },
  { id: 'REPORTING',          label: 'Reporting' },
];

function useTypewriter(text, speed = 14) {
  const [displayed, setDisplayed] = useState('');
  useEffect(() => {
    setDisplayed('');
    if (!text) return;
    let i = 0;
    const timer = setInterval(() => {
      i++;
      setDisplayed(text.slice(0, i));
      if (i >= text.length) clearInterval(timer);
    }, speed);
    return () => clearInterval(timer);
  }, [text, speed]);
  return displayed;
}

// Circular Confidence Ring component
function ConfidenceRing({ score, verdict }) {
  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const strokeColor =
    verdict === 'VALIDATED'
      ? 'var(--accent-green)'
      : verdict === 'VALIDATED_WITH_CONDITIONS'
      ? 'var(--accent-amber)'
      : 'var(--accent-rose)';

  return (
    <div className="confidence-gauge-wrap">
      <svg className="confidence-gauge-svg" viewBox="0 0 90 90">
        <circle
          className="confidence-gauge-bg"
          cx="45"
          cy="45"
          r={radius}
        />
        <circle
          className="confidence-gauge-fill"
          cx="45"
          cy="45"
          r={radius}
          stroke={strokeColor}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="confidence-gauge-text">{score}%</div>
    </div>
  );
}

export default function LiveLoopMonitor({ sessionId, onComplete }) {
  const [logs, setLogs] = useState([]);
  const [stage, setStage] = useState('PROFILING');
  const [isFinished, setIsFinished] = useState(false);
  const [isError, setIsError] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [pauseDuration, setPauseDuration] = useState(0);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [tierCounts, setTierCounts] = useState({ tier1: 0, tier2: 0, tier3: 0 });
  const [testedCount, setTestedCount] = useState(0);
  const [lastThought, setLastThought] = useState('');
  const [adversarialDebates, setAdversarialDebates] = useState({});
  const [activeDebateId, setActiveDebateId] = useState(null);

  // Level 3 State
  const [dataGaps, setDataGaps] = useState(null);
  const [activeGapModal, setActiveGapModal] = useState(null);
  const [enrichmentInfo, setEnrichmentInfo] = useState(null);

  const logEndRef = useRef(null);
  const startTimeRef = useRef(Date.now());
  const timerRef = useRef(null);
  const pauseTimerRef = useRef(null);

  const typedThought = useTypewriter(lastThought, 12);

  useEffect(() => {
    if (isFinished) return;
    timerRef.current = setInterval(() => {
      setElapsedMs(Date.now() - startTimeRef.current);
    }, 500);
    return () => clearInterval(timerRef.current);
  }, [isFinished]);

  // Pause duration timer
  useEffect(() => {
    if (isPaused) {
      pauseTimerRef.current = setInterval(() => {
        setPauseDuration((p) => p + 1);
      }, 1000);
    } else {
      clearInterval(pauseTimerRef.current);
      setPauseDuration(0);
    }
    return () => clearInterval(pauseTimerRef.current);
  }, [isPaused]);

  useEffect(() => {
    if (!sessionId) return;
    startTimeRef.current = Date.now();

    const eventSource = new EventSource(`${API}/api/stream/${sessionId}`);

    eventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.stage === 'PING') return;

        setLogs((prev) => [...prev, data]);

        // Map adversarial stages
        if (data.stage?.startsWith('ADVERSARIAL_')) {
          setStage('ADVERSARIAL_REVIEW');
        } else if (data.stage) {
          setStage(data.stage);
        }

        if (data.message) setLastThought(data.message);

        // Handle Level 3 Data Gap Analysis
        if (data.stage === 'DATA_GAP_ANALYSIS' && data.payload?.gap_report) {
          setDataGaps(data.payload.gap_report);
        }

        // Handle Level 3 Data Request / Pause
        if (data.stage === 'DATA_REQUEST' && data.payload?.gap) {
          const gap = data.payload.gap;
          if (data.payload.paused) {
            setIsPaused(true);
          }
          setActiveGapModal(gap);
        }

        // Handle Enrichment info
        if (data.payload?.enrichment_info) {
          setEnrichmentInfo(data.payload.enrichment_info);
          setIsPaused(false);
        }

        // Handle Adversarial Falsify event
        if (data.stage === 'ADVERSARIAL_FALSIFY' && data.payload?.hypothesis_id) {
          const hid = data.payload.hypothesis_id;
          setActiveDebateId(hid);
          setAdversarialDebates((prev) => ({
            ...prev,
            [hid]: {
              ...(prev[hid] || {}),
              hypothesis_id: hid,
              hypothesis_title: data.payload.hypothesis_title,
              falsification: data.payload.falsification,
            },
          }));
        }

        // Handle Adversarial Corroborate event
        if (data.stage === 'ADVERSARIAL_CORROBORATE' && data.payload?.hypothesis_id) {
          const hid = data.payload.hypothesis_id;
          setAdversarialDebates((prev) => ({
            ...prev,
            [hid]: {
              ...(prev[hid] || {}),
              corroboration: data.payload.corroboration,
            },
          }));
        }

        // Handle Adversarial Arbitrate event
        if (data.stage === 'ADVERSARIAL_ARBITRATE' && data.payload?.hypothesis_id) {
          const hid = data.payload.hypothesis_id;
          const verd = data.payload.verdict;
          setAdversarialDebates((prev) => ({
            ...prev,
            [hid]: {
              ...(prev[hid] || {}),
              arbitration: data.payload.arbitration,
              verdict: verd,
              confidence_score: data.payload.confidence_score,
            },
          }));

          setTierCounts((prev) => ({
            tier1: verd === 'VALIDATED' ? prev.tier1 + 1 : prev.tier1,
            tier2: verd === 'VALIDATED_WITH_CONDITIONS' ? prev.tier2 + 1 : prev.tier2,
            tier3: verd === 'INVALIDATED' ? prev.tier3 + 1 : prev.tier3,
          }));
        }

        if (data.stage === 'EXPERIMENTATION' && data.agent === 'PythonSandbox') {
          setTestedCount((p) => p + 1);
        }

        if (data.stage === 'COMPLETE') {
          setIsFinished(true);
          setIsPaused(false);
          clearInterval(timerRef.current);
          eventSource.close();
          onComplete(sessionId);
        } else if (data.stage === 'ERROR') {
          setIsError(true);
          setIsFinished(true);
          setIsPaused(false);
          clearInterval(timerRef.current);
          eventSource.close();
        }
      } catch (err) {
        console.error('SSE parse error:', err);
      }
    };

    eventSource.onerror = () => eventSource.close();
    return () => eventSource.close();
  }, [sessionId, onComplete]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const activeIdx = STAGES.findIndex((s) => s.id === stage);
  const elapsed = elapsedMs / 1000;
  const elapsedStr =
    elapsed < 60
      ? `${elapsed.toFixed(1)}s`
      : `${Math.floor(elapsed / 60)}m ${(elapsed % 60).toFixed(0)}s`;

  const debateKeys = Object.keys(adversarialDebates);
  const activeDebate = adversarialDebates[activeDebateId] || (debateKeys.length > 0 ? adversarialDebates[debateKeys[debateKeys.length - 1]] : null);

  return (
    <div className="fade-in" style={{ maxWidth: 1120, margin: '0 auto' }}>
      {/* ── Data Request Modal (Level 3) ── */}
      <DataGapModal
        gap={activeGapModal}
        sessionId={sessionId}
        isOpen={Boolean(activeGapModal)}
        onClose={() => setActiveGapModal(null)}
        onDataProvided={(res) => {
          setIsPaused(false);
          setActiveGapModal(null);
        }}
        onSkipped={(res) => {
          setIsPaused(false);
          setActiveGapModal(null);
        }}
      />

      {/* ── Pipeline Paused Indicator Banner (Level 3) ── */}
      {isPaused && (
        <div className="pipeline-paused-banner fade-in">
          <div className="flex items-center gap-3">
            <span className="pulse-dot-amber" />
            <div>
              <div style={{ fontWeight: 800, fontSize: 13, color: 'var(--accent-amber)' }}>
                Investigation Paused — Awaiting Supplemental Data
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                {activeGapModal?.title || 'Data Gap requires user input'} · Paused for {pauseDuration}s
              </div>
            </div>
          </div>
          <button
            className="btn btn-primary"
            onClick={() => activeGapModal && setActiveGapModal({ ...activeGapModal })}
            style={{ fontSize: 11, height: 28, padding: '0 12px' }}
          >
            Open Data Request
          </button>
        </div>
      )}

      {/* ── Enriched Dataset Banner (Level 3) ── */}
      {enrichmentInfo && (
        <div className="dataset-enriched-banner fade-in">
          <div className="flex items-center gap-2">
            <Sparkles size={14} color="var(--accent-green)" />
            <span style={{ fontWeight: 700, fontSize: 12, color: 'var(--accent-green)' }}>
              Enriched Dataset Active
            </span>
            <span className="pill pill-green" style={{ fontSize: 10 }}>
              {enrichmentInfo.original_shape?.[1]} cols → {enrichmentInfo.enriched_shape?.[1]} cols
            </span>
            <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
              {enrichmentInfo.rows_matched} rows joined via {enrichmentInfo.strategy} strategy ({enrichmentInfo.merge_keys?.join(', ')})
            </span>
          </div>
        </div>
      )}

      {/* ── Header ── */}
      <div className="card" style={{ padding: 'var(--space-5)', marginBottom: 'var(--space-4)' }}>
        <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-4)' }}>
          <div className="flex items-center gap-3">
            <div className="agent-avatar agent-hyp">
              <Cpu size={16} className={!isFinished && !isPaused ? 'spin' : ''} />
            </div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 800 }}>Level 3 Active Discovery & Peer Review Loop</div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                session: {sessionId} · 9 active agents · Active data acquisition
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {isError ? (
              <span className="pill pill-rose"><span className="pill-dot" />Pipeline Error</span>
            ) : isPaused ? (
              <span className="pill pill-amber"><span className="pill-dot-pulse" />Paused for Data</span>
            ) : isFinished ? (
              <span className="pill pill-green"><span className="pill-dot" />Investigation Complete</span>
            ) : (
              <span className="pill pill-violet"><span className="pill-dot-pulse" />Pipeline Active</span>
            )}
          </div>
        </div>

        {/* ── Pipeline Progress Rail ── */}
        <div className="pipeline">
          {STAGES.map((s, i) => {
            const isDone = i < activeIdx || isFinished;
            const isCurrent = i === activeIdx && !isFinished;
            const isErr = isError && i === activeIdx;

            return (
              <React.Fragment key={s.id}>
                <div className="pipeline-step">
                  <div className={`pipeline-step-indicator ${
                    isErr ? 'step-error' : isDone ? 'step-done' : isCurrent ? 'step-active' : 'step-pending'
                  }`}>
                    {isDone && !isErr ? <CheckCircle size={13} /> : isErr ? <XCircle size={13} /> : i + 1}
                  </div>
                  <span className={`pipeline-step-label ${isCurrent ? 'active' : isDone ? 'done' : ''}`}>
                    {s.label}
                  </span>
                </div>
                {i < STAGES.length - 1 && (
                  <div className="pipeline-connector">
                    <div className="pipeline-connector-fill" style={{ width: isDone ? '100%' : isCurrent ? '50%' : '0%' }} />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* ── Level 3: Data Sufficiency Panel ── */}
      {dataGaps && (
        <div className="card fade-in" style={{ padding: 'var(--space-5)', marginBottom: 'var(--space-4)' }}>
          <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-3)' }}>
            <div className="flex items-center gap-2">
              <Search size={16} color="var(--accent-cyan)" />
              <span style={{ fontSize: 13, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Data Sufficiency & Gap Review (Agent 9)
              </span>
            </div>
            <div className="flex gap-2">
              {dataGaps.critical_count > 0 && (
                <span className="pill pill-rose">{dataGaps.critical_count} Critical</span>
              )}
              {dataGaps.important_count > 0 && (
                <span className="pill pill-amber">{dataGaps.important_count} Important</span>
              )}
              {dataGaps.optional_count > 0 && (
                <span className="pill pill-cyan">{dataGaps.optional_count} Optional</span>
              )}
            </div>
          </div>

          <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 'var(--space-3)' }}>
            {dataGaps.overall_assessment}
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--space-3)' }}>
            {dataGaps.gaps?.map((gap) => (
              <div
                key={gap.id}
                className={`data-gap-card ${gap.priority.toLowerCase()}`}
                onClick={() => setActiveGapModal(gap)}
                title="Click to view details or upload supplemental data"
              >
                <div className="flex items-center justify-between" style={{ marginBottom: 4 }}>
                  <span className={`pill ${gap.priority === 'CRITICAL' ? 'pill-rose' : gap.priority === 'IMPORTANT' ? 'pill-amber' : 'pill-cyan'}`} style={{ fontSize: 9 }}>
                    {gap.priority}
                  </span>
                  <span style={{ fontSize: 10, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                    {gap.id}
                  </span>
                </div>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
                  {gap.title}
                </div>
                <p style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.4, margin: 0 }}>
                  {gap.why_it_matters?.slice(0, 110)}...
                </p>
                <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 4, fontSize: 10, color: 'var(--accent-violet)' }}>
                  <span>Provide data</span> <ArrowUpRight size={12} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Live Adversarial Peer Review Panel ── */}
      {activeDebate && (
        <div className="adversarial-panel fade-in">
          <div className="adversarial-header">
            <div>
              <div className="adversarial-title">
                <Scale size={18} color="var(--accent-amber)" />
                <span>Adversarial Peer Review Debate</span>
                <span className="pill pill-cyan" style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>
                  {activeDebate.hypothesis_id}
                </span>
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
                {activeDebate.hypothesis_title}
              </div>
            </div>

            {/* Switch between contested hypotheses */}
            {debateKeys.length > 1 && (
              <div className="flex gap-1">
                {debateKeys.map((hid) => (
                  <button
                    key={hid}
                    onClick={() => setActiveDebateId(hid)}
                    className={`pill ${activeDebate.hypothesis_id === hid ? 'pill-violet' : 'pill-neutral'}`}
                    style={{ cursor: 'pointer', fontFamily: 'var(--font-mono)' }}
                  >
                    {hid}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Paired Challenges & Responses */}
          {activeDebate.falsification?.challenges?.map((chal, idx) => {
            const resp = activeDebate.corroboration?.responses?.find(
              (r) => r.challenge_id === chal.id || activeDebate.corroboration?.responses?.[idx]
            );

            return (
              <div key={chal.id || idx} className="debate-pair-grid">
                {/* 🔴 Left: Falsification Challenge */}
                <div className="falsification-card">
                  <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-2)' }}>
                    <span className="pill pill-rose" style={{ fontSize: 10 }}>
                      🔴 Challenge {chal.id || `C${idx + 1}`} · {chal.category}
                    </span>
                  </div>
                  <p style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.5 }}>
                    {chal.challenge_text}
                  </p>
                  {chal.data_reference && (
                    <div className="data-ref-tag">
                      <span>Data cited:</span> {chal.data_reference}
                    </div>
                  )}
                </div>

                {/* 🟢 Right: Corroboration Response */}
                {resp ? (
                  <div className="corroboration-card">
                    <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-2)' }}>
                      <span className={`pill ${resp.stance === 'REBUTTED' ? 'pill-green' : resp.stance === 'PARTIALLY_CONCEDED' ? 'pill-amber' : 'pill-rose'}`} style={{ fontSize: 10 }}>
                        🟢 Defense to {chal.id || `C${idx + 1}`} · {resp.stance}
                      </span>
                    </div>
                    <p style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.5 }}>
                      {resp.rebuttal_text}
                    </p>
                    {resp.supporting_data && (
                      <div className="data-ref-tag" style={{ borderColor: 'rgba(16, 185, 129, 0.3)', color: 'var(--accent-green)' }}>
                        <span>Support:</span> {resp.supporting_data}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="skeleton" style={{ height: 110, borderRadius: 'var(--radius-lg)' }} />
                )}
              </div>
            );
          })}

          {/* 🟡 Center: Arbitration Editor Verdict */}
          {activeDebate.arbitration && (
            <div className={`arbitration-verdict-card ${activeDebate.verdict === 'VALIDATED' ? 'validated' : activeDebate.verdict === 'VALIDATED_WITH_CONDITIONS' ? 'conditional' : 'invalidated'}`}>
              <ConfidenceRing
                score={activeDebate.confidence_score || 85}
                verdict={activeDebate.verdict}
              />

              <div>
                <span className={`verdict-badge ${activeDebate.verdict === 'VALIDATED' ? 'validated' : activeDebate.verdict === 'VALIDATED_WITH_CONDITIONS' ? 'conditional' : 'invalidated'}`}>
                  {activeDebate.verdict === 'VALIDATED' ? '✅ Tier 1: VALIDATED' : activeDebate.verdict === 'VALIDATED_WITH_CONDITIONS' ? '⚠️ Tier 2: VALIDATED WITH CONDITIONS' : '❌ Tier 3: INVALIDATED'}
                </span>
              </div>

              <p style={{ fontSize: 13, color: 'var(--text-secondary)', maxWidth: 640, margin: 'var(--space-2) auto var(--space-3)', lineHeight: 1.6 }}>
                "{activeDebate.arbitration.editorial_reasoning}"
              </p>

              {activeDebate.arbitration.conditions?.length > 0 && (
                <div className="conditions-drawer" style={{ textAlign: 'left', maxWidth: 640, margin: '0 auto' }}>
                  <div className="conditions-drawer-title">
                    <AlertTriangle size={12} /> Stated Empirical Conditions & Limitations:
                  </div>
                  {activeDebate.arbitration.conditions.map((cond, ci) => (
                    <div key={ci} style={{ marginBottom: 4 }}>• {cond}</div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── Main Monitor Grid: Event Logs + Mini HUD ── */}
      <div className="grid-2" style={{ gap: 'var(--space-4)', marginTop: 'var(--space-4)', marginBottom: 'var(--space-4)' }}>
        {/* Agent Log Feed */}
        <div className="card" style={{ padding: 'var(--space-4)' }}>
          <div className="flex items-center gap-2" style={{ marginBottom: 'var(--space-3)', paddingBottom: 'var(--space-3)', borderBottom: '1px solid var(--card-border)' }}>
            <Terminal size={14} color="var(--text-secondary)" />
            <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
              Live Agent Events
            </span>
            <span className="pill pill-neutral" style={{ marginLeft: 'auto', fontSize: 10 }}>
              {logs.length} events
            </span>
          </div>

          <div className="log-feed">
            {logs.map((log, i) => {
              const cfg = AGENT_CONFIG[log.agent] || AGENT_CONFIG.System;
              const ts = log.timestamp
                ? new Date(log.timestamp * 1000).toISOString().substr(11, 8)
                : '';
              return (
                <div key={i} className="log-entry">
                  <span className="log-time">{ts}</span>
                  <div className="flex items-center gap-2" style={{ minWidth: 160 }}>
                    <div className={`agent-avatar ${cfg.className}`} style={{ width: 20, height: 20, minWidth: 20, borderRadius: 4 }}>
                      {cfg.icon}
                    </div>
                    <span className="log-agent" style={{ color: cfg.logColor, minWidth: 'auto' }}>
                      {cfg.label}
                    </span>
                  </div>
                  <span className="log-message">{log.message}</span>
                </div>
              );
            })}
            <div ref={logEndRef} />
          </div>
        </div>

        {/* Right HUD & Thinking */}
        <div className="flex-col gap-4">
          <div className="card" style={{ padding: 'var(--space-4)' }}>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: 'var(--space-3)' }}>
              Peer Review Verdict Summary
            </div>
            <div className="flex-col gap-2" style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>
              <div className="hud-row">
                <span className="hud-label"><Clock size={11} style={{ display: 'inline', marginRight: 4 }} />Elapsed</span>
                <span className="hud-value running">{elapsedStr}</span>
              </div>
              <div className="hud-row">
                <span className="hud-label">⚗ Stage</span>
                <span className="hud-value" style={{ color: 'var(--accent-violet)' }}>{stage}</span>
              </div>
              <div className="hud-row">
                <span className="hud-label">🔬 Tests run</span>
                <span className="hud-value">{testedCount}</span>
              </div>
              <div className="hud-row">
                <span className="hud-label">✅ Tier 1 (Validated)</span>
                <span className="hud-value confirmed">{tierCounts.tier1}</span>
              </div>
              <div className="hud-row">
                <span className="hud-label">⚠️ Tier 2 (Conditional)</span>
                <span className="hud-value" style={{ color: 'var(--accent-amber)' }}>{tierCounts.tier2}</span>
              </div>
              <div className="hud-row">
                <span className="hud-label">❌ Tier 3 (Invalidated)</span>
                <span className="hud-value rejected">{tierCounts.tier3}</span>
              </div>
            </div>
          </div>

          {/* Thinking bubble */}
          {!isFinished && lastThought && (
            <div className="thinking-panel fade-in">
              <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--accent-violet)', textTransform: 'uppercase', marginBottom: 'var(--space-2)' }}>
                🧠 Agent Reasoning & Debate
              </div>
              <div className="thinking-text">
                <span>{typedThought}</span>
                <span className="thinking-cursor" />
              </div>
            </div>
          )}

          {/* Finished State */}
          {isFinished && !isError && (
            <div className="fade-in" style={{
              padding: 'var(--space-5)',
              background: 'var(--accent-green-dim)',
              border: '1px solid var(--accent-green-mid)',
              borderRadius: 'var(--radius-lg)',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: 32, marginBottom: 'var(--space-2)' }}>🔬</div>
              <div style={{ fontWeight: 800, color: 'var(--accent-green)', marginBottom: 4 }}>Adversarial Peer Review Complete</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                {tierCounts.tier1} Tier 1 validated, {tierCounts.tier2} Tier 2 conditional in {elapsedStr}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
