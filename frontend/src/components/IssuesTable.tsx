import React, { useState, useMemo } from 'react'
import { AnalysisReport } from '../types'
import IssueDetail from './IssueDetail'
import { ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'

interface IssuesTableProps {
  report: AnalysisReport
}

type SortBy = 'score-asc' | 'score-desc' | 'severity' | 'key'
type FilterSeverity = 'all' | 'critical' | 'moderate' | 'info'

export default function IssuesTable({ report }: IssuesTableProps) {
  const [sortBy, setSortBy] = useState<SortBy>('severity')
  const [filterSeverity, setFilterSeverity] = useState<FilterSeverity>('all')
  const [searchText, setSearchText] = useState('')
  const [expandedKey, setExpandedKey] = useState<string | null>(null)

  const filtered = useMemo(() => {
    let items = report.issues

    // Filter by severity
    if (filterSeverity !== 'all') {
      items = items.filter((issue) => issue.severity === filterSeverity)
    }

    // Filter by search
    if (searchText) {
      const lower = searchText.toLowerCase()
      items = items.filter(
        (issue) =>
          issue.issue_key.toLowerCase().includes(lower) ||
          issue.issue_title.toLowerCase().includes(lower)
      )
    }

    return items
  }, [report.issues, filterSeverity, searchText])

  const sorted = useMemo(() => {
    const copy = [...filtered]

    if (sortBy === 'score-asc') {
      copy.sort((a, b) => a.score - b.score)
    } else if (sortBy === 'score-desc') {
      copy.sort((a, b) => b.score - a.score)
    } else if (sortBy === 'severity') {
      const severityOrder = { critical: 0, moderate: 1, info: 2 }
      copy.sort((a, b) => {
        const seqA = severityOrder[a.severity as keyof typeof severityOrder]
        const seqB = severityOrder[b.severity as keyof typeof severityOrder]
        if (seqA !== seqB) return seqA - seqB
        return a.score - b.score
      })
    } else if (sortBy === 'key') {
      copy.sort((a, b) => a.issue_key.localeCompare(b.issue_key))
    }

    return copy
  }, [filtered, sortBy])

  const getSeverityColor = (severity: string) => {
    if (severity === 'critical') return 'bg-red-100 text-red-700'
    if (severity === 'moderate') return 'bg-amber-100 text-amber-700'
    return 'bg-blue-100 text-blue-700'
  }

  const getTypeColor = (type: string) => {
    if (type === 'Epic') return 'bg-purple-100 text-purple-700'
    if (type === 'Story') return 'bg-green-100 text-green-700'
    if (type === 'Task') return 'bg-blue-100 text-blue-700'
    return 'bg-red-100 text-red-700'
  }

  const getScoreColor = (score: number) => {
    if (score > 75) return '#10b981'
    if (score >= 50) return '#f59e0b'
    return '#ef4444'
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
      <div className="p-6 border-b border-slate-200">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Issues ({sorted.length})</h2>

        {/* Controls */}
        <div className="flex flex-col gap-4">
          {/* Search */}
          <input
            type="text"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Search by issue key or title..."
            className="px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />

          {/* Filters & Sort */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <label className="text-xs font-semibold text-slate-600 mb-2 block">
                Filter by Severity
              </label>
              <div className="flex gap-2">
                {['all', 'critical', 'moderate', 'info'].map((sev) => (
                  <button
                    key={sev}
                    onClick={() => setFilterSeverity(sev as FilterSeverity)}
                    className={`px-3 py-1 rounded text-xs font-medium transition ${
                      filterSeverity === sev
                        ? sev === 'all'
                          ? 'bg-slate-800 text-white'
                          : sev === 'critical'
                          ? 'bg-red-600 text-white'
                          : sev === 'moderate'
                          ? 'bg-amber-600 text-white'
                          : 'bg-blue-600 text-white'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    {sev === 'all' ? 'All' : sev.charAt(0).toUpperCase() + sev.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex-1">
              <label className="text-xs font-semibold text-slate-600 mb-2 block">
                Sort by
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortBy)}
                title="Sort issues by"
                className="px-3 py-1 border border-slate-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="severity">Severity (High → Low)</option>
                <option value="score-asc">Score (Low → High)</option>
                <option value="score-desc">Score (High → Low)</option>
                <option value="key">Key (A → Z)</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50">
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600">KEY</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600">TYPE</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600">TITLE</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600">SCORE</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600">SEVERITY</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600">FINDINGS</th>
              <th className="px-6 py-3 text-center text-xs font-semibold text-slate-600">DETAILS</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((issue) => (
              <React.Fragment key={issue.issue_key}>
                <tr
                  className="border-b border-slate-200 hover:bg-slate-50 cursor-pointer transition"
                  onClick={() =>
                    setExpandedKey(expandedKey === issue.issue_key ? null : issue.issue_key)
                  }
                >
                  <td className="px-6 py-4 text-sm font-semibold text-blue-600">
                    <a
                      href={issue.issue_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="flex items-center gap-2 hover:underline"
                    >
                      {issue.issue_key}
                      <ExternalLink size={14} className="opacity-50" />
                    </a>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`text-xs font-semibold px-2 py-1 rounded ${getTypeColor(issue.issue_type)}`}>
                      {issue.issue_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-700 max-w-xs truncate">
                    {issue.issue_title}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold"
                        style={{ backgroundColor: getScoreColor(issue.score) }}
                        data-testid={`score-badge-${issue.issue_key}`}
                      >
                        {Math.round(issue.score)}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`text-xs font-semibold px-2 py-1 rounded ${getSeverityColor(issue.severity)}`}>
                      {issue.severity.charAt(0).toUpperCase() + issue.severity.slice(1)}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600">
                    {issue.findings.length} findings
                  </td>
                  <td className="px-6 py-4 text-center">
                    {expandedKey === issue.issue_key ? (
                      <ChevronUp size={18} className="inline text-slate-400" />
                    ) : (
                      <ChevronDown size={18} className="inline text-slate-400" />
                    )}
                  </td>
                </tr>
                <tr>
                  <td colSpan={7} className="p-0">
                    <IssueDetail
                      issue={issue}
                      isExpanded={expandedKey === issue.issue_key}
                    />
                  </td>
                </tr>
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {sorted.length === 0 && (
        <div className="p-12 text-center">
          <p className="text-slate-500">No issues match your filters.</p>
        </div>
      )}
    </div>
  )
}
