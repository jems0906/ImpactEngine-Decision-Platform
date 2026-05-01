from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta

from fastapi import WebSocket
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models import ActionEvent, ApprovalState, KPI, Rule, Severity
from app.schemas import ActionEventResponse, DashboardPayload, KPIResponse, ROIResponse, RuleResponse, ScenarioResponse


def evaluate_severity(kpi: KPI) -> Severity:
    if kpi.direction == "above":
        if kpi.value >= kpi.threshold * 1.15:
            return Severity.critical
        if kpi.value >= kpi.threshold:
            return Severity.warning
        return Severity.healthy

    if kpi.value <= kpi.threshold * 0.85:
        return Severity.critical
    if kpi.value <= kpi.threshold:
        return Severity.warning
    return Severity.healthy


def compare(value: float, comparator: str, threshold: float) -> bool:
    if comparator == ">":
        return value > threshold
    if comparator == "<":
        return value < threshold
    raise ValueError(f"Unsupported comparator: {comparator}")


def simulate_kpi(kpi: KPI) -> None:
    drift = random.uniform(-1.2, 1.6)
    if kpi.key == "delivery_delay":
        drift += 0.3
    elif kpi.key == "churn_risk":
        drift += 0.2
    elif kpi.key == "inventory_low":
        drift -= 0.4

    kpi.trend = round(drift, 2)
    kpi.value = round(max(0.5, kpi.value + drift), 2)
    kpi.severity = evaluate_severity(kpi)
    kpi.updated_at = datetime.utcnow()


def should_trigger(rule: Rule, kpi: KPI, session: Session) -> bool:
    if not rule.enabled or not compare(kpi.value, rule.comparator, rule.threshold):
        return False

    last_event = (
        session.query(ActionEvent)
        .filter(ActionEvent.rule_name == rule.name)
        .order_by(ActionEvent.created_at.desc())
        .first()
    )
    if last_event is None:
        return True

    cooldown_window = datetime.utcnow() - timedelta(minutes=rule.cooldown_minutes)
    return last_event.created_at < cooldown_window


def build_action_message(rule: Rule, kpi: KPI) -> str:
    return f"{rule.message_template} Current {kpi.name.lower()} is {kpi.value}{kpi.unit}."


def process_rules(session: Session) -> list[ActionEvent]:
    triggered_events: list[ActionEvent] = []
    kpis = {kpi.key: kpi for kpi in session.query(KPI).all()}
    for rule in session.query(Rule).filter(Rule.enabled.is_(True)).all():
        kpi = kpis.get(rule.kpi_key)
        if kpi is None or not should_trigger(rule, kpi, session):
            continue

        status = ApprovalState.required if rule.approval_required else ApprovalState.approved
        if rule.action_channel.value == "escalation" and kpi.value >= rule.threshold + 2:
            status = ApprovalState.escalated

        event = ActionEvent(
            rule_name=rule.name,
            kpi_key=kpi.key,
            kpi_value=kpi.value,
            channel=rule.action_channel,
            target=rule.action_target,
            status=status,
            message=build_action_message(rule, kpi),
            estimated_value=rule.estimated_value,
            action_cost=rule.action_cost,
        )
        session.add(event)
        triggered_events.append(event)

    session.commit()
    for event in triggered_events:
        session.refresh(event)
    return triggered_events


def serialize_dashboard(session: Session) -> DashboardPayload:
    kpis = [KPIResponse.model_validate(kpi, from_attributes=True) for kpi in session.query(KPI).order_by(KPI.id).all()]
    rules = [RuleResponse.model_validate(rule, from_attributes=True) for rule in session.query(Rule).order_by(Rule.id).all()]
    actions = [
        ActionEventResponse.model_validate(event, from_attributes=True)
        for event in session.query(ActionEvent).order_by(ActionEvent.created_at.desc()).limit(12).all()
    ]

    actions_taken = session.query(func.count(ActionEvent.id)).scalar() or 0
    estimated_value_created = session.query(func.coalesce(func.sum(ActionEvent.estimated_value), 0)).scalar() or 0
    action_cost = session.query(func.coalesce(func.sum(ActionEvent.action_cost), 0)).scalar() or 0
    roi = ROIResponse(
        actions_taken=int(actions_taken),
        estimated_value_created=float(estimated_value_created),
        action_cost=float(action_cost),
        net_roi=float(estimated_value_created - action_cost),
    )
    scenario = ScenarioResponse(
        customer="Northslope Logistics",
        operator_prompt="Alert me when delivery delays > 5%, auto-notify carriers, escalate if > 2 days.",
        current_impact="Automation cuts response time from 45 minutes to under 5 minutes.",
        value_protected=50000,
        automation_path=[
            "Monitor rolling delivery delay KPI",
            "Post Slack alert to carrier operations",
            "Open approval gate for escalation",
            "Escalate to VP Operations if risk persists",
        ],
    )
    return DashboardPayload(kpis=kpis, rules=rules, actions=actions, roi=roi, scenario=scenario)


class DashboardBroadcaster:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, payload: dict) -> None:
        disconnected = []
        for websocket in self._connections:
            try:
                await websocket.send_json(payload)
            except Exception:
                disconnected.append(websocket)
        for websocket in disconnected:
            self.disconnect(websocket)


async def run_simulation(
    broadcaster: DashboardBroadcaster,
    on_tick: Callable[[], Awaitable[None]] | None = None,
) -> None:
    settings = get_settings()
    while True:
        session = SessionLocal()
        try:
            for kpi in session.query(KPI).all():
                simulate_kpi(kpi)
            session.commit()
            process_rules(session)
            payload = serialize_dashboard(session).model_dump(mode="json")
        finally:
            session.close()

        await broadcaster.broadcast(payload)
        if on_tick is not None:
            await on_tick()
        await asyncio.sleep(settings.simulation_interval_seconds)
