import { useState } from 'react'
import { datasets } from '../services/api'

export default function DatasetUpload() {
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<{ path?: string } | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return
    setResult(null)
    try {
      const { data } = await datasets.upload(file)
      setResult(data)
    } catch {
      setResult({ path: 'Upload failed' })
    }
  }

  return (
    <div>
      <h1 style={{ margin: '0 0 1rem' }}>Dataset Upload</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
        Upload CSV or Parquet dataset. Max 500MB.
      </p>
      <div style={{ maxWidth: 500, background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <input
              type="file"
              accept=".csv,.parquet"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              style={{ color: 'var(--text)' }}
            />
          </div>
          <button type="submit" disabled={!file} style={{ padding: '0.75rem 1.5rem', background: 'var(--accent)', border: 'none', borderRadius: 4, color: 'var(--bg-primary)', fontWeight: 600 }}>
            Upload
          </button>
        </form>
        {result?.path && (
          <div style={{ marginTop: '1rem', padding: '1rem', background: 'var(--bg-primary)', borderRadius: 4 }}>
            <p style={{ margin: 0 }}>Saved to: {result.path}</p>
          </div>
        )}
      </div>
    </div>
  )
}
