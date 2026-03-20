import { useState, useEffect } from 'react'
import { reports, training } from '../services/api'

export default function ReportExport() {
  const [jobs, setJobs] = useState<{ job_id: string; phase?: string }[]>([])
  const [jobId, setJobId] = useState('')
  const [format, setFormat] = useState<'html' | 'markdown'>('html')
  const [result, setResult] = useState<{ path?: string; preview_url?: string } | null>(null)
  const [error, setError] = useState('')
  const [exporting, setExporting] = useState(false)
  const [previewing, setPreviewing] = useState(false)
  const [previewHtml, setPreviewHtml] = useState<string | null>(null)
  const [downloading, setDownloading] = useState(false)

  const cardStyle = {
    background: 'var(--bg-secondary)',
    padding: '1.5rem',
    borderRadius: 12,
    border: '1px solid var(--bg-card)',
  }

  const loadJobs = () =>
    training
      .list()
      .then(({ data }) =>
        setJobs((data.jobs || []).filter((j: { phase?: string }) => j.phase === 'completed')),
      )
      .catch(() => setJobs([]))

  useEffect(() => {
    loadJobs()
  }, [])

  const handleExport = async () => {
    if (!jobId) return
    setError('')
    setResult(null)
    setExporting(true)
    try {
      const { data: exported } = await reports.export(jobId, format)
      setResult(exported)
    } catch {
      setResult({ path: 'Export failed' })
      setError('Export failed')
    } finally {
      setExporting(false)
    }
  }

  const handlePreview = async () => {
    if (!jobId) return
    setError('')
    setPreviewing(true)
    setPreviewHtml(null)
    try {
      const { data } = await reports.preview(jobId, format)
      setPreviewHtml(data)
    } catch {
      setError('Preview failed')
    } finally {
      setPreviewing(false)
    }
  }

  const handleDownload = async () => {
    if (!jobId) return
    setError('')
    setDownloading(true)
    try {
      const { data } = await reports.download(jobId, format)
      const url = URL.createObjectURL(new Blob([data]))
      const ext = format === 'html' ? 'html' : 'md'
      const a = document.createElement('a')
      a.href = url
      a.download = `${jobId}_report.${ext}`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      setError('Download failed')
    } finally {
      setDownloading(false)
    }
  }

  const savedFileName = result?.path
    ? result.path.split(/[\\/]/).filter(Boolean).slice(-1)[0]
    : null

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ margin: '0 0 0.25rem', fontSize: '1.75rem' }}>Report Export</h1>
        <p style={{ color: 'var(--text-muted)', margin: 0 }}>
          Export experiment reports in <b>HTML</b> or <b>Markdown</b>, then preview and download.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', alignItems: 'start' }}>
        <div style={cardStyle}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Job</div>
              <div style={{ fontWeight: 700, marginTop: '0.25rem' }}>{jobId ? jobId : 'Select completed job'}</div>
            </div>
            <button
              type="button"
              onClick={loadJobs}
              style={{ padding: '0.5rem 0.75rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', color: 'var(--text-muted)', borderRadius: 8 }}
            >
              Refresh
            </button>
          </div>

          {error && (
            <div style={{ padding: '0.75rem', background: 'rgba(248,113,113,0.15)', border: '1px solid var(--danger)', borderRadius: 10, color: 'var(--danger)', marginBottom: '1rem' }}>
              {error}
            </div>
          )}

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem' }}>Select Job</label>
            <select
              value={jobId}
              onChange={(e) => setJobId(e.target.value)}
              style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 10, color: 'var(--text)' }}
            >
              <option value="">Select completed job...</option>
              {jobs.map((j) => (
                <option key={j.job_id} value={j.job_id}>
                  {j.job_id}
                </option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem' }}>Format</label>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value as 'html' | 'markdown')}
              style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 10, color: 'var(--text)' }}
            >
              <option value="html">HTML</option>
              <option value="markdown">Markdown</option>
            </select>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={handleExport}
              disabled={!jobId || exporting}
              style={{ padding: '0.75rem 1rem', background: 'var(--accent)', border: 'none', borderRadius: 10, color: 'var(--bg-primary)', fontWeight: 700, opacity: !jobId || exporting ? 0.7 : 1 }}
            >
              {exporting ? 'Exporting...' : 'Export'}
            </button>
            <button
              type="button"
              onClick={handlePreview}
              disabled={!jobId || previewing}
              style={{ padding: '0.75rem 1rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 10, color: 'var(--text)', fontWeight: 700, opacity: !jobId || previewing ? 0.7 : 1 }}
            >
              {previewing ? 'Loading preview...' : 'Preview'}
            </button>
            <button
              type="button"
              onClick={handleDownload}
              disabled={!jobId || downloading}
              style={{ padding: '0.75rem 1rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 10, color: 'var(--text)', fontWeight: 700, opacity: !jobId || downloading ? 0.7 : 1 }}
            >
              {downloading ? 'Downloading...' : 'Download'}
            </button>
          </div>

          {savedFileName && (
            <p style={{ marginTop: '1rem', color: 'var(--text-muted)' }}>
              Saved: <span style={{ color: 'var(--accent)', fontFamily: 'var(--font-mono)' }}>{savedFileName}</span>
            </p>
          )}
        </div>

        <div style={cardStyle}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Preview</div>
              <div style={{ fontWeight: 700, marginTop: '0.25rem' }}>
                {format === 'html' ? 'HTML Report' : 'Markdown Report'}
              </div>
            </div>
          </div>

          {previewing && <p style={{ color: 'var(--text-muted)' }}>Generating preview...</p>}
          {!previewing && !previewHtml && <p style={{ color: 'var(--text-muted)' }}>Click “Preview” to view the report here.</p>}

          {previewHtml && (
            <div style={{ marginTop: '0.75rem' }}>
              <iframe
                title="Report preview"
                style={{ width: '100%', height: 680, border: '1px solid var(--bg-card)', borderRadius: 12, background: 'white' }}
                srcDoc={previewHtml}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
