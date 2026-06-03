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

## 🚀 Setting up Zendesk Integration

Go to Zendesk Admin Center > Apps and Integrations > Webhooks.

Create a new Webhook:

#### Endpoint URL: https://your-domain.com/api/v1/webhook/zendesk

#### Request Method: POST

#### Request Format: JSON

Go to `Objects and Rules > Business Rules > Triggers`.

Create a new Trigger named Gemini AI Triage:

```
Conditions: Ticket is Created

Actions: Notify active webhook -> Select your Gemini Webhook.

JSON Body payload:

JSON
     {
       "ticket_id": "{{ticket.id}}",
       "subject": "{{ticket.subject}}",
       "description": "{{ticket.description}}"
     }
```
The Webhook-Middleware.py script uses FastAPI to handle incoming webhooks from Zendesk. It uses the modern Google GenAI SDK to analyze the ticket, enforce a clean JSON schema for triage metrics, and securely update the ticket back in Zendesk using an internal note.

## 🔒 Production Best Practices Implemented

* **Asynchronous Offloading:** Built on Python's async/await paradigms utilizing `BackgroundTasks` to prevent webhooks hanging or causing API response lag inside the primary CRM interface.
* **Agent Guardrails:** The model is entirely locked into an internal-facing persona. It cannot reply to end-users directly, completely cutting off the vector of public-facing hallucinations.
* **Strict Schema Contracts:** Leverages `response_schema` directly at the compiler level inside the Google GenAI SDK to guarantee the incoming telemetry strings match specific database keys exactly.
