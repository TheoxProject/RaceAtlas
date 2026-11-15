import { useEffect, useId, useRef, useState } from 'react';
import { newPasswordError } from './accountBootstrap.js';

const LABELS = { logoutAll: 'Déconnecter tous les appareils', changePassword: 'Changer le mot de passe', deleteAccount: 'Supprimer mon compte' };
export function securityError(error) {
  if (error?.code === 'reauthentication_failed') return 'Le mot de passe actuel est incorrect. Votre compte reste connecté.';
  if (error?.code === 'invalid_password') return 'Choisissez un nouveau mot de passe conforme et moins courant.';
  if (error?.code === 'context_changed') return 'Le compte actif a changé. Vérifiez le compte avant une nouvelle action.';
  if (error?.status === 401) return 'Votre connexion n’est plus active. Vérifiez le compte.';
  if (error?.status === 403) return 'La demande a été refusée. Actualisez le compte avant de recommencer.';
  if (error?.status === 429) return 'Trop de demandes. Patientez avant un nouvel essai explicite.';
  return 'Le résultat de cette opération n’est pas confirmé. Elle peut avoir déjà été traitée. Vérifiez le compte ; aucun nouvel essai automatique n’est effectué.';
}
function SecurityForm({ action, account, controller, onBack }) {
  const id = useId(), first = useRef(null), checkbox = useRef(null);
  const [current, setCurrent] = useState(''), [password, setPassword] = useState(''), [repeat, setRepeat] = useState(''), [confirmed, setConfirmed] = useState(false), [error, setError] = useState(null);
  useEffect(() => { first.current?.focus(); }, []);
  async function submit(event) {
    event.preventDefault(); controller.clearFeedback();
    let message = !current ? 'Indiquez votre mot de passe actuel.' : null;
    if (!message && action === 'changePassword') message = newPasswordError(password) || (password !== repeat ? 'Les deux nouveaux mots de passe doivent être identiques, espaces compris.' : null);
    if (!message && action === 'deleteAccount' && !confirmed) message = 'Confirmez explicitement la suppression de votre compte.';
    setError(message);
    if (message) { if (action === 'deleteAccount' && current && !confirmed) checkbox.current?.focus(); else first.current?.focus(); return; }
    const expected = account.account.id;
    try { await controller.sensitive(action, { current_password: current, ...(action === 'changePassword' ? { new_password: password } : {}) }); }
    finally {
      setCurrent(''); setPassword(''); setRepeat(''); setConfirmed(false);
      const state = controller.getSnapshot();
      if (state.account?.id === expected && state.error?.code === 'reauthentication_failed') first.current?.focus();
    }
  }
  return <form className="account-form" noValidate onSubmit={submit} aria-busy={account.busy}>
    <h3>{LABELS[action]}</h3>
    {action === 'logoutAll' && <p>Toutes vos sessions seront révoquées. Vous devrez vous reconnecter.</p>}
    {action === 'deleteAccount' && <p>Cette action supprime votre compte et ses sauvegardes personnelles. Les données publiques des courses ne sont pas supprimées.</p>}
    <label htmlFor={`${id}-current`}>Mot de passe actuel<input ref={first} id={`${id}-current`} type="password" autoComplete="current-password" value={current} onChange={event => setCurrent(event.target.value)} aria-describedby={`${id}-validation`} required /></label>
    {action === 'changePassword' && <><label htmlFor={`${id}-new`}>Nouveau mot de passe<input id={`${id}-new`} type="password" autoComplete="new-password" value={password} onChange={event => setPassword(event.target.value)} aria-describedby={`${id}-policy ${id}-validation`} required /></label><p id={`${id}-policy`} className="hint">15 à 128 caractères Unicode, au plus 512 octets UTF-8. Les espaces sont conservés.</p><label htmlFor={`${id}-repeat`}>Confirmer le nouveau mot de passe<input id={`${id}-repeat`} type="password" autoComplete="new-password" value={repeat} onChange={event => setRepeat(event.target.value)} required /></label></>}
    {action === 'deleteAccount' && <label className="security-confirm"><input ref={checkbox} type="checkbox" checked={confirmed} onChange={event => setConfirmed(event.target.checked)} />Je confirme la suppression de mon compte et de mes sauvegardes.</label>}
    <p id={`${id}-validation`} className="account-error" role={error ? 'alert' : undefined}>{error}</p>
    {account.error && <p className="account-error" role="alert">{securityError(account.error)}</p>}
    <button type="submit" className={action === 'deleteAccount' ? 'account-danger' : 'account-primary'} disabled={account.busy || account.revalidating}>{account.busy ? 'Demande en cours…' : LABELS[action]}</button>
    <button type="button" className="text-button" disabled={account.busy} onClick={onBack}>Retour à la sécurité</button>
  </form>;
}
export function AccountSecurityPanel({ account, controller }) {
  const [action, setAction] = useState(null);
  const navigate = value => { controller.clearFeedback(); setAction(value); };
  if (action) return <SecurityForm key={action} action={action} account={account} controller={controller} onBack={() => navigate(null)} />;
  return <section className="security-actions" aria-label="Sécurité du compte">
    <p>Les actions ci-dessous concernent le compte affiché. Les opérations sensibles demandent votre mot de passe actuel.</p>
    {account.error && <p role="alert" className="account-error">{securityError(account.error)}</p>}
    <button disabled={account.busy || account.revalidating} onClick={() => controller.sensitive('logout')}>Se déconnecter</button>
    {Object.entries(LABELS).map(([value, label]) => <button key={value} className={value === 'deleteAccount' ? 'account-danger' : ''} disabled={account.busy || account.revalidating} onClick={() => navigate(value)}>{label}</button>)}
    {account.error && <button className="text-button" disabled={account.busy} onClick={() => controller.refresh()}>Vérifier le compte</button>}
  </section>;
}
