import { useEffect, useState } from "react";

import { approveAction, createDashboardSocket, fetchDashboard } from "./api";
import type { DashboardPayload, KPI } from "./types";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDelta(value: number): string {
  return `${value > 0 ? "+" : ""}${value.toFixed(1)}%`;
}

function severityLabel(kpi: KPI): string {
  if (kpi.direction === "above") {
    return `${kpi.value.toFixed(1)}${kpi.unit} / threshold ${kpi.threshold}${kpi.unit}`;
  }
  return `${kpi.value.toFixed(1)} ${kpi.unit} / floor ${kpi.threshold} ${kpi.unit}`;
}

export function App() {
  const [dashboard, setDashboard] = useState<DashboardPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [approvingId, setApprovingId] = useState<number | null>(null);

  useEffect(() => {
    let socket: WebSocket | undefined;
    fetchDashboard()
      .then((payload) => {
        setDashboard(payload);
        socket = createDashboardSocket(setDashboard);
      })
      .catch((requestError: Error) => setError(requestError.message));

    return () => {
      socket?.close();
    };
  }, []);

  if (error) {
    return <main className="shell"><p className="status-card error">{error}</p></main>;
  }

  if (!dashboard) {
    return <main className="shell"><p className="status-card">Loading live KPI intelligence...</p></main>;
  }

  async function handleApprove(actionId: number): Promise<void> {
    setApprovingId(actionId);
    setError(null);
    try {
      await approveAction(actionId);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Failed to approve action");
    } finally {
      setApprovingId(null);
    }
  }

  return (
    <main className="shell">
      <section className="hero">
        <div>
          <span className="eyebrow">Real-time business KPI action engine</span>
          <h1>ImpactEngine Decision Platform</h1>
          <p className="lede">
            Connect enterprise signals, operationalize decision rules, and prove financial impact with live ROI.
          </p>
        </div>
        <div className="hero-metrics">
          <div className="stat-card">
            <span>Actions taken</span>
            <strong>{dashboard.roi.actions_taken}</strong>
          </div>
          <div className="stat-card accent">
            <span>Net ROI</span>
            <strong>{formatCurrency(dashboard.roi.net_roi)}</strong>
          </div>
        </div>
      </section>

      <section className="panel-grid kpi-grid">
        {dashboard.kpis.map((kpi) => (
          <article key={kpi.key} className={`kpi-card ${kpi.severity}`}>
            <header>
              <span>{kpi.name}</span>
              <strong>{kpi.value.toFixed(1)}{kpi.unit}</strong>
            </header>
            <p>{kpi.description}</p>
            <footer>
              <span>{severityLabel(kpi)}</span>
              <span>{formatDelta(kpi.trend)}</span>
            </footer>
          </article>
        ))}
      </section>

      <section className="panel-grid overview-grid">
        <article className="panel roi-panel">
          <div className="panel-header">
            <h2>ROI Calculator</h2>
            <span>Value created vs. action cost</span>
          </div>
          <div className="roi-metrics">
            <div>
              <span>Estimated value</span>
              <strong>{formatCurrency(dashboard.roi.estimated_value_created)}</strong>
            </div>
            <div>
              <span>Action cost</span>
              <strong>{formatCurrency(dashboard.roi.action_cost)}</strong>
            </div>
            <div>
              <span>Net ROI</span>
              <strong>{formatCurrency(dashboard.roi.net_roi)}</strong>
            </div>
          </div>
        </article>

        <article className="panel scenario-panel">
          <div className="panel-header">
            <h2>Customer Scenario</h2>
            <span>{dashboard.scenario.customer}</span>
          </div>
          <p className="scenario-prompt">{dashboard.scenario.operator_prompt}</p>
          <p>{dashboard.scenario.current_impact}</p>
          <strong className="scenario-value">{formatCurrency(dashboard.scenario.value_protected)} / month protected</strong>
          <ul className="timeline">
            {dashboard.scenario.automation_path.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ul>
        </article>
      </section>

      <section className="panel-grid overview-grid">
        <article className="panel">
          <div className="panel-header">
            <h2>Rule Engine</h2>
            <span>Automated and approval-gated actions</span>
          </div>
          <div className="rule-list">
            {dashboard.rules.map((rule) => (
              <div key={rule.id} className="rule-item">
                <div>
                  <strong>{rule.name}</strong>
                  <p>{rule.message_template}</p>
                </div>
                <div className="rule-meta">
                  <span>{rule.kpi_key} {rule.comparator} {rule.threshold}</span>
                  <span>{rule.action_channel} → {rule.action_target}</span>
                  <span>{rule.approval_required ? "Approval gate" : "Auto-approved"}</span>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-header">
            <h2>Action Feed</h2>
            <span>Slack, email, workflow, escalation</span>
          </div>
          <div className="action-list">
            {dashboard.actions.map((action) => (
              <div key={action.id} className="action-item">
                <div>
                  <strong>{action.rule_name}</strong>
                  <p>{action.message}</p>
                </div>
                <div className="action-meta">
                  <span>{action.channel} → {action.target}</span>
                  <span className={`badge ${action.status}`}>{action.status}</span>
                  <span>{formatCurrency(action.estimated_value)} value</span>
                  {action.status === "required" ? (
                    <button
                      className="approve-button"
                      onClick={() => void handleApprove(action.id)}
                      disabled={approvingId === action.id}
                      type="button"
                    >
                      {approvingId === action.id ? "Approving..." : "Approve action"}
                    </button>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        </article>
      </section>
    </main>
  );
}
