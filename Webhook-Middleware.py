import os
import httpx
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
import google.generativeai as genai

app = FastAPI(title="Zendesk Gemini Triage Agent")

# ==========================================
# CONFIGURATION & ENVIRONMENT VARIABLES
# ==========================================
ZENDESK_SUBDOMAIN = os.environ.get("ZENDESK_SUBDOMAIN") # e.g., "mycompany"
ZENDESK_EMAIL = os.environ.get("ZENDESK_EMAIL")
ZENDESK_API_TOKEN = os.environ.get("ZENDESK_API_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not all([ZENDESK_SUBDOMAIN, ZENDESK_EMAIL, ZENDESK_API_TOKEN, GEMINI_API_KEY]):
    raise ValueError("Missing required environment variables.")

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Define strict structured output schema for ticket triage
TRIAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "description": "Must be one of: Hardware, Software, Access/IAM, Network, Billing"},
        "priority": {"type": "string", "description": "Must be one of: urgent, high, normal, low"},
        "sentiment": {"type": "string", "description": "Customer sentiment: frustrated, neutral, or positive"},
        "suggested_reply": {"type": "string", "description": "A polite, internal-facing response draft for the IT agent to review."}
    },
    "required": ["category", "priority", "sentiment", "suggested_reply"]
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config={
        "temperature": 0.2,
        "response_mime_type": "application/json",
        "response_schema": TRIAGE_SCHEMA
    },
    system_instruction="You are an advanced IT Support Triage AI. Analyze the incoming ticket text. Classify it, evaluate urgency, and draft a high-quality resolution step for human engineers."
)

# ==========================================
# ASYNC TRIAGE LOGIC
# ==========================================
async def triage_and_update_ticket(ticket_id: int, subject: str, description: str):
    # 1. Ask Gemini to analyze the ticket
    prompt = f"Ticket Subject: {subject}\nTicket Description: {description}"
    try:
        response = model.generate_content(prompt)
        import json
        analysis = json.loads(response.text)
    except Exception as e:
        print(f"Gemini Generation Error: {e}")
        return

    # 2. Format the Internal Note for the Zendesk Support Agent
    internal_body = (
        f"🤖 **Gemini AI Triage Diagnostics**\n"
        f"• **Category:** {analysis['category']}\n"
        f"• **Assessed Priority:** {analysis['priority'].upper()}\n"
        f"• **User Sentiment:** {analysis['sentiment']}\n\n"
        f"💡 **Suggested Draft Response:**\n{analysis['suggested_reply']}"
    )

    # 3. Build the Payload to Update Zendesk via REST API
    # This sets the priority and adds the AI diagnostics as a private internal note
    payload = {
        "ticket": {
            "priority": analysis["priority"],
            "comment": {
                "body": internal_body,
                "public": False # Ensures it is an internal note, NOT sent to customer yet
            }
        }
    }

    # 4. Authenticate and send request to Zendesk REST API
    zendesk_url = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets/{ticket_id}.json"
    auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)

    async with httpx.AsyncClient() as client:
        res = await client.put(zendesk_url, json=payload, auth=auth)
        if res.status_code == 200:
            print(f"Successfully triaged ticket #{ticket_id}")
        else:
            print(f"Failed to update Zendesk. Status: {res.status_code}, Body: {res.text}")

# ==========================================
# WEBHOOK ENDPOINT
# ==========================================
@app.post("/api/v1/webhook/zendesk")
async def zendesk_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        ticket_id = data.get("ticket_id")
        subject = data.get("subject")
        description = data.get("description")

        if not ticket_id:
            raise HTTPException(status_code=400, detail="Missing ticket_id")

        # Process the heavy AI API call asynchronously to respond to Zendesk immediately (< 200ms)
        background_tasks.add_task(triage_and_update_ticket, ticket_id, subject, description)
        
        return {"status": "accepted", "message": "Triage queued successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))