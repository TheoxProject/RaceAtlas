import { afterEach, expect, test, vi } from 'vitest';
import { MAX_CALENDAR_YEAR, MIN_CALENDAR_YEAR, monthGrid, moveCalendarMonth, projectCalendar, selectCalendarMonth } from './calendar.js';
import { changePeriod, initialPeriod, periodRange } from './catalog.js';
import fixture from '../../fixtures/catalog.v1.json';

afterEach(() => vi.unstubAllEnvs());
const period = (year, month, day = 1) => ({ ...initialPeriod(new Date(Date.UTC(year, month - 1, day, 12))), mode: 'month' });
const entry = id => {
  const race = fixture.races.find(race => race.id === id);
  return { race, matching_scope_ids: race.entry_scopes.map(scope => scope.id) };
};
const dailyIds = (projection, date) => projection.days.find(day => day.date === date)?.items.map(item => item.race.id);

test.each([
  [2024, 2, 29, '2024-01-29', '2024-03-03', 35],
  [2025, 2, 28, '2025-01-27', '2025-03-02', 35],
  [2025, 6, 30, '2025-05-26', '2025-07-06', 42],
  [2025, 8, 31, '2025-07-28', '2025-08-31', 35],
  [2021, 2, 28, '2021-02-01', '2021-02-28', 28],
])('month %i-%i has %i civil days and complete Monday–Sunday rows', (year, month, count, first, last, length) => {
  const grid = monthGrid(year, month);
  expect(grid).toHaveLength(length);
  expect(grid[0].date).toBe(first);
  expect(grid.at(-1).date).toBe(last);
  expect(grid.filter(day => day.inMonth)).toHaveLength(count);
  expect(new Set(grid.map(day => day.date)).size).toBe(length);
  grid.forEach((day, index) => {
    expect(new Date(`${day.date}T00:00:00Z`).getUTCDay()).toBe((index + 1) % 7);
    expect(day.items).toEqual([]);
    if (index) expect(+new Date(`${day.date}T00:00:00Z`) - +new Date(`${grid[index - 1].date}T00:00:00Z`)).toBe(86400000);
  });
});

test.each([[1900, 28], [2000, 29], [2100, 28], [2200, 28]])('civil year %i has %i days in February, including century rules', (year, count) => {
  expect(monthGrid(year, 2).filter(day => day.inMonth)).toHaveLength(count);
});

test.each(['Pacific/Honolulu', 'Europe/Paris', 'Pacific/Kiritimati'])('civil grid is independent of device timezone %s', zone => {
  vi.stubEnv('TZ', zone);
  expect(monthGrid(2027, 1)[0].date).toBe('2026-12-28');
  expect(monthGrid(2027, 1).at(-1).date).toBe('2027-01-31');
  expect(monthGrid(2024, 2).filter(day => day.inMonth).at(-1).date).toBe('2024-02-29');
});

test.each(['year', 'week'])('opening from %s selects the shared Paris civil month rather than the ISO year', mode => {
  const anchor = initialPeriod(new Date('2026-12-31T23:30:00Z'));
  const current = changePeriod(anchor, { mode });
  expect(current).toMatchObject({ year: 2027, month: 1, day: 1, isoYear: 2026, week: 53 });
  const selected = selectCalendarMonth(current);
  expect(selected).toEqual({ ...current, mode: 'month' });
  expect(periodRange(selected)).toEqual({ from: '2027-01-01', to: '2027-01-31' });
  expect(selectCalendarMonth(selected)).toBe(selected);
  expect(selectCalendarMonth(selected, 2027, 1)).toBe(selected);
  expect(moveCalendarMonth(selected, 0)).toBe(selected);
});

test('month-to-month no-ops and civil return preserve the original anchor and scope-neutral state', () => {
  const anchor = initialPeriod(new Date('2025-12-31T12:00:00Z'));
  const month = selectCalendarMonth(anchor);
  expect(month).toMatchObject({ year: 2025, month: 12, day: 31, isoYear: 2026, week: 1 });
  expect(selectCalendarMonth(month)).toBe(month);
  expect(changePeriod(month, { mode: 'month' })).toBe(month);
  expect(periodRange(month)).toEqual({ from: '2025-12-01', to: '2025-12-31' });
});

test('navigation crosses December/January and clamps a genuinely changed February anchor', () => {
  const december = selectCalendarMonth(initialPeriod(new Date('2026-12-31T12:00:00Z')));
  const january = moveCalendarMonth(december, 1);
  expect(january).toMatchObject({ year: 2027, month: 1, day: 31 });
  expect(periodRange(january)).toEqual({ from: '2027-01-01', to: '2027-01-31' });
  expect(moveCalendarMonth(january, -1)).toEqual(december);
  expect(moveCalendarMonth(january, 1)).toMatchObject({ year: 2027, month: 2, day: 28 });
  const leap = selectCalendarMonth(initialPeriod(new Date('2024-01-31T12:00:00Z')));
  expect(moveCalendarMonth(leap, 1)).toMatchObject({ year: 2024, month: 2, day: 29 });
});

test.each([[1899, 12], [2201, 1], [2026.5, 1], [2026, 0], [2026, 13], [2026, 2.5], [NaN, 1], [2026, NaN], ['2026', 1]])('invalid month %s-%s leaves state identical and has no grid or projection', (year, month) => {
  const current = period(2027, 1);
  expect(selectCalendarMonth(current, year, month)).toBe(current);
  expect(monthGrid(year, month)).toEqual([]);
  expect(projectCalendar({ year, month }, { items: [entry('race-mtb-multiday')] })).toEqual({ days: [], items: [], candidates: [], total: 0 });
});

