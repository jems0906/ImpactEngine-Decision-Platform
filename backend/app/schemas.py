from datetime import datetime

from pydantic import BaseModel

from app.models import ActionChannel, ApprovalState, Severity


class KPIResponse(BaseModel):
    key: str
    name: str
    unit: str
    value: float
    threshold: float
    direction: str
    trend: float
    severity: Severity
    description: str
    updated_at: datetime


class RuleResponse(BaseModel):
    id: int
    name: str
    kpi_key: str
    comparator: str
    threshold: float
    action_channel: ActionChannel
    action_target: str
    approval_required: bool
    message_template: str
    estimated_value: float
    action_cost: float
    cooldown_minutes: int
    enabled: bool


class ActionEventResponse(BaseModel):
    id: int
    rule_name: str
    kpi_key: str
    kpi_value: float
    channel: ActionChannel
    target: str
    status: ApprovalState
    message: str
    estimated_value: float
    action_cost: float
    created_at: datetime


class ROIResponse(BaseModel):
    actions_taken: int
    estimated_value_created: float
    action_cost: float
    net_roi: float


class ScenarioResponse(BaseModel):
    customer: str
    operator_prompt: str
    current_impact: str
    value_protected: float
    automation_path: list[str]


class DashboardPayload(BaseModel):
    kpis: list[KPIResponse]
    rules: list[RuleResponse]
    actions: list[ActionEventResponse]
    roi: ROIResponse
    scenario: ScenarioResponse
