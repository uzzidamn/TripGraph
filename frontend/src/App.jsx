import { useState } from 'react'
import EvalPanel from './components/eval/EvalPanel'
import './App.css'

const TABS = ['Home', 'Evaluation']

function App() {
  const [tab, setTab] = useState('Home')

  return (
    <>
      {/* Nav */}
      <nav style={{
        display: 'flex', gap: 0, borderBottom: '1px solid #e2e8f0',
        background: '#fff', padding: '0 24px',
      }}>
        <span style={{ fontWeight: 700, padding: '14px 16px 14px 0', color: '#1e293b', fontSize: 16 }}>
          TripGraph AI
        </span>
        {TABS.map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              border: 'none', background: 'none', padding: '14px 16px', cursor: 'pointer',
              fontWeight: tab === t ? 700 : 400,
              color: tab === t ? '#3b82f6' : '#64748b',
              borderBottom: tab === t ? '2px solid #3b82f6' : '2px solid transparent',
              fontSize: 14,
            }}
          >
            {t}
          </button>
        ))}
      </nav>

      {/* Content */}
      {tab === 'Home' && (
        <div style={{ maxWidth: 900, margin: '60px auto', padding: '0 24px', textAlign: 'center' }}>
          <h1 style={{ fontSize: 32, fontWeight: 700, marginBottom: 8 }}>TripGraph AI</h1>
          <p style={{ color: '#64748b', fontSize: 16 }}>
            GenAI-Agentic Group Travel Planner — converts group chat into structured itineraries.
          </p>
          <p style={{ marginTop: 24, color: '#94a3b8' }}>
            Use the <strong>Evaluation</strong> tab to run the golden dataset against the live pipeline.
          </p>
        </div>
      )}

      {tab === 'Evaluation' && <EvalPanel />}
    </>
  )
}

export default App
