# 🎬 IMDb Top 250 Monitor & Auto-Deployment Pipeline

This monitoring service tracks the IMDb Top 250 chart. It scrapes the WAF-free mirror `http://top250.info/charts/`, parses the movies, detects ranking changes/new entries/exits, and pushes localized Chinese notifications using TMDB translations. It includes a built-in CI/CD auto-deployment pipeline using GitHub Actions.

## ✨ Features

- **Robust Scraping**: Avoids AWS WAF challenges using the lightweight `top250.info` mirror.
- **Chinese Translations**: Automatically retrieves and prioritizes Chinese titles from TMDB.
- **Multiple Notifiers**: Supports WeCom (Enterprise WeChat) Webhooks, Email, and **Personal WeChat ClawBot**.
- **Auto-Deployment**: Integrated GitHub Actions CI/CD automatically deploys updates to the server on every commit to `main`.
- **Systemd Daemons**: Run the monitor and the WeChat push receiver reliably as daemons.

---

## 🛠️ WeChat ClawBot Notification Setup

To push notifications to your personal WeChat, you can use the newly integrated WeChat ClawBot (`openclaw-weixin`) interface. It runs as a background daemon on the server and exposes a local HTTP API for the monitor script.

### 1. Initial Interactive Login
Run the bot interactively on the server to configure it and scan the login QR code:
```bash
# Activate virtualenv on the server
source /IMDB/Augment/venv/bin/activate

# Start the bot interactively
python wechat_bot.py
```
1. **Choose Provider**: Select DeepSeek or DusAPI (or just configure placeholder credentials if you only need notification push).
2. **Scan QR Code**: Scan the QR code rendered in the terminal using your personal WeChat.
3. **数字配对码**: If WeChat asks for a numeric code, enter the digits displayed on your phone into the terminal.
4. **Send Initial Message**: Once connected, **send a message (e.g. `hello`) to the bot on WeChat**. This populates the active session context token.

### 2. Configure Systemd Daemon
Install the WeChat ClawBot as a systemd service to run it continuously and handle auto-reconnections:
```bash
sudo cp /IMDB/Augment/wechat-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable wechat-bot
sudo systemctl start wechat-bot
```

### 3. Update Config file
Edit `config.env` on the server (or locally in the environment configuration) to use `wechat_clawbot`:
```env
NOTIFICATION_TYPE=wechat_clawbot
WECHAT_CLAWBOT_PUSH_URL=http://127.0.0.1:5001/send
```
If you want to send notifications to both WeCom and your personal WeChat, set:
```env
NOTIFICATION_TYPE=webhook,wechat_clawbot
```

---

## 🚀 Deployment Instructions

When you push changes to the `main` branch on GitHub:
1. The GitHub Actions workflow [.github/workflows/deploy.yml](file:///.github/workflows/deploy.yml) is triggered.
2. It logs in using the `SSH_PRIVATE_KEY` repository secret.
3. Syncs the files via `rsync` (excluding logs, databases, and configuration environments).
4. Installs updated dependencies automatically on the server.
5. Restarts the `imdb-monitor.service` daemon automatically.

---

## 📋 Systemd Services Management

To manage both daemons on the server:

### IMDb Monitor Daemon (Daily Cron)
- **Status**: `sudo systemctl status imdb-monitor.service`
- **Restart**: `sudo systemctl restart imdb-monitor.service`
- **Logs**: `sudo journalctl -u imdb-monitor.service -f`

### WeChat ClawBot Daemon (Local API & Reconnects)
- **Status**: `sudo systemctl status wechat-bot.service`
- **Restart**: `sudo systemctl restart wechat-bot.service`
- **Logs**: `sudo journalctl -u wechat-bot.service -f`
