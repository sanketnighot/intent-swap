#!/usr/bin/env node

require("dotenv").config();
const fs = require("fs");
const path = require("path");
const { ethers } = require("ethers");

function requiredEnv(name) {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required env var: ${name}`);
  }
  return value;
}

async function main() {
  const rpcUrl = requiredEnv("RPC_URL");
  const privateKey = requiredEnv("PRIVATE_KEY");
  const poolManagerAddress = requiredEnv("POOL_MANAGER_ADDRESS");

  const artifactPath = path.resolve(
    __dirname,
    "../artifacts/contracts/IntentSwapHook.sol/IntentSwapHook.json"
  );

  if (!fs.existsSync(artifactPath)) {
    throw new Error(
      `Artifact not found at ${artifactPath}. Compile the contract before deploying.`
    );
  }

  const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));
  const provider = new ethers.JsonRpcProvider(rpcUrl);
  const wallet = new ethers.Wallet(privateKey, provider);

  const factory = new ethers.ContractFactory(artifact.abi, artifact.bytecode, wallet);
  const hook = await factory.deploy(poolManagerAddress);
  await hook.waitForDeployment();

  console.log(`IntentSwapHook deployed at: ${await hook.getAddress()}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
