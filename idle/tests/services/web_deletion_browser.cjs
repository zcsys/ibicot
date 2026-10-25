/* Actual headless browser + synthetic live HTTP only. Never log credentials. */
const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const base = process.argv[2], output = process.argv[3];
let browser, stage = 'startup';
const results = [];
function check(ok, label) { if (!ok) throw new Error(label); }
async function api(method, endpoint, body, token) {
  const response = await fetch(base + endpoint, {method, headers: {
    ...(body ? {'Content-Type': 'application/json'} : {}),
    ...(token ? {Authorization: 'Bearer ' + token} : {})}, body: body ? JSON.stringify(body) : undefined});
  return {status: response.status, data: await response.json()};
}
(async () => {
  browser = await chromium.launch({channel: 'chrome', headless: true});
  const browserVersion = browser.version();
  const context = await browser.newContext({viewport: {width: 1280, height: 900}});
  const page = await context.newPage();
  let requests = [], temporary = '', errors = 0;
  page.on('pageerror', () => { errors++; });
  page.on('request', req => { requests.push({method: req.method(), path: new URL(req.url()).pathname, sameOrigin: new URL(req.url()).origin === base}); });
  page.on('response', async response => {
    if (new URL(response.url()).pathname === '/v1/sessions' && response.status() === 200) {
      try { const value = await response.json(); temporary = value.session_token; } catch (_) {}
    }
  });
  async function fresh() { await page.goto(base + '/account/delete'); requests = []; temporary = ''; }
  async function review(account, code = account.recovery_code) {
    await page.locator('#account-id').fill(account.account_id);
    await page.locator('#recovery-code').fill(code);
    await page.getByRole('button', {name: 'Continue to confirmation'}).click();
    check(await page.locator('#confirmation').isVisible(), 'review_visible');
    check(await page.locator('#account-id').inputValue() === '' && await page.locator('#recovery-code').inputValue() === '', 'dom_inputs_wiped');
  }
  async function confirm() {
    await page.locator('#understood').check();
    await page.getByRole('button', {name: 'Delete account permanently'}).click();
  }
  async function settled() { await page.locator('#credentials').waitFor({state: 'visible'}); }
  const make = async () => (await api('POST', '/v1/accounts', {consent_cloud: true})).data;
  stage = 'read-only page and storage'; await fresh();
  check(await page.title() === 'Delete a Tideglass account', 'page_title');
  check(await page.evaluate(() => localStorage.length === 0 && sessionStorage.length === 0), 'no_browser_storage');
  check((await context.cookies()).length === 0, 'no_cookie');
  check(requests.every(r => r.method === 'GET' && r.sameOrigin), 'get_only');
  await page.screenshot({path: path.join(output, 'empty-desktop.png'), fullPage: true});
  results.push({scenario: stage, passed: true});
  stage = 'explicit confirmation and cancel';
  let account = await make(); await review(account);
  check(await page.locator('#delete-account').isDisabled(), 'confirm_required');
  check(!requests.some(r => r.method !== 'GET'), 'no_auth_before_confirm');
  await page.getByRole('button', {name: 'Cancel', exact: true}).click(); await settled();
  check(!requests.some(r => r.method !== 'GET'), 'cancel_no_mutation');
  check((await api('GET', '/v1/cloud', null, account.session_token)).status === 200, 'account_still_exists');
  results.push({scenario: stage, passed: true});
  stage = 'wrong recovery code'; await fresh(); await review(account, 'x'.repeat(43)); await confirm();
  await page.getByRole('status').filter({hasText: 'not accepted'}).waitFor(); await settled();
  check(!requests.some(r => r.method === 'DELETE'), 'wrong_code_no_delete');
  results.push({scenario: stage, passed: true});
  stage = 'actual confirmed deletion'; await fresh(); await review(account); await confirm();
  await page.getByRole('status').filter({hasText: 'Account deletion confirmed'}).waitFor(); await settled();
  check((await api('GET', '/v1/cloud', null, account.session_token)).status === 401, 'sessions_revoked_by_delete');
  check(requests.filter(r => r.method === 'DELETE').length === 1, 'single_delete');
  await page.screenshot({path: path.join(output, 'confirmed-desktop.png'), fullPage: true});
  results.push({scenario: stage, passed: true});
  stage = 'failed deletion and temporary-session revocation'; account = await make(); await fresh();
  await page.route('**/v1/account', route => route.fulfill({status: 503, contentType: 'application/json', body: '{"error":"synthetic_failure"}'}));
  await review(account); await confirm(); await page.getByRole('status').filter({hasText: 'Deletion was not confirmed'}).waitFor(); await settled();
  check(requests.some(r => r.path === '/v1/sessions/revoke'), 'revoke_attempted');
  check(typeof temporary === 'string' && temporary.length === 43, 'temporary_issued');
  check((await api('GET', '/v1/cloud', null, temporary)).status === 401, 'temporary_revoked');
  check((await api('GET', '/v1/cloud', null, account.session_token)).status === 200, 'other_session_preserved');
  await page.unroute('**/v1/account'); results.push({scenario: stage, passed: true});
  stage = 'response loss after actual committed deletion'; account = await make(); await fresh();
  await page.route('**/v1/account', async route => { await route.fetch(); await route.abort('failed'); });
  await review(account); await confirm(); await page.getByRole('status').filter({hasText: 'response was lost or invalid'}).waitFor(); await settled();
  check(!await page.getByRole('status').textContent().then(text => text.includes('Account deletion confirmed')), 'never_false_confirm');
  check((await api('GET', '/v1/cloud', null, account.session_token)).status === 401, 'lost_response_can_follow_commit');
  await page.unroute('**/v1/account'); results.push({scenario: stage, passed: true});
  stage = 'compact large text and keyboard confirmation'; await page.setViewportSize({width: 320, height: 900}); await fresh();
  await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
  check(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth), 'no_horizontal_overflow');
  await page.screenshot({path: path.join(output, 'empty-compact-200.png'), fullPage: true});
  account = await make(); await review(account);
  await page.screenshot({path: path.join(output, 'confirmation-compact-200.png'), fullPage: true});
  await page.locator('#understood').focus(); await page.keyboard.press('Space');
  check(await page.locator('#understood').isChecked(), 'keyboard_checkbox');
  await page.locator('#cancel').focus(); await page.keyboard.press('Enter'); await settled();
  check(!requests.some(r => r.method !== 'GET'), 'keyboard_cancel_no_request');
  results.push({scenario: stage, passed: true});
  stage = 'final privacy checks';
  check(await page.evaluate(() => localStorage.length === 0 && sessionStorage.length === 0), 'storage_still_empty');
  check((await context.cookies()).length === 0, 'cookies_still_empty');
  check(requests.every(r => r.sameOrigin), 'no_external_resources');check(errors === 0, 'no_page_errors');
  check(await page.locator('#account-id').inputValue() === '' && await page.locator('#recovery-code').inputValue() === '', 'final_inputs_wiped');
  results.push({scenario: stage, passed: true});
  await browser.close(); browser = null;
  const report = {synthetic: true, browser: 'Playwright Chrome headless', browser_version: browserVersion, real_http: true, passed: true,
    scenarios: results, captures: ['empty-desktop.png', 'confirmed-desktop.png', 'empty-compact-200.png', 'confirmation-compact-200.png'],
    limitations: ['No public deployment, legal approval, physical-device or screen-reader qualification.', 'Synthetic accounts only; credentials intentionally omitted from all evidence.']};
  fs.writeFileSync(path.join(output, 'browser-report.json'), JSON.stringify(report, null, 2) + '\n');
  process.stdout.write(JSON.stringify({passed: true, scenarios: results.length}) + '\n');
})().catch(async () => {
  if (browser) await browser.close().catch(() => {});
  fs.writeFileSync(path.join(output, 'browser-report.json'), JSON.stringify({synthetic: true, passed: false, failed_stage: stage, completed: results}, null, 2) + '\n');
  // Do not dump Playwright call arguments, response bodies, credentials or tokens.
  process.stderr.write('Browser qualification failed at: ' + stage + '\n'); process.exitCode = 1;
});
