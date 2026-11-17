import { readCalendar } from './calendarDownload.js';
import { opaqueSegment, SAVED_LABELS } from './season.js';
import { notificationPath, allowedNotificationPath, notificationPage, notificationKey } from './notifications.js';
const AUTH = '/api/v1/auth/';
const ACTIONS = {
  login: 'login', register: 'register', resend: 'confirmation/resend', forgot: 'password-reset/request',
  confirm: 'confirmation/complete', reset: 'password-reset/complete',
};
const SENSITIVE = {
  logout: { path: AUTH + 'logout', method: 'POST' },
  logoutAll: { path: AUTH + 'logout-all', method: 'POST' },
  changePassword: { path: AUTH + 'password/change', method: 'POST' },
  deleteAccount: { path: '/api/v1/me', method: 'DELETE' },
};
const READS = { entries: '/api/v1/me/saved-entries', calendar: '/api/v1/me/calendar.ics' };
const NOTIFICATION_ACK = '/api/v1/me/notifications/read-all';
const ROUTES = new Set(['/api/v1/me', NOTIFICATION_ACK, AUTH + 'csrf', ...Object.values(ACTIONS).map(path => AUTH + path), ...Object.values(READS), ...Object.values(SENSITIVE).map(item => item.path)]);
const ACCEPTED = 'Demande prise en compte. Vérifiez votre boîte de réception et vos courriers indésirables ; si un message vous parvient, suivez ses instructions.';

export class AccountRequestError extends Error {
  constructor(code, status = 0) { super('La demande de compte n’a pas abouti.'); this.code = code; this.status = status; }
}
const stopped = () => new DOMException('Demande interrompue.', 'AbortError');

