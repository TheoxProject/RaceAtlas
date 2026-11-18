import { expect, test, vi } from 'vitest';
import { createAccountController } from './privateAccount.js';
const A = { id: 'alice' }, B = { id: 'bob' }, proof = 'a'.repeat(64), cursor = 'opaque.' + 'b'.repeat(43);
const entry = scope => ({ id: 'saved-' + scope, scope_id: scope, created_at: '2026-11-17', scope: { id: scope, raw_label: scope }, race: { name: 'Course' } });
const item = (change, scope, read = false) => ({ change_id: change, scope_id: scope, kind: 'business', created_at: '2026-11-17T10:00:00Z', read_at: read ? '2026-11-17T11:00:00Z' : null, entry: entry(scope), delta: { before: { name: 'Avant' }, after: { name: 'Après' } }, provenance: { source_url: 'https://example.test/source', checked_at: '2026-11-17T10:00:00Z' } });
const page = (items = [item('change', 'one')], count = 87, more = false) => ({ items, unread_count: count, has_more: more, next_cursor: more ? cursor : null });
const reply = (status, data = {}) => ({ status, ok: status >= 200 && status < 300, json: async () => data });
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };
function setup() {
  const server = { actor: A, entries: [entry('one'), entry('two')], notifications: () => reply(200, page()), ack: () => reply(204), entriesRead: null };
  const fetcher = vi.fn(async (path, options) => {
    if (path.endsWith('/csrf')) return reply(200, { csrf_token: proof });
    if (path === '/api/v1/me') return reply(200, { account: server.actor });
    if (path === '/api/v1/me/saved-entries') return server.entriesRead ? server.entriesRead() : reply(200, { items: server.entries });
    if (path === '/api/v1/me/notifications/read-all') return server.ack();
    if (path.startsWith('/api/v1/me/notifications?')) return server.notifications(path);
    if (options.method === 'DELETE') { server.entries = server.entries.filter(e => path !== '/api/v1/me/saved-entries/' + e.id); return reply(204); }
    throw Error('Unexpected synthetic endpoint');
  });
  return { server, fetcher, c: createAccountController(fetcher) };
}

test('one season preflight sequences entries and notifications, exact global count', async () => {
  const { c, fetcher } = setup(); await c.refresh();
  expect(await c.loadSeason()).toBe(true);
  expect(c.getSnapshot()).toMatchObject({ busy: false, entries: { status: 'ready' }, notifications: { status: 'ready', unreadCount: 87, items: [item('change', 'one')] } });
  const requests = fetcher.mock.calls;
  expect(requests.filter(([p]) => p.endsWith('/csrf'))).toHaveLength(1);
  for (const [path, options] of requests.slice(2)) {
    expect(options.headers['X-CSRF-Token']).toBe(proof);
    expect(options).toMatchObject({ credentials: 'same-origin', mode: 'cors', cache: 'no-store', redirect: 'error', referrerPolicy: 'no-referrer' });
    expect(path.startsWith('/api/')).toBe(true);
  }
});

test('ScopeSaveActions listTask coalesces with season instead of aborting or looping', async () => {
  const { c, server, fetcher } = setup(), waiting = deferred(); await c.refresh();
  server.entriesRead = () => waiting.promise;
  const scopes = c.loadEntries();
  await vi.waitFor(() => expect(fetcher.mock.calls.some(([p]) => p === '/api/v1/me/saved-entries')).toBe(true));
  const season = c.loadSeason(); expect(c.loadSeason()).toBe(season);
  waiting.resolve(reply(200, { items: server.entries }));
  expect(await scopes).toBe(true); expect(await season).toBe(true);
  expect(fetcher.mock.calls.filter(([p]) => p === '/api/v1/me/saved-entries')).toHaveLength(1);
  expect(fetcher.mock.calls.filter(([p]) => p.startsWith('/api/v1/me/notifications?'))).toHaveLength(1);
});

test('pagination deduplicates composite identities and takes global count from server', async () => {
  const { c, server, fetcher } = setup(); await c.refresh();
  server.notifications = () => reply(200, page([item('change', 'one'), item('change', 'two')], 87, true));
  await c.loadSeason();
  server.notifications = () => reply(200, page([item('change', 'two'), item('next', 'two')], 86));
  expect(await c.loadNotifications({ more: true })).toBe(true);
  expect(c.getSnapshot().notifications.items).toHaveLength(3);
  expect(c.getSnapshot().notifications.unreadCount).toBe(86);
  expect(fetcher.mock.calls.at(-1)[0]).toBe('/api/v1/me/notifications?limit=50&cursor=' + cursor);
});

test('ACK204 then GET can return new unread; no false zero or second POST', async () => {
  const { c, server, fetcher } = setup(); await c.refresh(); await c.loadSeason();
  const counts = []; c.subscribe(() => counts.push(c.getSnapshot().notifications.unreadCount));
  server.notifications = () => reply(200, page([item('after-ack', 'one')], 1));
  expect(await c.markNotificationsRead()).toBe(true);
  expect(c.getSnapshot().notifications.unreadCount).toBe(1); expect(counts).not.toContain(0);
  expect(fetcher.mock.calls.filter(([p]) => p.endsWith('/read-all'))).toHaveLength(1);
});

