import { useState, useEffect } from 'react'
import { datasets } from '../services/api'
import { Table2 } from 'lucide-react'

export default function DatasetBrowser() {
  const [datasetList, setDatasetList] = useState<{ path: string; name: string }[]>([])
  const [selectedPath, setSelectedPath] = useState('')
  const selectedDataset = datasetList.find((d) => d.path === selectedPath)
  const selectedDatasetName = selectedDataset?.name || selectedPath
  const [data, setData] = useState<{
    columns: string[]
    rows: Record<string, string>[]
    total_rows: number | null
    preview_rows: number
    file_size_bytes?: number
    label_counts?: Record<string, number>
  } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [limit, setLimit] = useState(100)

  const loadDatasets = () => {
    datasets.list()
      .then(({ data: res }) => setDatasetList(res.datasets || []))
      .catch(() => setDatasetList([]))
  }

  useEffect(() => {
    loadDatasets()
  }, [])

  useEffect(() => {
    if (!selectedPath) {
      setData(null)
      return
    }
    setLoading(true)
    setError('')
    datasets.preview(selectedPath, limit)
      .then(({ data: res }) => setData(res))
      .catch((err) => setError(err.response?.data?.detail || String(err)))
      .finally(() => setLoading(false))
  }, [selectedPath, limit])

  const handleDelete = async () => {
    if (!selectedPath) return
    const isFeatureFile = selectedPath.includes('features_')
    const ok = window.confirm(
      `Delete ${isFeatureFile ? 'feature file' : 'dataset'}?\n\n${selectedDatasetName}\n\n${selectedPath}`,
    )
    if (!ok) return
    try {
      setError('')
      await datasets.delete(selectedPath)
      setSelectedPath('')
      setData(null)
      loadDatasets()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg || 'Delete failed')
    }
  }

  return (
    <div>
      <h1 style={{ margin: '0 0 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Table2 size={28} />
        Dataset Browser
      </h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
        Browse and preview dataset contents. Select a dataset to view its rows.
      </p>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.85rem' }}>Dataset</label>
          <select
            value={selectedPath}
            onChange={(e) => setSelectedPath(e.target.value)}
            style={{ padding: '0.6rem', minWidth: 200, background: 'var(--bg-secondary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
          >
            <option value="">Select dataset...</option>
            {datasetList.map((d) => (
              <option key={d.path} value={d.path}>{d.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.85rem' }}>&nbsp;</label>
          <button
            type="button"
            onClick={handleDelete}
            disabled={!selectedPath}
            style={{
              padding: '0.6rem 1rem',
              background: !selectedPath ? 'var(--bg-card)' : 'var(--danger)',
              border: 'none',
              borderRadius: 4,
              color: 'white',
              cursor: !selectedPath ? 'not-allowed' : 'pointer',
            }}
          >
            Delete
          </button>
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.85rem' }}>Rows to show</label>
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            style={{ padding: '0.6rem', background: 'var(--bg-secondary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
          >
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={250}>250</option>
            <option value={500}>500</option>
          </select>
        </div>
      </div>

      {error && (
        <div style={{ padding: '1rem', background: 'rgba(248,113,113,0.2)', borderRadius: 4, color: 'var(--danger)', marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      {loading && <p style={{ color: 'var(--text-muted)' }}>Loading...</p>}

      {data && !loading && (
        <>
          <p style={{ margin: '0 0 1rem', color: 'var(--text-muted)' }}>
            Selected: <span style={{ color: 'var(--accent)', fontFamily: 'var(--font-mono)' }}>{selectedDatasetName}</span>
          </p>
          {/* Status Panel */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
            gap: '1rem',
            marginBottom: '1rem',
          }}>
            <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>Total Rows</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>{data.total_rows != null ? data.total_rows.toLocaleString() : '—'}</div>
            </div>
            <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>Preview</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>{data.preview_rows.toLocaleString()} rows</div>
            </div>
            <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>Columns</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>{data.columns.length}</div>
            </div>
            {data.file_size_bytes != null && (
              <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>File Size</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>
                  {data.file_size_bytes >= 1e6 ? `${(data.file_size_bytes / 1e6).toFixed(2)} MB` : data.file_size_bytes >= 1e3 ? `${(data.file_size_bytes / 1e3).toFixed(2)} KB` : `${data.file_size_bytes} B`}
                </div>
              </div>
            )}
            {data.label_counts && Object.keys(data.label_counts).length > 0 && (
              <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)', gridColumn: '1 / -1' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Label Distribution</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
                  {Object.entries(data.label_counts).map(([label, count]) => (
                    <span key={label} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', padding: '0.25rem 0.5rem', background: 'var(--bg-primary)', borderRadius: 4, fontSize: '0.9rem' }}>
                      <span style={{ fontWeight: 600 }}>{label}:</span>
                      <span style={{ color: 'var(--accent)' }}>{count.toLocaleString()}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div style={{ background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)', overflow: 'hidden' }}>
          <div style={{ padding: '1rem', borderBottom: '1px solid var(--bg-card)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
              Showing {data.preview_rows} rows
              {data.columns.some((c) => c.startsWith('has_') || c.includes('_count')) && (
                <span style={{ marginLeft: '0.5rem', opacity: 0.8 }}>· Feature dataset (0/1 columns are binary indicators)</span>
              )}
              {data.total_rows != null && ` of ${data.total_rows.toLocaleString}`}
              {' · '}{data.columns.length} columns
            </span>
          </div>
          <div style={{ overflowX: 'auto', maxHeight: '70vh' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-secondary)', zIndex: 1 }}>
                <tr style={{ borderBottom: '1px solid var(--bg-card)' }}>
                  <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left', fontWeight: 600, background: 'var(--bg-primary)' }}>#</th>
                  {data.columns.map((col) => (
                    <th key={col} style={{ padding: '0.5rem 0.75rem', textAlign: 'left', fontWeight: 600, background: 'var(--bg-primary)', whiteSpace: 'nowrap' }}>
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.rows.map((row, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--bg-card)' }}>
                    <td style={{ padding: '0.5rem 0.75rem', color: 'var(--text-muted)' }}>{i + 1}</td>
                    {data.columns.map((col) => (
                      <td key={col} style={{ padding: '0.5rem 0.75rem', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }} title={String(row[col] ?? '')}>
                        {String(row[col] ?? '').slice(0, 100)}
                        {(row[col] ?? '').length > 100 ? '…' : ''}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        </>
      )}

      {!selectedPath && !loading && (
        <>
          {datasetList.length > 0 && (
            <div style={{ marginBottom: '1rem', padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>Datasets Available</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>{datasetList.length}</div>
            </div>
          )}
          <div style={{ padding: '2rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)', color: 'var(--text-muted)', textAlign: 'center' }}>
            Select a dataset to preview its contents
          </div>
        </>
      )}
    </div>
  )
}
