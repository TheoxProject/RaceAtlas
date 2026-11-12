import { afterEach, expect, test, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { App } from './App.jsx';
import { getJson, loadSelection } from './catalog.js';
import fixture from '../../fixtures/catalog.v1.json';

vi.mock('./MapView.jsx', () => ({ MapView: () => <div aria-label="Moteur carte isolé en test unitaire" /> }));
vi.mock('./catalog.js', async importOriginal => ({ ...await importOriginal(), getJson: vi.fn(), loadSelection: vi.fn() }));
const data = (items = fixture.races) => ({ total: items.length, items: items.map(race => ({ race, matching_scope_ids: [] })), features: [], unlocated_count: items.length, unlocatedIds: items.map(race => race.id), coverage: {} });
afterEach(() => { cleanup(); vi.resetAllMocks(); vi.useRealTimers(); });
function prepare(value = data()) { getJson.mockResolvedValue({ categories: [{ code: 'u15', label: 'U15' }] }); loadSelection.mockResolvedValue(value); }

test('unchanged ISO controls preserve details, requests and the New Year civil anchor', async () => {
  vi.setSystemTime(new Date('2027-01-01T12:00:00Z'));
  const race = fixture.races.find(race => race.id === 'race-mtb-multiday');
  prepare(data([race])); render(<App />);
  await screen.findByText('Données synthétiques · courses fictives');
  fireEvent.click(screen.getByRole('button', { name: 'Semaine ISO', exact: true }));
  await waitFor(() => expect(loadSelection.mock.lastCall[0]).toMatchObject({ from: '2026-12-28', to: '2027-01-03' }));
  fireEvent.click(screen.getByRole('button', { name: 'Explorer les communes' }));
  fireEvent.click(screen.getByRole('button', { name: new RegExp(race.name) }));
  const requests = loadSelection.mock.calls.length;
  for (const label of ['Année ISO', 'Semaine ISO']) {
    const input = screen.getByLabelText(label);
    fireEvent.focus(input); fireEvent.blur(input);
    input.focus(); fireEvent.keyDown(input, { key: 'Enter' });
  }
  fireEvent.click(screen.getByRole('button', { name: 'Semaine ISO', exact: true }));
  await new Promise(resolve => setTimeout(resolve, 250));
  expect(loadSelection).toHaveBeenCalledTimes(requests);
  expect(screen.getByRole('heading', { name: race.name })).toBeTruthy();
  fireEvent.click(screen.getByRole('button', { name: 'Mois', exact: true }));
  await waitFor(() => expect(loadSelection.mock.lastCall[0]).toMatchObject({ from: '2027-01-01', to: '2027-01-31' }));
  expect(screen.getByLabelText('Année civile').value).toBe('2027');
  expect(screen.getByLabelText('Mois').value).toBe('1');
  fireEvent.click(screen.getByRole('button', { name: 'Année', exact: true }));
  await waitFor(() => expect(loadSelection.mock.lastCall[0]).toMatchObject({ from: '2027-01-01', to: '2027-12-31' }));
});

test('New Year ISO mode uses the containing week and rejects fractional year/week selections', async () => {
  vi.setSystemTime(new Date('2027-01-01T12:00:00Z'));
  prepare(data([])); render(<App />);
  await screen.findByText('Aucune course dans cette sélection');
  expect(screen.getByLabelText('Année civile').value).toBe('2027');
  fireEvent.click(screen.getByRole('button', { name: 'Semaine ISO', exact: true }));
  await waitFor(() => expect(loadSelection.mock.lastCall[0]).toMatchObject({ from: '2026-12-28', to: '2027-01-03' }));
  expect(screen.getByLabelText('Année ISO').value).toBe('2026');
  expect(screen.getByLabelText('Semaine ISO').value).toBe('53');
  for (const [label, invalid, restored] of [['Année ISO', '2026.5', '2026'], ['Semaine ISO', '2.5', '53'], ['Semaine ISO', '', '53'], ['Semaine ISO', '0', '53'], ['Semaine ISO', '-1', '53']]) {
    const input = screen.getByLabelText(label);
    fireEvent.change(input, { target: { value: invalid } });
    fireEvent.blur(input);
    expect(input.value).toBe(restored);
  }
  expect(loadSelection.mock.lastCall[0]).toMatchObject({ from: '2026-12-28', to: '2027-01-03' });
  const year = screen.getByLabelText('Année ISO');
  fireEvent.change(year, { target: { value: '2027' } }); fireEvent.blur(year);
  await waitFor(() => expect(loadSelection.mock.lastCall[0]).toMatchObject({ from: '2027-12-27', to: '2028-01-02' }));
  expect(screen.getByLabelText('Semaine ISO').value).toBe('52');
  fireEvent.click(screen.getByRole('button', { name: 'Année', exact: true }));
  const civil = screen.getByLabelText('Année civile');
  fireEvent.change(civil, { target: { value: '2027.5' } }); fireEvent.blur(civil);
  expect(civil.value).toBe('2027');
});

test('current year selection and dynamic categories are independent of filtered races', async () => {
  prepare(data([])); render(<App />);
  expect(await screen.findByText('Aucune course dans cette sélection')).toBeTruthy();
  expect(screen.getByLabelText('U15')).toBeTruthy();
  expect(loadSelection.mock.calls[0][0].from).toBe(`${new Intl.DateTimeFormat('en', { timeZone: 'Europe/Paris', year: 'numeric' }).format(new Date())}-01-01`);
  fireEvent.click(screen.getByLabelText('U15'));
  fireEvent.click(screen.getByRole('button', { name: 'Toutes ensemble' }));
  await waitFor(() => expect(loadSelection.mock.lastCall[0]).toMatchObject({ categories: ['u15'], category_operator: 'and' }));
});
test('nonlocalized details retain null location and individual scopes', async () => {
  const race = fixture.races.find(race => race.id === 'race-unlocated');
  prepare(data([race])); render(<App />);
  await screen.findByText('Données synthétiques · courses fictives');
  fireEvent.click(screen.getByRole('button', { name: 'Explorer les communes' }));
  fireEvent.click(screen.getByRole('button', { name: new RegExp(race.name) }));
  expect(screen.getByRole('heading', { name: race.name })).toBeTruthy();
  expect(screen.getByText('Centre de commune non disponible')).toBeTruthy();
  expect(screen.getByText(/Votre admissibilité personnelle n’est pas évaluée/)).toBeTruthy();
});
test('data error is recoverable and metadata has its own retry', async () => {
  getJson.mockRejectedValueOnce(new Error()).mockResolvedValue({ categories: [] });
  loadSelection.mockRejectedValueOnce(new Error()).mockResolvedValue(data([]));
  render(<App />);
  await screen.findByText('Service temporairement indisponible.');
  fireEvent.click(screen.getByRole('button', { name: 'Réessayer les catégories' }));
  expect(await screen.findByText('Aucune catégorie renseignée.')).toBeTruthy();
  fireEvent.click(screen.getByRole('button', { name: 'Réessayer', exact: true }));
  expect(await screen.findByText('Aucune course dans cette sélection')).toBeTruthy();
});
test('a stale unabortable response cannot overwrite a later selection', async () => {
  getJson.mockResolvedValue({ categories: [] });
  let resolveOld;
  loadSelection.mockImplementationOnce(() => new Promise(resolve => { resolveOld = resolve; })).mockResolvedValue(data([]));
  render(<App />);
  await waitFor(() => expect(loadSelection).toHaveBeenCalledTimes(1));
  fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'new' } });
  await screen.findByText('Aucune course dans cette sélection');
  resolveOld(data());
  await new Promise(resolve => setTimeout(resolve, 20));
  expect(screen.getByText('Aucune course dans cette sélection')).toBeTruthy();
  expect(screen.queryByText('Données synthétiques · courses fictives')).toBeNull();
});

