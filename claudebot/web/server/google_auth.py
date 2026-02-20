#!/usr/bin/env python3
"""One-time OAuth authorization for Mimi's Google services.

Run this once locally to authorize Mimi. It will open a browser window
for you to sign in with msmimibot2@gmail.com and grant permissions.
The resulting token is saved to google_token.json for reuse.
"""

from google_services import get_credentials, google_status

if __name__ == "__main__":
    print("Starting Google OAuth flow for Mimi...")
    print("A browser window will open — sign in with msmimibot2@gmail.com\n")

    try:
        creds = get_credentials()
        status = google_status()
        print("\nSuccess! Mimi is now connected to Google services.")
        print(f"  Email: {status['email']}")
        print(f"  Scopes: {len(status['scopes'])} granted")
        print(f"  Token saved to: google_token.json")
        print("\nMimi can now read/send email, manage calendar, and create docs.")
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure google_credentials.json is in this directory.")
