"""One-time Gmail login. Run on your own computer, never in CI.

    python scripts/gmail_auth.py path/to/client_secret.json

A browser opens; sign in with the inbox the pipeline should read and allow read-only
access. The script prints three values to paste into .env (local) and GitHub Secrets.
"""

import json
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

from briefing.collectors.gmail import SCOPES


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    secrets_path = sys.argv[1]
    flow = InstalledAppFlow.from_client_secrets_file(secrets_path, SCOPES)
    # access_type=offline + prompt=consent guarantees Google returns a refresh token.
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    with open(secrets_path) as f:
        client = next(iter(json.load(f).values()))
    print("\nAdd these to .env and to GitHub → Settings → Secrets and variables → Actions:\n")
    print(f"GMAIL_CLIENT_ID={client['client_id']}")
    print(f"GMAIL_CLIENT_SECRET={client['client_secret']}")
    print(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}")


if __name__ == "__main__":
    main()
