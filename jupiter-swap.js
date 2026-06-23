#!/usr/bin/env node
/**
 * Jupiter Swap Bridge - executed from Python bot
 * Usage: node jupiter-swap.js <action> <inputMint> <outputMint> <amount> <slippageBps> <userPubkey>
 */
const { createJupiterApiClient, QuoteGetSwapModeEnum } = require('@jup-ag/api');
const { Connection, Keypair, VersionedTransaction } = require('@solana/web3.js');
const bs58 = require('bs58');

const RPC = 'https://api.mainnet-beta.solana.com';
const connection = new Connection(RPC, 'confirmed');
const api = createJupiterApiClient();

async function main() {
  const [action, inputMint, outputMint, amount, slippageBps, userPubkey] = process.argv.slice(2);
  
  if (!action || !inputMint || !outputMint || !amount) {
    console.error(JSON.stringify({ error: 'Usage: jupiter-swap.js <action> <inputMint> <outputMint> <amount> <slippageBps> <userPubkey>' }));
    process.exit(1);
  }

  try {
    // Get quote using the API client
    const quote = await api.quoteGet({
      inputMint,
      outputMint,
      amount: parseInt(amount),
      slippageBps: parseInt(slippageBps || '100'),
      swapMode: QuoteGetSwapModeEnum.ExactIn,
    });

    if (!quote) {
      console.error(JSON.stringify({ error: 'No route found' }));
      process.exit(1);
    }

    if (action === 'quote') {
      const result = {
        inAmount: quote.inAmount,
        outAmount: quote.outAmount,
        routePlan: (quote.routePlan || []).map(r => ({
          label: r.swapInfo.label,
          inAmount: r.swapInfo.inAmount,
          outAmount: r.swapInfo.outAmount,
        })),
      };
      console.log(JSON.stringify(result));
    } else if (action === 'swap') {
      if (!process.env.PRIVATE_KEY_B58) {
        console.error(JSON.stringify({ error: 'PRIVATE_KEY_B58 env var required for swap' }));
        process.exit(1);
      }

      const keypair = Keypair.fromSecretKey(bs58.decode(process.env.PRIVATE_KEY_B58));
      const userKey = userPubkey || keypair.publicKey.toBase58();

      // Get swap transaction via API
      const swapResult = await api.swapPost({
        quoteResponse: quote,
        userPublicKey: userKey,
        wrapAndUnwrapSol: true,
        dynamicComputeUnitLimit: true,
      });

      const txBuffer = Buffer.from(swapResult.swapTransaction, 'base64');
      console.log(JSON.stringify({ swapTransaction: txBuffer.toString('base64') }));
    }
  } catch (e) {
    console.error(JSON.stringify({ error: e.message || String(e) }));
    process.exit(1);
  }
}

main();
