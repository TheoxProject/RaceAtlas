import { afterEach, expect, test, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { App } from './App.jsx';

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

test('renders database detail through discovery then detail, preserving null location', async () => {
  const fetch = vi.fn().mockResolvedValueOnce({ ok: true, json: async () => ({ race_id: 'opaque-id' }) })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ name: 'Fictive persistée', discipline: 'road',
      start_date: '2026-11-11', end_date: '2026-11-11', department: '69', location: null, entry_scopes: [] }) });
  vi.stubGlobal('fetch', fetch);
  render(<App />);
  expect(screen.getByRole('status').textContent).toContain('Chargement');
  expect(await screen.findByRole('heading', { name: 'Fictive persistée' })).toBeTruthy();
  expect(screen.getByText('Commune inconnue')).toBeTruthy();
  expect(fetch.mock.calls[1][0]).toBe('/api/v1/races/opaque-id');
});

test('empty database is explicit', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ race_id: null }) }));
  render(<App />);
  expect(await screen.findByText('Aucune épreuve de démonstration')).toBeTruthy();
});

test('unavailable service is recoverable', async () => {
  const fetch = vi.fn().mockResolvedValueOnce({ ok: false })
    .mockResolvedValue({ ok: true, json: async () => ({ race_id: null }) });
  vi.stubGlobal('fetch', fetch);
  render(<App />);
  expect(await screen.findByRole('alert')).toBeTruthy();
  fireEvent.click(screen.getByRole('button', { name: 'Actualiser la démonstration' }));
  expect(await screen.findByText('Aucune épreuve de démonstration')).toBeTruthy();
});
