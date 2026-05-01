from app.models import ActionChannel, KPI, Rule, Severity


def seed_database(session) -> None:
    if session.query(KPI).count() > 0:
        return

    kpis = [
        KPI(
            key="revenue_drop",
            name="Revenue Drop",
            unit="%",
            value=4.2,
            threshold=5.0,
            direction="above",
            trend=-1.3,
            severity=Severity.warning,
            description="Daily revenue movement against target baseline.",
        ),
        KPI(
            key="inventory_low",
            name="Inventory At Risk",
            unit="days",
            value=8.0,
            threshold=10.0,
            direction="below",
            trend=-0.8,
            severity=Severity.warning,
            description="Days of stock coverage for top-selling SKUs.",
        ),
        KPI(
            key="sla_breach",
            name="SLA Breach Risk",
            unit="%",
            value=3.1,
            threshold=4.0,
            direction="above",
            trend=0.6,
            severity=Severity.healthy,
            description="Open service requests trending toward breach.",
        ),
        KPI(
            key="churn_risk",
            name="Churn Risk",
            unit="%",
            value=28.0,
            threshold=30.0,
            direction="above",
            trend=1.8,
            severity=Severity.warning,
            description="Predicted churn exposure in strategic accounts.",
        ),
        KPI(
            key="delivery_delay",
            name="Delivery Delays",
            unit="%",
            value=4.7,
            threshold=5.0,
            direction="above",
            trend=0.9,
            severity=Severity.warning,
            description="Percentage of delayed deliveries over rolling 24 hours.",
        ),
    ]

    rules = [
        Rule(
            name="Retention Workflow Trigger",
            kpi_key="churn_risk",
            comparator=">",
            threshold=30.0,
            action_channel=ActionChannel.workflow,
            action_target="Retention squad",
            approval_required=False,
            message_template="If churn risk > 30%, trigger retention workflow for at-risk accounts.",
            estimated_value=35000,
            action_cost=2500,
            cooldown_minutes=15,
        ),
        Rule(
            name="Carrier Notification",
            kpi_key="delivery_delay",
            comparator=">",
            threshold=5.0,
            action_channel=ActionChannel.slack,
            action_target="#carrier-ops",
            approval_required=False,
            message_template="Notify carriers when delivery delays exceed 5%.",
            estimated_value=18000,
            action_cost=500,
            cooldown_minutes=10,
        ),
        Rule(
            name="Delay Executive Escalation",
            kpi_key="delivery_delay",
            comparator=">",
            threshold=7.0,
            action_channel=ActionChannel.escalation,
            action_target="VP Operations",
            approval_required=True,
            message_template="Escalate when delivery delays imply risk of 2+ day disruption.",
            estimated_value=50000,
            action_cost=1500,
            cooldown_minutes=30,
        ),
        Rule(
            name="Inventory Recovery Alert",
            kpi_key="inventory_low",
            comparator="<",
            threshold=10.0,
            action_channel=ActionChannel.email,
            action_target="supply-chain@impactengine.io",
            approval_required=True,
            message_template="Request replenishment approval when inventory coverage falls below 10 days.",
            estimated_value=22000,
            action_cost=800,
            cooldown_minutes=30,
        ),
    ]

    session.add_all(kpis)
    session.add_all(rules)
    session.commit()
