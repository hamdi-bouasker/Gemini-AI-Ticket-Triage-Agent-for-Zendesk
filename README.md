# Gemini-AI-Ticket-Triage-Agent-for-Zendesk
An event-driven middleware solution that connects Zendesk ITSM to Google's Gemini Pro API. This engine intercepts incoming support tickets via Zendesk webhooks, instantaneously analyzes user intent, urgency, and sentiment, and injects actionable triage telemetry and response drafts back into the ticket as private internal notes for human engineers.

## ⚙️ Architecture Workflow

1. **Trigger:** A user submits a new support ticket in Zendesk. A native Zendesk Trigger intercepts the creation event and calls our application webhook via JSON payload.
2. **Asynchronous Ingestion:** The FastAPI application captures the payload and instantly responds back to Zendesk with a `200 OK` (preventing timeouts), processing the actual heavy AI payload in a background worker threat pool.
3. **Structured AI Synthesis:** The middleware prompts Gemini 1.5 Pro under strict schema configurations. Gemini parses the ticket data and structuralizes its output into JSON containing strict category groupings, priority mapping, and customer sentiment evaluation.
4. **Enriched Triage Injection:** The engine connects back to the Zendesk REST API via OAuth tokenized basic auth, updating the ticket priority levels programmatically and writing a private, internal markdown block containing the AI diagnostics and custom draft resolution paths.

## 🛠️ Configuration & Environment Variables

The agent expects the following variables to be mapped to the host operating system or container environment:

```env
ZENDESK_SUBDOMAIN="your-company-subdomain"
ZENDESK_EMAIL="your-admin-email@company.com"
ZENDESK_API_TOKEN="your_zendesk_api_token"
GEMINI_API_KEY="your_google_gemini_api_key"
```
