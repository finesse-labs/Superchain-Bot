# 🛠️ Superchain Activity — by Finesse Labs × CF

A powerful automation tool designed to maintain and simulate activity across the Superchain ecosystem.

---

## 🔧 Configuration

All settings are located in `config.py` and `tasks.py`.

### ⏱️ Timings & Retry Logic
- `PAUSE_BETWEEN_WALLETS` — Delay between processing wallets.
- `PAUSE_BETWEEN_MODULES` — Delay between executing modules.
- `RETRIES` — Number of retry attempts on failure.
- `PAUSE_BETWEEN_RETRIES` — Delay before each retry.

### ⚙️ Initial Modules
- `OKX_WITHDRAW` — Withdraw ETH from OKX.
- `DISPERSE_BRIDGE` — Bridge ETH from selected networks to others via `DisperseChainsSettings`.
- Activity modules per chain are configured in `RandomDailyTxConfig`.

**Supported Modules:**

`UNISWAP`, `SUSHI_SWAP`, `MATCHA_SWAP`, `BUNGEE_SWAP`, `OWLTO_SWAP`, `SWAP_ALL_TO_ETH`, `RANDOM_SWAPS`, `RELAY_SWAP`, `INKY_SWAP`, `OKU_SWAP`, `DEFILLAMA_SWAP`, `RUBYSCORE_VOTE`, `CONTRACT_DEPLOY`, `STARGATE_BRIDGE`, `WRAPPER_UNWRAPPER`, `VENUS_DEPOSIT`, `VENUS_WITHDRAW`, `INK_GM`, and more.

> Each module's specific config can be found in the lower section of `config.py`.

---

## 📁 File Structure

- `wallets.txt` — List of EVM private keys (starting with `0x`)
- `proxies.txt` — Proxies in `username:password@host:port` format
- `tasks.py` — Route constructor for execution flows
- `config.py` — Module and global settings

---

## 🚀 Quickstart
0. Activate VENV:
   ```bash
   python -m venv menv
   source menv/bin/activate
   ```

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the app:
   ```bash
   python main.py
   ```

   - `Generate new database` — Initialize fresh DB  
   - `Work with existing database` — Operate on existing DB

---

## 🧠 About

Built with ❤️ by **Finesse Labs** & **CF** — a collaboration by builders for builders.