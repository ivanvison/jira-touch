# Jira Touch 🔄

A Python automation tool that forces Jira issues to reindex by "touching" them in bulk. Built with Playwright for reliable browser automation.

Built using CursorAI, Composer, Claude Opus 4.5.

## 🎯 Purpose

After a massive Jira migration, you may encounter issues where hundreds of items aren't visible in the new Jira instance—even though they exist in the database. The only way to make them visible is to "touch" each issue (trigger an update that forces reindexing).

This script automates that process by:
1. Logging into your Jira instance
2. Navigating to each issue
3. Logging 1 minute of work on each issue (minimal change that triggers reindex)
4. Tracking progress and automatically retrying failed items

## ✨ Features

- **Bulk Processing**: Handle hundreds of issues in a single session
- **Automatic Retry**: Failed issues are saved back to the keys file for easy retry
- **Progress Tracking**: Real-time progress with success/failure counts
- **2FA Support**: Pauses for manual verification code entry (script assumes you have 2FA turned on)
- **Resumable**: If interrupted, just run again with the remaining keys

## 📋 Prerequisites

- Python 3.8+
- A Jira Cloud instance with Time Tracking enabled
- Your Atlassian account credentials
- Browser automation support (Chromium)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ivanvison/jira-touch.git
   cd jira-touch
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

5. **Configure environment**
   ```bash
   # Copy the example config
   cp .env.example .env
   
   # Edit .env with your credentials
   ```

## ⚙️ Configuration

Create a `.env` file in the project root (use `.env.example` as a template):

```env
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_PASSWORD=your-password-or-api-token
KEYS_FILE=keys.txt
```

| Variable | Description | Required |
|----------|-------------|----------|
| `JIRA_BASE_URL` | Your Jira Cloud instance URL (no trailing slash) | ✅ |
| `JIRA_USERNAME` | Your Atlassian account email | ✅ |
| `JIRA_PASSWORD` | Your password or API token | ✅ |
| `KEYS_FILE` | Path to file with issue keys (default: `keys.txt`) | ✅ |

## 📝 Usage

1. **Create your keys file**
   
   Create a `keys.txt` file with one Jira issue key per line:
   ```
   PROJECT-123
   PROJECT-456
   SUPPORT-789
   ```

2. **Run the script**
   ```bash
   python jira_touch.py
   ```

3. **Enter verification code**
   
   When prompted, enter the 6-digit 2FA code sent to your email/authenticator.

4. **Monitor progress**
   
   The script will display progress for each issue:
   ```
   [1/500] PROJECT-123... ✓
   [2/500] PROJECT-456... ✓
   [3/500] PROJECT-789... ✗ (timeout error)
   ```

5. **Handle failures**
   
   Failed issues are automatically saved back to `keys.txt`. Simply run the script again to retry only the failed items.

## 📊 Example Output

```
📋 Loaded 500 keys from keys.txt
🚀 Opening browser...

📋 Logging in to Jira...

🔐 Verification code required!
   Enter your 6-digit verification code: 123456
   ⏳ Waiting for login to complete...

✅ Logged in! Starting to process 500 issues...

[1/500] PROJECT-123... ✓
[2/500] PROJECT-456... ✓
...

==================================================
✅ DONE!
   Total time: 2h 15m 30s
   Successful: 498/500
   Failed: 2/500

❌ FAILED KEYS:
   - PROJECT-789
   - PROJECT-999

💾 Failed keys saved to keys.txt (re-run to retry)
==================================================
```

## 🔒 Security Notes

- **Never commit your `.env` file** – it contains sensitive credentials
- The `.gitignore` is pre-configured to exclude `.env` and `keys.txt`
- Consider using an [Atlassian API token](https://id.atlassian.com/manage-profile/security/api-tokens) instead of your password
- Issue keys may contain sensitive project information

## 🛠️ Troubleshooting

### "Menu didn't open after 10 attempts"
The issue page may be slow to load. The script will retry automatically, but you may need to increase the `slow_mo` value in the script.

### "Verification code field not found"
Your Jira instance may have a different 2FA flow. Check the selector in the script.

### Browser closes unexpectedly
Check the console output for error messages. Common causes:
- Network timeout
- Session expired
- Jira maintenance

## 📄 License

MIT License – feel free to use, modify, and distribute.

## 🤝 Contributing

Contributions welcome!

---

*Built to solve a real problem: making 400+ invisible Jira issues visible after a migration.* ✨

