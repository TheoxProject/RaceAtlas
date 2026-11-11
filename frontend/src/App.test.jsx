import { afterEach, expect, test, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { App } from './App.jsx';
import { getJson, loadSelection } from './catalog.js';
import fixture from '../../fixtures/catalog.v1.json';

vi.mock('./MapView.jsx', () => ({ MapView: () => <div aria-label="Moteur carte isolé en test unitaire" /> }));
vi.mock('./catalog.js', async importOriginal => ({ ...await importOriginal(), getJson: vi.fn(), loadSelection: vi.fn() }));
const data = (items = fixture.races) => ({ total: items.length, items: items.map(race => ({ race, matching_scope_ids: [] })), features: [], unlocated_count: items.length, unlocatedIds: items.map(race => race.id), coverage: {} });
afterEach(() => { cleanup(); vi.resetAllMocks(); });
function prepare(value = data()) { getJson.mockResolvedValue({ categories: [{ code: 'u15', label: 'U15' }] }); loadSelection.mockResolvedValue(value); }

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
