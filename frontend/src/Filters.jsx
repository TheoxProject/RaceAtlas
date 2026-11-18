import { useId, useRef, useState } from 'react';
import { changePeriod, DEPARTMENTS, MONTHS, SPORTS, TYPES, weeksInYear } from './catalog.js';
import './discipline-picker.css';

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

function DisciplinePicker({ value, onChange }) {
  const [expanded, setExpanded] = useState(false);
  const button = useRef(null);
  const choicesId = useId();
  const summaryId = useId();
  const { disciplines, types } = value;
  const selectedNames = Object.entries(SPORTS)
    .filter(([code]) => disciplines.includes(code))
    .map(([, label]) => label);
  const summary = [
    selectedNames.join(', ') || 'Toutes les disciplines',
    ...types.map(code => TYPES[code][1]),
  ].join(' · ');
  const typesNarrowOtherSports = types.length > 0 && disciplines.some(
    discipline => !types.some(code => TYPES[code][0] === discipline),
  );

  function toggleDiscipline(code) {
    const checked = disciplines.includes(code);
    const next = checked ? disciplines.filter(discipline => discipline !== code) : [...disciplines, code];
    onChange({ disciplines: next, types: types.filter(type => next.includes(TYPES[type][0])) });
  }

  function closeOnEscape(event) {
    if (expanded && event.key === 'Escape') {
      event.stopPropagation();
      setExpanded(false);
      button.current.focus();
    }
  }

  return <div className="discipline-picker" onKeyDown={closeOnEscape}>
    <button ref={button} type="button" className="discipline-trigger" aria-label="Discipline" aria-describedby={summaryId} aria-expanded={expanded} aria-controls={choicesId} onClick={() => setExpanded(!expanded)}>
      <span><strong>Discipline</strong><small id={summaryId}>{summary}</small></span>
      <span className="discipline-chevron" aria-hidden="true" />
    </button>
    <div id={choicesId} className="discipline-choices" hidden={!expanded}>
      <fieldset aria-label="Disciplines">
        {Object.entries(SPORTS).map(([code, label]) => <label key={code} className="discipline-option">
          <input type="checkbox" checked={disciplines.includes(code)} onChange={() => toggleDiscipline(code)} />
          {label}
        </label>)}
      </fieldset>
      {Object.entries(SPORTS).filter(([code]) => disciplines.includes(code)).map(([sport, label]) => {
        const sportTypes = Object.entries(TYPES).filter(([, [discipline]]) => discipline === sport);
        if (!sportTypes.length) return null;
        return <fieldset key={sport} className="discipline-types">
          <legend>Types d’épreuve · {label}</legend>
          {sportTypes.map(([code, [, name]]) => <label key={code} className="discipline-option">
            <input type="checkbox" checked={types.includes(code)} onChange={() => onChange({
              types: types.includes(code) ? types.filter(type => type !== code) : [...types, code],
            })} />
            {name}
          </label>)}
        </fieldset>;
      })}
      {typesNarrowOtherSports && <p className="hint discipline-type-hint" role="status">Seules les courses correspondant à un type coché apparaissent.</p>}
    </div>
  </div>;
}

export function Filters({ value, onChange, options, optionsError, retryOptions, chooseCenter, setChooseCenter, center }) {
  const set = patch => onChange({ ...value, ...patch });
  const toggle = (key, item) => set({ [key]: value[key].includes(item) ? value[key].filter(code => code !== item) : [...value[key], item] });
  const geography = value.geography;
  return <>
    <label className="search-label"><span>Rechercher une course</span><input type="search" placeholder="Course, commune ou club…" value={value.query} onChange={event => set({ query: event.target.value })} maxLength={200} /></label>
    <DisciplinePicker value={value} onChange={set} />
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
