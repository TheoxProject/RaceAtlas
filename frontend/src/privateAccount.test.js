import { expect, test, vi } from 'vitest';
import { captureAccountAction, clearAccountAction, newPasswordError, asciiEmailError } from './accountBootstrap.js';
import { createAccountController } from './privateAccount.js';
const A = { id: 'a', email: 'alice@example.test' }, B = { id: 'b', email: 'bob@example.test' }, proof = 'a'.repeat(64);
const reply = (status, value = {}) => ({ status, ok: status >= 200 && status < 300, json: async () => value, blob: async () => new Blob(['synthetic']) });
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };
for (const kind of ['confirm-email', 'reset-password']) test(`bootstrap ${kind} is captured once and scrubbed`, () => {
  const location = { hash: `#${kind}=${'x'.repeat(43)}`, pathname: '/', search: '?public=value' };
  const history = { state: {}, replaceState: vi.fn(() => { location.hash = ''; }) };
  expect(captureAccountAction(location, history)).toEqual({ kind: kind === 'confirm-email' ? 'confirm' : 'reset', proof: 'x'.repeat(43) });
  expect(history.replaceState).toHaveBeenCalledWith(history.state, '', '/?public=value');
  expect(captureAccountAction(location, history)).toBeNull();
  expect(history.replaceState).toHaveBeenCalledTimes(1);
});
test('malformed links are scrubbed without retaining or coercing proofs', () => {
  for (const hash of ['#confirm-email=short', '#reset-password=' + 'x'.repeat(44), '#confirm-email=' + '%78'.repeat(43), '#anything=sensitive']) {
    const history = { replaceState: vi.fn() };
    expect(captureAccountAction({ hash, pathname: '/', search: '' }, history)).toEqual({ kind: 'invalid' });
    expect(history.replaceState.mock.lastCall[2]).toBe('/');
  }
});
test('Unicode bounds are codepoints/UTF8, not UTF16, and spaces/NUL are preserved', () => {
  expect(newPasswordError('😀'.repeat(128))).toBeNull();
  expect(newPasswordError(' '.repeat(15))).toBeNull();
  expect(newPasswordError('abc'.repeat(5) + '\0')).toBeNull();
  for (const value of ['x'.repeat(14), '😀'.repeat(129), 'x'.repeat(15) + '\ud800']) expect(newPasswordError(value)).not.toBeNull();
  expect(asciiEmailError(' Alice+tag@EXAMPLE.test ')).toBeNull();
  for (const value of ['é@example.test', 'a@localhost', 'a@bad..test', 'a b@example.test']) expect(asciiEmailError(value)).not.toBeNull();
});
test('wrong login401 preserves A and exact legacy password; transport remains same-origin', async () => {
  const password = '  Legacy unchanged password  ';
  const fetcher = vi.fn(async (path, options) => {
    if (path.endsWith('/csrf')) return reply(200, { csrf_token: proof });
    if (path === '/api/v1/me') return reply(200, { account: A });
    expect(JSON.parse(options.body)).toEqual({ email: B.email, password });
    return reply(401, { code: 'authentication_failed' });
  });
  const c = createAccountController(fetcher); await c.refresh();
  expect(await c.submit('login', { email: B.email, password })).toBe(false);
  expect(c.getSnapshot()).toMatchObject({ account: A, error: { status: 401 } });
  for (const [path, options] of fetcher.mock.calls) {
    expect(path.startsWith('/api/')).toBe(true);
    expect(options).toMatchObject({ credentials: 'same-origin', cache: 'no-store', mode: 'same-origin', redirect: 'error', referrerPolicy: 'no-referrer' });
    expect(options.headers.Authorization).toBeUndefined();
  }
});
for (const lateStatus of [200, 401]) test(`late ${lateStatus} cannot replace B when abort is ignored`, async () => {
  let actor = A, waitNext = false; const old = deferred();
  const fetcher = vi.fn(async path => {
    if (path.endsWith('/csrf')) return reply(200, { csrf_token: proof });
    if (path.endsWith('/login')) { actor = B; return reply(200, { account: B }); }
    if (waitNext) { waitNext = false; return old.promise; }
    return reply(200, { account: actor });
  });
  const c = createAccountController(fetcher); await c.refresh(); waitNext = true;
  const pending = c.refresh();
  expect(await c.submit('login', { email: B.email, password: 'synthetic only passphrase' })).toBe(true);
  old.resolve(reply(lateStatus, lateStatus === 200 ? { account: A } : { code: 'authentication_failed' }));
  await pending; expect(c.getSnapshot()).toMatchObject({ account: B, status: 'member', error: null });
});
test('csrf→me expected→read uses one proof, refuses switched identity without retry', async () => {
  let actor = A;
  const fetcher = vi.fn(async path => path.endsWith('/csrf') ? reply(200, { csrf_token: proof }) : path === '/api/v1/me' ? reply(200, { account: actor }) : reply(403, { code: 'forbidden' }));
  const c = createAccountController(fetcher); await c.refresh();
  await expect(c.readPrivate('entries')).rejects.toMatchObject({ status: 403 });
  expect(fetcher.mock.calls.slice(-3).map(([path]) => path)).toEqual(['/api/v1/auth/csrf', '/api/v1/me', '/api/v1/me/saved-entries']);
  expect(fetcher.mock.lastCall[1].headers).toEqual({ 'X-CSRF-Token': proof });
  expect(fetcher.mock.calls.at(-2)[1].headers).toEqual({ 'X-CSRF-Token': proof });
  actor = B; await expect(c.readPrivate('entries')).rejects.toMatchObject({ code: 'context_changed' });
  expect(c.getSnapshot().account).toEqual(B);
  expect(fetcher.mock.calls.filter(([path]) => path.endsWith('/saved-entries'))).toHaveLength(1);
});
test('resetB proof only in header, no auto-login, A context remains', async () => {
  const token = 'b'.repeat(43), password = '  New exact password for B  ';
  const fetcher = vi.fn(async path => path.endsWith('/csrf') ? reply(200, { csrf_token: proof }) : path === '/api/v1/me' ? reply(200, { account: A }) : reply(204));
  const c = createAccountController(fetcher); await c.refresh();
  expect(await c.submit('reset', { new_password: password }, token)).toBe(true);
  const [, options] = fetcher.mock.calls.find(([path]) => path.endsWith('/password-reset/complete'));
  expect(JSON.parse(options.body)).toEqual({ new_password: password });
  expect(options.headers).toMatchObject({ 'X-Account-Proof': token, 'X-CSRF-Token': proof });
  expect(c.getSnapshot().account).toEqual(A);
  expect(fetcher.mock.calls.some(([path]) => path.endsWith('/login'))).toBe(false);
});
test('offline failure never fabricates mail delivery or clears A', async () => {
  let offline = false;
  const fetcher = vi.fn(async path => { if (offline) throw new TypeError('synthetic offline'); return reply(200, path.endsWith('/csrf') ? { csrf_token: proof } : { account: A }); });
  const c = createAccountController(fetcher); await c.refresh(); offline = true;
  expect(await c.submit('resend', { email: B.email })).toBe(false);
  expect(c.getSnapshot()).toMatchObject({ account: A, error: { code: 'network' }, message: null });
});

