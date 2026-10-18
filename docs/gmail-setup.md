# Gmail setup (one time, about 20 minutes)

The pipeline reads newsletters from **tchow29@amherst.edu** with read-only access.
You do this once on your own computer; afterwards it runs unattended.

## 1. Label your newsletters

In Gmail (Amherst account): **Settings → See all settings → Filters and blocked addresses → Create a new filter**.

- **From:** list your newsletter senders separated by `OR`, e.g.
  `news@example.com OR briefing@example.org`
- Click **Create filter**, tick **Apply the label** → **New label** → `briefing`,
  and tick **Also apply filter to matching conversations**.

You can add senders to this filter any time; the pipeline reads whatever carries the label.

## 2. Create a Google Cloud app

1. Go to <https://console.cloud.google.com> and sign in. Try your Amherst account first.
   If it won't let you create a project, use your personal Google account; that works too.
2. Create a project named `daily-briefing`.
3. **APIs & Services → Library →** search **Gmail API → Enable**.
4. **Google Auth Platform** (called "OAuth consent screen" in older menus):
   - **Branding:** app name `daily-briefing`, your email as support and developer contact.
   - **Audience:** user type **External** (or **Internal** if it's offered under an Amherst-owned project).
     Add `tchow29@amherst.edu` as a test user.
   - **Data access → Add scopes:** `https://www.googleapis.com/auth/gmail.readonly`.
   - **Audience → Publish app** so its status is **In production**.
     *This matters:* in "Testing" status Google expires the login every 7 days and the pipeline
     silently stops. You don't need to submit for verification; it's just you.
5. **Clients → Create client →** type **Desktop app** → **Create** → **Download JSON**.
   Keep this file private; don't put it in the repo.

## 3. Log in once to get a refresh token

```bash
git clone https://github.com/timothychow113-rgb/daily-briefing.git
cd daily-briefing
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python scripts/gmail_auth.py ~/Downloads/client_secret_XXXX.json
```

A browser opens. Sign in as **tchow29@amherst.edu**.

- "Google hasn't verified this app": click **Advanced → Go to daily-briefing**. That's expected for a personal app.
- **"Access blocked" / "admin policy" / "this app is blocked":** Amherst's IT blocks outside apps.
  Stop here and tell Claude; the fallback is forwarding newsletters to your personal Gmail.

The script prints three lines (`GMAIL_CLIENT_ID=…`, `GMAIL_CLIENT_SECRET=…`, `GMAIL_REFRESH_TOKEN=…`).

## 4. Save the secrets

- **Locally:** `cp .env.example .env` and paste the three lines in.
- **GitHub:** repo **Settings → Secrets and variables → Actions → New repository secret**, one per line.

Never paste these values into chat, commits or issues.

## 5. Check it works

```bash
python -m briefing collect -v
```

You should see your labelled newsletters listed with their character counts.
