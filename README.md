<div align="center">
  <h1>💰 Personal Finance Application</h1>
  <p><strong>Enterprise-Grade Financial Intelligence, Automation, and Management Platform</strong></p>
</div>

Welcome to the **Personal Finance Application**, a comprehensive full-stack platform for managing and analyzing your finances. This application uses advanced multi-agent AI algorithms and a modern tech stack to help you aggregate, analyze, predict, and automate your financial life.

Designed for individuals, households, and small organizations, the platform brings enterprise-grade financial tools, automation, and intelligent insights to personal finance management.

---

## What This Application Does

This application fundamentally changes how you interact with your money:

- **Automation**: Schedule recurring transactions, trigger-based workflows, and use AI Autopilot to simulate and execute financial plans.
- **AI Assistance**: Chat with specialized AI agents (Investments, Debt, Budgeting, Income) that analyze your financial data and generate actionable insights.
- **Team Collaboration**: Work together with family or team members using shared workspaces, real-time activity feeds, and role-based access control.
- **Extensibility**: Build and install plugins to extend functionality with a secure sandbox environment.

---

## Key Features

### Core Financial Management

- **Dashboard**: Customizable command center showing your financial vitals (Net Worth, Cash Flow, Burn Rate) through interactive charts.
- **Transactions**: Full CRUD operations with rich metadata, categorization, attachments, and bulk actions.
- **Accounts**: Manage synchronized balances across Checking, Savings, Credit Cards, Loans, and Investments.
- **Budgeting**: Envelope-style budgeting with period-based tracking, rollovers, and alerts.
- **Recurring Payments**: Automatic detection and management of subscriptions and bills.

### AI-Powered Financial Copilot

Powered by Google Gemini and LangGraph, the AI system provides:

- **Expense Analysis**: Detects spending anomalies and identifies hidden subscriptions.
- **Budget Planning**: Recommends fund reallocation based on spending patterns.
- **Debt & Investment Optimization**: Proposes debt payoff strategies and investment rebalancing.
- **Receipt Scanning**: Upload receipt photos; AI extracts vendors, amounts, and creates transactions automatically.
- **Auto-Pilot**: AI drafts multi-step financial plans (e.g., "Move $500 to savings"), and you review and approve execution.

### Collaboration & Workspaces

- **Multi-Tenant Workspaces**: Create isolated environments for different households or businesses.
- **Access Control**: Owner, Admin, and Member roles with specific permissions.
- **Activity Feed**: Real-time timeline of financial events across the organization.
- **Comments & Annotations**: Discuss transactions, goals, and budgets with threaded conversations.

### Workflows & Automation

- **Category Rules**: Auto-categorize transactions using regex or matching patterns.
- **Event-Driven Actions**: Trigger custom actions based on events (e.g., low balance alerts).
- **Scheduled Jobs**: Background tasks for data aggregation and reconciliation.

### Plugin System

- **Plugin Marketplace**: Install third-party extensions in a secure sandbox environment.
- **API Access**: Generate API keys for custom tools and external integrations.
- **Webhooks**: Real-time state updates via HMAC-authenticated webhooks.

### Security

- **Authentication**: JWT with Google OAuth2 and password hashing.
- **Two-Factor Authentication**: TOTP with recovery codes.
- **Protection**: Brute-force prevention, rate limiting, CSRF protection.
- **Audit Logging**: Complete trail of system events for 365 days.

### Data & Export

- **Export Options**: CSV ledgers and PDF reports for tax preparation.
- **Monitoring**: Prometheus metrics and OpenTelemetry tracing support.

---

## Tech Stack

### Frontend

- **React 18** with Vite
- **TypeScript 5+**
- **Tailwind CSS** + Radix UI components (shadcn/ui style)
- **Zustand** for state management
- **React Query** for data fetching
- **React Hook Form** + Zod for forms
- **Recharts** for visualizations
- **Framer Motion** for animations
- **Wouter** for routing

### Backend

- **Node.js** with Express.js
- **TypeScript 5+**
- **MongoDB** (Mongoose) - 48 domain models
- **Redis** + BullMQ for background jobs
- **Passport.js** for authentication
- **Zod** for validation
- **Pino** for logging

### AI Core (Python)

- **Python 3.11+**
- **LangGraph/LangChain** for agent orchestration
- **Google Gemini** for AI tasks
- **FastAPI** for internal service

---

## Project Structure

```
personal-finance/
├── client/                     # React Frontend
│   ├── src/                    # Components, Hooks, Pages
│   └── package.json
├── server/                     # Node.js Backend
│   ├── AI_Core/                # Python AI Service
│   │   ├── agents/             # AI agent definitions
│   │   └── main.py             # FastAPI server
│   └── src/
│       ├── config/             # Configuration
│       ├── controllers/        # REST handlers
│       ├── middleware/         # Express middleware
│       ├── models/             # Database models
│       ├── services/           # Business logic
│       └── worker/             # Background jobs
├── packages/                   # Shared packages
├── docs/                       # Documentation guides
└── README.md
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [System Architecture](./docs/ARCHITECTURE.md) | Subsystem design and data flow |
| [Setup Guide](./docs/SETUP.md) | Local development setup |
| [API Reference](./docs/API.md) | REST API endpoints |
| [Database Models](./docs/DATABASE.md) | MongoDB schemas |
| [AI Core](./docs/AI_CORE.md) | AI system internals |
| [Frontend](./docs/FRONTEND.md) | Component architecture |
| [Security](./docs/SECURITY.md) | Security measures |
| [Deployment](./docs/DEPLOYMENT.md) | Deployment guides |

---

## Getting Started

### Prerequisites

- Node.js v18+
- MongoDB 6.0+
- Redis 7.0+
- Python 3.11+ (optional, for AI features)

### Installation

1. **Backend:**
```bash
cd server
npm install
cp .env.example .env
```

2. **Frontend:**
```bash
cd client
npm install
cp .env.example .env
```

### Running Locally

**Terminal 1 - Backend:**
```bash
cd server
npm run dev
# API: http://localhost:3000
```

**Terminal 2 - Frontend:**
```bash
cd client
npm run dev
# UI: http://localhost:5173
```

---

## Testing

**Server tests:**
```bash
cd server
npm test
```

**Client tests:**
```bash
cd client
npm test
```

<div align="center">
  <p>Built with ❤️ for financial clarity and independence.</p>
</div>
