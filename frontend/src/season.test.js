import { expect, test, vi } from 'vitest';
import { createAccountController } from './privateAccount.js';
import { opaqueSegment } from './season.js';
const A = { id: 'a', email: 'alice@example.test' }, B = { id: 'b', email: 'bob@example.test' };
const row = (id, scope, status = 'interested') => ({ id, scope_id: scope, status, created_at: '2026-11-14T00:00:00Z', race: { id: 'same-race' }, scope: { id: scope } });
const reply = (status, data = {}) => ({ status, ok: status >= 200 && status < 300, json: async () => data });
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };
function fixture(initial = [row('entry-one', 'scope-one'), row('entry-two', 'scope-two', 'planned')]) {
  let actor = A, failure = null, held = null, heldWrite = null;
  const store = { a: initial, b: [] };
  const fetcher = vi.fn(async (path, options) => {
    const owner = actor.id;
    if (path.endsWith('/csrf')) return reply(200, { csrf_token: 'a'.repeat(64) });
    if (path === '/api/v1/me') return reply(200, { account: actor });
    if (options.method === 'GET') {
      if (held) { const result = held; held = null; return result.promise; }
      return reply(200, { items: [...store[owner]] });
    }
    if (failure) { const result = failure; failure = null; if (result instanceof Error) throw result; return reply(result, { code: result === 403 ? 'forbidden' : 'authentication_failed' }); }
    if (heldWrite) { const wait = heldWrite; heldWrite = null; await wait.promise; }
    const target = decodeURIComponent(path.split('/').at(-1));
    if (options.method === 'DELETE') { store[owner] = store[owner].filter(item => item.id !== target); return reply(204); }
    const status = JSON.parse(options.body).status;
    const old = options.method === 'PATCH' ? store[owner].find(item => item.id === target) : store[owner].find(item => item.scope_id === target);
    const item = old ? { ...old, status } : row('entry-' + target, target, status);
    store[owner] = [...store[owner].filter(value => value.scope_id !== item.scope_id), item];
    return reply(200, { item });
  });
  const controller = createAccountController(fetcher);
  return { controller, fetcher, store, actor: value => { actor = value; }, fail: value => { failure = value; }, hold: value => { held = value; }, holdWrite: value => { heldWrite = value; } };
}

