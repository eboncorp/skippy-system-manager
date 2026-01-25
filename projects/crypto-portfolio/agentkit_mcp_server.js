#!/usr/bin/env node
/**
 * AgentKit MCP Server
 * Provides blockchain tools for Claude Code via Coinbase AgentKit
 *
 * Required environment variables:
 *   CDP_API_KEY_ID     - From CDP Portal API Keys
 *   CDP_API_KEY_SECRET - PKCS#8 format private key
 *   CDP_WALLET_SECRET  - From CDP Portal Server Wallet section
 *
 * Optional:
 *   NETWORK_ID - Network to use (default: base-mainnet)
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { getMcpTools } from "@coinbase/agentkit-model-context-protocol";
import {
  AgentKit,
  walletActionProvider,
  erc20ActionProvider,
  erc721ActionProvider,
  wethActionProvider,
  basenameActionProvider,
  cdpApiActionProvider,
} from "@coinbase/agentkit";
import { readFileSync } from "fs";
import { resolve } from "path";

// Load CDP API key from JSON file
function loadCdpKey() {
  const keyPath = process.env.CDP_API_KEY_FILE ||
    resolve(process.env.HOME, ".config/coinbase/gti_cdp_api_key.json");

  try {
    const keyData = JSON.parse(readFileSync(keyPath, "utf-8"));
    // Convert escaped newlines to actual newlines in the private key
    const privateKey = keyData.privateKey.replace(/\\n/g, "\n");
    return {
      cdpApiKeyId: keyData.name,
      cdpApiKeySecret: privateKey
    };
  } catch (error) {
    console.error(`Failed to load CDP key from ${keyPath}:`, error.message);
    process.exit(1);
  }
}

// Load wallet secret from file or environment
function loadWalletSecret() {
  // First check environment variable
  if (process.env.CDP_WALLET_SECRET) {
    return process.env.CDP_WALLET_SECRET;
  }

  // Then check file
  const secretPath = resolve(process.env.HOME, ".config/coinbase/wallet_secret.txt");
  try {
    return readFileSync(secretPath, "utf-8").trim();
  } catch (error) {
    console.error(`
ERROR: Wallet secret not found.

You must generate a Wallet Secret in the CDP Portal:
  https://portal.cdp.coinbase.com/products/server-wallet/accounts

Then either:
  1. Set CDP_WALLET_SECRET environment variable, or
  2. Save to: ${secretPath}
`);
    process.exit(1);
  }
}

async function main() {
  const cdpKey = loadCdpKey();
  const walletSecret = loadWalletSecret();
  const networkId = process.env.NETWORK_ID || "base-mainnet";

  console.error(`Initializing AgentKit on ${networkId}...`);

  // Initialize AgentKit with CDP credentials
  const agentKit = await AgentKit.from({
    cdpApiKeyId: cdpKey.cdpApiKeyId,
    cdpApiKeySecret: cdpKey.cdpApiKeySecret,
    cdpWalletSecret: walletSecret,
    networkId,
    actionProviders: [
      walletActionProvider(),
      erc20ActionProvider(),
      erc721ActionProvider(),
      wethActionProvider(),
      basenameActionProvider(),
      cdpApiActionProvider({
        apiKeyId: cdpKey.cdpApiKeyId,
        apiKeySecret: cdpKey.cdpApiKeySecret,
      }),
    ],
  });

  // Get MCP tools from AgentKit
  const { tools, toolHandler } = await getMcpTools(agentKit);

  console.error(`AgentKit MCP Server loaded with ${tools.length} tools`);

  // Create MCP server
  const server = new Server(
    {
      name: "coinbase-agentkit",
      version: "1.0.0",
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // Handle tool listing
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return { tools };
  });

  // Handle tool execution
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    try {
      return await toolHandler(name, args);
    } catch (error) {
      return {
        content: [{ type: "text", text: `Error: ${error.message}` }],
        isError: true,
      };
    }
  });

  // Connect via stdio
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
