import { expect, test, vi } from 'vitest';
import { createAccountController } from './privateAccount.js';
const A = { id: 'a', email: 'alice@example.test' }, B = { id: 'b', email: 'bob@example.test' };
const proof = 'p'.repeat(64);
function setup(status = 204, code, actionReply) {
  let actor = A;
  const fetcher = vi.fn(async (path, options) => {
    if (path.endsWith('/csrf')) return new Response(JSON.stringify({ csrf_token: proof }));
    if (path === '/api/v1/me' && options.method === 'GET') return new Response(JSON.stringify({ account: actor }));
    if (actionReply) return actionReply();
    return new Response(status === 204 ? null : JSON.stringify({ code }), { status });
  });
  const controller = createAccountController(fetcher);
  return { controller, fetcher, switchActor: value => { actor = value; } };
}
test.each(['logout', 'logoutAll', 'changePassword', 'deleteAccount'])('only exact204 confirms %s after bound preflight', async action => {
  const { controller: c, fetcher } = setup(); await c.refresh();
  expect(await c.sensitive(action, { current_password: ' old exact ', new_password: ' new exact ' })).toBe(true);
  expect(c.getSnapshot().account).toBeNull();
  const operation = fetcher.mock.lastCall[1];
  expect(operation.headers['X-CSRF-Token']).toBe(proof);
  expect(fetcher.mock.calls.at(-2)[1].headers['X-CSRF-Token']).toBe(proof);
  expect(JSON.parse(operation.body)).toEqual(action === 'logout' ? {} : { current_password: ' old exact ', ...(action === 'changePassword' ? { new_password: ' new exact ' } : {}) });
});
test.each([200, 202])('unexpected successful HTTP%s is unknown, never success or retry', async status => {
  const { controller: c, fetcher } = setup(status); await c.refresh();
  expect(await c.sensitive('logoutAll', { current_password: 'exact' })).toBe(false);
  expect(c.getSnapshot()).toMatchObject({ account: A, error: { code: 'unconfirmed_response' }, message: null });
  expect(fetcher).toHaveBeenCalledTimes(4);
});
test('reauth403 preserves account and network failure does not claim rollback', async () => {
  const { controller: c } = setup(403, 'reauthentication_failed'); await c.refresh();
  expect(await c.sensitive('deleteAccount', { current_password: 'wrong' })).toBe(false);
  expect(c.getSnapshot()).toMatchObject({ account: A, error: { code: 'reauthentication_failed', status: 403 } });
  const { controller: offline } = setup(204, null, () => { throw new TypeError('synthetic'); }); await offline.refresh();
  expect(await offline.sensitive('logout')).toBe(false);
  expect(offline.getSnapshot()).toMatchObject({ account: A, error: { code: 'network' }, message: null });
});
test('late resolved operation from A cannot clear B even if abort ignored', async () => {
  let resolve;
  const pending = new Promise(done => { resolve = done; });
  const { controller: c, switchActor } = setup(204, null, () => pending); await c.refresh();
  const action = c.sensitive('logout');
  // Wait until the operation reached the transport, not merely its preflight.
  for (let i = 0; i < 20; i++) await Promise.resolve();
  c.cancel(); switchActor(B); await c.refresh();
  resolve(new Response(null, { status: 204 }));
  expect(await action).toBe(false);
  expect(c.getSnapshot()).toMatchObject({ account: B, message: null, error: null });
});
test('current401 invalidates only this context; an old401 cannot invalidate ABA', async () => {
  const { controller: current } = setup(401, 'authentication_failed'); await current.refresh();
  expect(await current.sensitive('logout')).toBe(false);
  expect(current.getSnapshot().account).toBeNull();
  let resolve;
  const pending = new Promise(done => { resolve = done; });
  const { controller: c, switchActor } = setup(204, null, () => pending); await c.refresh();
  const action = c.sensitive('logout');
  for (let i = 0; i < 20; i++) await Promise.resolve();
  c.cancel(); switchActor(B); await c.refresh(); switchActor(A); await c.refresh();
  resolve(new Response(JSON.stringify({ code: 'authentication_failed' }), { status: 401 }));
  expect(await action).toBe(false);
  expect(c.getSnapshot()).toMatchObject({ account: A, message: null, error: null });
});
test('calendar uses the bound proof and loses its lease after any refresh', async () => {
  const { controller: c, fetcher } = setup(200, null, () => new Response('BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n', { headers: { 'Content-Type': 'text/calendar; charset=utf-8' } }));
  await c.refresh();
  const result = await c.prepareCalendar();
  expect(result.blob.size).toBeGreaterThan(0);
  expect(c.isCurrent(result.context)).toBe(true);
  expect(fetcher.mock.lastCall[0]).toBe('/api/v1/me/calendar.ics');
  expect(fetcher.mock.lastCall[1].headers['X-CSRF-Token']).toBe(proof);
  await c.refresh();
  expect(c.isCurrent(result.context)).toBe(false);
});
test.each([206, 202])('calendar rejects HTTP%s without returning any file', async status => {
  const { controller: c } = setup(status, null, () => new Response('synthetic', { status, headers: { 'Content-Type': 'text/calendar' } }));
  await c.refresh();
  expect(await c.prepareCalendar()).toBeNull();
  expect(c.getSnapshot()).toMatchObject({ account: A, error: { code: 'unconfirmed_response' } });
});