// No public fetch monkeypatch, provider headers, storage, logs or session bearer in JS.
export function createAccountController(fetcher = (...args) => globalThis.fetch(...args)) {
  const emptyEntries = () => ({ status: 'idle', items: [], error: null });
  const emptyNotifications = () => ({ status: 'idle', items: [], unreadCount: null, nextCursor: null, hasMore: false, error: null, message: null });
  let state = { status: 'unknown', account: null, busy: false, revalidating: false, error: null, message: null, contextEpoch: 0, entries: emptyEntries(), notifications: emptyNotifications(), entryError: null };
  let generation = 0, contextEpoch = 0, listTask = null, seasonTask = null, notificationTask = null, refreshQueued = false;
  const listeners = new Set(), pending = new Set();
  const publish = patch => { state = { ...state, ...patch }; listeners.forEach(listener => listener()); };
  const invalidate = () => { generation += 1; pending.forEach(controller => controller.abort()); pending.clear(); return generation; };
  const advanceContext = () => { contextEpoch += 1; listTask = null; seasonTask = null; notificationTask = null; return { contextEpoch, entries: emptyEntries(), notifications: emptyNotifications(), entryError: null }; };
  const current = operation => operation.ticket === generation && operation.epoch === contextEpoch;
  const begin = () => { const ticket = invalidate(), controller = new AbortController(); pending.add(controller); return { ticket, epoch: contextEpoch, controller }; };
  const assertCurrent = operation => { if (!current(operation) || operation.controller.signal.aborted) throw stopped(); };
  const contextFor = operation => Object.freeze({ generation: operation.ticket, contextEpoch: operation.epoch, accountId: state.account?.id || null });
  const isCurrent = context => context && context.generation === generation && context.contextEpoch === contextEpoch && context.accountId === state.account?.id && state.status === 'member' && !state.revalidating;
  const entryPath = /^\/api\/v1\/me\/saved-entries\/(?:by-scope\/)?[^/?#]+$/;
  async function request(path, operation, { method = 'GET', body, headers = {}, binary = false, expectedStatus } = {}) {
    assertCurrent(operation);
    if (!ROUTES.has(path) && !entryPath.test(path) && !allowedNotificationPath(path)) throw new AccountRequestError('invalid_request');
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
    if (expectedStatus !== undefined && response.status !== expectedStatus) {
      try { await response.body?.cancel(); } catch { /* unknown response, no body exposed */ }
      assertCurrent(operation);
      throw new AccountRequestError('unconfirmed_response');
    }
    const result = binary ? await readCalendar(response, () => assertCurrent(operation)) : response.status === 204 ? null : await response.json();
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
  async function notificationHead(operation, proof, cursor = null) {
    const data = await request(notificationPath(cursor), operation, { headers: { 'X-CSRF-Token': proof }, expectedStatus: 200 });
    const page = notificationPage(data);
    if (!isCurrent(contextFor(operation))) throw stopped();
    return page;
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
    async prepareCalendar() {
      if (!state.account || state.status !== 'member' || state.busy || state.revalidating) return null;
      const expected = state.account, operation = begin();
      publish({ busy: true, error: null });
      try {
        const csrf = await preflight(operation, expected);
        const blob = await request(READS.calendar, operation, { headers: { 'X-CSRF-Token': csrf }, binary: true, expectedStatus: 200 });
        const context = contextFor(operation);
        if (!isCurrent(context)) throw stopped();
        return { blob, context };
      } catch (error) {
        if (current(operation) && error.status === 401) showAccount(null);
        failure(error, operation);
        return null;
      } finally { settle(operation); }
    },
    async sensitive(action, fields = {}) {
      if (!Object.hasOwn(SENSITIVE, action) || !state.account || state.status !== 'member' || state.busy || state.revalidating) return false;
      const config = SENSITIVE[action], expected = state.account;
      const body = action === 'logout' ? {} : { current_password: fields.current_password, ...(action === 'changePassword' ? { new_password: fields.new_password } : {}) };
      const patch = advanceContext(), operation = begin();
      publish({ ...patch, busy: true, error: null, message: null });
      try {
        const csrf = await preflight(operation, expected);
        await request(config.path, operation, { method: config.method, body, headers: { 'X-CSRF-Token': csrf }, expectedStatus: 204 });
        assertCurrent(operation);
        const message = action === 'deleteAccount' ? 'Votre compte et ses données personnelles ont été supprimés.' : action === 'changePassword' ? 'Mot de passe modifié. Reconnectez-vous ; vos anciennes sessions ont été révoquées.' : action === 'logoutAll' ? 'Déconnexion de tous vos appareils effectuée.' : 'Déconnexion effectuée sur cet appareil.';
        showAccount(null, { busy: false, message, error: null });
        return true;
      } catch (error) {
        if (current(operation) && error.status === 401) showAccount(null, { message: 'Votre connexion n’est plus active. Vérifiez le compte avant une nouvelle action.' });
        failure(error, operation);
        return false;
      } finally { settle(operation); }
    },
    loadEntries() {
      if (listTask) return listTask;
      if (!state.account || state.status !== 'member' || state.revalidating || state.busy) return Promise.resolve(false);
      let readContext = null;
      publish({ entries: { status: 'loading', items: [], error: null }, entryError: null });
      const task = (async () => {
        try {
          const pendingRead = api.readPrivate('entries');
          readContext = api.captureContext();
          const result = await pendingRead;
          if (!isCurrent(result.context)) return false;
          if (!Array.isArray(result.data.items) || result.data.items.length > 1000) throw new AccountRequestError('invalid_response');
          publish({ entries: { status: 'ready', items: result.data.items, error: null } });
          return true;
        } catch (error) {
          if (isCurrent(readContext) && error.name !== 'AbortError') publish({ entries: { status: 'error', items: [], error: { code: error.code || 'network', status: error.status || 0 } } });
          return false;
        } finally { if (listTask === task) listTask = null; }
      })();
      listTask = task;
      return task;
    },
    loadSeason({ refresh = false } = {}) {
      if (seasonTask) return seasonTask;
      if (!state.account || state.status !== 'member' || state.busy || state.revalidating) return Promise.resolve(false);
      const expected = state.account.id, epoch = contextEpoch;
      const task = Promise.resolve().then(async () => {
        // ScopeSaveActions may already be reading behind the dialog. Let that
        // operation finish before starting our single preflight/read pipeline.
        const waiting = listTask, waitingTicket = generation;
        if (waiting && !await waiting) return false;
        if (generation !== waitingTicket || state.account?.id !== expected || contextEpoch !== epoch || state.busy || state.revalidating) return false;
        const needsEntries = refresh || state.entries.status !== 'ready', operation = begin();
        let entriesReady = !needsEntries;
        publish({ busy: true, notifications: { ...emptyNotifications(), status: 'loading' }, ...(needsEntries ? { entries: { status: 'loading', items: [], error: null }, entryError: null } : {}) });
        try {
          const proof = await preflight(operation, state.account);
          if (needsEntries) {
            const data = await request(READS.entries, operation, { headers: { 'X-CSRF-Token': proof }, expectedStatus: 200 });
            if (!Array.isArray(data.items) || data.items.length > 1000) throw new AccountRequestError('invalid_response');
            if (!isCurrent(contextFor(operation))) throw stopped();
            publish({ entries: { status: 'ready', items: data.items, error: null } });
            entriesReady = true;
          }
          const page = await notificationHead(operation, proof);
          if (!isCurrent(contextFor(operation))) throw stopped();
          publish({ notifications: { ...page, status: 'ready', error: null, message: null } });
          return true;
        } catch (error) {
          if (current(operation)) {
            if (error.status === 401) showAccount(null);
            else publish({ notifications: { ...emptyNotifications(), status: 'error', error: { code: error.code || 'network', status: error.status || 0 } }, ...(!entriesReady ? { entries: { status: 'error', items: [], error: { code: error.code || 'network', status: error.status || 0 } } } : {}) });
          }
          failure(error, operation);
          return false;
        } finally { settle(operation); }
      }).finally(() => { if (seasonTask === task) seasonTask = null; });
      seasonTask = task;
      return task;
    },
    loadNotifications({ more = false } = {}) {
      if (notificationTask) return notificationTask;
      if (!state.account || state.status !== 'member' || state.busy || state.revalidating || listTask) return Promise.resolve(false);
      if (more && (!state.notifications.hasMore || !state.notifications.nextCursor)) return Promise.resolve(false);
      const previous = state.notifications, expected = state.account, operation = begin();
      const task = (async () => {
        publish({ busy: true, notifications: { ...previous, status: 'loading', unreadCount: null, error: null, message: null } });
        try {
          const proof = await preflight(operation, expected);
          const page = await notificationHead(operation, proof, more ? previous.nextCursor : null);
          const items = new Map((more ? previous.items : []).map(item => [notificationKey(item), item]));
          page.items.forEach(item => items.set(notificationKey(item), item));
          if (!isCurrent(contextFor(operation))) throw stopped();
          publish({ notifications: { ...page, items: [...items.values()], status: 'ready', error: null, message: null } });
          return true;
        } catch (error) {
          if (current(operation)) {
            if (error.status === 401) showAccount(null);
            else publish({ notifications: { ...previous, status: 'error', unreadCount: null, error: { code: error.code || 'network', status: error.status || 0 } } });
          }
          failure(error, operation);
          return false;
        } finally { settle(operation); }
      })().finally(() => { if (notificationTask === task) notificationTask = null; });
      notificationTask = task;
      return task;
    },
    async markNotificationsRead() {
      if (!state.account || state.status !== 'member' || state.busy || state.revalidating || state.notifications.status !== 'ready' || !state.notifications.unreadCount) return false;
      const expected = state.account, operation = begin();
      let acknowledged = false;
      publish({ busy: true, notifications: { ...emptyNotifications(), status: 'loading' } });
      try {
        const proof = await preflight(operation, expected);
        await request(NOTIFICATION_ACK, operation, { method: 'POST', body: {}, headers: { 'X-CSRF-Token': proof }, expectedStatus: 204 });
        acknowledged = true;
        const page = await notificationHead(operation, proof);
        if (!isCurrent(contextFor(operation))) throw stopped();
        publish({ notifications: { ...page, status: 'ready', error: null, message: 'Lecture enregistrée. Les nouvelles notifications restent à lire.' } });
        return true;
      } catch (error) {
        if (current(operation)) {
          if (error.status === 401) showAccount(null);
          else publish({ notifications: { ...emptyNotifications(), status: 'error', error: { code: error.code || 'network', status: error.status || 0 }, message: acknowledged ? 'Lecture enregistrée. Actualisez pour vérifier les nouveautés.' : null } });
        }
        failure(error, operation);
        return false;
      } finally { settle(operation); }
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
        await request(READS.entries + '/' + opaqueSegment(entryId), operation, { method: 'DELETE', body: {}, headers: { 'X-CSRF-Token': csrf }, expectedStatus: 204 });
        assertCurrent(operation);
        publish({ notifications: { ...emptyNotifications(), items: state.notifications.items.filter(item => item.scope_id !== saved.scope_id) } });
        return items.filter(item => item.id !== entryId);
      });
    },
  };
  return api;
}
