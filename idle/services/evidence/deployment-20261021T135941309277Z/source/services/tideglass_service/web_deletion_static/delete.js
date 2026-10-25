/* No storage, cookies, analytics, credential logging or external requests. */
(() => {
  'use strict';
  const form = document.getElementById('credentials');
  const accountInput = document.getElementById('account-id');
  const codeInput = document.getElementById('recovery-code');
  const confirmation = document.getElementById('confirmation');
  const understood = document.getElementById('understood');
  const deleteButton = document.getElementById('delete-account');
  const cancelButton = document.getElementById('cancel');
  const status = document.getElementById('status');
  const accountPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
  const codePattern = /^[A-Za-z0-9_-]{43}$/;
  let pending = null, token = '', busy = false, generation = 0, expiry = null;
  let controller = null;
  document.getElementById('service-origin').textContent = location.origin;

  function wipeInputs() { accountInput.value = ''; codeInput.value = ''; understood.checked = false; }
  function say(text) { status.textContent = text; status.focus(); }
  function reset() {
    pending = null; wipeInputs(); clearTimeout(expiry); expiry = null;
    confirmation.hidden = true; form.hidden = false; deleteButton.disabled = true;
    cancelButton.disabled = false;
  }
  async function request(path, method, body, bearer = '', timeout = 15000, tracked = true) {
    const active = new AbortController(); if (tracked) controller = active;
    const timer = setTimeout(() => active.abort(), timeout);
    try {
      const response = await fetch(path, {
        method, mode: 'same-origin', credentials: 'omit', cache: 'no-store', redirect: 'error',
        referrerPolicy: 'no-referrer', signal: active.signal,
        headers: {'Content-Type': 'application/json', 'X-Tideglass-Deletion': '1',
          ...(bearer ? {'Authorization': 'Bearer ' + bearer} : {})},
        body: JSON.stringify(body)
      });
      // Read at most 8 KiB. Never show or log an untrusted response body.
      const reader = response.body.getReader(); let total = 0; const chunks = [];
      while (true) {
        const {done, value} = await reader.read(); if (done) break;
        total += value.length;
        if (total > 8192) { await reader.cancel(); throw new Error('response_bound'); }
        chunks.push(value);
      }
      const bytes = new Uint8Array(total); let offset = 0;
      for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
      return {status: response.status, data: JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes))};
    } finally { clearTimeout(timer); if (controller === active) controller = null; }
  }
  async function revoke(credential) {
    if (!credential) return;
    try { await request('/v1/sessions/revoke', 'POST', {all_devices: false}, credential, 5000, false); }
    catch (_) { /* Best effort only. A failed response is not a revocation claim. */ }
  }
  form.addEventListener('submit', event => {
    event.preventDefault();
    if (busy) return;
    const account = accountInput.value.trim(); const code = codeInput.value.trim();
    if (!accountPattern.test(account) || !codePattern.test(code)) {
      wipeInputs(); say('Enter a valid account ID and recovery code. No request was sent.'); return;
    }
    pending = {account, code}; wipeInputs(); status.textContent = '';
    form.hidden = true; confirmation.hidden = false; deleteButton.disabled = true;
    document.getElementById('confirmation-title').focus();
    clearTimeout(expiry);
    expiry = setTimeout(() => {
      if (!busy) { reset(); say('The confirmation expired. Re-enter your details to continue. No request was sent.'); }
    }, 120000);
  });
  understood.addEventListener('change', () => { deleteButton.disabled = busy || !pending || !understood.checked; });
  cancelButton.addEventListener('click', () => {
    if (busy) return;
    reset(); say('Cancelled. No account request was sent.');
  });
  deleteButton.addEventListener('click', async () => {
    if (busy || !pending || !understood.checked) return;
    busy = true; deleteButton.disabled = true; cancelButton.disabled = true;
    clearTimeout(expiry); const attempt = ++generation;
    let credentials = pending; pending = null; let phase = 'authenticate'; let confirmed = false; let issued = '';
    say('Authenticating and requesting deletion. Please keep this page open.');
    try {
      const auth = await request('/v1/sessions', 'POST', {account_id: credentials.account, recovery_code: credentials.code});
      if (typeof auth.data?.session_token === 'string' && codePattern.test(auth.data.session_token)) issued = auth.data.session_token;
      if (auth.status !== 200 || auth.data.account_id !== credentials.account || !codePattern.test(auth.data.session_token)) {
        if (attempt === generation) say(auth.status === 401 ?
          'The account ID or recovery code was not accepted. No deletion was confirmed.' :
          'Authentication did not complete. No deletion request was sent. A temporary session may remain if the response was lost.');
        return;
      }
      if (attempt !== generation) return;
      token = issued;
      phase = 'delete';
      const result = await request('/v1/account', 'DELETE', {recovery_code: credentials.code, confirm_delete: true}, issued);
      confirmed = result.status === 200 && result.data.deleted === true &&
        result.data.guest_progress_unchanged === true && result.data.store_purchases_not_cancelled === true;
      if (attempt === generation) say(confirmed ?
        'Account deletion confirmed. Active service records and sessions were deleted. Your local guest harbor and personal exports remain. Store purchases were not cancelled.' :
        'Deletion was not confirmed. The account may or may not have been deleted. Re-enter your details to check or retry; this page cannot infer the outcome from a failed response.');
    } catch (_) {
      if (attempt === generation) say(phase === 'delete' ?
        'The deletion response was lost or invalid. The account may or may not have been deleted. Re-enter your details to check or retry.' :
        'Authentication did not complete. No deletion request was sent. A temporary session may remain if the response was lost.');
    } finally {
      credentials = null;
      if (token === issued) token = '';
      if (attempt === generation) wipeInputs();
      if (!confirmed) await revoke(issued);
      issued = '';
      if (attempt === generation) { busy = false; reset(); }
    }
  });
  window.addEventListener('pagehide', () => {
    generation++; if (controller) controller.abort();
    const temporary = token; token = ''; busy = false; reset();
    if (temporary) {
      // Navigating away cannot cancel an already committed deletion. This only
      // attempts to revoke this temporary session; no all-device revocation.
      fetch('/v1/sessions/revoke', {method: 'POST', mode: 'same-origin', credentials: 'omit',
        cache: 'no-store', redirect: 'error', referrerPolicy: 'no-referrer', keepalive: true,
        headers: {'Content-Type': 'application/json', 'X-Tideglass-Deletion': '1', 'Authorization': 'Bearer ' + temporary},
        body: JSON.stringify({all_devices: false})}).catch(() => {});
    }
  });
  window.addEventListener('pageshow', event => { if (event.persisted) { reset(); status.textContent = ''; } });
})();
