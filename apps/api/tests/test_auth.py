import os
import firebase_admin
from firebase_admin import credentials, auth
import httpx
import json

# Configuration
SERVICE_ACCOUNT_PATH = 'secrets/firebase_sa.json' # Path inside container
API_URL = "http://api:8080" # docker service name

def get_web_api_key():
    key = os.environ.get("FIREBASE_WEB_API_KEY")
    if not key and __name__ == "__main__":
        print("Error: FIREBASE_WEB_API_KEY environment variable not set.")
        print("Please find your Web API Key in Firebase Console > Project Settings > General.")
        print("Run with: export FIREBASE_WEB_API_KEY=... && python3 apps/api/tests/test_auth.py")
        exit(1)
    return key

FIREBASE_WEB_API_KEY = get_web_api_key()

def setup_firebase_admin():
    if not firebase_admin._apps:
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred)
        print("Firebase Admin initialized.")

def get_id_token(custom_token):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={FIREBASE_WEB_API_KEY}"
    payload = {"token": custom_token, "returnSecureToken": True}
    
    try:
        resp = httpx.post(url, json=payload)
        if resp.status_code != 200:
            print(f"Error exchanging token: {resp.text}")
            return None
        return resp.json().get("idToken")
    except Exception as e:
        print(f"Error connecting to Identity Toolkit: {e}")
        return None

def verify_protected_endpoint(id_token):
    print(f"\nTesting {API_URL}/me with ID token...")
    headers = {"Authorization": f"Bearer {id_token}"}
    
    try:
        # Use a timeout because container networking can be tricky
        resp = httpx.get(f"{API_URL}/me", headers=headers, timeout=10.0)
        if resp.status_code == 200:
            print("SUCCESS: Authenticated request to /me passed!")
            print(f"Response: {json.dumps(resp.json(), indent=2)}")
            return True
        else:
            print(f"FAILED: Request failed with status {resp.status_code}")
            print(f"Response: {resp.text}")
            return False
    except Exception as e:
        print(f"Error contacting API: {e}")
        return False

if __name__ == "__main__":
    try:
        setup_firebase_admin()
        
        # 1. Mint Custom Token
        test_uid = "test-user-auth-script"
        custom_token = auth.create_custom_token(test_uid).decode('utf-8')
        print(f"Generated Custom Token for UID: {test_uid}")
        
        # 2. Exchange for ID Token
        id_token = get_id_token(custom_token)
        
        if id_token:
            print("Successfully exchanged for ID Token.")
            # 3. Call API
            if verify_protected_endpoint(id_token):
                exit(0)
            else:
                exit(1)
        else:
            print("Failed to get ID Token.")
            exit(1)
            
    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)
