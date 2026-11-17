import { notificationChanges, notificationKey, observedDate, sourceLink } from './notifications.js';
import { seasonError } from './season.js';

export function NotificationsPanel({ account, controller }) {
  const data = account.notifications;
  if (!data) return null;
  const loading = ['idle', 'loading'].includes(data.status);
  return <section className="notifications-panel" aria-labelledby="notifications-title" aria-busy={loading}>
    <h3 id="notifications-title">Changements récents</h3>
    <p role="status">{data.unreadCount === null ? 'Compteur à actualiser' : `${data.unreadCount} nouveauté${data.unreadCount !== 1 ? 's' : ''}`}</p>
    <p className="hint">Toutes vos listes sauvegardées sont suivies, sans les filtres publics. Une absence à la source n’est pas une annulation.</p>
    {loading && <p role="status">Chargement des changements…</p>}
    {data.message && <p role="status">{data.message}</p>}
    {data.error && <p role="alert">{seasonError(data.error)}</p>}
    <div className="notification-actions">
      <button disabled={account.busy || account.revalidating} onClick={() => controller.loadNotifications()}>Actualiser les changements</button>
      <button disabled={account.busy || account.revalidating || data.status !== 'ready' || !data.unreadCount} onClick={() => controller.markNotificationsRead()}>Marquer comme lues</button>
    </div>
    <p className="hint">Cette action concerne toutes les notifications disponibles, y compris celles non affichées.</p>
    {data.status === 'ready' && !data.items.length && <p>Aucun changement disponible pour vos listes.</p>}
    {data.items.map(item => {
      const url = sourceLink(item.provenance.source_url);
      return <article className="notification-card" key={notificationKey(item)}>
        <p className={item.read_at ? 'notification-read' : 'notification-unread'}>{item.read_at ? 'Lue' : 'Non lue'}</p>
        <h4>{item.entry.race.name}</h4><p>{item.entry.scope.raw_label || 'Liste à préciser'}</p>
        <p className="hint">Constaté le {observedDate(item.created_at)}</p>
        <dl>{notificationChanges(item.delta).map(change => <div key={change.label}><dt>{change.label}</dt><dd>{change.text || <><span>Avant : {change.before}</span><span>Après : {change.after}</span></>}</dd></div>)}</dl>
        <p className="hint">Les conditions publiées ne déterminent pas votre admissibilité personnelle.</p>
        <p className="hint">Source vérifiée le {observedDate(item.provenance.checked_at)}.</p>
        {url && <a href={url} target="_blank" rel="noreferrer">Consulter la source ↗</a>}
      </article>;
    })}
    {data.hasMore && <button disabled={account.busy || account.revalidating} onClick={() => controller.loadNotifications({ more: true })}>Charger la suite</button>}
    {data.items.length > 0 && <p className="hint">Les pages reflètent les informations disponibles à leur lecture. Actualisez pour retrouver les nouveautés.</p>}
  </section>;
}
