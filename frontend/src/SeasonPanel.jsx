import { useEffect, useState } from 'react';
import { RaceDetails, formatDate } from './RaceDetails.jsx';
import { SAVED_LABELS, seasonError } from './season.js';

export function SeasonPanel({ account, controller }) {
  const [selection, setSelection] = useState(null);
  useEffect(() => {
    if (account.status === 'member' && !account.revalidating && !account.busy && account.entries.status === 'idle') controller.loadEntries();
  }, [account.status, account.revalidating, account.busy, account.entries.status, controller]);
  if (account.status !== 'member' || account.revalidating || ['idle', 'loading'].includes(account.entries.status)) return <p role="status">Chargement de votre saison…</p>;
  if (account.entries.status === 'error') return <div><p role="alert">{seasonError(account.entries.error)}</p><button disabled={account.busy} onClick={() => controller.loadEntries()}>Actualiser ma saison</button></div>;
  const items = account.entries.items;
  const selected = selection?.epoch === account.contextEpoch ? items.find(item => item.id === selection.id) : null;
  if (selected) return <div className="season-detail"><RaceDetails item={selected} privateScope={selected.scope} labels={{}} showMatches={false} account={account} controller={controller} onBack={() => setSelection(null)} /></div>;
  return <section className="season-panel" aria-label="Vos sauvegardes">
    <p>Toutes vos sauvegardes, sans les filtres de la carte ou du calendrier.</p>
    <p role="status">{items.length} sauvegarde{items.length !== 1 && 's'}</p>
    {!items.length && <p>Votre saison est vide. Choisissez une liste dans les détails d’une course pour la sauvegarder.</p>}
    {items.map(item => <button className="season-row" key={item.id} onClick={() => setSelection({ id: item.id, epoch: account.contextEpoch })}><strong>{item.race.name}</strong><span>{item.scope.raw_label}</span><span>{SAVED_LABELS[item.status]} · {formatDate(item.race.start_date)}</span></button>)}
    <p className="hint">« Inscrit » est déclaré par vous, non vérifié par la FFC. Votre admissibilité personnelle n’est pas évaluée.</p>
    <button className="text-button" disabled={account.busy} onClick={() => controller.loadEntries()}>Actualiser ma saison</button>
  </section>;
}
