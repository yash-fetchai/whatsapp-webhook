from fastapi import FastAPI, Request
from twilio.rest import Client
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Retrieve Twilio Account SID and Auth Token from environment variables
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

app = FastAPI()

# Create the Twilio client
client = Client(account_sid, auth_token)

@app.get('/')
def test():
    print("webhook is working")

@app.post("/whatsapp-webhook")
async def incoming_message(request: Request):
    try:
        # Use request.form() to parse the URL-encoded data
        form_data = await request.form()

        # Extract the necessary fields from the form data
        message_sid = form_data.get("SmsMessageSid")
        from_number = form_data.get("From")
        to_number = form_data.get("To")
        body = form_data.get("Body")
        num_media_str = form_data.get("NumMedia")
        if num_media_str is not None:
            num_media = int(num_media_str)
        else:
            num_media = 0

        # Handle media-related parameters if media is present
        media_content_types = []
        media_urls = []

        if num_media > 0:
            for n in range(num_media):
                media_content_types.append(form_data.get(f"MediaContentType{n}"))
                media_urls.append(form_data.get(f"MediaUrl{n}"))
            # Process media content types and URLs here

        # Log the received message
        print(f"Received message from {from_number} to {to_number}: {body}")

        # Add your logic to respond to the incoming message here if needed.

        # Now, you can also send a response if necessary
        current_time = datetime.now().strftime("%I:%M %p")
        current_date = datetime.now().strftime("%d/%m/%Y")

        message_body = f'Hello, this is a testing message sent at {current_time} IST on {current_date}'
        response = client.messages.create(
            from_='whatsapp:+14155238886',
            body=message_body,
            to='whatsapp:+919579345348'
        )

        print(response)

        return {"message": "Message received successfully"}
    except Exception as e:
        return {"error": f"Error handling incoming message: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
