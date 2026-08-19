import React, { useEffect, useState } from 'react';
import { CheckCircle, AlertCircle } from 'lucide-react';

const LLM_META = {
  gemini: {
    name: 'Gemini 2.5 Flash',
    org: 'Google',
    emoji: '✦',
    color: 'var(--accent-cyan)',
    description: 'Fast, free tier available',
  },
  gpt4o: {
    name: 'GPT-4o',
    org: 'OpenAI',
    emoji: '◆',
    color: '#10A37F',
    description: 'Most capable, higher cost',
  },
  claude: {
    name: 'Claude 3.5 Sonnet',
    org: 'Anthropic',
    emoji: '◉',
    color: '#D97706',
    description: 'Superior reasoning',
  },
};

export default function LLMSelector({ selectedModel, onSelect }) {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://127.0.0.1:5050/api/models')
      .then(r => r.json())
      .then(d => {
        setModels(d.models || []);
        setLoading(false);
        // Auto-select first available
        if (!selectedModel) {
          const first = (d.models || []).find(m => m.available);
          if (first) onSelect(first.key);
        }
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="grid-3">
        {[1,2,3].map(i => (
          <div key={i} className="skeleton" style={{ height: '120px', borderRadius: 'var(--radius-lg)' }} />
        ))}
      </div>
    );
  }

  return (
    <div>
      <div className="grid-3">
        {models.map(model => {
          const meta = LLM_META[model.key] || {};
          const isSelected = selectedModel === model.key;

          return (
            <div
              key={model.key}
              id={`llm-card-${model.key}`}
              className={`llm-card ${isSelected ? 'selected' : ''} ${!model.available ? 'unavailable' : ''}`}
              onClick={() => model.available && onSelect(model.key)}
              role="button"
              tabIndex={model.available ? 0 : -1}
              onKeyDown={e => e.key === 'Enter' && model.available && onSelect(model.key)}
            >
              {/* Availability badge */}
              <div className="llm-card-badge">
                {model.available ? (
                  <CheckCircle size={13} color="var(--accent-green)" />
                ) : (
                  <AlertCircle size={13} color="var(--text-tertiary)" />
                )}
              </div>

              {/* Logo */}
              <div className="llm-card-logo" style={{
                background: isSelected ? `${meta.color}20` : 'var(--bg-elevated)',
                border: `1px solid ${isSelected ? meta.color + '40' : 'var(--card-border)'}`,
              }}>
                <span style={{ fontSize: 24, color: meta.color }}>{meta.emoji}</span>
              </div>

              <div className="llm-card-name">{meta.org}</div>
              <div className="llm-card-model">{meta.name}</div>
              <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 2 }}>
                {model.available ? meta.description : 'No API key configured'}
              </div>
            </div>
          );
        })}
      </div>

      {!models.some(m => m.available) && (
        <div style={{
          marginTop: 'var(--space-3)',
          padding: 'var(--space-3) var(--space-4)',
          background: 'var(--accent-amber-dim)',
          border: '1px solid rgba(245,158,11,0.30)',
          borderRadius: 'var(--radius-md)',
          fontSize: 12,
          color: 'var(--accent-amber)',
        }}>
          ⚠ No LLM API keys configured. Copy <code>.env.example</code> to <code>.env</code> and add at least one key.
          The system will use the built-in statistical heuristic engine as fallback.
        </div>
      )}
    </div>
  );
}
