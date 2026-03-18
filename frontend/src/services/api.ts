import axios from 'axios'

// Use VITE_API_URL when proxy fails (e.g. backend on different port). Example: http://localhost:8001
const apiBase = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL.replace(/\/$/, '')}/api`
  : '/api'

const api = axios.create({
  baseURL: apiBase,
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export const auth = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  register: (data: { username: string; email: string; password: string }) =>
    api.post('/auth/register', data),
}

export const datasets = {
  list: () => api.get('/datasets/'),
  preview: (path: string, limit?: number) =>
    api.get('/datasets/preview', { params: { path, limit: limit ?? 100 } }),
  generate: (config: { total_samples: number; attack_ratio: number; output_format?: string; random_seed?: number; label_noise_ratio?: number }) =>
    api.post('/datasets/generate', config),
  generationStatus: (jobId: string) => api.get(`/datasets/generation/${jobId}/status`),
  reset: () => api.post('/datasets/reset'),
  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/datasets/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
}

export const features = {
  extract: (config: { input_path: string; output_path?: string; feature_mode: string; format?: string }) =>
    api.post('/features/extract', config),
}

export const training = {
  list: () => api.get('/training/'),
  start: (config: Record<string, unknown>) => api.post('/training/start', config),
  status: (jobId: string) => api.get(`/training/${jobId}/status`),
}

export const models = {
  list: () => api.get('/models/'),
  detail: (modelId: string) => api.get(`/models/${modelId}`),
  download: (modelId: string) => api.get(`/models/${modelId}/download`, { responseType: 'blob' }),
  reset: () => api.post('/models/reset'),
}

export const inference = {
  predict: (payload: Record<string, unknown>) => api.post('/inference/predict', payload),
}

export const experiments = {
  list: () => api.get('/experiments/'),
}

export const reports = {
  export: (jobId: string, format: string) => api.post('/reports/export', { job_id: jobId, format }),
}

export const ids = {
  analyze: (data: { method?: string; url?: string; body?: string; query_params?: string }) =>
    api.post('/ids/analyze', data),
  alerts: (params?: { limit?: number; since?: number }) => api.get('/ids/alerts', { params }),
  stats: () => api.get('/ids/stats'),
  clear: () => api.post('/ids/clear'),
}

export const robustness = {
  analyze: (config: { model_id?: string; data_path: string; test_type?: 'zero_out' | 'ablation'; top_n?: number }) =>
    api.post('/robustness/analyze', config),
}
