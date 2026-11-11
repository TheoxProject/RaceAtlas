import { changePeriod, DEPARTMENTS, MONTHS, SPORTS, TYPES, weeksInYear } from './catalog.js';

export function PeriodControls({ period, setPeriod }) {
  const change = patch => setPeriod(value => changePeriod(value, patch));
  const weekMode = period.mode === 'week', year = weekMode ? period.isoYear ?? period.year : period.year;
  const commitYear = event => {
    const value = Number(event.target.value);
    if (Number.isInteger(value) && value >= 1900 && value <= 2200) change(weekMode ? { isoYear: value } : { year: value });
    else event.target.value = year;
  };
  const commitWeek = event => {
    const value = Number(event.target.value);
    if (Number.isInteger(value) && value >= 1) {
      const week = Math.min(value, weeksInYear(year));
      event.target.value = week;
      change({ week });
    }
    else event.target.value = period.week;
  };
  return <section className="period-controls" aria-label="Période des courses">
    <div className="segmented">{[['year', 'Année'], ['month', 'Mois'], ['week', 'Semaine ISO']].map(([value, label]) => <button key={value} aria-pressed={period.mode === value} onClick={() => change({ mode: value })}>{label}</button>)}</div>
    <label>{weekMode ? 'Année ISO' : 'Année'}<input key={`${period.mode}-${year}`} aria-label={weekMode ? 'Année ISO' : 'Année civile'} type="number" min="1900" max="2200" step="1" defaultValue={year} onBlur={commitYear} onKeyDown={event => { if (event.key === 'Enter') event.currentTarget.blur(); }} /></label>
    {period.mode === 'month' && <label>Mois<select aria-label="Mois" value={period.month} onChange={event => change({ month: Number(event.target.value) })}>{MONTHS.map((name, index) => <option key={name} value={index + 1}>{name}</option>)}</select></label>}
    {weekMode && <label>Semaine ISO<input key={`${year}-${period.week}`} type="number" min="1" max={weeksInYear(year)} step="1" defaultValue={period.week} onBlur={commitWeek} onKeyDown={event => { if (event.key === 'Enter') event.currentTarget.blur(); }} /></label>}
  </section>;
}

export function Filters({ value, onChange, options, optionsError, retryOptions, chooseCenter, setChooseCenter, center }) {
  const set = patch => onChange({ ...value, ...patch });
  const toggle = (key, item) => set({ [key]: value[key].includes(item) ? value[key].filter(code => code !== item) : [...value[key], item] });
  const geography = value.geography;
  return <>
    <label className="search-label"><span>Rechercher une course</span><input type="search" placeholder="Course, commune ou club…" value={value.query} onChange={event => set({ query: event.target.value })} maxLength={200} /></label>
    <fieldset><legend>Votre discipline</legend><div className="check-grid">{Object.entries(SPORTS).map(([code, name]) => <label key={code}><input type="checkbox" checked={value.disciplines.includes(code)} onChange={() => {
      const disciplines = value.disciplines.includes(code) ? value.disciplines.filter(item => item !== code) : [...value.disciplines, code];
      set({ disciplines, types: value.types.filter(item => !disciplines.length || disciplines.includes(TYPES[item][0])) });
    }} />{name}</label>)}</div></fieldset>
    <details><summary>Type d’épreuve</summary><div className="check-grid">{Object.entries(TYPES).filter(([, [sport]]) => !value.disciplines.length || value.disciplines.includes(sport)).map(([code, [, name]]) => <label key={code}><input type="checkbox" checked={value.types.includes(code)} onChange={() => toggle('types', code)} />{name}</label>)}</div></details>
    <fieldset><legend>Catégories acceptées</legend>
      <div className="segmented category-mode">{[['or', 'Au moins une'], ['and', 'Toutes ensemble']].map(([code, name]) => <button key={code} aria-pressed={value.category_operator === code} onClick={() => set({ category_operator: code })}>{name}</button>)}</div>
      <p className="hint">« Toutes » doit correspondre à une même liste d’engagement.</p>
      {optionsError ? <div role="alert"><p>Catégories indisponibles.</p><button onClick={retryOptions}>Réessayer les catégories</button></div> : options ? <div className="check-grid categories">{options.categories.length ? options.categories.map(category => <label key={category.code}><input type="checkbox" checked={value.categories.includes(category.code)} onChange={() => toggle('categories', category.code)} />{category.label}</label>) : <p className="hint">Aucune catégorie renseignée.</p>}</div> : <p className="hint">Chargement des catégories…</p>}
    </fieldset>
    <fieldset><legend>Où rouler ?</legend><label>Zone<select aria-label="Zone" value={geography.mode} onChange={event => {
      const mode = event.target.value;
      if (mode === 'radius' && !center) { setChooseCenter(true); return; }
      setChooseCenter(false);
      set({ geography: mode === 'all' ? { mode } : mode === 'departments' ? { mode, departments: ['26'] } : { mode, center, radius_km: 50 } });
    }}><option value="all">Toute la région</option><option value="departments">Par département</option><option value="radius">Autour d’un point</option></select></label>
      {geography.mode === 'departments' && <div className="check-grid">{Object.entries(DEPARTMENTS).map(([code, name]) => <label key={code}><input type="checkbox" checked={geography.departments.includes(code)} onChange={() => {
        const departments = geography.departments.includes(code) ? geography.departments.filter(item => item !== code) : [...geography.departments, code];
        set({ geography: departments.length ? { mode: 'departments', departments } : { mode: 'all' } });
      }} />{code} · {name}</label>)}</div>}
      {(geography.mode === 'radius' || chooseCenter) && <>
        <button className="outline" onClick={() => setChooseCenter(!chooseCenter)}>{chooseCenter ? 'Annuler le choix du point' : 'Changer le point sur la carte'}</button>
        {chooseCenter && <p role="status" className="hint">Choisissez votre point sur la carte ou saisissez ses coordonnées.</p>}
        <form className="coordinate-form" onSubmit={event => {
          event.preventDefault(); const data = new FormData(event.currentTarget);
          const point = [Number(data.get('longitude')), Number(data.get('latitude'))];
          set({ geography: { mode: 'radius', center: point, radius_km: geography.radius_km || 50 } }); setChooseCenter(false);
        }}><label>Longitude<input name="longitude" type="number" step="any" min="-180" max="180" required defaultValue={center?.[0] ?? ''} /></label><label>Latitude<input name="latitude" type="number" step="any" min="-90" max="90" required defaultValue={center?.[1] ?? ''} /></label><button type="submit">Choisir ce point</button></form>
        {geography.mode === 'radius' && <label>Rayon : {geography.radius_km} km<input aria-label="Rayon en kilomètres" type="range" min="1" max="500" value={geography.radius_km} onChange={event => set({ geography: { ...geography, radius_km: Number(event.target.value) } })} /></label>}
        <p className="hint">Distance aux centres des communes, pas aux départs des courses.</p>
      </>}
    </fieldset>
  </>;
}
