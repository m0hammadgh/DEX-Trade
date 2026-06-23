#!/usr/bin/env node
/**
 * One-time USDT → SOL swap using Jupiter API v1
 */
const { Connection, Keypair, VersionedTransaction } = require('@solana/web3.js');
const bs58 = require('bs58').default;
const fetch = (...args) => import('node-fetch').then(m => m.default(...args));

const RPC = 'https://api.mainnet-beta.solana.com';
const connection = new Connection(RPC, 'confirmed');

const USDT_MINT = 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB';
const SOL_MINT = 'So11111111111111111111111111111111111111112';

async function main() {
  const keypair = Keypair.fromSecretKey(bs58.decode(process.env.PRIVATE_KEY_B58));
  const wallet = keypair.publicKey.toBase58();
  console.log(`Wallet: ${wallet}`);

  // Get USDT balance via RPC
  const tokenAccounts = await connection.getTokenAccountsByOwner(keypair.publicKey, {
    mint: new (require('@solana/web3.js').PublicKey)(USDT_MINT),
  });
  
  if (tokenAccounts.value.length === 0) {
    console.log('No USDT token account');
    return;
  }
  
  const balanceResp = await connection.getTokenAccountBalance(tokenAccounts.value[0].pubkey);
  const usdtBalance = parseFloat(balanceResp.value.uiAmount);
  console.log(`USDT balance: ${usdtBalance}`);

  const swapAmount = Math.floor(usdtBalance * 0.99 * 1e6); // 99% in raw
  console.log(`Swapping ${(swapAmount/1e6).toFixed(2)} USDT → SOL`);

  // Get quote from Jupiter API
  const quoteUrl = `https://api.jup.ag/swap/v1/quote?inputMint=${USDT_MINT}&outputMint=${SOL_MINT}&amount=${swapAmount}&slippageBps=100`;
  const quoteResp = await fetch(quoteUrl);
  const quote = await quoteResp.json();
  
  if (!quote.outAmount) {
    console.log(`❌ Quote failed: ${JSON.stringify(quote)}`);
    return;
  }
  
  const outSol = parseInt(quote.outAmount) / 1e9;
  console.log(`✅ Quote: ${outSol.toFixed(4)} SOL`);

  // Get swap transaction
  const swapResp = await fetch('https://api.jup.ag/swap/v1/swap', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      quoteResponse: quote,
      userPublicKey: wallet,
      wrapAndUnwrapSol: true,
      dynamicComputeUnitLimit: true,
    }),
  });

  const swapData = await swapResp.json();
  
  if (!swapData.swapTransaction) {
    console.log(`❌ Swap failed: ${JSON.stringify(swapData).substring(0, 200)}`);
    return;
  }

  // Decode, sign and send
  const txBuffer = Buffer.from(swapData.swapTransaction, 'base64');
  const tx = VersionedTransaction.deserialize(txBuffer);
  tx.sign([keypair]);
  
  console.log('Sending transaction...');
  const sig = await connection.sendRawTransaction(tx.serialize());
  console.log(`✅ TX sent: ${sig}`);
  
  // Wait for confirmation
  const result = await connection.confirmTransaction(sig);
  if (result.value.err) {
    console.log(`❌ Failed: ${result.value.err}`);
  } else {
    console.log(`✅ SUCCESS! Swapped ${(swapAmount/1e6).toFixed(2)} USDT → ${outSol.toFixed(4)} SOL`);
    console.log(`   New SOL balance: ${outSol + 0.0738 - 0.001} SOL (estimated)`);
  }
}

main().catch(e => console.error(`❌ Error: ${e.message}`));
