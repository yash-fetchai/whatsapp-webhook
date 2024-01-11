from fastapi import FastAPI, Request, HTTPException
from twilio.rest import Client
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve Twilio Account SID and Auth Token from environment variables
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

# Check if credentials are present
if account_sid is None or auth_token is None:
    raise ValueError("Twilio credentials not found in .env file")

app = FastAPI()

# Create the Twilio client
client = Client(account_sid, auth_token)


@app.get('/')
def test():
    print("webhook is working fine")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return ("webhook is working")


@app.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request):
    message_data = await request.json()
    phone_number = message_data.get("From", "")
    profile_name = message_data.get("ProfileName", "User")

    response_message = f"Hi {profile_name} 👋, what are you looking for? 💬
"


    # Send the reply using the Twilio client
    try:
        message = client.messages.create(
            from_='whatsapp:+447897026355',
            body=response_message,
            to='whatsapp:' + phone_number
        )
        return {"status": "success", "message_sid": message.sid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send reply: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
