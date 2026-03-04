import React from 'react'
import { IssueAnalysis } from '../types'
import FindingCard from './FindingCard'
import { ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'

interface IssueDetailProps {
  issue: IssueAnalysis
  isExpanded: boolean
  onToggle: () => void
}

export default function IssueDetail({ issue, isExpanded, onToggle }: IssueDetailProps) {
  if (!isExpanded) return null

  return (
    <div className="bg-slate-50 border-t border-slate-200 p-6">
      <div className="space-y-6">
        {/* Description */}
        <div>
          <h4 className="text-sm font-semibold text-slate-800 mb-2">Description</h4>
          {issue.findings.some(f => f.field === 'description') ? (
            <p className="text-sm text-slate-700 italic">See findings below for details</p>
          ) : (
            <p className="text-sm text-slate-600">No description provided</p>
          )}
        </div>

        {/* Findings */}
        <div>
          <h4 className="text-sm font-semibold text-slate-800 mb-3">
            Findings ({issue.findings.length})
          </h4>
          <div className="space-y-3">
            {issue.findings.map((finding) => (
              <FindingCard key={finding.rule_id} finding={finding} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