test('discard erases the initial envelope shared by bootstrap and React props', () => {
  const action = captureAccountAction({ hash: '#confirm-email=' + 'z'.repeat(43), pathname: '/', search: '' }, { replaceState() {} });
  const retainedInitialProp = action;
  expect(retainedInitialProp.proof).toBe('z'.repeat(43));
  clearAccountAction(action);
  expect(retainedInitialProp).toEqual({ kind: 'confirm', proof: null });
  clearAccountAction(action);
  expect(retainedInitialProp.proof).toBeNull();
});
test('proofB with meA is refused at the bound preflight without any operation retry', async () => {
  let inIntent = false;
  const fetcher = vi.fn(async (path, options) => {
    if (path.endsWith('/csrf')) { inIntent = true; return reply(200, { csrf_token: proof }); }
    if (path === '/api/v1/me') {
      if (inIntent) { expect(options.headers['X-CSRF-Token']).toBe(proof); return reply(403, { code: 'forbidden' }); }
      return reply(200, { account: A });
    }
    throw new Error('Operation must not run');
  });
  const c = createAccountController(fetcher); await c.refresh();
  expect(await c.submit('login', { email: B.email, password: 'synthetic test password' })).toBe(false);
  expect(c.getSnapshot().account).toEqual(A);
  expect(fetcher.mock.calls.filter(([path]) => path.endsWith('/login'))).toHaveLength(0);
});

test('identity-changing passive refresh discards prior feedback, same-actor refresh preserves success', async () => {
  let actor = A;
  const fetcher = vi.fn(async path => path.endsWith('/csrf') ? reply(200, { csrf_token: proof }) : path === '/api/v1/me' ? reply(200, { account: actor }) : reply(202, { status: 'accepted' }));
  const c = createAccountController(fetcher); await c.refresh();
  expect(await c.submit('forgot', { email: B.email })).toBe(true);
  const message = c.getSnapshot().message; expect(message).toMatch(/admissible/);
  await c.refresh(); expect(c.getSnapshot().message).toBe(message);
  actor = B; await c.refresh();
  expect(c.getSnapshot()).toMatchObject({ account: B, message: null, error: null });
});
