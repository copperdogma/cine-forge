import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

/**
 * Minimal UI Smoke Probe
 * 
 * Used as a fallback when browser MCP tools are unavailable in the current agent session.
 * 
 * Usage:
 * 1. npm install playwright
 * 2. node scripts/ui_smoke_probe.mjs [url]
 */

async function run() {
  const url = process.argv[2] || 'http://localhost:5176/';
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  console.log(`Navigating to ${url}...`);
  
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  try {
    await page.goto(url, { waitUntil: 'networkidle' });
    
    // Wait for core UI signal
    await page.waitForSelector('text=CineForge', { timeout: 10000 });
    
    const title = await page.title();
    console.log(`Page title: ${title}`);

    const artifactsDir = 'tmp/browser-smoke';
    if (!fs.existsSync(artifactsDir)) {
      fs.mkdirSync(artifactsDir, { recursive: true });
    }

    const screenshotPath = path.join(artifactsDir, `smoke-${Date.now()}.png`);
    await page.screenshot({ path: screenshotPath });
    console.log(`Screenshot saved to ${screenshotPath}`);

    if (consoleErrors.length > 0) {
      console.error('Console errors detected:');
      consoleErrors.forEach(err => console.error(`- ${err}`));
    } else {
      console.log('No console errors detected.');
    }

  } catch (err) {
    console.error(`Failed to load page: ${err.message}`);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

run();
