export type Severity = "healthy" | "warning" | "critical";
export type ApprovalState = "none" | "required" | "approved" | "escalated";
export type ActionChannel = "slack" | "email" | "workflow" | "escalation";

export interface KPI {
  key: string;
  name: string;
  unit: string;
  value: number;
  threshold: number;
  direction: string;
  trend: number;
  severity: Severity;
  description: string;
  updated_at: string;
}

export interface Rule {
  id: number;
  name: string;
  kpi_key: string;
  comparator: string;
  threshold: number;
  action_channel: ActionChannel;
  action_target: string;
  approval_required: boolean;
  message_template: string;
  estimated_value: number;
  action_cost: number;
  cooldown_minutes: number;
  enabled: boolean;
}

export interface ActionEvent {
  id: number;
  rule_name: string;
  kpi_key: string;
  kpi_value: number;
  channel: ActionChannel;
  target: string;
  status: ApprovalState;
  message: string;
  estimated_value: number;
  action_cost: number;
  created_at: string;
}

export interface DashboardPayload {
  kpis: KPI[];
  rules: Rule[];
  actions: ActionEvent[];
  roi: {
    actions_taken: number;
    estimated_value_created: number;
    action_cost: number;
    net_roi: number;
  };
  scenario: {
    customer: string;
    operator_prompt: string;
    current_impact: string;
    value_protected: number;
    automation_path: string[];
  };
}
