import fs from 'node:fs';
import path from 'node:path';

import { chromium } from 'playwright';

/**
 * Generic desktop/mobile UI health probe used when the interactive browser is unavailable.
 *
 * This is a mechanical smoke check, not representative-project UX acceptance.
 * Usage: node scripts/ui_smoke_probe.mjs [url] [--mode desktop|mobile|both]
 */

const VIEWPORTS = {
  desktop: { width: 1440, height: 1000, isMobile: false },
  mobile: { width: 390, height: 844, isMobile: true },
};

function parseArgs(argv) {
  const args = [...argv];
  let url = 'http://localhost:5176/';
  let mode = 'both';
  let screenshotDir = 'tmp/browser-smoke';

  if (args[0] && !args[0].startsWith('--')) {
    url = args.shift();
  }
  while (args.length) {
    const flag = args.shift();
    const value = args.shift();
    if (flag === '--mode' && ['desktop', 'mobile', 'both'].includes(value)) {
      mode = value;
    } else if (flag === '--screenshot-dir' && value) {
      screenshotDir = value;
    } else {
      throw new Error(`Unknown or invalid argument: ${flag}${value ? ` ${value}` : ''}`);
    }
  }
  return { url, mode, screenshotDir };
}

async function probeViewport(browser, { url, viewportName, screenshotDir }) {
  const viewport = VIEWPORTS[viewportName];
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    isMobile: viewport.isMobile,
  });
  const page = await context.newPage();
  const errors = [];

  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(`console: ${message.text()}`);
  });
  page.on('pageerror', (error) => errors.push(`pageerror: ${error.message}`));
  page.on('requestfailed', (request) => {
    errors.push(`requestfailed: ${request.method()} ${request.url()} (${request.failure()?.errorText})`);
  });
  page.on('response', (response) => {
    if (response.status() >= 400) {
      errors.push(`response: ${response.status()} ${response.url()}`);
    }
  });

  try {
    const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30_000 });
    if (!response || response.status() >= 400) {
      throw new Error(`navigation returned ${response?.status() ?? 'no response'}`);
    }
    await page.getByText('CineForge', { exact: false }).first().waitFor({
      state: 'visible',
      timeout: 10_000,
    });
    await page.waitForTimeout(750);

    const title = (await page.title()).trim();
    const bodyText = (await page.locator('body').innerText()).trim();
    if (!title) throw new Error('document title is empty');
    if (bodyText.length < 20) throw new Error('page body is effectively empty');

    fs.mkdirSync(screenshotDir, { recursive: true });
    const screenshotPath = path.resolve(
      screenshotDir,
      `smoke-${viewportName}-${Date.now()}.png`,
    );
    await page.screenshot({ path: screenshotPath, fullPage: true });

    if (errors.length) {
      throw new Error(`${viewportName} browser errors:\n- ${errors.join('\n- ')}`);
    }
    return { viewport: viewportName, title, screenshotPath };
  } finally {
    await context.close();
  }
}

async function run() {
  const options = parseArgs(process.argv.slice(2));
  const viewportNames = options.mode === 'both' ? ['desktop', 'mobile'] : [options.mode];
  const browser = await chromium.launch();
  try {
    const results = [];
    for (const viewportName of viewportNames) {
      results.push(await probeViewport(browser, { ...options, viewportName }));
    }
    console.log(JSON.stringify({
      status: 'passed',
      scope: 'mechanical UI health only; not representative-project UX acceptance',
      url: options.url,
      results,
    }, null, 2));
  } finally {
    await browser.close();
  }
}

run().catch((error) => {
  console.error(`UI smoke probe failed: ${error.message}`);
  process.exitCode = 1;
});