test('navigation cannot escape the supported civil year range', () => {
  const first = period(MIN_CALENDAR_YEAR, 1);
  const last = period(MAX_CALENDAR_YEAR, 12);
  expect(moveCalendarMonth(first, -1)).toBe(first);
  expect(moveCalendarMonth(last, 1)).toBe(last);
  expect(periodRange(moveCalendarMonth(first, 1)).from).toBe('1900-02-01');
  expect(periodRange(moveCalendarMonth(last, -1)).from).toBe('2200-11-01');
  for (const delta of [NaN, Infinity, -Infinity, 0.5, '1', Number.MAX_SAFE_INTEGER + 1, -10000, 10000]) expect(moveCalendarMonth(first, delta)).toBe(first);
});

test('the cross-year fixture is clipped inclusively per month, deduplicated by race ID, never by scope', () => {
  const selected = entry('race-mtb-multiday');
  const originalWitnesses = selected.matching_scope_ids;
  const duplicate = { ...selected, matching_scope_ids: [] };
  const selection = { items: [selected, selected, duplicate], unlocatedIds: [] };
  const december = projectCalendar(period(2026, 12), selection);
  const january = projectCalendar(period(2027, 1), selection);
  expect(december.total).toBe(1);
  expect(january.total).toBe(1);
  expect(dailyIds(december, '2026-12-31')).toEqual(['race-mtb-multiday']);
  expect(dailyIds(january, '2027-01-01')).toEqual(['race-mtb-multiday']);
  expect(dailyIds(january, '2027-01-02')).toEqual(['race-mtb-multiday']);
  expect(dailyIds(january, '2027-01-03')).toEqual([]);
  expect(dailyIds(december, '2027-01-01')).toEqual([]);
  expect(dailyIds(january, '2026-12-31')).toEqual([]);
  expect(january.days.flatMap(day => day.items)).toHaveLength(2);
  expect(january.items).toHaveLength(1);
  expect(january.items[0]).toBe(selected);
  expect(january.days.find(day => day.date === '2027-01-01').items[0]).toBe(selected);
  expect(selected.matching_scope_ids).toBe(originalWitnesses);
});

test('long spans stay clipped to the displayed month, with no partial data on outside cells', () => {
  const selected = entry('race-road-combined');
  const spanning = { ...selected, race: { ...selected.race, start_date: '2025-12-01', end_date: '2027-03-31' } };
  const projection = projectCalendar(period(2026, 2), { items: [spanning] });
  expect(projection.total).toBe(1);
  expect(projection.days.filter(day => day.items.length)).toHaveLength(28);
  expect(projection.days.filter(day => !day.inMonth).every(day => day.items.length === 0)).toBe(true);
});

test('unlocated races remain confirmed outside radius and become separate candidates only within radius', () => {
  const located = entry('race-road-combined'), unlocated = entry('race-unlocated');
  const selection = { items: [located, unlocated, unlocated], unlocatedIds: [unlocated.race.id] };
  const outside = projectCalendar(period(2026, 11), selection);
  expect(outside.items).toEqual([located, unlocated]);
  expect(outside.total).toBe(2);
  expect(outside.candidates).toEqual([]);
  expect(dailyIds(outside, unlocated.race.start_date)).toContain(unlocated.race.id);
  const radius = projectCalendar(period(2026, 11), selection, { radius: true });
  expect(radius.items).toEqual([located]);
  expect(radius.total).toBe(1);
  expect(radius.candidates).toEqual([unlocated]);
  expect(radius.candidates[0]).toBe(unlocated);
  expect(radius.days.flatMap(day => day.items).every(item => item.race.id !== unlocated.race.id)).toBe(true);
  expect(unlocated.race.location).toBeNull();
});

test('scope witnesses, cancelled/to-verify data and the caller selection are preserved unchanged', () => {
  const selected = entry('race-cancelled'), missing = entry('race-missing');
  const selection = { items: [selected, missing] };
  const before = JSON.stringify(selection);
  const projection = projectCalendar(period(2026, 11), selection);
  expect(projection.items[0]).toBe(selected);
  expect(projection.items[0].matching_scope_ids).toBe(selected.matching_scope_ids);
  expect(projection.items[0].race.status).toBe('cancelled');
  expect(projection.items[1]).toBe(missing);
  expect(projection.items[1].race.source_presence).toBe('to_verify');
  expect(JSON.stringify(selection)).toBe(before);
});

test('two races in one competition count twice, while several scope witnesses never multiply a race', () => {
  const combined = entry('race-road-combined'), split = entry('race-road-split');
  expect(split.matching_scope_ids).toHaveLength(2);
  expect(combined.race.competition_id).toBe(split.race.competition_id);
  const projection = projectCalendar(period(2026, 11), { items: [combined, split] });
  expect(projection.total).toBe(2);
  expect(dailyIds(projection, '2026-11-11')).toEqual(['race-road-combined', 'race-road-split']);
  expect(projection.items[1].matching_scope_ids).toBe(split.matching_scope_ids);
});

test('empty, pending and non-overlapping selections give no phantom events or candidates', () => {
  for (const selection of [undefined, { items: [] }, { items: [entry('race-mtb-multiday')], unlocatedIds: ['race-mtb-multiday'] }]) {
    const projection = projectCalendar(period(2026, 2), selection, { radius: true });
    expect(projection.total).toBe(0);
    expect(projection.items).toEqual([]);
    expect(projection.candidates).toEqual([]);
    expect(projection.days.every(day => day.items.length === 0)).toBe(true);
  }
});
