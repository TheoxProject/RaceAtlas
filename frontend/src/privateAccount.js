import { opaqueSegment, SAVED_LABELS } from './season.js';
const AUTH = '/api/v1/auth/';
const ACTIONS = {
  login: 'login', register: 'register', resend: 'confirmation/resend', forgot: 'password-reset/request',
  confirm: 'confirmation/complete', reset: 'password-reset/complete',
};
const READS = { entries: '/api/v1/me/saved-entries', calendar: '/api/v1/me/calendar.ics' };
const ROUTES = new Set(['/api/v1/me', AUTH + 'csrf', ...Object.values(ACTIONS).map(path => AUTH + path), ...Object.values(READS)]);
const ACCEPTED = 'Demande prise en compte. Vérifiez votre boîte de réception et vos courriers indésirables ; si un message vous parvient, suivez ses instructions.';

export class AccountRequestError extends Error {
  constructor(code, status = 0) { super('La demande de compte n’a pas abouti.'); this.code = code; this.status = status; }
}
const stopped = () => new DOMException('Demande interrompue.', 'AbortError');

// No public fetch monkeypatch, provider headers, storage, logs or session bearer in JS.
export function createAccountController(fetcher = (...args) => globalThis.fetch(...args)) {
  const emptyEntries = () => ({ status: 'idle', items: [], error: null });
  let state = { status: 'unknown', account: null, busy: false, revalidating: false, error: null, message: null, contextEpoch: 0, entries: emptyEntries(), entryError: null };
  let generation = 0, contextEpoch = 0, listTask = null, refreshQueued = false;
  const listeners = new Set(), pending = new Set();
  const publish = patch => { state = { ...state, ...patch }; listeners.forEach(listener => listener()); };
  const invalidate = () => { generation += 1; pending.forEach(controller => controller.abort()); pending.clear(); return generation; };
  const advanceContext = () => { contextEpoch += 1; listTask = null; return { contextEpoch, entries: emptyEntries(), entryError: null }; };
  const current = operation => operation.ticket === generation && operation.epoch === contextEpoch;
  const begin = () => { const ticket = invalidate(), controller = new AbortController(); pending.add(controller); return { ticket, epoch: contextEpoch, controller }; };
  const assertCurrent = operation => { if (!current(operation) || operation.controller.signal.aborted) throw stopped(); };
  const contextFor = operation => Object.freeze({ generation: operation.ticket, contextEpoch: operation.epoch, accountId: state.account?.id || null });
  const isCurrent = context => context && context.generation === generation && context.contextEpoch === contextEpoch && context.accountId === state.account?.id && state.status === 'member' && !state.revalidating;
  const entryPath = /^\/api\/v1\/me\/saved-entries\/(?:by-scope\/)?[^/?#]+$/;
  async function request(path, operation, { method = 'GET', body, headers = {}, binary = false } = {}) {
    if (!ROUTES.has(path) && !entryPath.test(path)) throw new AccountRequestError('invalid_request');
    const response = await fetcher(path, {
      method, credentials: 'same-origin', cache: 'no-store', redirect: 'error', referrerPolicy: 'no-referrer', mode: 'same-origin',
      signal: operation.controller.signal, headers: { ...headers, ...(body === undefined ? {} : { 'Content-Type': 'application/json' }) },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
    assertCurrent(operation);
    if (!response.ok) {
      let code = 'unavailable';
      try { code = (await response.json()).code || code; } catch { /* no raw response text */ }
      assertCurrent(operation);
      throw new AccountRequestError(code, response.status);
    }
    const result = binary ? await response.blob() : response.status === 204 ? null : await response.json();
    assertCurrent(operation);
    return result;
  }
  async function me(operation, proof) {
    try { return (await request('/api/v1/me', operation, { headers: proof ? { 'X-CSRF-Token': proof } : {} })).account; }
    catch (error) { if (error.status === 401) return null; throw error; }
  }
  function showAccount(account, patch = {}) {
    const changed = (account?.id || null) !== (state.account?.id || null);
    publish({ ...(changed ? { ...advanceContext(), message: null } : {}), account, status: account ? 'member' : 'anonymous', revalidating: false, ...patch });
  }
  function failure(error, operation, patch = {}) {
    if (operation.ticket !== generation || error.name === 'AbortError' || operation.epoch !== contextEpoch && error.code !== 'context_changed') return;
    publish({ busy: false, error: { code: error.code || 'network', status: error.status || 0 }, ...patch });
  }
  async function preflight(operation, expected) {
    const { csrf_token: proof } = await request(AUTH + 'csrf', operation);
    const actual = await me(operation, proof);
    if ((actual?.id || null) !== (expected?.id || null)) {
      showAccount(actual, { message: null });
      publish({ entries: { status: 'error', items: [], error: { code: 'context_changed' } } });
      throw new AccountRequestError('context_changed');
    }
    return proof;
  }
  function settle(operation) {
    pending.delete(operation.controller);
    if (operation.ticket === generation && state.busy) publish({ busy: false });
    if (refreshQueued && !state.busy) { refreshQueued = false; api.refresh(); }
  }
  async function writeEntry(scopeId, action) {
    if (!state.account || state.status !== 'member' || state.busy || state.revalidating || state.entries.status !== 'ready') return false;
    const expected = state.account, items = state.entries.items, operation = begin();
    publish({ busy: true, error: null, entryError: null });
    try {
      const csrf = await preflight(operation, expected);
      const next = await action(operation, csrf, items);
      const context = contextFor(operation);
      if (!isCurrent(context)) throw stopped();
      publish({ entries: { status: 'ready', items: next, error: null }, busy: false });
      return true;
    } catch (error) {
      if (current(operation)) {
        if (error.status === 401) showAccount(null);
        else publish({ entryError: { scopeId, code: error.code || 'network', status: error.status || 0 }, ...(error.status ? {} : { entries: { status: 'error', items: [], error: { code: 'network' } } }) });
      }
      failure(error, operation);
      return false;
    } finally { settle(operation); }
  }
  const api = {
    getSnapshot: () => state,
    subscribe: listener => { listeners.add(listener); return () => listeners.delete(listener); },
    captureContext: () => Object.freeze({ generation, contextEpoch, accountId: state.account?.id || null }),
    isCurrent,
    cancel() { invalidate(); refreshQueued = false; publish({ ...advanceContext(), busy: false, revalidating: false }); },
    clearFeedback() { publish({ error: null, message: null, entryError: null }); },
    async refresh() {
      if (state.busy) {
        if (!refreshQueued) { refreshQueued = true; publish({ ...advanceContext(), revalidating: true }); }
        return;
      }
      const patch = advanceContext(), operation = begin();
      publish({ ...patch, revalidating: true });
      try { const account = await me(operation); assertCurrent(operation); showAccount(account, { error: null, ...((account?.id || null) !== (state.account?.id || null) ? { message: null } : {}) }); }
      catch (error) { failure(error, operation, { status: 'unavailable', account: null, revalidating: false }); }
      finally { settle(operation); }
    },
    async submit(action, fields = {}, proof) {
      if (!Object.hasOwn(ACTIONS, action) || state.busy) return false;
      const expected = state.account, patch = advanceContext(), operation = begin();
      publish({ ...patch, busy: true, revalidating: false, error: null, message: null });
      try {
        const csrf = await preflight(operation, expected);
        await request(AUTH + ACTIONS[action], operation, { method: 'POST', body: fields, headers: { 'X-CSRF-Token': csrf, ...(proof ? { 'X-Account-Proof': proof } : {}) } });
        const account = await me(operation);
        assertCurrent(operation);
        const message = action === 'confirm' ? 'Adresse confirmée. Vous pouvez maintenant vous connecter.' : action === 'reset' ? 'Mot de passe réinitialisé. Cette action ne vous connecte pas automatiquement.' : action === 'login' ? 'Connexion réussie.' : ACCEPTED;
        showAccount(account, { busy: false, message, error: null });
        return true;
      } catch (error) { failure(error, operation); return false; }
      finally { settle(operation); }
    },
    async readPrivate(kind) {
      const expected = state.account;
      if (!expected || !Object.hasOwn(READS, kind) || state.busy || state.revalidating) throw new AccountRequestError('authentication_failed', 401);
      const operation = begin();
      try {
        const csrf = await preflight(operation, expected);
        const data = await request(READS[kind], operation, { headers: { 'X-CSRF-Token': csrf }, binary: kind === 'calendar' });
        return { data, context: contextFor(operation) };
      } catch (error) {
        if (current(operation) && error.status === 401) showAccount(null);
        failure(error, operation);
        throw error;
      } finally { settle(operation); }
    },
    loadEntries() {
      if (!state.account || state.status !== 'member' || state.revalidating || state.busy) return Promise.resolve(false);
      if (listTask) return listTask;
      const epoch = contextEpoch;
      publish({ entries: { status: 'loading', items: [], error: null }, entryError: null });
      const task = (async () => {
        try {
          const result = await api.readPrivate('entries');
          if (!isCurrent(result.context)) return false;
          if (!Array.isArray(result.data.items) || result.data.items.length > 1000) throw new AccountRequestError('invalid_response');
          publish({ entries: { status: 'ready', items: result.data.items, error: null } });
          return true;
        } catch (error) {
          if (epoch === contextEpoch && error.name !== 'AbortError') publish({ entries: { status: 'error', items: [], error: { code: error.code || 'network', status: error.status || 0 } } });
          return false;
        } finally { if (listTask === task) listTask = null; }
      })();
      listTask = task;
      return task;
    },
    saveScope(scopeId, status) {
      if (!Object.hasOwn(SAVED_LABELS, status)) return Promise.resolve(false);
      let encoded;
      try { encoded = opaqueSegment(scopeId); } catch { return Promise.resolve(false); }
      return writeEntry(scopeId, async (operation, csrf, items) => {
        const existing = items.find(item => item.scope_id === scopeId);
        const path = existing ? READS.entries + '/' + opaqueSegment(existing.id) : READS.entries + '/by-scope/' + encoded;
        const result = await request(path, operation, { method: existing ? 'PATCH' : 'PUT', body: { status }, headers: { 'X-CSRF-Token': csrf } });
        if (result.item?.scope_id !== scopeId) throw new AccountRequestError('invalid_response');
        return [...items.filter(item => item.scope_id !== scopeId), result.item].sort((a, b) => a.created_at.localeCompare(b.created_at) || a.id.localeCompare(b.id));
      });
    },
    removeEntry(entryId) {
      const saved = state.entries.items.find(item => item.id === entryId);
      if (!saved) return Promise.resolve(false);
      return writeEntry(saved.scope_id, async (operation, csrf, items) => {
        await request(READS.entries + '/' + opaqueSegment(entryId), operation, { method: 'DELETE', body: {}, headers: { 'X-CSRF-Token': csrf } });
        return items.filter(item => item.id !== entryId);
      });
    },
  };
  return api;
}
