export default function ResultsTable({ rows }) {
  if (!rows.length) return null;

  const badge = (status) => {
    const map = { pass: '#22c55e', fail: '#ef4444', error: '#f97316' };
    return (
      <span style={{
        background: map[status] || '#6b7280',
        color: '#fff',
        borderRadius: 4,
        padding: '2px 8px',
        fontSize: 12,
        fontWeight: 600,
        textTransform: 'uppercase',
      }}>
        {status}
      </span>
    );
  };

  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
      <thead>
        <tr style={{ background: '#f1f5f9', textAlign: 'left' }}>
          {['ID', 'Category', 'Status', 'Detail'].map(h => (
            <th key={h} style={{ padding: '8px 12px', borderBottom: '1px solid #e2e8f0' }}>{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={row.test_case_id} style={{ background: i % 2 === 0 ? '#fff' : '#f8fafc' }}>
            <td style={{ padding: '8px 12px', fontFamily: 'monospace', fontWeight: 600 }}>
              {row.test_case_id}
            </td>
            <td style={{ padding: '8px 12px', color: '#475569' }}>{row.category}</td>
            <td style={{ padding: '8px 12px' }}>{badge(row.status)}</td>
            <td style={{ padding: '8px 12px', color: '#dc2626', fontSize: 12 }}>
              {row.detail || ''}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
