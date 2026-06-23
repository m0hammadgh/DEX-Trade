#!/usr/bin/env python3
"""
DEX-Trade Bot v1.0
Monitors BITFA DEX Telegram channel for trading signals
Executes buys/sells on Solana via Jupiter + pump.fun
"""
import asyncio, json, os, re, time, base58, requests
from telethon import TelegramClient, events
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed

# ====== CONFIG ======
API_ID = 41025
API_HASH = "fb0a10e0610addd9cbd4e50bdd162618"
BITFA_CHAT_ID = -1002395777754

# Load wallet keys
with open("/tmp/wallet_keys.json") as f:
    KEYS = json.load(f)

SOLANA_ADDR = KEYS["solana"]["address"]
PRIVATE_KEY_B58 = KEYS["solana"]["private_key_b58"]
KEYPAIR = Keypair.from_base58_string(PRIVATE_KEY_B58)

SOLANA_RPC = "https://api.mainnet-beta.solana.com"
JUPITER_API = "https://api.jup.ag/swap/v1"

# Tokens
SOL_MINT = "So11111111111111111111111111111111111111112"
USDT_MINT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
PUMPFUN_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"

# Track positions: symbol -> {contract, buy_amount_sol, entry_price}
positions = {}

# ====== HELPER FUNCTIONS ======

async def get_sol_balance():
    """Get SOL balance"""
    async with AsyncClient(SOLANA_RPC) as client:
        resp = await client.get_balance(KEYPAIR.pubkey())
        return resp.value / 1e9

async def get_token_balance_and_info(mint_str):
    """Get token balance and decimals for a specific mint"""
    mint = Pubkey.from_string(mint_str)
    async with AsyncClient(SOLANA_RPC) as client:
        resp = await client.get_token_accounts_by_owner(
            KEYPAIR.pubkey(),
            {"mint": mint}
        )
        accounts = resp.value
        if accounts:
            addr = accounts[0].pubkey
            bal = await client.get_token_account_balance(addr)
            if bal.value:
                decimals = bal.value.decimals
                raw_amount = int(bal.value.amount)
                ui_amount = float(bal.value.ui_amount_string)
                return ui_amount, raw_amount, decimals
        return 0, 0, 0

def extract_signal(text):
    """Parse BITFA DEX signal message"""
    msg = text.strip()
    
    # Check if it's a buy signal
    is_buy = "#Signal" in msg and "📈" in msg
    
    # Extract contract address (between backticks or dexscreener link)
    contract = ""
    addr_match = re.search(r'`([^`]+)`', msg)
    if addr_match:
        contract = addr_match.group(1)
    
    # Extract coin symbol ($COIN)
    coin = ""
    coin_match = re.search(r'\$(\w+)', msg)
    if coin_match:
        coin = coin_match.group(1)
    
    # Extract chain
    chain = "SOL"
    if "BNB" in msg or "BSC" in msg:
        chain = "BNB"
    
    # Check if sell signal
    is_sell = False
    sell_type = ""
    sell_phrases = {
        "full": ["بفروشین", "همه رو بفروش", "سیو سود انجام شود", "همراه روند هستیم"],
        "capital": ["اصل سرمایه خارج شود", "اصل سرمایه کشیده بشه", "سرمایه خارج"],
        "partial": ["مقداری سیو سود", "سیو سود انجام شود"],
    }
    
    for stype, phrases in sell_phrases.items():
        for p in phrases:
            if p in msg:
                is_sell = True
                sell_type = stype
                break
    
    # Extract percentage (profit)
    pct = 0
    pct_match = re.search(r'(\d+)%', msg)
    if pct_match:
        pct = int(pct_match.group(1))
    
    # Extract entry price
    entry_price = 0
    price_match = re.search(r'(\d+\.?\d*)\s*$', msg.split("Contract")[0].split("Entry")[-1].strip() if "Entry" in msg else "")
    if price_match and "Signal" in msg:
        try:
            entry_price = float(price_match.group(1))
        except:
            pass
    
    return {
        "is_buy": is_buy,
        "is_sell": is_sell,
        "sell_type": sell_type,
        "coin": coin,
        "contract": contract,
        "chain": chain,
        "percentage": pct,
        "entry_price": entry_price,
        "raw": msg[:100],
    }

