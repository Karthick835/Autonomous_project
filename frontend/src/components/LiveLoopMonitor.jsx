import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Terminal, Cpu, CheckCircle, XCircle, AlertTriangle, Clock, Microscope, Lightbulb, Code2, ShieldCheck, FileBarChart, Database, BarChart3 } from 'lucide-react';

const API = 'http://127.0.0.1:5050';

const AGENT_CONFIG = {
  DataProfilerAgent: {
    label: 'Data Profiler',
    icon: <Microscope size={14} />,
    className: 'agent-profiler',
    logColor: 'var(--accent-cyan)',
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
  { id: 'PROFILING',       label: 'Data Profiling' },
  { id: 'HYPOTHESIZING',   label: 'Hypothesizing' },
  { id: 'EXPERIMENTATION', label: 'Experiments' },
  { id: 'VALIDATION',      label: 'Validation' },
  { id: 'REPORTING',       label: 'Reporting' },
];

// Typewriter hook
function useTypewriter(text, speed = 18) {
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

export default function LiveLoopMonitor({ sessionId, onComplete }) {
  const [logs, setLogs] = useState([]);
  const [stage, setStage] = useState('PROFILING');
  const [isFinished, setIsFinished] = useState(false);
  const [isError, setIsError] = useState(false);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [confirmedCount, setConfirmedCount] = useState(0);
  const [testedCount, setTestedCount] = useState(0);
  const [lastThought, setLastThought] = useState('');
  const logEndRef = useRef(null);
  const startTimeRef = useRef(Date.now());
  const timerRef = useRef(null);

  const typedThought = useTypewriter(lastThought, 14);

  // Elapsed timer
  useEffect(() => {
    if (isFinished) return;
    timerRef.current = setInterval(() => {
      setElapsedMs(Date.now() - startTimeRef.current);
    }, 500);
    return () => clearInterval(timerRef.current);
  }, [isFinished]);

  useEffect(() => {
    if (!sessionId) return;
    startTimeRef.current = Date.now();

    const eventSource = new EventSource(`${API}/api/stream/${sessionId}`);

    eventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.stage === 'PING') return;

        setLogs(prev => [...prev, data]);
        if (data.stage) setStage(data.stage);

        // Update thinking text
        if (data.message) setLastThought(data.message);

        // Track counts from validation messages
        if (data.stage === 'VALIDATION' && data.payload?.validation) {
          setConfirmedCount(data.payload.validation.confirmed_discoveries || 0);
          setTestedCount(data.payload.validation.total_tested || 0);
        }

        // Track experiment completions
        if (data.stage === 'EXPERIMENTATION' && data.agent === 'PythonSandbox') {
          setTestedCount(p => p + 1);
        }

        if (data.stage === 'COMPLETE') {
          setIsFinished(true);
          clearInterval(timerRef.current);
          eventSource.close();
          onComplete(sessionId);
        } else if (data.stage === 'ERROR') {
          setIsError(true);
          setIsFinished(true);
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

  const activeIdx = STAGES.findIndex(s => s.id === stage);
  const elapsed = elapsedMs / 1000;
  const elapsedStr = elapsed < 60
    ? `${elapsed.toFixed(1)}s`
    : `${Math.floor(elapsed / 60)}m ${(elapsed % 60).toFixed(0)}s`;

  return (
    <div className="fade-in" style={{ maxWidth: 1080, margin: '0 auto' }}>

      {/* ── Header ── */}
      <div className="card" style={{ padding: 'var(--space-5)', marginBottom: 'var(--space-4)' }}>
        <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-4)' }}>
          <div className="flex items-center gap-3">
            <div className="agent-avatar agent-hyp">
              <Cpu size={16} className={!isFinished ? 'spin' : ''} />
            </div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 700 }}>Autonomous AI Scientist Loop</div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                session: {sessionId}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {isError ? (
              <span className="pill pill-rose"><span className="pill-dot" />Pipeline Error</span>
            ) : isFinished ? (
              <span className="pill pill-green"><span className="pill-dot" />Complete</span>
            ) : (
              <span className="pill pill-violet"><span className="pill-dot-pulse" />Running</span>
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

      <div className="grid-2" style={{ gap: 'var(--space-4)', marginBottom: 'var(--space-4)' }}>
        {/* ── Agent Log Feed ── */}
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

        {/* ── Right panel: HUD + Thinking ── */}
        <div className="flex-col gap-4">
          {/* Mini HUD */}
          <div className="card" style={{ padding: 'var(--space-4)' }}>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: 'var(--space-3)' }}>
              Live Statistics
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
                <span className="hud-label">✅ Confirmed</span>
                <span className="hud-value confirmed">{confirmedCount}</span>
              </div>
              <div className="hud-row">
                <span className="hud-label">Status</span>
                <span className={`hud-value ${isFinished ? 'confirmed' : 'running'}`}>
                  {isError ? 'ERROR' : isFinished ? 'DONE' : 'RUNNING'}
                </span>
              </div>
            </div>
          </div>

          {/* Thinking bubble */}
          {!isFinished && lastThought && (
            <div className="thinking-panel fade-in">
              <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--accent-violet)', textTransform: 'uppercase', marginBottom: 'var(--space-2)' }}>
                🧠 Agent Reasoning
              </div>
              <div className="thinking-text">
                <span>{typedThought}</span>
                <span className="thinking-cursor" />
              </div>
            </div>
          )}

          {/* Done state */}
          {isFinished && !isError && (
            <div className="fade-in" style={{
              padding: 'var(--space-5)',
              background: 'var(--accent-green-dim)',
              border: '1px solid var(--accent-green-mid)',
              borderRadius: 'var(--radius-lg)',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: 32, marginBottom: 'var(--space-2)' }}>🎉</div>
              <div style={{ fontWeight: 700, color: 'var(--accent-green)', marginBottom: 4 }}>Investigation Complete!</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                {confirmedCount} discovery(ies) confirmed in {elapsedStr}
              </div>
            </div>
          )}

          {isError && (
            <div style={{
              padding: 'var(--space-4)',
              background: 'var(--accent-rose-dim)',
              border: '1px solid var(--accent-rose-mid)',
              borderRadius: 'var(--radius-lg)',
            }}>
              <div className="flex items-center gap-2" style={{ color: 'var(--accent-rose)', fontWeight: 600, marginBottom: 8 }}>
                <AlertTriangle size={14} /> Pipeline Error
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                Check the log for details. Verify API keys in your .env file.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
