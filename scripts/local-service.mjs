#!/usr/bin/env node

import { execFileSync, spawn } from "node:child_process";
import { existsSync } from "node:fs";
import http from "node:http";
import { dirname, resolve } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { resolveLocalDevPorts } from "./local-dev-ports.mjs";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const HOST = process.env.CINE_FORGE_HOST || "127.0.0.1";
const PNPM = process.env.PNPM || "pnpm";
const runtime = resolveLocalDevPorts("cine-forge", ROOT);

function resolvePython() {
  if (process.env.CINE_FORGE_PYTHON) return process.env.CINE_FORGE_PYTHON;
  const localPython = resolve(ROOT, ".venv/bin/python");
  if (existsSync(localPython)) return localPython;
  const primaryPython = resolve(runtime.primaryRoot, ".venv/bin/python");
  if (existsSync(primaryPython)) return primaryPython;
  return process.env.PYTHON || "python3";
}

const PYTHON = resolvePython();

const SERVICES = {
  api: {
    label: "CineForge API",
    port: runtime.ports.api,
    host: HOST,
    healthPath: "/api/health",
    openPath: "/docs",
    command: () => [PYTHON, ["-m", "cine_forge.api", "--port", String(runtime.ports.api)]],
    cwd: ROOT,
    env: () => ({ PYTHONPATH: process.env.PYTHONPATH || "src" }),
    isExpectedHealth: (response) => response.status === 200
  },
  ui: {
    label: "CineForge UI",
    port: runtime.ports.ui,
    host: HOST,
    healthPath: "/",
    openPath: "/",
    command: () => [PNPM, ["run", "dev", "--", "--host", HOST]],
    cwd: resolve(ROOT, "ui"),
    env: () => ({
      CINE_FORGE_UI_PORT: String(runtime.ports.ui),
      FRONTEND_PORT: String(runtime.ports.ui),
      CINE_FORGE_API_URL: `http://${HOST}:${runtime.ports.api}`
    }),
    isExpectedHealth: (response) => response.status === 200
  }
};

const TARGETS = {
  app: ["api", "ui"],
  all: ["api", "ui"],
  api: ["api"],
  ui: ["ui"]
};

function usage() {
  console.log(`Usage:
  node scripts/local-service.mjs status [app|api|ui|all]
  node scripts/local-service.mjs start <app|api|ui> [--restart|--takeover]
  node scripts/local-service.mjs stop [app|api|ui|all] [--force]

Recommended commands:
  npm run local:app
  npm run local:status
  npm run local:stop`);
}

function serviceUrl(service, route = "") {
  return `http://${service.host}:${service.port}${route}`;
}

function listenerPids(port) {
  try {
    return execFileSync("lsof", [`-tiTCP:${port}`, "-sTCP:LISTEN"], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"]
    }).split("\n").map((line) => line.trim()).filter(Boolean);
  } catch {
    return [];
  }
}

function processCommand(pid) {
  try {
    return execFileSync("ps", ["-p", String(pid), "-o", "command="], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"]
    }).trim();
  } catch {
    return "";
  }
}

function processCwd(pid) {
  try {
    const output = execFileSync("lsof", ["-a", "-p", String(pid), "-d", "cwd", "-Fn"], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"]
    });
    const line = output.split("\n").find((entry) => entry.startsWith("n"));
    return line ? resolve(line.slice(1)) : "";
  } catch {
    return "";
  }
}

function sameCheckoutProcess(pid) {
  const cwd = processCwd(pid);
  return cwd === ROOT || cwd.startsWith(`${ROOT}/`);
}

function describePids(pids) {
  return pids.map((pid) => {
    const command = processCommand(pid) || "(command unavailable)";
    const cwd = processCwd(pid);
    return `  pid ${pid}: ${command}${cwd ? ` cwd=${cwd}` : ""}`;
  }).join("\n");
}

function sleep(ms) {
  return new Promise((resolveSleep) => {
    setTimeout(resolveSleep, ms);
  });
}

async function probeService(service) {
  return new Promise((resolveProbe) => {
    const req = http.get(serviceUrl(service, service.healthPath), { timeout: 800 }, (res) => {
      let text = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => {
        text += chunk;
      });
      res.on("end", () => {
        resolveProbe({
          reachable: true,
          expected: service.isExpectedHealth({ status: res.statusCode ?? 0, text }),
          status: res.statusCode ?? 0
        });
      });
    });
    req.on("timeout", () => {
      req.destroy();
      resolveProbe({ reachable: false, expected: false, status: 0 });
    });
    req.on("error", () => {
      resolveProbe({ reachable: false, expected: false, status: 0 });
    });
  });
}

function resolveTarget(target = "app") {
  return TARGETS[target] ?? null;
}

async function waitForPortToClear(port, timeoutMs = 2500) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (listenerPids(port).length === 0) return true;
    await sleep(100);
  }
  return listenerPids(port).length === 0;
}

async function stopPids(pids, { force = false } = {}) {
  for (const pid of pids) {
    try {
      process.kill(Number(pid), "SIGTERM");
    } catch {
      // Process may already be gone.
    }
  }
  await sleep(350);
  if (!force) return;
  for (const pid of pids) {
    try {
      process.kill(Number(pid), 0);
      process.kill(Number(pid), "SIGKILL");
    } catch {
      // Process may already be gone.
    }
  }
}

