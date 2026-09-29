Markdown
# 📊 KPI Data Quality & Observability Platform

An automated, end-to-end data observability and quality platform designed to monitor business KPIs, detect time-series anomalies, generate AI root-cause analysis via Gemini API, dispatch interactive Slack alerts, and present insights via a Streamlit dashboard.

---

## 🏗️ Architecture

PostgreSQL (Supabase) ──► Metric Engine ──► Anomaly Detection (Z-Score/IQR)
│
┌───────────────────────┴───────────────────────┐
▼                                               ▼
Gemini AI Explainer                            Slack Webhook Alerts
│                                               │
└───────────────────────┬───────────────────────┘
▼
Streamlit Observability Dashboard


---

## 🔒 Environment Variables

The following secrets are required for both GitHub Actions and Streamlit Community Cloud:

| Key | Description |
| :--- | :--- |
| `SUPABASE_URL` | Your Supabase Project API URL (`https://<project-id>.supabase.co`) |
| `SUPABASE_KEY` | Your Supabase `anon` public key |
| `GEMINI_API_KEY` | Google AI Studio API key |
| `SLACK_WEBHOOK_URL` | Incoming Slack Webhook URL |

---

## 🛡️ Security Checklist
- [x] Zero API keys committed to Git repository history.
- [x] `.env` listed in `.gitignore`.
- [x] GitHub Secret Scanning Push Protection enabled.
- [x] Production environment credentials injected via secure secrets management.