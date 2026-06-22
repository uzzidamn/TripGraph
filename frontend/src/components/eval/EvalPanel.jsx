import { useState, useRef } from 'react';
import ResultsTable from './ResultsTable';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const CATEGORIES = [
  'Guardrail', 'Constraint Extraction', 'Missing Information', 'Contradictions',
  'User Memory', 'Past-Trip Dedup', 'Destination Retrieval', 'Activity Matching',
  'Budget Validation', 'Replanning', 'Parallel Execution', 'Multi-turn',
  'Edge Cases', 'Memory Updater',
];

export default function EvalPanel() {
  const [rows, setRows]         = useState([]);
  const [running, setRunning]   = useState(false);
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [category, setCategory] = useState('');
  const [caseId, setCaseId]     = useState('');
  const abortRef                = useRef(null);

  const run = async (filter) => {
    setRunning(true);
    setRows([]);
    setProgress({ done: 0, total: 0 });

    const ctrl = new AbortController();
    abortRef.current = ctrl;

    try {
      const res = await fetch(`${API_BASE}/api/eval/run-dataset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filter: filter || null }),
        signal: ctrl.signal,
      });

      const reader = res.body.getReader();
      const dec    = new TextDecoder();
      let buf      = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        const lines = buf.split('\n');
        buf = lines.pop();
        for (const line of lines) {
          if (!line.trim()) continue;
          const obj = JSON.parse(line);
          if (obj.type === 'start') {
            // metadata event — set the total so the progress bar renders correctly
            if (obj.total === 0) {
              setRunning(false);
              return;
            }
            setProgress({ done: 0, total: obj.total });
            continue;
          }
          setRows(prev => [...prev, obj]);
          if (obj.progress) setProgress(obj.progress);
        }
      }
    } catch (e) {
      if (e.name !== 'AbortError') console.error(e);
    } finally {
      setRunning(false);
    }
  };

  const stop = () => { abortRef.current?.abort(); setRunning(false); };

  const passCount  = rows.filter(r => r.status === 'pass').length;
  const failCount  = rows.filter(r => r.status === 'fail').length;
  const errorCount = rows.filter(r => r.status === 'error').length;

  const pct = progress.total > 0
    ? Math.round((progress.done / progress.total) * 100)
    : 0;

  return (
    <div style={{ maxWidth: 900, margin: '40px auto', padding: '0 24px', fontFamily: 'system-ui, sans-serif' }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>Golden Dataset Evaluation</h1>
      <p style={{ color: '#64748b', marginBottom: 24 }}>
        Run the Bucket 2 golden dataset against the live pipeline.
      </p>

      {/* Controls */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 20 }}>
        <button
          onClick={() => run(null)}
          disabled={running}
          style={btnStyle('#3b82f6')}
        >
          Run All ({GOLDEN_DATASET_COUNT} cases)
        </button>

        <select
          value={category}
          onChange={e => setCategory(e.target.value)}
          style={inputStyle}
        >
          <option value="">Category…</option>
          {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <button
          onClick={() => category && run({ category })}
          disabled={running || !category}
          style={btnStyle('#7c3aed')}
        >
          Run Category
        </button>

        <input
          placeholder="Case ID e.g. TC001"
          value={caseId}
          onChange={e => setCaseId(e.target.value.toUpperCase())}
          style={{ ...inputStyle, width: 160 }}
        />
        <button
          onClick={() => caseId && run({ test_case_ids: [caseId] })}
          disabled={running || !caseId}
          style={btnStyle('#0891b2')}
        >
          Run Single
        </button>

        {running && (
          <button onClick={stop} style={btnStyle('#ef4444')}>Stop</button>
        )}
      </div>

      {/* Progress bar */}
      {(running || progress.done > 0) && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: '#64748b', marginBottom: 4 }}>
            <span>{progress.done} / {progress.total} completed</span>
            <span>
              <span style={{ color: '#22c55e' }}>✓ {passCount}</span>
              {' '}
              <span style={{ color: '#ef4444' }}>✗ {failCount}</span>
              {' '}
              {errorCount > 0 && <span style={{ color: '#f97316' }}>! {errorCount}</span>}
            </span>
          </div>
          <div style={{ background: '#e2e8f0', borderRadius: 4, height: 8 }}>
            <div style={{
              background: failCount > 0 ? '#ef4444' : '#22c55e',
              width: `${pct}%`,
              height: 8,
              borderRadius: 4,
              transition: 'width 0.3s',
            }} />
          </div>
        </div>
      )}

      {/* No-matches banner */}
      {!running && rows.length === 0 && progress.total === 0 && progress.done === 0 ? null : (
        !running && rows.length === 0 && progress.total > 0 && (
          <div style={{ padding: '12px 16px', background: '#fef9c3', borderRadius: 8,
                        border: '1px solid #fde047', marginBottom: 16, fontSize: 14 }}>
            No matching cases for the current filter.
          </div>
        )
      )}

      {/* Results table */}
      <ResultsTable rows={rows} />

      {!running && rows.length > 0 && (
        <p style={{ marginTop: 16, color: '#64748b', fontSize: 13 }}>
          Done — {passCount} passed, {failCount} failed, {errorCount} errors.
        </p>
      )}
    </div>
  );
}

const GOLDEN_DATASET_COUNT = 116;

const btnStyle = (bg) => ({
  background: bg,
  color: '#fff',
  border: 'none',
  borderRadius: 6,
  padding: '8px 16px',
  cursor: 'pointer',
  fontWeight: 600,
  fontSize: 14,
  opacity: 1,
});

const inputStyle = {
  border: '1px solid #cbd5e1',
  borderRadius: 6,
  padding: '8px 12px',
  fontSize: 14,
  outline: 'none',
};
