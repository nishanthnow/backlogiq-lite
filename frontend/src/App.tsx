import React, { useState } from 'react'
import Header from './components/Header'
import ConnectionForm from './components/ConnectionForm'
import ProgressBar from './components/ProgressBar'
import ScoreOverview from './components/ScoreOverview'
import IssuesTable from './components/IssuesTable'
import { AnalyzeRequest, AnalysisReport } from './types'
import { analyzeBacklogStream } from './api/client'

export default function App() {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [report, setReport] = useState<AnalysisReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState<{
    phase: string
    current: number
    total: number
  } | null>(null)
  const [abortController, setAbortController] = useState<AbortController | null>(null)

  const handleAnalyze = async (request: AnalyzeRequest) => {
    setIsAnalyzing(true)
    setError(null)
    setReport(null)
    setProgress({ phase: 'connecting', current: 0, total: 0 })

    await analyzeBacklogStream(
      request,
      (progressData) => {
        setProgress({
          phase: progressData.phase,
          current: progressData.current || 0,
          total: progressData.total || 0,
        })
      },
      (analysisReport) => {
        setReport(analysisReport)
        setProgress(null)
        setIsAnalyzing(false)
      },
      (err) => {
        setError(err)
        setProgress(null)
        setIsAnalyzing(false)
      }
    )
  }

  const handleCancel = () => {
    if (abortController) {
      abortController.abort()
      setAbortController(null)
    }
    setIsAnalyzing(false)
    setProgress(null)
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* Connection Form */}
          <ConnectionForm onSubmit={handleAnalyze} isLoading={isAnalyzing} />

          {/* Progress Bar */}
          {isAnalyzing && progress && (
            <div className="space-y-4">
              <ProgressBar
                phase={progress.phase}
                current={progress.current}
                total={progress.total}
              />
              <button
                onClick={handleCancel}
                className="w-full py-2 px-4 bg-slate-200 hover:bg-slate-300 text-slate-800 rounded-lg font-medium transition"
              >
                Cancel Analysis
              </button>
            </div>
          )}

          {/* Error Alert */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
              <p className="font-semibold">Error</p>
              <p className="text-sm mt-1">{error}</p>
            </div>
          )}

          {/* Results */}
          {report && (
            <>
              <ScoreOverview report={report} />
              <IssuesTable report={report} />
            </>
          )}
        </div>
      </main>
    </div>
  )
}
