#!/usr/bin/env node
/**
 * AgentKit MCP Server
 * Provides blockchain tools for Claude Code via Coinbase AgentKit
 *
 * Tools include: wallet operations, token transfers, NFTs,
 * DeFi protocols, and more
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
import { readFileSync, writeFileSync, existsSync } from "fs";
import { resolve } from "path";
import { randomBytes } from "crypto";

// Load CDP API key from JSON file
function loadCdpKey() {
  const keyPath = process.env.CDP_API_KEY_FILE ||
    resolve(process.env.HOME, ".config/coinbase/cdp_api_key.json");

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

// Get or create wallet secret for persistence
function getWalletSecret() {
  const secretPath = resolve(process.env.HOME, ".config/coinbase/wallet_secret.txt");

  if (existsSync(secretPath)) {
    return readFileSync(secretPath, "utf-8").trim();
  }

  // Generate a new wallet secret
  const secret = randomBytes(32).toString("hex");
  writeFileSync(secretPath, secret, { mode: 0o600 });
  console.error("Generated new wallet secret at", secretPath);
  return secret;
}

async function main() {
  const cdpKey = loadCdpKey();
  const walletSecret = getWalletSecret();

  // Initialize AgentKit with CDP credentials and action providers
  const agentKit = await AgentKit.from({
    cdpApiKeyId: cdpKey.cdpApiKeyId,
    cdpApiKeySecret: cdpKey.cdpApiKeySecret,
    cdpWalletSecret: walletSecret,
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
