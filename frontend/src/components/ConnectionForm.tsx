import React, { useState } from 'react'
import { AnalyzeRequest } from '../types'

interface ConnectionFormProps {
  onSubmit: (request: AnalyzeRequest) => void
  isLoading: boolean
}

export default function ConnectionForm({ onSubmit, isLoading }: ConnectionFormProps) {
  const [jiraUrl, setJiraUrl] = useState('')
  const [pat, setPat] = useState('')
  const [projectKey, setProjectKey] = useState('')
  const [issueTypes, setIssueTypes] = useState(['Story', 'Epic'])
  const [maxIssues, setMaxIssues] = useState(200)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!jiraUrl.startsWith('https://')) {
      newErrors.jiraUrl = 'URL must start with https://'
    }
    if (!pat.trim()) {
      newErrors.pat = 'Personal Access Token is required'
    }
    if (!projectKey.trim() || projectKey.length < 2 || projectKey.length > 10) {
      newErrors.projectKey = 'Project key must be 2-10 characters'
    }
    if (issueTypes.length === 0) {
      newErrors.issueTypes = 'Select at least one issue type'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleToggleIssueType = (type: string) => {
    setIssueTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    )
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return

    onSubmit({
      jira_url: jiraUrl,
      pat: pat,
      project_key: projectKey.toUpperCase(),
      issue_types: issueTypes,
      max_issues: maxIssues,
    })
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-slate-200">
      <h2 className="text-lg font-semibold text-slate-800 mb-6">Connect to Jira</h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Jira URL */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Jira Cloud URL
          </label>
          <input
            type="url"
            value={jiraUrl}
            onChange={(e) => setJiraUrl(e.target.value)}
            placeholder="https://yourorg.atlassian.net"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${
              errors.jiraUrl
                ? 'border-red-300 focus:ring-red-500'
                : 'border-slate-300 focus:ring-blue-500'
            }`}
            disabled={isLoading}
          />
          {errors.jiraUrl && <p className="text-sm text-red-600 mt-1">{errors.jiraUrl}</p>}
        </div>

        {/* Personal Access Token */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <label className="block text-sm font-medium text-slate-700">
              Personal Access Token
            </label>
            <a
              href="https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-600 hover:underline"
            >
              How to create →
            </a>
          </div>
          <input
            type="password"
            value={pat}
            onChange={(e) => setPat(e.target.value)}
            placeholder="Your PAT"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${
              errors.pat
                ? 'border-red-300 focus:ring-red-500'
                : 'border-slate-300 focus:ring-blue-500'
            }`}
            disabled={isLoading}
          />
          {errors.pat && <p className="text-sm text-red-600 mt-1">{errors.pat}</p>}
        </div>

        {/* Project Key */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Project Key
          </label>
          <input
            type="text"
            value={projectKey}
            onChange={(e) => setProjectKey(e.target.value.toUpperCase())}
            placeholder="e.g., PROJ"
            className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 ${
              errors.projectKey
                ? 'border-red-300 focus:ring-red-500'
                : 'border-slate-300 focus:ring-blue-500'
            }`}
            disabled={isLoading}
          />
          {errors.projectKey && <p className="text-sm text-red-600 mt-1">{errors.projectKey}</p>}
        </div>

        {/* Issue Types */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-3">
            Issue Types
          </label>
          <div className="flex gap-4">
            {['Epic', 'Story', 'Task', 'Bug'].map((type) => (
              <label key={type} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={issueTypes.includes(type)}
                  onChange={() => handleToggleIssueType(type)}
                  disabled={isLoading}
                  className="w-4 h-4 rounded border-slate-300"
                />
                <span className="text-sm text-slate-700">{type}</span>
              </label>
            ))}
          </div>
          {errors.issueTypes && <p className="text-sm text-red-600 mt-2">{errors.issueTypes}</p>}
        </div>

        {/* Max Issues */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Max Issues to Analyze
          </label>
          <input
            type="number"
            min="1"
            max="1000"
            value={maxIssues}
            onChange={(e) => setMaxIssues(parseInt(e.target.value) || 200)}
            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className={`w-full py-3 px-4 rounded-lg font-semibold text-white transition ${
            isLoading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-emerald-600 hover:bg-emerald-700'
          }`}
        >
          {isLoading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Analyzing...
            </span>
          ) : (
            'Analyze Backlog'
          )}
        </button>
      </form>
    </div>
  )
}