async def execute_buy(contract_str, signal_info):
    """Buy token using Jupiter API"""
    print(f"\n🟢 BUY signal: ${signal_info['coin']}")
    print(f"   Contract: {contract_str[:20]}...")
    
    # Get available balance
    sol_bal = await get_sol_balance()
    print(f"   SOL balance: {sol_bal:.6f}")
    
    # Reserve 0.005 SOL for gas
    trade_amount = (sol_bal - 0.005) * 0.5  # Half of available
    if trade_amount <= 0:
        print(f"   ❌ Insufficient SOL for trade")
        return False
    
    trade_lamports = int(trade_amount * 1e9)
    print(f"   Trading {trade_amount:.4f} SOL")
    
    # Get Jupiter quote
    try:
        resp = requests.get(f"{JUPITER_API}/quote", params={
            "inputMint": SOL_MINT,
            "outputMint": contract_str,
            "amount": trade_lamports,
            "slippageBps": 500,  # 5% slippage for memecoins
        }, timeout=10)
        
        if resp.status_code != 200 or "error" in resp.text:
            print(f"   ❌ Jupiter quote error: {resp.text[:100]}")
            return False
        
        quote = resp.json()
        out_amount = float(quote.get("outAmount", 0)) / 1e9
        print(f"   ✅ Quote: {trade_amount:.4f} SOL → {out_amount:.9f} tokens")
        
        # Get swap transaction
        swap_resp = requests.post(f"{JUPITER_API}/swap", json={
            "quoteResponse": quote,
            "userPublicKey": SOLANA_ADDR,
            "wrapAndUnwrapSol": True,
            "dynamicComputeUnitLimit": True,
        }, timeout=10)
        
        if swap_resp.status_code != 200:
            print(f"   ❌ Swap tx error: {swap_resp.text[:100]}")
            return False
        
        swap_data = swap_resp.json()
        
        # Sign and send transaction
        from solders.transaction import VersionedTransaction
        import base64
        
        tx_b64 = swap_data["swapTransaction"]
        tx_bytes = base64.b64decode(tx_b64)
        tx = VersionedTransaction.from_bytes(tx_bytes)
        signed = VersionedTransaction(tx.message, [KEYPAIR])
        
        async with AsyncClient(SOLANA_RPC) as client:
            sig = await client.send_raw_transaction(bytes(signed))
            print(f"   ✅ TX sent: {sig}")
            
            # Wait for confirmation
            await asyncio.sleep(3)
            return True
            
    except Exception as e:
        print(f"   ❌ Buy error: {e}")
        return False