test('opaque IDs support nonUUID Unicode and encode segments without query/header injection', () => {
  expect(opaqueSegment('scope é?#')).toBe('scope%20%C3%A9%3F%23');
  for (const value of ['', 'x'.repeat(65), 'bad\0', '\ud800', null]) expect(() => opaqueSegment(value)).toThrow();
});
test('all saved scopes load once and publication stays controller-owned, not a public filter', async () => {
  const f = fixture(), c = f.controller; await c.refresh();
  expect(await Promise.all([c.loadEntries(), c.loadEntries()])).toEqual([true, true]);
  expect(c.getSnapshot().entries.items.map(item => item.scope_id)).toEqual(['scope-one', 'scope-two']);
  expect(f.fetcher.mock.calls.filter(([path]) => path.endsWith('/saved-entries'))).toHaveLength(1);
  expect(f.fetcher.mock.calls.at(-2)[1].headers['X-CSRF-Token']).toBe('a'.repeat(64));
});
test('two scopes same race preserve individual status and server responses are authoritative', async () => {
  const f = fixture(), c = f.controller; await c.refresh(); await c.loadEntries();
  expect(await c.saveScope('scope-one', 'registered')).toBe(true);
  expect(c.getSnapshot().entries.items.map(item => item.status)).toEqual(['registered', 'planned']);
  const call = f.fetcher.mock.calls.find(([,options]) => options.method === 'PATCH');
  expect(call[0]).toBe('/api/v1/me/saved-entries/entry-one');
  expect(JSON.parse(call[1].body)).toEqual({ status: 'registered' });
  expect(await c.removeEntry('entry-one')).toBe(true);
  expect(c.getSnapshot().entries.items.map(item => item.id)).toEqual(['entry-two']);
  expect(await c.saveScope('opaque scope é', 'completed')).toBe(true);
  expect(f.fetcher.mock.calls.some(([path]) => path.endsWith('by-scope/opaque%20scope%20%C3%A9'))).toBe(true);
});
test('refresh clears private entries immediately and a resolved lease cannot survive ABA', async () => {
  const f = fixture(), c = f.controller; await c.refresh(); await c.loadEntries();
  const lease = c.captureContext(); expect(c.isCurrent(lease)).toBe(true);
  f.actor(B); const refresh = c.refresh();
  expect(c.getSnapshot().entries.items).toEqual([]);
  expect(c.isCurrent(lease)).toBe(false);
  await refresh; f.actor(A); await c.refresh();
  expect(c.getSnapshot().account).toEqual(A);
  expect(c.isCurrent(lease)).toBe(false);
});
test('context switch AFTER readPrivate resolves cannot publish its result through loadEntries', async () => {
  const f = fixture(), c = f.controller; await c.refresh();
  const read = c.readPrivate;
  c.readPrivate = async kind => { const resolved = await read(kind); f.actor(B); await c.refresh(); return resolved; };
  expect(await c.loadEntries()).toBe(false);
  expect(c.getSnapshot()).toMatchObject({ account: B, entries: { items: [] } });
});
test('unabortable late list A cannot republish after actor B has loaded its own list', async () => {
  const f = fixture(), c = f.controller; await c.refresh();
  const held = deferred(); f.hold(held);
  const old = c.loadEntries();
  await vi.waitFor(() => expect(f.fetcher.mock.calls.some(([path]) => path.endsWith('/saved-entries'))).toBe(true));
  f.actor(B); await c.refresh(); await c.loadEntries();
  held.resolve(reply(200, { items: [row('secret-a', 'scope-a')] }));
  await old;
  expect(c.getSnapshot()).toMatchObject({ account: B, entries: { status: 'ready', items: [] } });
});
test('403 preserves actor and saved truth, network outcome clears list until explicit read, never retries mutation', async () => {
  const f = fixture(), c = f.controller; await c.refresh(); await c.loadEntries();
  f.fail(403); expect(await c.saveScope('scope-one', 'registered')).toBe(false);
  expect(c.getSnapshot().account).toEqual(A);
  expect(c.getSnapshot().entries.items[0].status).toBe('interested');
  f.fail(new TypeError('synthetic network'));
  expect(await c.saveScope('scope-one', 'registered')).toBe(false);
  expect(c.getSnapshot().entries).toMatchObject({ status: 'error', items: [] });
  expect(f.fetcher.mock.calls.filter(([,options]) => options.method === 'PATCH')).toHaveLength(2);
  await c.loadEntries(); expect(c.getSnapshot().entries.items).toHaveLength(2);
});

test('refresh during dispatched write hides private data, then revalidates without claiming or retrying the write', async () => {
  const f = fixture(), c = f.controller; await c.refresh(); await c.loadEntries();
  const hold = deferred(); f.holdWrite(hold);
  const operation = c.saveScope('scope-one', 'registered');
  await vi.waitFor(() => expect(f.fetcher.mock.calls.some(([,options]) => options.method === 'PATCH')).toBe(true));
  const old = c.captureContext(); f.actor(B);
  await c.refresh();
  expect(c.getSnapshot().entries.items).toEqual([]);
  expect(c.isCurrent(old)).toBe(false);
  hold.resolve(); expect(await operation).toBe(false);
  await vi.waitFor(() => expect(c.getSnapshot()).toMatchObject({ account: B, busy: false, revalidating: false }));
  expect(c.getSnapshot().entries.items).toEqual([]);
  expect(f.store.a.find(item => item.scope_id === 'scope-one').status).toBe('registered');
  expect(f.fetcher.mock.calls.filter(([,options]) => options.method === 'PATCH')).toHaveLength(1);
});
