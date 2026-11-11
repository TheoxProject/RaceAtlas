export const SPORTS = { road: 'Route', gravel: 'Gravel', mtb: 'VTT', cyclocross: 'Cyclo-cross' };
export const TYPES = { road_race: ['road', 'Course en ligne'], time_trial: ['road', 'CLM'], gravel_race: ['gravel', 'Gravel'], xco: ['mtb', 'Cross-country'], enduro: ['mtb', 'Enduro'], downhill: ['mtb', 'Descente'], cyclocross: ['cyclocross', 'Cyclo-cross'] };
export const DEPARTMENTS = { '01': 'Ain', '03': 'Allier', '07': 'Ardèche', '15': 'Cantal', '26': 'Drôme', '38': 'Isère', '42': 'Loire', '43': 'Haute-Loire', '63': 'Puy-de-Dôme', '69': 'Rhône', '73': 'Savoie', '74': 'Haute-Savoie' };
export const MONTHS = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'];
const day = 86400000;
const isoDate = date => date.toISOString().slice(0, 10);
export function parisToday(now = new Date()) {
  const parts = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Paris', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(now);
  return Object.fromEntries(parts.filter(part => part.type !== 'literal').map(part => [part.type, Number(part.value)]));
}
export function isoMonday(year, week = 1) {
  const fourth = new Date(Date.UTC(year, 0, 4));
  return new Date(+fourth - ((fourth.getUTCDay() + 6) % 7) * day + (week - 1) * 7 * day);
}
export function weeksInYear(year) { return Math.round((isoMonday(year + 1) - isoMonday(year)) / (7 * day)); }
function anchoredPeriod(date) {
  const thursday = new Date(+date + (3 - (date.getUTCDay() + 6) % 7) * day);
  const isoYear = thursday.getUTCFullYear();
  return { year: date.getUTCFullYear(), month: date.getUTCMonth() + 1, day: date.getUTCDate(), isoYear, week: Math.floor((+date - isoMonday(isoYear)) / (7 * day)) + 1 };
}
export function initialPeriod(now = new Date()) {
  const today = parisToday(now);
  return { mode: 'year', ...anchoredPeriod(new Date(Date.UTC(today.year, today.month - 1, today.day))) };
}
export function changePeriod(period, patch) {
  if (patch.isoYear !== undefined || patch.week !== undefined) {
    const isoYear = patch.isoYear ?? period.isoYear ?? period.year;
    const week = Math.min(patch.week ?? period.week, weeksInYear(isoYear));
    return { ...period, ...patch, ...anchoredPeriod(isoMonday(isoYear, week)) };
  }
  if (patch.year !== undefined || patch.month !== undefined) {
    const year = patch.year ?? period.year, month = patch.month ?? period.month;
    const lastDay = new Date(Date.UTC(year, month, 0)).getUTCDate();
    return { ...period, ...patch, ...anchoredPeriod(new Date(Date.UTC(year, month - 1, Math.min(period.day ?? 1, lastDay)))) };
  }
  return { ...period, ...patch };
}
export function periodRange(period) {
  if (period.mode === 'week') {
    const year = period.isoYear ?? period.year;
    const from = isoMonday(year, Math.min(period.week, weeksInYear(year)));
    return { from: isoDate(from), to: isoDate(new Date(+from + 6 * day)) };
  }
  const month = period.mode === 'month' ? period.month : 1;
  return { from: isoDate(new Date(Date.UTC(period.year, month - 1, 1))), to: isoDate(new Date(Date.UTC(period.year, period.mode === 'month' ? month : 12, 0))) };
}
export function initialFilters() {
  return { disciplines: [], types: [], categories: [], category_operator: 'or', query: '', geography: { mode: 'all' } };
}
export function groupCommunes(features) {
  const groups = new Map();
  for (const feature of features) {
    const id = feature.properties.commune_id;
    if (!groups.has(id)) groups.set(id, { id, coordinates: feature.geometry.coordinates, raceIds: new Set() });
    groups.get(id).raceIds.add(feature.properties.race_id);
  }
  return [...groups.values()].map(group => ({ ...group, raceIds: [...group.raceIds] }));
}
export async function getJson(url, signal) {
  const response = await fetch(url, { signal });
  if (!response.ok) { const error = new Error('Service temporairement indisponible.'); error.status = response.status; throw error; }
  return response.json();
}
export async function loadSelection(filter, signal, request = getJson) {
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const rows = new Map(), features = new Map(), candidates = new Set(), cursors = new Set();
      let cursor = null, first;
      do {
        const params = new URLSearchParams({ filter: JSON.stringify(filter), limit: '200' });
        if (cursor) params.set('cursor', cursor);
        const [page, map] = await Promise.all(['/api/v1/races', '/api/v1/map'].map(path => request(`${path}?${params}`, signal)));
        first ??= page;
        if (page.catalog_version !== first.catalog_version || map.catalog_version !== first.catalog_version || page.next_cursor !== map.next_cursor) throw Object.assign(new Error('changed'), { status: 409 });
        for (const item of page.items) rows.set(item.race.id, item);
        for (const feature of map.features) features.set(feature.id, feature);
        for (const id of map.unlocated_ids) candidates.add(id);
        cursor = page.next_cursor;
        if (cursor && cursors.has(cursor)) throw new Error('Invalid continuation');
        cursors.add(cursor);
      } while (cursor);
      // Radius candidates are excluded from RacePage.items; fetch their existing details.
      const missing = [...candidates].filter(id => !rows.has(id));
      // Bounded concurrency also protects a large unlocated catalogue.
      for (let index = 0; index < missing.length; index += 8) {
        await Promise.all(missing.slice(index, index + 8).map(async id => {
          const race = await request(`/api/v1/races/${encodeURIComponent(id)}`, signal);
          rows.set(id, { race, matching_scope_ids: [] });
        }));
      }
      const check = await request(`/api/v1/races?${new URLSearchParams({ filter: JSON.stringify(filter), limit: '1' })}`, signal);
      if (check.catalog_version !== first.catalog_version) throw Object.assign(new Error('changed'), { status: 409 });
      return { ...first, items: [...rows.values()], features: [...features.values()], unlocatedIds: [...candidates] };
    } catch (error) {
      if (signal?.aborted || error.status !== 409 || attempt === 2) throw error;
    }
  }
}
