import React from 'react'
import { AnalysisReport } from '../types'

interface ScoreOverviewProps {
  report: AnalysisReport
}

function getGrade(score: number): string {
  if (score >= 90) return 'A'
  if (score >= 75) return 'B'
  if (score >= 60) return 'C'
  if (score >= 40) return 'D'
  return 'F'
}

function getScoreColor(score: number): string {
  if (score > 75) return '#10b981' // green
  if (score >= 50) return '#f59e0b' // amber
  return '#ef4444' // red
}

export default function ScoreOverview({ report }: ScoreOverviewProps) {
  const grade = getGrade(report.overall_score)
  const scoreColor = getScoreColor(report.overall_score)
  const circumference = 2 * Math.PI * 45

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-slate-200">
      <h2 className="text-lg font-semibold text-slate-800 mb-6">Backlog Health Score</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Score Circle */}
        <div className="flex flex-col items-center justify-center">
          <svg width="160" height="160" viewBox="0 0 160 160" className="mb-4">
            {/* Background circle */}
            <circle
              cx="80"
              cy="80"
              r="45"
              fill="none"
              stroke="#e2e8f0"
              strokeWidth="8"
            />
            {/* Progress circle */}
            <circle
              cx="80"
              cy="80"
              r="45"
              fill="none"
              stroke={scoreColor}
              strokeWidth="8"
              strokeDasharray={circumference}
              strokeDashoffset={circumference - (report.overall_score / 100) * circumference}
              strokeLinecap="round"
              style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}
              transform="rotate(-90 80 80)"
            />
          </svg>
          <div className="text-center">
            <p className="text-4xl font-bold" style={{ color: scoreColor }}>
              {Math.round(report.overall_score)}
            </p>
            <p className="text-slate-600 text-sm mt-2">Overall Score</p>
            <div className="mt-4">
              <span className={`inline-flex items-center justify-center w-10 h-10 rounded-full font-bold text-white ${
                grade === 'A' ? 'bg-green-600' :
                grade === 'B' ? 'bg-blue-600' :
                grade === 'C' ? 'bg-yellow-600' :
                grade === 'D' ? 'bg-orange-600' :
                'bg-red-600'
              }`}>
                {grade}
              </span>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="space-y-4">
          <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
            <p className="text-sm text-slate-600 mb-1">Total Issues Analyzed</p>
            <p className="text-3xl font-bold text-slate-800">{report.total_issues}</p>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="bg-red-50 rounded-lg p-4 border border-red-200">
              <p className="text-xs text-red-700 font-semibold mb-2">CRITICAL</p>
              <p className="text-2xl font-bold text-red-600">
                {report.severity_breakdown['critical'] || 0}
              </p>
            </div>
            <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
              <p className="text-xs text-amber-700 font-semibold mb-2">MODERATE</p>
              <p className="text-2xl font-bold text-amber-600">
                {report.severity_breakdown['moderate'] || 0}
              </p>
            </div>
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <p className="text-xs text-blue-700 font-semibold mb-2">INFO</p>
              <p className="text-2xl font-bold text-blue-600">
                {report.severity_breakdown['info'] || 0}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
