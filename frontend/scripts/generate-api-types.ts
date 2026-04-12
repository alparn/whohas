#!/usr/bin/env npx tsx
import { execSync } from "child_process";

const OPENAPI_URL =
  process.env.OPENAPI_URL ?? "http://localhost:8000/openapi.json";
const OUTPUT = "src/lib/api-types.ts";

console.log(`Generating types from ${OPENAPI_URL} → ${OUTPUT}`);
execSync(`npx openapi-typescript ${OPENAPI_URL} -o ${OUTPUT}`, {
  stdio: "inherit",
});
console.log("Done.");
