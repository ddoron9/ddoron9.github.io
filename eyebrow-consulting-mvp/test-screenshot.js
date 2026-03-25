import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1280, height: 800 });

  const htmlPath = path.join(__dirname, 'web', 'index.html');
  await page.goto('file://' + htmlPath);

  console.log('Page loaded, waiting for initialization...');
  await page.waitForSelector('#demoBtn', { timeout: 10000 }).catch(() => {});

  console.log('Clicking demo button...');
  await page.click('#demoBtn');

  // Wait for completion by checking decision text or a delay
  try {
    await page.waitForFunction(() => {
      const decision = document.getElementById('decision');
      return decision && (decision.textContent || '').includes('완료');
    }, { timeout: 30000 });
  } catch (e) {
    console.log('Decision not ready in time, waiting additional fixed time...');
    await page.waitForTimeout(15000);
  }

  // Capture result canvases
  const saved = [];
  for (let i = 1; i <= 3; i++) {
    try {
      const canvas = await page.$(`#resultCanvas${i}`);
      if (!canvas) continue;
      const buffer = await canvas.screenshot();
      const filename = path.join(__dirname, `test_result_${i}_${Date.now()}.png`);
      fs.writeFileSync(filename, buffer);
      saved.push(filename);
      console.log(`Saved: ${filename}`);
    } catch (err) {
      console.error(`Error capturing canvas ${i}:`, err.message);
    }
  }

  await browser.close();
  console.log('Test completed. Files:', saved.join(' '));
  process.exit(0);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
