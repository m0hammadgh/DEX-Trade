<div align="center">
  <br/>
  <img src="https://img.shields.io/badge/Solana-9945FF?style=for-the-badge&logo=solana&logoColor=white" alt="Solana"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Telegram-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram"/>
  <img src="https://img.shields.io/badge/Jupiter-FF6B35?style=for-the-badge&logo=jupiter&logoColor=white" alt="Jupiter"/>
  <br/><br/>

  # ⚡ DEX-Trade Bot

  ### Real‑time Automated Trading on Solana via Telegram Signals 🚀

  <br/>

  [![Version](https://img.shields.io/badge/version-1.1.0-blue?style=flat-square)](https://github.com/m0hammadgh/DEX-Trade)
  [![Status](https://img.shields.io/badge/status-active-success?style=flat-square)]()
  [![License](https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square)]()
  [![Made by](https://img.shields.io/badge/made%20by-M%20GH-ff69b4?style=flat-square)](https://github.com/m0hammadgh)

  <br/>

  <p align="center">
    <b>Built with ❤️ by <a href="https://github.com/m0hammadgh">M GH</a></b>
  </p>

  <br/>
</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [How It Works](#-how-it-works)
- [Signal Parsing](#-signal-parsing)
- [Trading Strategy](#-trading-strategy)
- [Getting Started](#-getting-started)
- [Configuration](#-configuration)
- [Deployment](#-deployment)
- [Tech Stack](#-tech-stack)
- [License](#-license)

---

## 🌟 Overview

**DEX-Trade Bot** is a high‑performance, automated trading bot that listens to **BITFA DEX** Telegram signal channels in real‑time, extracts buy/sell signals, and executes swaps instantly on **Solana** via the **Jupiter Aggregator**.

> Built by **M GH** — a fully autonomous trading agent that never sleeps 🤖

---

## 🎯 Key Features

| Feature | Description |
|---------|-------------|
| ⚡ **Real‑time Monitoring** | Listens 24/7 to Telegram signal groups — detects signals in **1–3 seconds** |
| 🧠 **Smart Signal Parsing** | Understands Persian/English signals; extracts coin, contract, chain, entry price |
| 🛒 **Automated Buying** | Swaps **50% of available SOL** through Jupiter for best‑price routing (5% slippage) |
| 💰 **Automated Selling** | Full, partial (70%), or capital‑protection (50%) sells based on signal type |
| 📊 **Live P&L Tracking** | Tracks positions in‑memory; calculates profit/loss per trade automatically |
| 🔔 **Push Notifications** | Sends real‑time alerts via HTTP webhook for every executed trade |
| 🔐 **Secure Wallet Mgmt** | Uses Solana keypair with Base58 private key — runs fully on your own server |
| ⛽ **Smart Gas Reserve** | Automatically reserves 0.005 SOL for transaction fees |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    📱 Telegram (BITFA DEX)                   │
│  🟢 #Signal 📈 $COIN `Contract` Entry $0.xx 🛑 بفروشین    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  🤖 DEX-Trade Bot (Python)                   │
│                                                             │
│  ┌─────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │ Telethon     │  │ Signal Parser  │  │ Position       │  │
│  │ Client       │──▶ (re + Persian  │──▶ Manager        │  │
│  │ (Event Loop) │  │  NLP)          │  │ (in‑memory)    │  │
│  └─────────────┘  └────────────────┘  └────────────────┘  │
│                           │                                 │
│                           ▼                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │             Execution Engine                          │  │
│  │  ┌──────────────┐   ┌──────────────┐                  │  │
│  │  │ Buy via      │   │ Sell via     │                  │  │
│  │  │ Jupiter API  │   │ Jupiter API  │                  │  │
│  │  └──────┬───────┘   └──────┬───────┘                  │  │
│  └─────────┼──────────────────┼─────────────────────────┘  │
└────────────┼──────────────────┼────────────────────────────┘
             │                  │
             ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    ☀️ Solana Blockchain                      │
│                                                             │
│  ┌────────────────────┐    ┌────────────────────┐          │
│  │   Jupiter DEX      │◀──▶│   DEX Aggregation   │          │
│  │   (Best Routes)    │    │  (Orca, Raydium…)   │          │
│  └────────────────────┘    └────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 How It Works

### 1. 📥 Signal Ingestion

The bot uses **Telethon** (Telegram MTProto client) to connect to the **BITFA DEX** group. Every new message triggers an event handler — **no polling, no delays**.

### 2. 🧪 Signal Parsing

The parser (function `extract_signal`) processes messages in real‑time:

```python
# Example input:
# 🟢 #Signal 📈 $WIF `EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm`
# Chain: SOL | Entry: $0.50

# Parsed output:
{
  "is_buy": True,
  "is_sell": False,
  "coin": "WIF",
  "contract": "EKpQGSJ...",
  "chain": "SOL",
  "entry_price": 0.50,
  "percentage": 0
}
```

### 3. 💱 Trade Execution

| Step | Action |
|------|--------|
| 1 | Check SOL balance |
| 2 | Reserve 0.005 SOL for gas |
| 3 | Calculate trade amount = **(balance - gas) × 50%** |
| 4 | Query Jupiter API for best swap route |
| 5 | Sign transaction with wallet keypair |
| 6 | Submit to Solana mainnet |
| 7 | Track position + send notification |

### 4. 🔔 Notifications

Every action sends a detailed **HTTP webhook notification**:

```
✅ Buy Executed
$WIF
Spent: 0.40 SOL
Tokens: 1234.567890123
New Balance: 0.41 SOL
TX: 4X7m3wq9...
```

---

## 📝 Signal Parsing

The bot understands **Persian** sell signals — here's the full map:

### Buy Signals

| Pattern | Example |
|---------|---------|
| `#Signal 📈 $COIN \`contract\`` | 🟢 #Signal 📈 $WIF \`EKpQGSJ...\` |

### Sell Signals

| Type | Persian Phrase | Action |
|------|----------------|--------|
| 🛑 **Full Sell** | `بفروشین` / `همه رو بفروش` / `سیو سود انجام شود` | Sell **70%** of position |
| 💼 **Capital Protection** | `اصل سرمایه خارج شود` / `سرمایه خارج` | Sell **50%** of position |
| 🔄 **Follow Trend** | `همراه روند هستیم` | Sell **70%** of position |

### Filters

- ✅ **SOL chain only** — signals on BNB/BSC are automatically **skipped**
- ✅ **Requires contract address** in backticks for buy execution

---

## 📈 Trading Strategy

```
SOL Balance: 1.00 SOL
    │
    ├── Reserve: 0.005 SOL (gas) ⛽
    │
    ├── Trade Amount: (1.00 - 0.005) × 50% = 0.4975 SOL
    │
    │   ╔══════════════════════════════════════╗
    │   ║    🟢 BUY → Swap via Jupiter         ║
    │   ║    50% of available SOL each signal  ║
    │   ╚══════════════════════════════════════╝
    │
    ├── ... wait for SELL signal ...
    │
    │   ╔══════════════════════════════════════╗
    │   ║    🔴 SELL → Swap tokens → SOL       ║
    │   ║    Full (70%), Capital (50%)          ║
    │   ║    P&L calculated automatically 🧮   ║
    │   ╚══════════════════════════════════════╝
    │
    └── Updated Balance: 1.00 + P&L
```

> **Why 50%?** The half‑balance strategy ensures capital preservation — you always have SOL left for the next signal, even after a losing trade.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A Solana wallet (we use **SafePal**)
- Telegram API credentials (`api_id` + `api_hash` from [my.telegram.org](https://my.telegram.org))

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/m0hammadgh/DEX-Trade.git
cd DEX-Trade

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up wallet keys
echo '{
  "solana": {
    "address": "YOUR_SOL_ADDRESS",
    "private_key_b58": "YOUR_PRIVATE_KEY_BASE58"
  }
}' > /tmp/wallet_keys.json

# 4. Update API credentials in bot.py
#    Edit API_ID and API_HASH on lines 15-16

# 5. Run QR login (first time only)
python3 qr_login.py

# 6. Launch the bot
python3 bot.py
```

---

## ⚙️ Configuration

All config is at the top of `bot.py`:

| Variable | Value | Purpose |
|----------|-------|---------|
| `API_ID` | `41025` | Telegram app ID |
| `API_HASH` | `fb0a10e0...` | Telegram app hash |
| `BITFA_CHAT_ID` | `-1002395777754` | Signal group ID |
| `SOL_MINT` | `So11111111111111111111111111111111111111112` | SOL token mint |
| `USDT_MINT` | `Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB` | USDT (Sol) mint |
| `SLIPPAGE_BPS` | `500` | 5% slippage for memecoins |
| `GAS_RESERVE` | `0.005` | SOL reserved for fees |
| `TRADE_RATIO` | `0.5` | 50% of available SOL per trade |

---

## 📦 Tech Stack

![Solana](https://img.shields.io/badge/Solana-9945FF?style=flat-square&logo=solana&logoColor=white)
![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![Telethon](https://img.shields.io/badge/Telethon-26A5E4?style=flat-square&logo=telegram&logoColor=white)
![Jupiter](https://img.shields.io/badge/Jupiter_API-FF6B35?style=flat-square&logo=jupiter&logoColor=white)
![solders](https://img.shields.io/badge/solders-0.27-E34F26?style=flat-square)
![Solana RPC](https://img.shields.io/badge/Solana_RPC-mainnet-00D4AA?style=flat-square)

| Component | Technology |
|-----------|-----------|
| 🤖 Bot Framework | **Python 3.11** |
| 📱 Telegram Client | **Telethon** (MTProto) |
| ⛓️ Blockchain SDK | **solders** + **solana.py** |
| 🔄 DEX Aggregator | **Jupiter API** (v1/quote + v1/swap) |
| 💼 Wallet | **SafePal** (Solana), Base58 keypair |
| 🔔 Notifications | **HTTP Webhook** |
| ☁️ Hosting | **Linux VPS / Dedicated Server** |

---

## 👨‍💻 Author

**DEX-Trade Bot** was created and is maintained by **M GH**.

<div align="center">
  <br/>
  <a href="https://github.com/m0hammadgh">
    <img src="https://img.shields.io/badge/GitHub-m0hammadgh-181717?style=for-the-badge&logo=github" alt="GitHub"/>
  </a>
  <br/>
  <sub>Built with ❤️, Python, and a whole lot of ☕</sub>
  <br/><br/>
</div>

---

## ⚠️ Disclaimer

> **⚠️ Trading cryptocurrencies involves substantial risk.**
> This bot is provided as‑is for **educational purposes**. The author (M GH) is not responsible for any financial losses incurred. Use at your own risk.

---

<div align="center">
  <br/>
  <a href="#-dex-trade-bot">⬆️ Back to top</a>
  <br/><br/>
  <sub>© 2025 M GH — DEX-Trade Bot</sub>
</div>
