import { useEffect, useMemo, useState } from 'react';
import { getJson, groupCommunes, initialFilters, initialPeriod, loadSelection, periodRange, SPORTS } from './catalog.js';
import { Filters, PeriodControls } from './Filters.jsx';
import { MapView } from './MapView.jsx';
import { formatDate, RaceDetails } from './RaceDetails.jsx';

export function App() {
  const [period, setPeriod] = useState(initialPeriod), [filters, setFilters] = useState(initialFilters);
  const [mode, setMode] = useState('altitude'), [attempt, setAttempt] = useState(0);
  const [terrainFailed, setTerrainFailed] = useState(false);
  const [state, setState] = useState({ status: 'loading' }), [options, setOptions] = useState(null), [optionsError, setOptionsError] = useState(false);
  const [optionsAttempt, setOptionsAttempt] = useState(0), [filtersOpen, setFiltersOpen] = useState(false), [explore, setExplore] = useState(false);
  const [selected, setSelected] = useState(null), [groupIds, setGroupIds] = useState(null), [chooseCenter, setChooseCenter] = useState(false);
  const filter = useMemo(() => ({ ...filters, ...periodRange(period) }), [filters, period]);
  useEffect(() => {
    const controller = new AbortController();
    getJson('/api/v1/catalog/options', controller.signal).then(value => { if (!controller.signal.aborted) { setOptions(value); setOptionsError(false); } }).catch(error => { if (error.name !== 'AbortError') setOptionsError(true); });
    return () => controller.abort();
  }, [optionsAttempt]);
  useEffect(() => {
    const controller = new AbortController();
    const timeout = setTimeout(() => {
      setState({ status: 'loading' }); setSelected(null); setGroupIds(null);
      loadSelection(filter, controller.signal).then(data => { if (!controller.signal.aborted) setState({ status: 'ready', data }); }).catch(error => { if (!controller.signal.aborted) setState({ status: 'error', changing: error.status === 409 }); });
    }, 180);
    return () => { clearTimeout(timeout); controller.abort(); };
  }, [filter, attempt]);
  const data = state.data;
  const items = data?.items || [], features = data?.features || [];
  const groups = groupCommunes(features);
  const labels = Object.fromEntries((options?.categories || []).map(category => [category.code, category.label]));
  const unlocated = new Set(data?.unlocatedIds || []);
  const selectedItem = items.find(item => item.race.id === selected);
  const visibleItems = groupIds ? items.filter(item => groupIds.includes(item.race.id)) : items;
  const isRadius = filters.geography.mode === 'radius';
  const showGroup = ids => { setGroupIds(ids); setSelected(ids.length === 1 ? ids[0] : null); setExplore(true); };
  const onCenter = point => { setFilters(value => ({ ...value, geography: { mode: 'radius', center: point, radius_km: value.geography.radius_km || 50 } })); setChooseCenter(false); };
  const allSynthetic = items.length > 0 && items.every(item => item.race.source.provider === 'synthetic');
  return <main className="atlas-app">
    <header className="app-header"><a href="/" className="brand" aria-label="RaceAtlas, accueil"><span className="brand-mark">↗</span>Race<span>Atlas</span></a><span className="region-label">AUVERGNE-RHÔNE-ALPES <span>12 départements · un terrain de jeu</span></span><span className="header-tag">Trouvez votre prochaine ligne de départ.</span></header>
    <div className="app-body">
      <aside className={`filters-panel ${filtersOpen ? 'is-open' : ''}`} aria-label="Filtres des courses">
        <div className="panel-heading"><div><p className="eyebrow">À vous de jouer</p><h1>Votre prochaine<br />course commence ici.</h1></div><button className="mobile-only text-button" onClick={() => setFiltersOpen(false)} aria-label="Fermer les filtres">✕</button></div>
        <Filters value={filters} onChange={setFilters} options={options} optionsError={optionsError} retryOptions={() => setOptionsAttempt(value => value + 1)} center={filters.geography.center} chooseCenter={chooseCenter} setChooseCenter={setChooseCenter} />
        <button className="reset-button" onClick={() => { setFilters(initialFilters()); setChooseCenter(false); }}>Réinitialiser les filtres</button>
        <button className="mobile-only apply-filters" onClick={() => setFiltersOpen(false)}>Voir les courses sur la carte</button>
      </aside>
      <section className="map-workspace" aria-label="Explorer les courses">
        <div className="workspace-toolbar"><div className="toolbar-title"><p className="eyebrow">Le cyclisme, grandeur nature</p><h2>Explorez votre saison.</h2></div><PeriodControls period={period} setPeriod={setPeriod} /></div>
        <div className="map-shell">
          <MapView features={features} races={items} mode={mode} setMode={setMode} onReliefError={setTerrainFailed} onSelect={showGroup} chooseCenter={chooseCenter} onCenter={onCenter} />
          <div className="map-topline"><div className="result-count" aria-live="polite">{state.status === 'loading' ? 'Recherche des courses…' : state.status === 'error' ? 'Sélection indisponible' : <><strong>{data.total}</strong> course{data.total !== 1 && 's'} {isRadius ? 'dans le rayon' : 'à explorer'}<span>{groups.length} commune{groups.length !== 1 && 's'} localisée{groups.length !== 1 && 's'}</span></>}</div>
            <div className="terrain-switch" aria-label="Relief de la carte"><button aria-pressed={mode === 'altitude'} onClick={() => setMode('altitude')}>△ Altitude <small>2,5D</small></button><button disabled={terrainFailed} aria-pressed={mode === 'summit'} onClick={() => setMode('summit')}>▲ Summit <small>3D</small></button></div>
          </div>
          <div className="map-actions"><button className="mobile-only" onClick={() => setFiltersOpen(true)}>☷ Filtres</button><button onClick={() => { setExplore(!explore); setGroupIds(null); setSelected(null); }} aria-expanded={explore}>Explorer les communes</button><button className="refresh-button" aria-label="Actualiser les courses" onClick={() => setAttempt(value => value + 1)}>↻</button></div>
          {chooseCenter && <div className="center-instruction" role="status">Cliquez sur la carte pour choisir votre point de recherche.</div>}
          {state.status === 'error' && <div className="map-state" role="alert"><h2>{state.changing ? 'Le catalogue évolue.' : 'Service temporairement indisponible.'}</h2><p>{state.changing ? 'Actualisez la sélection pour retrouver des résultats cohérents.' : 'Vos filtres sont conservés. Réessayez dans quelques instants.'}</p><button onClick={() => setAttempt(value => value + 1)}>Réessayer</button></div>}
          {state.status === 'ready' && data.total === 0 && <div className="empty-state"><h2>Aucune course dans cette sélection</h2><p>Essayez une autre période ou élargissez vos filtres.{data.unlocated_count > 0 && ' Des localisations restent à confirmer.'}</p></div>}
          {explore && <aside className="results-panel" aria-label="Courses et détails"><div className="results-heading"><span>{selectedItem ? 'L’épreuve en détail' : 'Les courses de votre sélection'}</span><button className="text-button" aria-label="Fermer les détails" onClick={() => setExplore(false)}>✕</button></div>
            {selectedItem ? <RaceDetails item={selectedItem} labels={labels} showMatches={filters.categories.length > 0} candidate={isRadius && unlocated.has(selectedItem.race.id)} onBack={() => setSelected(null)} /> : <>
              <p className="hint">Les points représentent des centres de communes, pas les départs des courses.</p>
              {visibleItems.filter(item => !unlocated.has(item.race.id)).map(item => <button key={item.race.id} className="race-row" onClick={() => setSelected(item.race.id)}><span>{SPORTS[item.race.discipline]} · {item.race.location?.commune_name}</span><strong>{item.race.name}</strong><span>{formatDate(item.race.start_date)} <b>↗</b></span></button>)}
              {unlocated.size > 0 && <section className="unlocated-section"><h3>{isRadius ? 'Localisations à confirmer' : 'Courses non localisées'} · {unlocated.size}</h3><p className="hint">{isRadius ? 'Candidates aux autres filtres, exclues du total du rayon.' : 'Ces courses n’ont pas de centre de commune disponible.'}</p>{visibleItems.filter(item => unlocated.has(item.race.id)).map(item => <button key={item.race.id} className="race-row" onClick={() => setSelected(item.race.id)}><span>{SPORTS[item.race.discipline]} · localisation à préciser</span><strong>{item.race.name}</strong><span>{formatDate(item.race.start_date)} <b>↗</b></span></button>)}</section>}
            </>}
          </aside>}
        </div>
        <footer className="workspace-footer"><span><i />{allSynthetic ? 'Données synthétiques · courses fictives' : 'Centres de communes · départs à vérifier'}</span>{data?.unlocated_count > 0 && <button className="text-button" onClick={() => { setGroupIds([...unlocated]); setSelected(null); setExplore(true); }}>{data.unlocated_count} localisation{data.unlocated_count > 1 && 's'} à préciser ↗</button>}<span>{data?.coverage.last_successful_sync_at ? `Dernière synchronisation réussie : ${formatDate(data.coverage.last_successful_sync_at.slice(0, 10))}` : 'Couverture de la source non établie'}</span></footer>
      </section>
    </div>
  </main>;
}