test('calendar opens the civil month from ISO and returns to that month with shared details and no-op requests', async () => {
  vi.setSystemTime(new Date('2027-01-01T12:00:00Z'));
  const race = fixture.races.find(race => race.id === 'race-mtb-multiday');
  prepare(data([race])); render(<App />);
  await screen.findByText('Données synthétiques · courses fictives');
  fireEvent.click(screen.getByRole('button', { name: 'Semaine ISO', exact: true }));
  await waitFor(() => expect(loadSelection.mock.lastCall[0]).toMatchObject({ from: '2026-12-28' }));
  fireEvent.click(screen.getByRole('button', { name: 'Calendrier', exact: true }));
  expect(screen.queryByRole('button', { name: 'Année', exact: true })).toBeNull();
  expect(screen.getByRole('status').textContent).toBe('Recherche des courses…');
  await screen.findByText('1 course ce mois-ci');
  expect(loadSelection.mock.lastCall[0]).toMatchObject({ from: '2027-01-01', to: '2027-01-31' });
  fireEvent.click(screen.getAllByRole('button', { name: new RegExp(race.name) })[0]);
  expect(screen.getByRole('heading', { name: race.name })).toBeTruthy();
  const requests = loadSelection.mock.calls.length;
  fireEvent.blur(screen.getByLabelText('Année civile'));
  fireEvent.change(screen.getByLabelText('Mois'), { target: { value: '1' } });
  fireEvent.click(screen.getByRole('button', { name: 'Calendrier', exact: true }));
  await new Promise(resolve => setTimeout(resolve, 200));
  expect(loadSelection).toHaveBeenCalledTimes(requests);
  expect(screen.getByRole('heading', { name: race.name })).toBeTruthy();
  fireEvent.click(screen.getByRole('button', { name: 'Carte', exact: true }));
  expect(screen.getByLabelText('Mois').value).toBe('1');
  expect(screen.getByRole('button', { name: 'Mois', exact: true }).getAttribute('aria-pressed')).toBe('true');
  expect(loadSelection).toHaveBeenCalledTimes(requests);
});

test('calendar immediately hides old data under a new month, including debounce and delayed response', async () => {
  vi.setSystemTime(new Date('2027-01-01T12:00:00Z'));
  const race = fixture.races.find(race => race.id === 'race-mtb-multiday');
  prepare(data([race])); render(<App />);
  await screen.findByText('Données synthétiques · courses fictives');
  fireEvent.click(screen.getByRole('button', { name: 'Calendrier', exact: true }));
  await screen.findByText('1 course ce mois-ci');
  let resolveNext;
  loadSelection.mockImplementationOnce(() => new Promise(resolve => { resolveNext = resolve; }));
  fireEvent.click(screen.getByRole('button', { name: 'Mois suivant' }));
  expect(screen.getByRole('heading', { name: 'Février 2027' })).toBeTruthy();
  expect(screen.getByRole('status').textContent).toBe('Recherche des courses…');
  expect(screen.queryByText('1 course ce mois-ci')).toBeNull();
  expect(screen.queryByRole('button', { name: new RegExp(race.name) })).toBeNull();
  await waitFor(() => expect(resolveNext).toBeTypeOf('function'));
  resolveNext(data([]));
  await screen.findByText('0 courses ce mois-ci');
});
