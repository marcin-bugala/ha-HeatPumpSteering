// Real browser events against the wrapper, with a local stand-in native card.
// No HA account, data, or service calls. Run: node tests/test_readonly_card.cjs
const assert = require('node:assert/strict');
const path = require('node:path');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ channel: process.env.POC_BROWSER_CHANNEL || 'chrome', headless: true });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.setContent('<button id="control">Editable control</button>');
    await page.evaluate(() => {
      window.counts = { clicks: 0, keys: 0, hover: 0, info: 0, control: 0 };
      document.addEventListener('hass-more-info', () => window.counts.info++);
      document.querySelector('#control').addEventListener('click', () => window.counts.control++);
      class FixtureCard extends HTMLElement {
        constructor() {
          super();
          this.attachShadow({ mode: 'open' });
          this.shadowRoot.innerHTML = '<button style="margin:20px;width:300px;height:100px">Read-only graph</button>';
          const button = this.shadowRoot.querySelector('button');
          button.addEventListener('click', () => window.counts.clicks++);
          button.addEventListener('keydown', () => window.counts.keys++);
          button.addEventListener('pointerover', () => window.counts.hover++);
        }
        getCardSize() { return 4; }
      }
      customElements.define('fixture-card', FixtureCard);
      window.loadCardHelpers = async () => ({ createCardElement: () => document.createElement('fixture-card') });
    });
    await page.addScriptTag({ path: path.resolve(__dirname, '../www/hp-poc-readonly-card.js') });
    await page.evaluate(() => {
      const wrapper = document.createElement('hp-poc-readonly-card');
      wrapper.hass = { test: 1 };
      wrapper.setConfig({ card: { type: 'history-graph' } });
      document.body.append(wrapper);
    });
    const graph = page.locator('hp-poc-readonly-card fixture-card button');
    await graph.hover();
    await graph.click();
    await graph.dblclick();
    await graph.focus();
    await graph.press('Enter');
    await graph.press('Space');
    await graph.evaluate(button => button.dispatchEvent(new CustomEvent('hass-more-info', { bubbles: true, composed: true })));
    await page.locator('#control').click();
    const counts = await page.evaluate(() => window.counts);
    assert.equal(counts.clicks, 0);
    assert.equal(counts.keys, 0);
    assert.equal(counts.info, 0);
    assert.ok(counts.hover > 0, 'Hover must remain available');
    assert.equal(counts.control, 1, 'Controls outside wrapper must remain editable');
    assert.equal(await page.evaluate(() => document.querySelector('hp-poc-readonly-card')._card.hass.test), 1);
    assert.equal(await page.evaluate(() => document.querySelector('hp-poc-readonly-card').getCardSize()), 4);
    await page.evaluate(() => { document.querySelector('hp-poc-readonly-card').hass = { test: 2 }; });
    assert.equal(await page.evaluate(() => document.querySelector('hp-poc-readonly-card')._card.hass.test), 2);
    assert.deepEqual(errors, []);
    console.log('Read-only card browser checks passed: clicks, keyboard, more-info, hover, controls and updates.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
