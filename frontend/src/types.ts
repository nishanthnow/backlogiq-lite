export interface RuleFinding {
  rule_id: string;
  rule_name: string;
  score: number;
  max_score: number;
  severity: "critical" | "moderate" | "info";
  finding: string;
  suggestion: string;
  field: string;
}

export interface IssueAnalysis {
  issue_key: string;
  issue_url: string;
  issue_type: string;
  issue_title: string;
  score: number;
  severity: "critical" | "moderate" | "info";
  findings: RuleFinding[];
}

export interface AnalysisReport {
  overall_score: number;
  total_issues: number;
  severity_breakdown: Record<string, number>;
  issues: IssueAnalysis[];
  analyzed_at: string;
  ai_enabled: boolean;
}

export interface AnalyzeRequest {
  jira_url: string;
  pat: string;
  project_key: string;
  issue_types: string[];
  max_issues: number;
}
