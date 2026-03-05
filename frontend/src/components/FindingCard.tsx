import { useState } from 'react'
import { RuleFinding } from '../types'

interface FindingCardProps {
  finding: RuleFinding
}

export default function FindingCard({ finding }: FindingCardProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(finding.suggestion)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const borderColor =
    finding.severity === 'critical' ? 'border-red-300' :
    finding.severity === 'moderate' ? 'border-amber-300' :
    'border-blue-300'

  const bgColor =
    finding.severity === 'critical' ? 'bg-red-50' :
    finding.severity === 'moderate' ? 'bg-amber-50' :
    'bg-blue-50'

  const badgeColor =
    finding.severity === 'critical' ? 'bg-red-100 text-red-700' :
    finding.severity === 'moderate' ? 'bg-amber-100 text-amber-700' :
    'bg-blue-100 text-blue-700'

  const badgeText =
    finding.severity === 'critical' ? 'CRITICAL' :
    finding.severity === 'moderate' ? 'MODERATE' :
    'INFO'

  return (
    <div className={`border-l-4 ${borderColor} ${bgColor} rounded-lg p-4`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <p className="font-semibold text-slate-800">{finding.rule_name}</p>
          <p className="text-xs text-slate-500 mt-1">{finding.rule_id}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`${badgeColor} text-xs font-semibold px-2 py-1 rounded`}>
            {badgeText}
          </span>
          <span className="text-sm font-semibold text-slate-700">
            {Math.round(finding.score)}/{Math.round(finding.max_score)}
          </span>
        </div>
      </div>

      {/* Finding */}
      <div className="mb-3">
        <p className="text-sm text-slate-700">{finding.finding}</p>
      </div>

      {/* Suggestion */}
      <div className="bg-white rounded p-3 mb-3 border border-slate-200">
        <p className="text-sm text-slate-700">{finding.suggestion}</p>
      </div>

      {/* Copy Button */}
      <button
        onClick={handleCopy}
        className="text-xs text-blue-600 hover:text-blue-700 font-medium"
      >
        {copied ? '✓ Copied!' : 'Copy suggestion'}
      </button>
    </div>
  )
}
