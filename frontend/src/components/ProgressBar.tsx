import { useEffect, useState } from 'react'

interface ProgressBarProps {
  phase: string
  current?: number
  total?: number
}

export default function ProgressBar({ phase, current = 0, total = 0 }: ProgressBarProps) {
  const [elapsed, setElapsed] = useState(0)
  const [startTime] = useState(Date.now())

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)

    return () => clearInterval(timer)
  }, [startTime])

  let phaseText = 'Initializing...'
  let progressPercent = 0

  if (phase === 'connecting') {
    phaseText = 'Connecting to Jira...'
    progressPercent = 10
  } else if (phase === 'fetching') {
    phaseText = `Fetching issues...`
    progressPercent = 25
  } else if (phase === 'analyzing' && total > 0) {
    phaseText = `Running quality checks... (${current}/${total})`
    progressPercent = 25 + (current / total) * 70
  }

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m${secs}s`
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-slate-200">
      <div className="space-y-4">
        <div>
          <p className="text-sm font-medium text-slate-700 mb-2">{phaseText}</p>
          <div className="w-full bg-slate-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${Math.min(progressPercent, 100)}%` }}
            />
          </div>
        </div>
        <div className="text-xs text-slate-500 flex justify-between">
          <span>Elapsed: {formatTime(elapsed)}</span>
          {current > 0 && total > 0 && (
            <span>
              Est. remaining: {formatTime(Math.ceil((total - current) * (elapsed / current)))}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
