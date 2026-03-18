import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { models } from '../services/api'

export default function ModelManagement() {
  const [modelList, setModelList] = useState<{ id: string; path: string; name: string }[]>([])

  useEffect(() => {
    models.list().then(({ data }) => setModelList(data.models || [])).catch(() => setModelList([]))
  }, [])

  return (
    <div>
      <h1 style={{ margin: '0 0 1rem' }}>Model Management</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
        List, view details, and download trained models.
      </p>
      <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
        {modelList.length === 0 ? (
          <p style={{ color: 'var(--text-muted)' }}>No models found. Train a model first.</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--bg-card)' }}>
                <th style={{ textAlign: 'left', padding: '0.75rem' }}>ID</th>
                <th style={{ textAlign: 'left', padding: '0.75rem' }}>Path</th>
                <th style={{ textAlign: 'left', padding: '0.75rem' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {modelList.map((m) => (
                <tr key={m.id} style={{ borderBottom: '1px solid var(--bg-card)' }}>
                  <td style={{ padding: '0.75rem' }}>{m.id}</td>
                  <td style={{ padding: '0.75rem', color: 'var(--text-muted)' }}>{m.path}</td>
                  <td style={{ padding: '0.75rem', display: 'flex', gap: '1rem' }}>
                    <Link to={`/models/${m.id}`} style={{ color: 'var(--accent)' }}>View Details</Link>
                    <a href={`/api/models/${m.id}/download`} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent)' }}>
                      Download
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
