import threading
import time
from dotenv import load_dotenv
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
from twilio.rest import Client
from fastapi import FastAPI, HTTPException
from fastapi.requests import Request
import requests
from urllib.parse import parse_qs
import os

load_dotenv()

FAUNA_URL = 'https://accounts.fetch.ai'
SCOPE = 'av'
CLIENT_ID = 'courierMarketplace'
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
fauna_url = os.getenv("FAUNA_URL")
redirect_uri = os.getenv("REDIRECT_URI")
access_code = None

class MyServer(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        global access_code

        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if 'code' in params:
            access_code = params['code'][0]

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{}')

app = FastAPI()


client = Client(account_sid, auth_token)

@app.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request):
    global access_code

    try:
        raw_data = await request.body()
        if not raw_data:
            raise HTTPException(status_code=400, detail="Empty request body")

        # Parse URL-encoded data into a dictionary
        message_data = parse_qs(raw_data.decode())
        print("Parsed data:", message_data)

        profile_name = message_data.get("ProfileName", ["User"])[0]
        waid = message_data.get("WaId", [""])[0]
        recipient_number = message_data.get("From", [""])[0]

        redirect_uri = 'http://localhost:3000/'
        authentication_url = f"https://accounts.fetch.ai/login/?redirect_uri={redirect_uri}&client_id=courierMarketplace&response_type=code&waid={waid}"
        response_message = f"Hi {profile_name} 👋.\nPlease authenticate yourself by following the link below 👇\n{authentication_url}"

        # Send the reply using the Twilio client
        message = client.messages.create(
            from_='whatsapp:+447897026355',
            body=response_message,
            to=f'{recipient_number}'  # Use f-string format
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


if __name__ == '__main__':
    params = {'redirect_uri': 'http://localhost:8555', 'client_id': CLIENT_ID, 'response_type': 'code', 'scope': SCOPE}
    url = f'{FAUNA_URL}/login/?{urllib.parse.urlencode(params)}'
    print(url)

    web_server = HTTPServer(('127.0.0.1', 8555), MyServer)
    print("Server started")

    def run_server():
        web_server.serve_forever()

    t = threading.Thread(target=run_server)
    t.start()
    try:
        while True:
            if access_code is not None:
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        web_server.shutdown()
        t.join()

    # Now that you have the access_code, proceed with token retrieval and other actions as needed.
    token_request_body = {
        'grant_type': 'authorization_code',
        'code': access_code,
        'client_id': CLIENT_ID,
        'scope': SCOPE,
    }

    try:
        # Perform token request
        token_response = requests.post(
            f'{FAUNA_URL}/v1/tokens',
            json=token_request_body,
        )
        token_response.raise_for_status()
        token_data = token_response.json()

        print("Token Response:", token_data)

        if 'access_token' in token_data:
            # Print token
            access_token = token_data['access_token']
            print(f"Token: {access_token}")

            # Fetch user data 
            

        else:
            print("No token received")

    except requests.exceptions.RequestException as error:
        print(f"Error during token request: {error}")
