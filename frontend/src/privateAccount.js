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
  let state = { status: 'unknown', account: null, busy: false, error: null, message: null };
  let generation = 0;
  const listeners = new Set(), pending = new Set();
  const publish = patch => { state = { ...state, ...patch }; listeners.forEach(listener => listener()); };
  const invalidate = () => { generation += 1; pending.forEach(controller => controller.abort()); pending.clear(); return generation; };
  const current = ticket => ticket === generation;
  const begin = () => { const ticket = invalidate(), controller = new AbortController(); pending.add(controller); return { ticket, controller }; };
  const assertCurrent = operation => { if (!current(operation.ticket) || operation.controller.signal.aborted) throw stopped(); };
  async function request(path, operation, { method = 'GET', body, headers = {}, binary = false } = {}) {
    if (!ROUTES.has(path)) throw new AccountRequestError('invalid_request');
    const response = await fetcher(path, {
      method, credentials: 'same-origin', cache: 'no-store', redirect: 'error', referrerPolicy: 'no-referrer', mode: 'same-origin',
      signal: operation.controller.signal, headers: { ...headers, ...(body === undefined ? {} : { 'Content-Type': 'application/json' }) },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
    assertCurrent(operation);
    if (!response.ok) {
      let code = 'unavailable';
      try { code = (await response.json()).code || code; } catch { /* never expose response text */ }
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
  function showAccount(account, patch = {}) { publish({ account, status: account ? 'member' : 'anonymous', ...patch }); }
  function failure(error, operation, patch = {}) {
    if (!current(operation.ticket) || error.name === 'AbortError') return;
    publish({ busy: false, error: { code: error.code || 'network', status: error.status || 0 }, ...patch });
  }
  async function preflight(operation, expected) {
    const { csrf_token: proof } = await request(AUTH + 'csrf', operation);
    const actual = await me(operation, proof);
    if ((actual?.id || null) !== (expected?.id || null)) {
      showAccount(actual, { message: null });
      throw new AccountRequestError('context_changed');
    }
    return proof;
  }
  return {
    getSnapshot: () => state,
    subscribe: listener => { listeners.add(listener); return () => listeners.delete(listener); },
    cancel() { invalidate(); publish({ busy: false }); },
    clearFeedback() { publish({ error: null, message: null }); },
    async refresh() {
      if (state.busy) return;
      const operation = begin();
      try { const account = await me(operation); assertCurrent(operation); showAccount(account, { error: null, ...((account?.id || null) !== (state.account?.id || null) ? { message: null } : {}) }); }
      catch (error) { failure(error, operation, { status: 'unavailable', account: null }); }
      finally { pending.delete(operation.controller); }
    },
    async submit(action, fields = {}, proof) {
      if (!Object.hasOwn(ACTIONS, action) || state.busy) return false;
      const expected = state.account, operation = begin();
      publish({ busy: true, error: null, message: null });
      try {
        const csrf = await preflight(operation, expected);
        await request(AUTH + ACTIONS[action], operation, { method: 'POST', body: fields, headers: { 'X-CSRF-Token': csrf, ...(proof ? { 'X-Account-Proof': proof } : {}) } });
        const account = await me(operation);
        assertCurrent(operation);
        const message = action === 'confirm' ? 'Adresse confirmée. Vous pouvez maintenant vous connecter.' : action === 'reset' ? 'Mot de passe réinitialisé. Cette action ne vous connecte pas automatiquement.' : action === 'login' ? 'Connexion réussie.' : ACCEPTED;
        showAccount(account, { busy: false, message, error: null });
        return true;
      } catch (error) { failure(error, operation); return false; }
      finally { pending.delete(operation.controller); }
    },
    async readPrivate(kind) {
      const expected = state.account;
      if (!expected || !Object.hasOwn(READS, kind)) throw new AccountRequestError('authentication_failed', 401);
      const operation = begin();
      try {
        const csrf = await preflight(operation, expected);
        const result = await request(READS[kind], operation, { headers: { 'X-CSRF-Token': csrf }, binary: kind === 'calendar' });
        return result;
      } catch (error) {
        if (current(operation.ticket) && error.status === 401) showAccount(null);
        failure(error, operation);
        throw error;
      } finally { pending.delete(operation.controller); }
    },
  };
}