async def execute_sell(contract_str, signal_info):
    """Sell token using Jupiter API"""
    print(f"\n🔴 SELL signal: ${signal_info['coin']}")
    
    # Get token balance
    token_ui, token_raw, token_decimals = await get_token_balance_and_info(contract_str)
    print(f"   Token balance: {token_ui:.9f} (raw: {token_raw})")
    
    if token_ui <= 0:
        print(f"   ❌ No tokens to sell")
        return False
    
    # Determine sell amount (in raw units)
    if signal_info["sell_type"] == "capital":
        # Sell 50% (recover capital)
        sell_amount = int(token_raw * 0.5)
    elif signal_info["sell_type"] == "full":
        sell_amount = int(token_raw * 0.7)  # 70%
    else:
        sell_amount = token_raw  # all
    
    # Get Jupiter quote for token → SOL
    try:
        resp = requests.get(f"{JUPITER_API}/quote", params={
            "inputMint": contract_str,
            "outputMint": SOL_MINT,
            "amount": sell_amount,
            "slippageBps": 500,
        }, timeout=10)
        
        if resp.status_code != 200 or "error" in resp.text:
            print(f"   ❌ Sell quote error: {resp.text[:100]}")
            return False
        
        quote = resp.json()
        out_sol = float(quote.get("outAmount", 0)) / 1e9
        print(f"   ✅ Quote: token → {out_sol:.6f} SOL")
        
        swap_resp = requests.post(f"{JUPITER_API}/swap", json={
            "quoteResponse": quote,
            "userPublicKey": SOLANA_ADDR,
            "wrapAndUnwrapSol": True,
            "dynamicComputeUnitLimit": True,
        }, timeout=10)
        
        if swap_resp.status_code != 200:
            print(f"   ❌ Sell tx error: {swap_resp.text[:100]}")
            return False
        
        swap_data = swap_resp.json()
        
        from solders.transaction import VersionedTransaction
        import base64
        
        tx_b64 = swap_data["swapTransaction"]
        tx_bytes = base64.b64decode(tx_b64)
        tx = VersionedTransaction.from_bytes(tx_bytes)
        signed = VersionedTransaction(tx.message, [KEYPAIR])
        
        async with AsyncClient(SOLANA_RPC) as client:
            sig = await client.send_raw_transaction(bytes(signed))
            print(f"   ✅ Sell TX sent: {sig}")
            return True
            
    except Exception as e:
        print(f"   ❌ Sell error: {e}")
        return False

# ====== TELEGRAM HANDLER ======

async def handle_signal(signal_info):
    """Process a signal from BITFA DEX"""
    print(f"\n{'='*50}")
    print(f"📨 New signal: {signal_info['raw'][:80]}")
    print(f"{'='*50}")
    
    if not signal_info["is_buy"] and not signal_info["is_sell"]:
        print("   ℹ️ Update message (no action)")
        return
    
    if signal_info["chain"] != "SOL":
        print("   ⏭️ Skipping non-SOL chain signal")
        return
    
    if signal_info["is_buy"] and signal_info["contract"]:
        await execute_buy(signal_info["contract"], signal_info)
    
    elif signal_info["is_sell"]:
        # Find position to sell
        coin = signal_info.get("coin", "")
        contract_to_sell = ""
        
        if coin and coin in positions:
            contract_to_sell = positions[coin]
        else:
            # Search positions by partial match
            for sym, addr in positions.items():
                if coin.lower() in sym.lower():
                    contract_to_sell = addr
                    break
        
        if contract_to_sell:
            await execute_sell(contract_to_sell, signal_info)
        else:
            print(f"   ℹ️ No open position for ${coin}")

async def main():
    print("🚀 DEX-Trade Bot Starting...")
    print(f"   Wallet: {SOLANA_ADDR}")
    
    # Check initial balance
    bal = await get_sol_balance()
    print(f"   Balance: {bal:.6f} SOL")
    
    # Start Telethon client
    client = TelegramClient("/root/bitfa_session", API_ID, API_HASH,
        device_model="SM-S928B",
        system_version="SDK 35",
        app_version="10.15.0",
    )
    
    await client.connect()
    if not await client.is_user_authorized():
        print("❌ Not authorized! Run QR login first.")
        return
    
    me = await client.get_me()
    print(f"   Telegram: {me.first_name}")
    
    # Get BITFA DEX entity
    bitfa = await client.get_entity(BITFA_CHAT_ID)
    print(f"   Monitoring: {bitfa.title if hasattr(bitfa,'title') else 'BITFA DEX'}")
    
    # Register message handler
    @client.on(events.NewMessage(chats=bitfa))
    async def new_message(event):
        text = event.message.text or ""
        if not text.strip():
            return
        
        signal = extract_signal(text)
        await handle_signal(signal)
    
    print("\n✅ Bot is running! Listening for signals...")
    print("   (Press Ctrl+C to stop)")
    
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ Bot stopped")
