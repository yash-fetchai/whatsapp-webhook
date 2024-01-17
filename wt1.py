from fastapi import FastAPI, HTTPException, Query
from twilio.rest import Client
from dotenv import load_dotenv
from urllib.parse import parse_qs
import os
import requests
from fastapi.requests import Request

# Load environment variables from .env file
load_dotenv()

# Retrieve Twilio Account SID, Auth Token, Fauna URL, and Redirect URI from environment variables
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
fauna_url = os.getenv("FAUNA_URL")
redirect_uri = os.getenv("REDIRECT_URI")

# Check if credentials are present
if account_sid is None or auth_token is None or fauna_url is None or redirect_uri is None:
    raise ValueError("Twilio or Fauna credentials not found in .env file")

app = FastAPI()

# Create the Twilio client
client = Client(account_sid, auth_token)
code= None

def generate_user_auth_url(waid):
    redirect_uri = 'http://localhost:3000/'
    url = f"https://accounts.fetch.ai/login/?redirect_uri={redirect_uri}&client_id=courierMarketplace&response_type=code&waid={waid}"
    return url

def authenticate_user():
    token_request_body = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": "courierMarketplace",
        "scope":"av"
    }

    try:
        # Perform token request
        token_response = requests.post(
            "https://accounts.fetch.ai/v1/tokens",
            headers={"Content-Type": "application/json"},
            json=token_request_body,
        )
        token_response.raise_for_status()
        token_data = token_response.json()

        print("Token Response:", token_data)

        if "access_token" in token_data:
            # Print token
            access_token = token_data["access_token"]
            print(f"Token: {access_token}")

            # Fetch user data
            user_data_response = requests.get(
                "https://accounts.fetch.ai/v1/profile",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_data_response.raise_for_status()
            user_data = user_data_response.json()

            # Print user data
            print("User Data:", user_data)

            # Optionally, navigate to "/auth-mobile"
            # navigate("/auth-mobile")

        else:
            print("No token received")

    except requests.exceptions.RequestException as error:
        print(f"Error: {error}")

@app.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request):
    try:
        raw_data = await request.body()
        if not raw_data:
            raise HTTPException(status_code=400, detail="Empty request body")

        # Parse URL-encoded data into a dictionary
        message_data = parse_qs(raw_data.decode())
        print("Parsed data:", message_data)

        code = message_data.get("code", [""])[0]  # Extract 'code' from the message_data

        profile_name = message_data.get("ProfileName", ["User"])[0]
        waid = message_data.get("WaId", [""])[0]
        recipient_number = message_data.get("From", [""])[0]

        response_message = f"Hi {profile_name} 👋.\nPlease authenticate yourself by following the link below 👇\n{generate_user_auth_url(waid)}"

        # Send the reply using the Twilio client
        message = client.messages.create(
            from_='whatsapp:+447897026355',
            body=response_message,
            to=f'{recipient_number}'  # Use f-string format
        )
        authenticate_user(code)
        return {"status": "success", "message_sid": message.sid}
    except HTTPException as e:
        raise e  # Re-raise the HTTPException
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