for (const status of [200, 202, 0]) test(`unconfirmed ACK${status} is unknown and never retried`, async () => {
  const { c, server, fetcher } = setup(); await c.refresh(); await c.loadSeason();
  server.ack = () => { if (!status) throw TypeError('Synthetic offline'); return reply(status); };
  expect(await c.markNotificationsRead()).toBe(false);
  expect(c.getSnapshot().notifications).toMatchObject({ status: 'error', unreadCount: null, message: null });
  expect(await c.markNotificationsRead()).toBe(false);
  expect(fetcher.mock.calls.filter(([p]) => p.endsWith('/read-all'))).toHaveLength(1);
  expect(fetcher.mock.calls.filter(([p]) => p.startsWith('/api/v1/me/notifications?'))).toHaveLength(1);
});

test('confirmed ACK with failed refresh is distinct and refresh does not resend POST', async () => {
  const { c, server, fetcher } = setup(); await c.refresh(); await c.loadSeason();
  server.notifications = () => { throw TypeError('Synthetic offline'); };
  expect(await c.markNotificationsRead()).toBe(false);
  expect(c.getSnapshot().notifications.message).toMatch(/Lecture enregistrée/);
  expect(c.getSnapshot().notifications.unreadCount).toBeNull();
  server.notifications = () => reply(200, page([], 0)); await c.loadNotifications();
  expect(fetcher.mock.calls.filter(([p]) => p.endsWith('/read-all'))).toHaveLength(1);
});

test('removal clears only its scopes, invalidates off-page count and reloads server truth', async () => {
  const { c, server } = setup(); await c.refresh();
  server.notifications = () => reply(200, page([item('a', 'one'), item('b', 'one'), item('c', 'two')], 100));
  await c.loadSeason(); await c.removeEntry('saved-one');
  expect(c.getSnapshot().notifications.unreadCount).toBeNull();
  expect(c.getSnapshot().notifications.items.map(x => x.scope_id)).toEqual(['two']);
  server.notifications = () => reply(200, page([item('c', 'two')], 44));
  await c.loadSeason(); expect(c.getSnapshot().notifications.unreadCount).toBe(44);
});

for (const late of [200, 401]) test(`late${late} after ABA cannot publish, logout or settle new task`, async () => {
  const { c, server } = setup(); await c.refresh(); await c.loadSeason();
  const old = deferred(); server.notifications = () => old.promise;
  const abandoned = c.loadNotifications(); await Promise.resolve();
  c.cancel(); server.actor = B; await c.refresh(); server.actor = A; await c.refresh();
  const fresh = deferred(); server.notifications = () => fresh.promise;
  const active = c.loadSeason(); await Promise.resolve();
  old.resolve(reply(late, late === 200 ? page([item('old', 'one')], 999) : { code: 'authentication_failed' }));
  await abandoned;
  expect(c.getSnapshot().account).toEqual(A); expect(c.getSnapshot().busy).toBe(true);
  fresh.resolve(reply(200, page([item('fresh', 'one')], 1))); await active;
  expect(c.getSnapshot().notifications.items[0].change_id).toBe('fresh');
});

test('initial listTask wait cannot resume old season intent after actor ABA', async () => {
  const { c, server, fetcher } = setup(), old = deferred(); await c.refresh();
  server.entriesRead = () => old.promise; const list = c.loadEntries();
  await vi.waitFor(() => expect(fetcher.mock.calls.some(([p]) => p.endsWith('/saved-entries'))).toBe(true));
  const season = c.loadSeason(); await Promise.resolve();
  c.cancel(); server.actor = B; await c.refresh(); server.actor = A; await c.refresh();
  old.resolve(reply(200, { items: server.entries })); await list;
  expect(await season).toBe(false);
  expect(fetcher.mock.calls.filter(([p]) => p.startsWith('/api/v1/me/notifications?'))).toHaveLength(0);
});

test('initial wait also preserves ticket when another read starts in same actor epoch', async () => {
  const { c, server, fetcher } = setup(), old = deferred(); await c.refresh();
  server.entriesRead = () => old.promise; const list = c.loadEntries();
  await vi.waitFor(() => expect(fetcher.mock.calls.some(([p]) => p.endsWith('/saved-entries'))).toBe(true));
  const season = c.loadSeason(); await Promise.resolve();
  let competing;
  const off = c.subscribe(() => { if (!competing && c.getSnapshot().entries.status === 'ready') competing = c.readPrivate('entries'); });
  old.resolve(reply(200, { items: server.entries })); await list;
  expect(await season).toBe(false); await competing; off();
  expect(fetcher.mock.calls.filter(([p]) => p.startsWith('/api/v1/me/notifications?'))).toHaveLength(0);
});
