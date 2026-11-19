import { expect, test } from 'vitest';
import { neutralStyle, raceStyle, raceStyleLabel, raceStyles } from './raceTypes.js';

test('race styles use distinct colours for the supported published types and disciplines', () => {
  const styles = [
    ['road', ['road_race'], 'Route · Course en ligne'],
    ['road', ['time_trial'], 'Route · CLM'],
    ['road', ['hill_climb'], 'Route · Grimpée'],
    ['track', [], 'Piste'],
    ['cyclocross', ['cyclocross'], 'Cyclo-cross'],
    ['gravel', ['gravel_race'], 'Gravel'],
    ['mtb', [], 'VTT'],
    ['mtb', ['xco'], 'VTT · Cross-country'],
    ['mtb', ['enduro'], 'VTT · Enduro'],
    ['mtb', ['downhill'], 'VTT · Descente'],
  ].map(([discipline, types, label]) => {
    const race = { discipline, types };
    const style = raceStyle(race);
    expect(raceStyleLabel(race, style)).toBe(label);
    expect(style).not.toBe(neutralStyle);
    return style;
  });
  expect(new Set(styles.map(style => style.color)).size).toBe(styles.length);
  expect(new Set(raceStyles)).toEqual(new Set([neutralStyle, ...styles]));
});

test('unknown or multiple types use honest neutral or discipline-level labels', () => {
  const road = { discipline: 'road', types: ['xco'] };
  const mixed = { discipline: 'road', types: ['hill_climb', 'time_trial'] };
  const duplicates = { discipline: 'road', types: ['hill_climb', 'hill_climb'] };
  expect(raceStyle(road)).toBe(neutralStyle);
  expect(raceStyleLabel(road, raceStyle(road))).toBe('Route · Type non précisé');
  expect(raceStyle(mixed)).toBe(neutralStyle);
  expect(raceStyleLabel(mixed, raceStyle(mixed))).toBe('Route · Types variés');
  expect(raceStyleLabel(duplicates, raceStyle(duplicates))).toBe('Route · Grimpée');
  expect(raceStyleLabel({ discipline: 'mtb' }, raceStyle({ discipline: 'mtb' }))).toBe('VTT');
});
