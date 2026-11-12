import { MONTHS, SPORTS } from './catalog.js';
import { MAX_CALENDAR_YEAR, MIN_CALENDAR_YEAR, moveCalendarMonth, selectCalendarMonth } from './calendar.js';
import './calendar.css';

const WEEKDAYS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];
const dayLabel = date => new Intl.DateTimeFormat('fr-FR', { timeZone: 'UTC', weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(`${date}T12:00:00Z`));

export function Calendar({ period, setPeriod, projection, status, onDay, onRace, onCandidates }) {
  return <section className="calendar-view" aria-label="Calendrier mensuel" aria-busy={status === 'loading'}>
    <div className="calendar-heading"><div><p className="eyebrow">Votre saison, jour après jour</p><h2>{MONTHS[period.month - 1]} {period.year}</h2></div>
      <div className="calendar-navigation"><button aria-label="Mois précédent" disabled={period.year === MIN_CALENDAR_YEAR && period.month === 1} onClick={() => setPeriod(value => moveCalendarMonth(value, -1))}>←</button><button aria-label="Mois suivant" disabled={period.year === MAX_CALENDAR_YEAR && period.month === 12} onClick={() => setPeriod(value => moveCalendarMonth(value, 1))}>→</button></div>
    </div>
    <p className="calendar-summary" role="status">{status === 'loading' ? 'Recherche des courses…' : status === 'error' ? 'Sélection indisponible' : `${projection.total} course${projection.total !== 1 ? 's' : ''} ce mois-ci`}</p>
    <table className="calendar-grid"><caption className="visually-hidden">Courses de {MONTHS[period.month - 1]} {period.year}, du lundi au dimanche</caption><thead><tr>{WEEKDAYS.map(day => <th key={day} scope="col"><abbr title={day}>{day.slice(0, 3)}</abbr></th>)}</tr></thead><tbody>
      {Array.from({ length: projection.days.length / 7 }, (_, week) => <tr key={week}>{projection.days.slice(week * 7, week * 7 + 7).map(day => <td key={day.date} data-date={day.date} className={day.inMonth ? '' : 'outside-month'}>
        <button className="calendar-day" disabled={!day.inMonth || status !== 'ready'} aria-label={`${dayLabel(day.date)} · ${day.items.length} course${day.items.length !== 1 ? 's' : ''}`} onClick={() => onDay(day)}><span>{day.day}</span>{day.items.length > 0 && <small>{day.items.length} course{day.items.length !== 1 && 's'}</small>}</button>
        <div className="calendar-chips">{day.items.slice(0, 2).map(item => <button key={item.race.id} className="calendar-race" data-race-id={item.race.id} title={item.race.name} aria-label={`${item.race.name} · ${SPORTS[item.race.discipline]} · ${dayLabel(day.date)}`} onClick={() => onRace(item, day)}>{item.race.name}</button>)}</div>
      </td>)}</tr>)}
    </tbody></table>
    {status === 'ready' && projection.candidates.length > 0 && <div className="calendar-candidates"><p>Localisations à confirmer : {projection.candidates.length} candidate{projection.candidates.length !== 1 && 's'}, exclues des jours et du total du rayon.</p><button onClick={() => onCandidates(projection.candidates)}>Consulter les localisations à confirmer</button></div>}
    <p className="hint">Choisissez un jour pour consulter toutes ses courses. Une épreuve sur plusieurs jours compte une seule fois dans le total mensuel.</p>
  </section>;
}

export function CalendarPeriodControls({ period, setPeriod }) {
  const commitYear = event => {
    const year = Number(event.target.value);
    if (Number.isInteger(year) && year >= MIN_CALENDAR_YEAR && year <= MAX_CALENDAR_YEAR) setPeriod(value => selectCalendarMonth(value, year));
    else event.target.value = period.year;
  };
  return <section className="period-controls" aria-label="Période des courses">
    <label>Année<input key={period.year} aria-label="Année civile" type="number" min={MIN_CALENDAR_YEAR} max={MAX_CALENDAR_YEAR} step="1" defaultValue={period.year} onBlur={commitYear} onKeyDown={event => { if (event.key === 'Enter') event.currentTarget.blur(); }} /></label>
    <label>Mois<select aria-label="Mois" value={period.month} onChange={event => { const month = Number(event.target.value); setPeriod(value => selectCalendarMonth(value, value.year, month)); }}>{MONTHS.map((name, index) => <option key={name} value={index + 1}>{name}</option>)}</select></label>
  </section>;
}
