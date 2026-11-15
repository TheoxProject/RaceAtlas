import { ScopeSaveActions } from './ScopeSaveActions.jsx';
import { SPORTS, TYPES } from './catalog.js';

export function formatDate(value) { return new Date(`${value}T12:00:00Z`).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'Europe/Paris' }); }
function Rule({ rule, labels }) {
  const restriction = rule.restrictions;
  return <div className="eligibility-rule"><strong>{rule.category_codes.map(code => labels[code] || code.replaceAll('_', ' ')).join(' · ') || 'Catégories non précisées'}</strong>
    <p>{rule.raw_label}</p><ul>
      {restriction.sex !== 'any' && <li>{({ men: 'Hommes', women: 'Femmes', unknown: 'Sexe non précisé' })[restriction.sex]}</li>}
      {(restriction.min_age != null || restriction.max_age != null) && <li>Âge : {restriction.min_age ?? 'non précisé'} à {restriction.max_age ?? 'non précisé'} ans{restriction.age_reference === 'season_end' ? ` en fin de saison ${restriction.age_season ?? ''}` : restriction.age_reference === 'event_date' ? ' le jour de la course' : ' · référence à vérifier'}</li>}
      {restriction.engagers.length > 0 && <li>Engagement : {restriction.engagers.join(', ')}</li>}
      {restriction.other_text && <li>{restriction.other_text}</li>}
    </ul></div>;
}
export function RaceDetails({ item, labels, showMatches, candidate, onBack, privateScope = null, account, controller, onConnect }) {
  const race = item.race;
  return <article className="race-detail">
    <button className="text-button" onClick={onBack}>← Retour aux courses</button>
    <p className="eyebrow">{SPORTS[race.discipline]} · {race.location?.commune_name || 'Commune à préciser'}</p>
    <h2>{race.name}</h2>
    <p className="date-line">{formatDate(race.start_date)}{race.end_date !== race.start_date && ` → ${formatDate(race.end_date)}`}</p>
    {race.status === 'cancelled' && <p className="notice danger">Course annulée selon la source.</p>}
    {race.status === 'postponed' && <p className="notice">Course reportée selon la source.</p>}
    {(race.source_presence !== 'present' || race.status === 'unknown') && <p className="notice">Fiche à vérifier auprès de l’organisateur. Une absence à la source ne signifie pas une annulation.</p>}
    {candidate && <p className="notice">Localisation à confirmer : cette course n’est pas comptée dans les résultats du rayon.</p>}
    <dl className="race-facts"><div><dt>Type</dt><dd>{race.types.map(code => TYPES[code]?.[1]).join(', ') || 'Non précisé'}</dd></div><div><dt>Organisateur</dt><dd>{race.organizer || 'Non précisé'}</dd></div><div><dt>Département</dt><dd>{race.department}</dd></div><div><dt>Localisation</dt><dd>{race.location?.coordinates ? 'Centre de commune uniquement' : 'Centre de commune non disponible'}</dd></div></dl>
    <h3>Listes d’engagement</h3><p className="hint">Consultez chaque liste et ses restrictions. Votre admissibilité personnelle n’est pas évaluée.</p>
    {(privateScope ? [privateScope] : race.entry_scopes).map((scope, index) => <section className="scope" key={scope.id}>
      <h4>{scope.raw_label || `Liste ${index + 1}`}</h4>
      {showMatches && item.matching_scope_ids.includes(scope.id) && <p className="match-label">Correspond aux catégories sélectionnées</p>}
      {scope.eligibility_status !== 'confirmed' && <p className="notice">Catégories {scope.eligibility_status === 'ambiguous' ? 'ambiguës' : 'non confirmées'} : vérifiez les conditions.</p>}
      {scope.identity_status !== 'verified' && <p className="hint">Identité de cette liste à vérifier.</p>}
      {scope.rules.map(rule => <Rule key={rule.id} rule={rule} labels={labels} />)}
      {account && controller && <ScopeSaveActions scopeId={scope.id} account={account} controller={controller} onConnect={onConnect} />}
    </section>)}
    <section className="source-note"><h3>Source et fraîcheur</h3><p>{race.source.provider === 'synthetic' ? 'Donnée synthétique de démonstration' : 'Fédération Française de Cyclisme'} · saison source {race.source.source_season}</p><p>Fiche consultée le {formatDate(race.source.checked_at.slice(0, 10))}. Les conditions peuvent évoluer.</p>{race.source.provider !== 'synthetic' && <a href={race.source.source_url} target="_blank" rel="noreferrer">Consulter la source ↗</a>}</section>
  </article>;
}
