import React, { useEffect, useState, useRef } from 'react';
import { Cpu, Terminal, ShieldCheck, FileCheck, CheckCircle, AlertTriangle } from 'lucide-react';

export default function LiveLoopMonitor({ sessionId, onComplete }) {
  const [logs, setLogs] = useState([]);
  const [stage, setStage] = useState('PROFILING');
  const [isFinished, setIsFinished] = useState(false);
  const logEndRef = useRef(null);

  useEffect(() => {
    if (!sessionId) return;

    const eventSource = new EventSource(`http://127.0.0.1:5050/api/stream/${sessionId}`);





    eventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.stage === 'PING') return;

        setLogs(prev => [...prev, data]);
        if (data.stage) setStage(data.stage);

        if (data.stage === 'COMPLETE') {
          setIsFinished(true);
          eventSource.close();
          onComplete(sessionId);
        } else if (data.stage === 'ERROR') {
          setIsFinished(true);
          eventSource.close();
        }
      } catch (err) {
        console.error("SSE parse error:", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("SSE Connection error:", err);
      eventSource.close();
    };

    return () => eventSource.close();
  }, [sessionId, onComplete]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const stages = [
    { id: 'PROFILING', label: 'Data Profiling' },
    { id: 'HYPOTHESIZING', label: 'Hypothesis Formulation' },
    { id: 'EXPERIMENTATION', label: 'Sandbox Execution' },
    { id: 'VALIDATION', label: 'FDR & Effect Validation' },
    { id: 'REPORTING', label: 'Report Generation' }
  ];

  return (
    <div className="glass-panel" style={{ padding: '24px', maxWidth: '950px', margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ padding: '10px', background: 'rgba(6, 182, 212, 0.15)', borderRadius: '10px', color: '#38bdf8' }}>
            <Cpu size={24} className="animate-spin" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 600 }}>2. Autonomous AI Scientist Loop</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Session ID: <code style={{ color: '#38bdf8' }}>{sessionId}</code></p>
          </div>
        </div>
        <span className={`badge ${isFinished ? 'confirmed' : 'running'}`}>
          {isFinished ? 'Execution Complete' : 'Thinking Loop Active'}
        </span>
      </div>

      {/* Progress Pipeline */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px', padding: '12px', background: '#090d16', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
        {stages.map((s, idx) => {
          const activeIndex = stages.findIndex(st => st.id === stage);
          const isDone = idx < activeIndex || isFinished;
          const isCurrent = s.id === stage && !isFinished;

          return (
            <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: '6px', opacity: isDone || isCurrent ? 1 : 0.4 }}>
              <div style={{
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                background: isDone ? '#10b981' : isCurrent ? '#6366f1' : '#374151',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.75rem',
                fontWeight: 700
              }}>
                {isDone ? '✓' : idx + 1}
              </div>
              <span style={{ fontSize: '0.8rem', fontWeight: 500 }}>{s.label}</span>
            </div>
          );
        })}
      </div>

      {/* Real-time Activity Feed */}
      <div style={{ background: '#090d16', borderRadius: '8px', border: '1px solid var(--border-color)', padding: '16px', height: '360px', overflowY: 'auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '12px', paddingBottom: '8px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
          <Terminal size={16} color="#9ca3af" />
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>LIVE AGENT EVENT LOGS</span>
        </div>

        {logs.map((log, i) => (
          <div key={i} style={{ marginBottom: '8px', fontSize: '0.85rem', display: 'flex', gap: '10px' }}>
            <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem', minWidth: '60px' }}>
              {log.timestamp ? new Date(log.timestamp * 1000).toISOString().substr(11, 8) : ''}
            </span>
            <span style={{
              color: log.agent === 'DataProfilerAgent' ? '#38bdf8' :
                     log.agent === 'HypothesizerAgent' ? '#a855f7' :
                     log.agent === 'CodeEngineerAgent' ? '#f59e0b' :
                     log.agent === 'StatisticalValidatorAgent' ? '#10b981' : '#e5e7eb',
              fontWeight: 600,
              minWidth: '160px'
            }}>
              [{log.agent}]
            </span>
            <span style={{ color: 'var(--text-main)' }}>{log.message}</span>
          </div>
        ))}
        <div ref={logEndRef} />
      </div>
    </div>
  );
}
