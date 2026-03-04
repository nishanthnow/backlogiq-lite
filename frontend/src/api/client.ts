import axios, { AxiosInstance } from 'axios'
import { AnalyzeRequest, AnalysisReport } from '../types'

const client: AxiosInstance = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
client.interceptors.request.use(
  (config) => {
    // Add token if it exists in localStorage
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login if needed
      localStorage.removeItem('auth_token')
    }
    return Promise.reject(error)
  }
)

export async function analyzeBacklog(request: AnalyzeRequest): Promise<AnalysisReport> {
  const response = await client.post<AnalysisReport>('/analyze', request)
  return response.data
}

export interface ProgressEvent {
  phase: string
  message?: string
  current?: number
  total?: number
}

export async function analyzeBacklogStream(
  request: AnalyzeRequest,
  onProgress: (data: ProgressEvent) => void,
  onComplete: (report: AnalysisReport) => void,
  onError: (error: string) => void
): Promise<void> {
  try {
    const response = await fetch('/api/analyze?stream=true', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      onError(`HTTP ${response.status}: ${response.statusText}`)
      return
    }

    if (!response.body) {
      onError('No response body')
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // Split by double newlines to separate events
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || '' // Keep the last incomplete part in buffer

      for (const part of parts) {
        if (!part.trim()) continue

        // Parse SSE format: "event: type\ndata: json"
        const lines = part.split('\n')
        let eventType = ''
        let eventData = ''

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.substring('event: '.length)
          } else if (line.startsWith('data: ')) {
            eventData = line.substring('data: '.length)
          }
        }

        if (!eventType || !eventData) continue

        try {
          const data = JSON.parse(eventData)

          if (eventType === 'progress') {
            onProgress(data as ProgressEvent)
          } else if (eventType === 'complete') {
            onComplete(data as AnalysisReport)
          } else if (eventType === 'error') {
            onError(data.message || 'Unknown error')
          }
        } catch (e) {
          console.error('Failed to parse SSE event', e)
        }
      }
    }
  } catch (err: any) {
    onError(err.message || 'Connection error')
  }
}

export default client

