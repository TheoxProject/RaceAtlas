import { expect, test, vi } from 'vitest';
import { changePeriod, groupCommunes, initialPeriod, loadSelection, parisToday, periodRange, weeksInYear } from './catalog.js';

test('initial year uses the current Paris civil year, including UTC New Year boundary', () => {
  expect(initialPeriod(new Date('2026-12-31T23:30:00Z'))).toEqual({ mode: 'year', year: 2027, month: 1, day: 1, isoYear: 2026, week: 53 });
  expect(parisToday(new Date('2026-06-01T22:30:00Z'))).toEqual({ year: 2026, month: 6, day: 2 });
});
test('civil and ISO views share the focused date at both New Year boundaries', () => {
  const january = initialPeriod(new Date('2027-01-01T12:00:00Z'));
  expect(periodRange(changePeriod(january, { mode: 'week' }))).toEqual({ from: '2026-12-28', to: '2027-01-03' });
  expect(periodRange(changePeriod(january, { mode: 'month' }))).toEqual({ from: '2027-01-01', to: '2027-01-31' });
  const december = initialPeriod(new Date('2025-12-31T12:00:00Z'));
  expect(december).toMatchObject({ year: 2025, isoYear: 2026, week: 1 });
  expect(periodRange(changePeriod(december, { mode: 'week' }))).toEqual({ from: '2025-12-29', to: '2026-01-04' });
});
test('changing the focused month/year recomputes ISO and clamps leap days; changing ISO synchronizes civil month', () => {
  const leap = initialPeriod(new Date('2024-02-29T12:00:00Z'));
  expect(changePeriod(leap, { year: 2025 })).toMatchObject({ year: 2025, month: 2, day: 28, isoYear: 2025, week: 9 });
  const week = changePeriod(initialPeriod(new Date('2027-01-01T12:00:00Z')), { mode: 'week' });
  const next = changePeriod(week, { isoYear: 2027 });
  expect(next).toMatchObject({ isoYear: 2027, week: 52, year: 2027, month: 12, day: 27 });
  expect(periodRange(changePeriod(next, { mode: 'month' }))).toEqual({ from: '2027-12-01', to: '2027-12-31' });
  expect(changePeriod(next, { month: 1 })).toMatchObject({ year: 2027, month: 1, day: 27, isoYear: 2027, week: 4 });
});
test.each([
  [{ mode: 'year', year: 2026 }, { from: '2026-01-01', to: '2026-12-31' }],
  [{ mode: 'month', year: 2024, month: 2 }, { from: '2024-02-01', to: '2024-02-29' }],
  [{ mode: 'month', year: 2025, month: 2 }, { from: '2025-02-01', to: '2025-02-28' }],
  [{ mode: 'week', year: 2026, week: 1 }, { from: '2025-12-29', to: '2026-01-04' }],
  [{ mode: 'week', year: 2020, week: 53 }, { from: '2020-12-28', to: '2021-01-03' }],
  [{ mode: 'week', year: 2021, week: 53 }, { from: '2021-12-27', to: '2022-01-02' }],
])('inclusive period %j', (period, expected) => expect(periodRange(period)).toEqual(expected));
test('ISO week counts account for leap years and the weekday of January 1', () => {
  expect([2020, 2021, 2024, 2026].map(weeksInYear)).toEqual([53, 52, 52, 53]);
});
test('commune grouping deduplicates races before spatial clustering', () => {
  const feature = (id, commune) => ({ id, geometry: { coordinates: [4, 45] }, properties: { race_id: id, commune_id: commune } });
  expect(groupCommunes([feature('a', 'one'), feature('a', 'one'), feature('b', 'one'), feature('c', 'two')]).map(group => group.raceIds)).toEqual([['a', 'b'], ['c']]);
});
const race = id => ({ id, name: id });
const page = (cursor = null, version = 'v1', items = []) => ({ catalog_version: version, next_cursor: cursor, total: items.length, items: items.map(id => ({ race: race(id), matching_scope_ids: [] })), unlocated_count: 0, coverage: {} });
const map = (cursor = null, version = 'v1', ids = []) => ({ catalog_version: version, next_cursor: cursor, features: [], unlocated_ids: ids });

test('all radius pages load even when confirmed items are empty; missing details fetched separately', async () => {
  const request = vi.fn().mockResolvedValueOnce(page('continue')).mockResolvedValueOnce(map('continue', 'v1', ['a']))
    .mockResolvedValueOnce(page()).mockResolvedValueOnce(map(null, 'v1', ['b']))
    .mockResolvedValueOnce(race('a')).mockResolvedValueOnce(race('b')).mockResolvedValueOnce(page());
  const data = await loadSelection({}, undefined, request);
  expect(data.items.map(item => item.race.id)).toEqual(['a', 'b']);
  expect(data.unlocatedIds).toEqual(['a', 'b']);
  expect(request.mock.calls[2][0]).toContain('cursor=continue');
});
test.each(['409', 'different endpoint versions', 'different page versions', 'final verification'])('bounded restart discards all earlier items on %s', async reason => {
  let failed = false, checks = 0;
  const request = vi.fn(async url => {
    const isMap = url.startsWith('/api/v1/map');
    if (!failed) {
      if (reason === '409') { failed = true; throw Object.assign(new Error(), { status: 409 }); }
      if (reason === 'different endpoint versions') { if (isMap) { failed = true; return map(null, 'changed'); } return page(null, 'v1', ['old']); }
      if (reason === 'different page versions') {
        if (url.includes('cursor=')) { failed = true; return isMap ? map(null, 'changed') : page(null, 'changed'); }
        return isMap ? map('next') : page('next', 'v1', ['old']);
      }
      if (url.includes('limit=1')) { failed = true; return page(null, 'changed'); }
      return isMap ? map() : page(null, 'v1', ['old']);
    }
    checks++;
    return isMap ? map(null, 'v2') : page(null, 'v2', ['fresh']);
  });
  const data = await loadSelection({}, undefined, request);
  expect(data.catalog_version).toBe('v2');
  expect(data.items.map(item => item.race.id)).toEqual(['fresh']);
  expect(checks).toBeGreaterThan(0);
});
test('repeated catalogue changes stop after three attempts', async () => {
  const request = vi.fn().mockRejectedValue(Object.assign(new Error(), { status: 409 }));
  await expect(loadSelection({}, undefined, request)).rejects.toMatchObject({ status: 409 });
  expect(request).toHaveBeenCalledTimes(6);
});
test('aborted requests and ordinary errors are never retried', async () => {
  const controller = new AbortController(); controller.abort();
  const request = vi.fn().mockRejectedValue(Object.assign(new Error(), { status: 409 }));
  await expect(loadSelection({}, controller.signal, request)).rejects.toThrow();
  expect(request).toHaveBeenCalledTimes(2);
});