async function ensureService(serviceName, flags) {
  const service = SERVICES[serviceName];
  const shouldRestart = flags.has("--restart");
  const takeover = flags.has("--takeover") || shouldRestart;
  const probe = await probeService(service);

  if (probe.expected && !shouldRestart) {
    console.log(`${service.label}: already running at ${serviceUrl(service)}.`);
    console.log(`  open: ${serviceUrl(service, service.openPath)}`);
    return null;
  }

  const pids = listenerPids(service.port);
  if (pids.length > 0) {
    const sameCheckout = pids.every(sameCheckoutProcess);
    if (sameCheckout && (takeover || !probe.expected)) {
      console.log(`${service.label}: replacing same-checkout process on ${service.port}.`);
      console.log(describePids(pids));
      await stopPids(pids, { force: shouldRestart });
      if (!(await waitForPortToClear(service.port))) {
        throw new Error(`${service.label}: port ${service.port} is still occupied after stop attempt.`);
      }
    } else {
      console.error(`${service.label}: port ${service.port} is already in use.`);
      console.error(describePids(pids));
      console.error(`Current checkout: ${ROOT}`);
      throw new Error(`${service.label}: cannot start while port ${service.port} is occupied.`);
    }
  }

  const [command, args] = service.command();
  console.log(`${service.label}: starting at ${serviceUrl(service)}.`);
  console.log(`  open: ${serviceUrl(service, service.openPath)}`);
  return spawn(command, args, {
    cwd: service.cwd,
    env: { ...process.env, ...service.env() },
    stdio: "inherit"
  });
}

async function waitForHealthy(serviceName, timeoutMs = 12000) {
  const service = SERVICES[serviceName];
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const probe = await probeService(service);
    if (probe.expected) return true;
    await sleep(250);
  }
  return false;
}

async function startTarget(target, flags) {
  const serviceNames = resolveTarget(target);
  if (!serviceNames || target === "all") {
    usage();
    process.exit(2);
  }

  for (const serviceName of serviceNames) {
    const service = SERVICES[serviceName];
    const pids = listenerPids(service.port);
    if (pids.length === 0 || pids.every(sameCheckoutProcess)) continue;
    console.error(`${service.label}: port ${service.port} is already owned outside this checkout.`);
    console.error(describePids(pids));
    console.error(`Current checkout: ${ROOT}`);
    process.exit(1);
  }

  const children = [];
  for (const serviceName of serviceNames) {
    const child = await ensureService(serviceName, flags);
    if (child) children.push(child);
  }

  for (const serviceName of serviceNames) {
    const ready = await waitForHealthy(serviceName);
    console.log(`${SERVICES[serviceName].label}: ${ready ? "ready" : "started, health not ready yet"}.`);
  }

  if (children.length === 0) return;
  console.log("Services started by this command are attached to this terminal. Press Ctrl-C to stop them.");

  await new Promise((resolveExit) => {
    let shuttingDown = false;
    function stopChildren(signal = "SIGTERM") {
      if (shuttingDown) return;
      shuttingDown = true;
      for (const child of children) {
        if (!child.killed) child.kill(signal);
      }
    }
    process.on("SIGINT", () => stopChildren("SIGINT"));
    process.on("SIGTERM", () => stopChildren("SIGTERM"));
    for (const child of children) {
      child.on("error", (error) => {
        console.error(error.message);
        stopChildren();
        resolveExit();
      });
      child.on("exit", () => {
        stopChildren();
        resolveExit();
      });
    }
  });
}

async function stopTarget(target, flags) {
  const serviceNames = resolveTarget(target);
  if (!serviceNames) {
    usage();
    process.exit(2);
  }

  const pids = new Set();
  for (const serviceName of [...serviceNames].reverse()) {
    for (const pid of listenerPids(SERVICES[serviceName].port)) {
      if (flags.has("--force") || sameCheckoutProcess(pid)) pids.add(pid);
    }
  }
  if (pids.size === 0) {
    console.log("No matching CineForge local services to stop.");
    return;
  }
  console.log("Stopping CineForge local services:");
  console.log(describePids([...pids]));
  await stopPids([...pids], { force: flags.has("--force") });
}

async function status(target = "app") {
  const serviceNames = resolveTarget(target);
  if (!serviceNames) {
    usage();
    process.exit(2);
  }

  console.log("CineForge local runtime");
  console.log(`  root: ${ROOT}`);
  console.log(`  python: ${PYTHON}`);
  console.log(`  allocation: ${runtime.allocationPath}`);
  console.log(`  slot: ${runtime.isPrimaryCheckout ? "primary" : runtime.slot}`);
  if (runtime.slotStatePath) console.log(`  slot state: ${runtime.slotStatePath}`);

  for (const serviceName of serviceNames) {
    const service = SERVICES[serviceName];
    const probe = await probeService(service);
    const pids = listenerPids(service.port);
    const sameCheckout = pids.length === 0 || pids.every(sameCheckoutProcess);
    const state = probe.expected
      ? sameCheckout ? "ready" : "ready in another checkout"
      : pids.length > 0 ? "occupied" : "stopped";
    console.log(`${service.label}: ${state}`);
    console.log(`  service: ${serviceUrl(service)}`);
    console.log(`  open:    ${serviceUrl(service, service.openPath)}`);
    if (pids.length > 0) console.log(describePids(pids));
  }
}

async function main() {
  const [action = "status", target = "app", ...rest] = process.argv.slice(2);
  const flags = new Set(rest);
  if (action === "status") {
    await status(target);
  } else if (action === "start") {
    await startTarget(target, flags);
  } else if (action === "stop") {
    await stopTarget(target, flags);
  } else {
    usage();
    process.exit(2);
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
