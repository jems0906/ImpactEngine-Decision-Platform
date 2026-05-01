# ImpactEngine Decision Platform

ImpactEngine Decision Platform is a real-time business KPI action engine. It ingests operational signals, evaluates decision rules, triggers automated actions with approval gates, and visualizes ROI from the actions taken.

## Stack

- FastAPI backend with WebSockets
- React + TypeScript frontend
- PostgreSQL for persistence
- Docker Compose for local orchestration

## Core capabilities

- Live KPI dashboard for revenue drop, inventory pressure, SLA breaches, churn risk, and delivery delays
- Rule engine for action automation such as retention workflows, carrier notifications, and executive escalation
- Approval gates for sensitive actions
- ROI calculator showing cost avoided and value created
- Scenario-driven operations workflow for delivery delays and churn prevention

## Project structure

- `backend/` FastAPI service, rule engine, persistence, and real-time event broadcaster
- `frontend/` React dashboard consuming REST and WebSocket APIs
- `docker-compose.yml` local PostgreSQL plus app services

## Run locally

### Backend

1. Create a virtual environment and install dependencies.
2. Copy `backend/.env.example` to `backend/.env` if needed.
3. Run `uvicorn app.main:app --reload --app-dir backend`.

### Frontend

1. Install dependencies in `frontend/` with `npm install`.
2. Run `npm run dev`.

### Docker Compose

Run `docker compose up --build` from the repository root.

## Demo flow

The backend seeds a sample enterprise operations environment. A background simulation updates KPI values every few seconds, evaluates rules, records actions, and broadcasts dashboard updates to connected clients.
