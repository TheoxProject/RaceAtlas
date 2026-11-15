import { useEffect, useId, useState } from 'react';
import { SAVED_LABELS, seasonError } from './season.js';

export function ScopeSaveActions({ scopeId, account, controller, onConnect }) {
  const id = useId(), [draft, setDraft] = useState({ epoch: -1, value: 'interested' });
  useEffect(() => {
    if (account.status === 'member' && !account.revalidating && !account.busy && account.entries.status === 'idle') controller.loadEntries();
  }, [account.status, account.revalidating, account.busy, account.entries.status, controller]);
  if (!account.account || account.status !== 'member') return <div className="scope-save"><button className="text-button" disabled={account.status === 'unknown'} onClick={onConnect}>{account.status === 'unavailable' ? 'Vérifier le compte pour sauvegarder' : 'Se connecter pour sauvegarder cette liste'}</button></div>;
  if (account.revalidating || ['idle', 'loading'].includes(account.entries.status)) return <p className="hint" role="status">Vérification de votre saison…</p>;
  if (account.entries.status === 'error') return <div className="scope-save"><p role="alert">{seasonError(account.entries.error)}</p><button disabled={account.busy} onClick={() => controller.loadEntries()}>Actualiser ma saison</button></div>;
  const saved = account.entries.items.find(item => item.scope_id === scopeId);
  const status = saved?.status || (draft.epoch === account.contextEpoch ? draft.value : 'interested');
  const error = account.entryError?.scopeId === scopeId ? account.entryError : null;
  return <div className="scope-save" data-scope-id={scopeId}>
    <label htmlFor={id}>Votre statut pour cette liste<select id={id} value={status} disabled={account.busy} onChange={event => saved ? controller.saveScope(scopeId, event.target.value) : setDraft({ epoch: account.contextEpoch, value: event.target.value })}>{Object.entries(SAVED_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
    <p className="hint">« Inscrit » est votre déclaration, non vérifiée par la FFC.</p>
    {saved ? <><p className="scope-saved" role="status">Sauvegardée : {SAVED_LABELS[saved.status]}</p><button className="text-button" disabled={account.busy} onClick={() => controller.removeEntry(saved.id)}>Retirer cette sauvegarde</button></> : <button disabled={account.busy} onClick={() => controller.saveScope(scopeId, status)}>Sauvegarder cette liste</button>}
    {account.busy && <p role="status" className="hint">Demande en cours…</p>}
    {error && <p className="account-error" role="alert">{seasonError(error)}</p>}
  </div>;
}
