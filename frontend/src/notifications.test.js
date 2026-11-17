import { expect, test } from 'vitest';
import { allowedNotificationPath, notificationChanges, notificationPage, notificationPath, sourceLink } from './notifications.js';

test('strict canonical notification allowlist cannot target another URL or query', () => {
  const cursor = 'opaque.' + 'a'.repeat(43);
  expect(allowedNotificationPath(notificationPath(cursor))).toBe(true);
  for (const path of ['https://example.test/api/v1/me/notifications?limit=50', '/api/v1/me/notifications?limit=50&limit=50', '/api/v1/me/notifications?limit=50&other=1', '/api/v1/me/notifications?limit=50#secret', '/api/v1/me/notifications?limit=100', '/api/v1/me/notifications?cursor=' + cursor + '&limit=50']) expect(allowedNotificationPath(path)).toBe(false);
  for (const value of ['', 'short', 'a'.repeat(1025), 'opaque.a&token=private']) expect(() => notificationPath(value)).toThrow();
});

test('notification response limits reject invalid totals/cursors without clipping', () => {
  const valid = { items: [], unread_count: 87, has_more: false, next_cursor: null };
  expect(notificationPage(valid).unreadCount).toBe(87);
  for (const patch of [{ unread_count: -1 }, { unread_count: Number.MAX_SAFE_INTEGER + 1 }, { has_more: true }, { next_cursor: 'bad' }, { items: Array(51).fill({}) }, { extra: 'é'.repeat(8193) }]) expect(() => notificationPage({ ...valid, ...patch })).toThrow();
});

test('differential and full snapshots show only meaningful changes, never competition IDs', () => {
  const before = { name: 'Avant', status: 'scheduled', types: ['road_race'], commune: { name: 'Fictive', department: '26' } };
  const after = { commune: { department: '26', name: 'Fictive' }, types: ['road_race'], status: 'scheduled', name: 'Après' };
  expect(notificationChanges({ before, after })).toEqual([{ label: 'Nom', before: 'Avant', after: 'Après' }]);
  const presence = notificationChanges({ before: { source_presence: 'present' }, after: { source_presence: 'to_verify' } });
  expect(presence).toHaveLength(1); expect(presence[0].after).toMatch(/absence ne signifie pas annulation/);
  const grouped = notificationChanges({ before: { competition: 'opaque-group-old' }, after: { competition: 'opaque-group-new' } });
  expect(JSON.stringify(grouped)).not.toContain('opaque-group');
});

test('published eligibility rule groups and uncertainty stay correlated and readable', () => {
  const groups = { status: 'ambiguous', identity_status: 'unverified', rules: [
    { raw_label: 'Groupe femmes', categories: ['access_1'], restrictions: { sex: 'women', min_age: 17, max_age: 18, age_reference: 'season_end', age_season: 2026, engagers: ['Club'], other_text: 'Restriction source' } },
    { raw_label: 'Autre groupe', categories: ['open_2'], restrictions: { sex: 'men', engagers: [] } },
  ] };
  const result = notificationChanges({ before: { eligibility: null }, after: { eligibility: groups } })[0];
  expect(result.after).toMatch(/ambiguës/); expect(result.after).toMatch(/Groupe femmes · access 1 · Femmes · Âge : 17 à 18 ans en fin de saison 2026 · Engagement : Club · Restriction source/);
  expect(result.after).toMatch(/Autre groupe · open 2 · Hommes/);
  expect(result.after).not.toContain('[object Object]');
  expect(sourceLink('javascript:alert(1)')).toBeNull(); expect(sourceLink('https://user:password@example.test')).toBeNull();
  expect(sourceLink('https://example.test/source')).toBe('https://example.test/source');
});
