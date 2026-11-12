import { afterEach, expect, test, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { Calendar, CalendarPeriodControls } from './Calendar.jsx';
import { projectCalendar } from './calendar.js';
import { initialPeriod } from './catalog.js';
import fixture from '../../fixtures/catalog.v1.json';

afterEach(cleanup);
const period = { ...initialPeriod(new Date('2027-01-01T12:00:00Z')), mode: 'month' };
const race = fixture.races.find(value => value.id === 'race-mtb-multiday');
const item = { race, matching_scope_ids: ['original-witness'] };

test('semantic month table clips multiday, exposes full labels and original objects', () => {
  const onDay = vi.fn(), onRace = vi.fn();
  render(<Calendar period={period} setPeriod={vi.fn()} projection={projectCalendar(period, { items: [item] })} status="ready" onDay={onDay} onRace={onRace} />);
  expect(screen.getByRole('table')).toBeTruthy();
  expect(screen.getAllByRole('columnheader')).toHaveLength(7);
  expect(screen.getByRole('status').textContent).toBe('1 course ce mois-ci');
  expect(screen.getAllByRole('button', { name: new RegExp(race.name) })).toHaveLength(2);
  fireEvent.click(screen.getByRole('button', { name: /vendredi 1 janvier 2027 · 1 course/ }));
  expect(onDay.mock.lastCall[0].items[0]).toBe(item);
  fireEvent.click(screen.getAllByRole('button', { name: new RegExp(race.name) })[0]);
  expect(onRace.mock.lastCall[0]).toBe(item);
  expect(screen.getByRole('button', { name: /jeudi 31 décembre 2026/ }).disabled).toBe(true);
});

test('dense days retain access to every item through day button', () => {
  const items = Array.from({ length: 6 }, (_, index) => ({ ...item, race: { ...race, id: `dense-${index}`, name: `Course ${index}` } }));
  const onDay = vi.fn();
  render(<Calendar period={period} setPeriod={vi.fn()} projection={projectCalendar(period, { items })} status="ready" onDay={onDay} onRace={vi.fn()} />);
  expect(screen.getAllByRole('button', { name: /Course [0-9]/ })).toHaveLength(4);
  fireEvent.click(screen.getByRole('button', { name: /vendredi 1 janvier 2027 · 6 courses/ }));
  expect(onDay.mock.lastCall[0].items).toEqual(items);
});

test('radius candidates stay outside table and are accessible separately', () => {
  const onCandidates = vi.fn();
  render(<Calendar period={period} setPeriod={vi.fn()} projection={projectCalendar(period, { items: [item], unlocatedIds: [race.id] }, { radius: true })} status="ready" onDay={vi.fn()} onRace={vi.fn()} onCandidates={onCandidates} />);
  expect(within(screen.getByRole('table')).queryByRole('button', { name: new RegExp(race.name) })).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Consulter les localisations à confirmer' }));
  expect(onCandidates.mock.lastCall[0][0]).toBe(item);
  expect(screen.getByRole('status').textContent).toBe('0 courses ce mois-ci');
});

test('month navigation bounds and functional updates preserve a preceding year commit', () => {
  let current = period;
  const setPeriod = fn => { current = fn(current); };
  render(<CalendarPeriodControls period={period} setPeriod={setPeriod} />);
  const year = screen.getByLabelText('Année civile');
  fireEvent.change(year, { target: { value: '2028' } }); fireEvent.blur(year);
  fireEvent.change(screen.getByLabelText('Mois'), { target: { value: '2' } });
  expect(current).toMatchObject({ year: 2028, month: 2, mode: 'month' });
  cleanup();
  render(<Calendar period={{ ...period, year: 1900, month: 1 }} setPeriod={setPeriod} projection={projectCalendar({ ...period, year: 1900, month: 1 }, null)} status="loading" />);
  expect(screen.getByRole('button', { name: 'Mois précédent' }).disabled).toBe(true);
  expect(screen.getByRole('status').textContent).toBe('Recherche des courses…');
});
