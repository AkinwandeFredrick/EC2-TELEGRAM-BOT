# Telegram AI Bot

A Telegram chatbot that gives users access to conversational AI and image generation — deployed on AWS EC2, powered by the Groq API and Pollinations AI.

---

## Features

- **AI Chat** — multi-turn conversations using Llama 3.3 70B via Groq (fast, free tier available)
- **Image Generation** — create 1024×1024 images from text prompts via Pollinations AI (no API key needed)
- **Per-user memory** — each user has their own conversation history (last 10 messages)
- **Typing indicator** — shows while the bot is waiting for a response
- **Session reset** — `/start` clears the conversation and starts fresh

---

## Commands

| Command | Description |
|---|---|
| `/start` | Reset your session and see the welcome message |
| `/image <prompt>` | Generate an image from a text description |
| Any text | Chat with the AI |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3 (async) |
| Bot framework | [python-telegram-bot](https://python-telegram-bot.org/) v20+ |
| LLM | [Groq API](https://console.groq.com) — `llama-3.3-70b-versatile` |
| Image generation | [Pollinations AI](https://pollinations.ai) — free, no auth |
| HTTP client | [httpx](https://www.python-httpx.org/) |
| Hosting | AWS EC2 (Ubuntu 22.04) |

---

## Getting Started

### Prerequisites

- Python 3.9+
- A Telegram bot token — get one from [@BotFather](https://t.me/BotFather) on Telegram
- A Groq API key — get one free at [console.groq.com](https://console.groq.com)

### 1. Clone the repository

```bash
git clone https://github.com/AkinwandeFredrick/telegram-ai-bot.git
cd telegram-ai-bot
```

### 2. Install dependencies

```bash
pip install python-telegram-bot httpx python-dotenv
```

### 3. Set up your environment variables

Copy the example file and fill in your real keys:

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder values:

```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
GROQ_API_KEY=your_groq_api_key_here
```

> **Never commit your `.env` file.** It is already listed in `.gitignore`.

### 4. Run the bot

```bash
python3 bot.py
```

You should see:
```
Bot started. Model: llama-3.3-70b-versatile
```

Open Telegram, find your bot, and send it a message to confirm it works.

---

## Deploying to AWS EC2

### Launch an instance

1. Go to the [EC2 Console](https://console.aws.amazon.com/ec2/)
2. Launch a new instance — **Ubuntu Server 22.04 LTS**, `t2.micro` (free tier)
3. Create and download a `.pem` key pair — store it safely

### Connect via SSH

```bash
chmod 400 ~/Downloads/your-key.pem
ssh -i ~/Downloads/your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### Set up the server

```bash
sudo apt update
sudo apt install python3-pip -y
pip3 install python-telegram-bot httpx
```

### Upload the bot

Run this from your local machine (not the SSH session):

```bash
scp -i ~/Downloads/your-key.pem bot.py ubuntu@YOUR_EC2_PUBLIC_IP:~/bot.py
```

### Set environment variables on the server

```bash
export TELEGRAM_TOKEN=your_token_here
export GROQ_API_KEY=your_key_here
```

To make them permanent across reboots, add the export lines to `~/.bashrc` and run `source ~/.bashrc`.

### Run as a permanent background service

Create a systemd service so the bot survives SSH disconnects and reboots:

```bash
sudo nano /etc/systemd/system/telegrambot.service
```

Paste the following:

```ini
[Unit]
Description=Telegram AI Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu
ExecStart=/usr/bin/python3 /home/ubuntu/bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Save (`Ctrl+X`, `Y`, `Enter`), then enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegrambot
sudo systemctl start telegrambot
sudo systemctl status telegrambot
```

### Useful service commands

```bash
sudo systemctl status telegrambot      # check if running
sudo systemctl restart telegrambot     # restart after code update
sudo systemctl stop telegrambot        # stop the bot
sudo journalctl -u telegrambot -f      # follow live logs
sudo journalctl -u telegrambot -n 50   # view last 50 log lines
```

---

## Project Structure

```
telegram-ai-bot/
├── bot.py            # main bot — all logic lives here
├── .env              # your real secrets (never commit this)
├── .env.example      # template showing which variables are needed
├── .gitignore        # ensures .env is never committed
└── README.md
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `TELEGRAM_TOKEN` | Your bot token from @BotFather |
| `GROQ_API_KEY` | Your API key from console.groq.com |

---

## Known Limitations

- **No persistent memory** — conversation history is lost when the bot restarts. A database (SQLite, Redis, DynamoDB) would be needed for persistence.
- **In-memory history grows unbounded** — if many unique users chat, memory usage increases with no automatic cleanup.
- **No rate limiting** — a single user could flood the Groq API and exhaust your quota.

---

## Roadmap

- [ ] Move to webhook mode for lower latency
- [ ] Add persistent conversation storage (SQLite or Redis)
- [ ] Add per-user rate limiting
- [ ] Support a configurable system prompt / bot persona
- [ ] Add `/imagine` alias for image generation
- [ ] Ship logs to CloudWatch for monitoring

---

## License

MIT — do whatever you want with this, just don't commit your API keys.
