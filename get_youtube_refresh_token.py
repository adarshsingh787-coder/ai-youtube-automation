"""One-time helper: exchange a downloaded Google Desktop OAuth client JSON for a refresh token.
Keep client_secret.json and the printed refresh token private.
"""
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
client_file = Path('client_secret.json')
if not client_file.exists():
    raise SystemExit('ERROR: client_secret.json not found. Download a Google OAuth Desktop client JSON and save it here.')
flow = InstalledAppFlow.from_client_secrets_file(str(client_file), SCOPES)
creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')
print('\n--- Copy these values into GitHub repository Actions secrets ---')
print('YOUTUBE_CLIENT_ID=' + str(creds.client_id))
print('YOUTUBE_CLIENT_SECRET=' + str(creds.client_secret))
print('YOUTUBE_REFRESH_TOKEN=' + str(creds.refresh_token))
print('\nKeep these values private. Do not commit them into GitHub.')
