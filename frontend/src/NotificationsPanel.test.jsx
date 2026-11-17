import { useSyncExternalStore } from 'react';
import { afterEach, expect, test, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { NotificationsPanel } from './NotificationsPanel.jsx';
import { SeasonPanel } from './SeasonPanel.jsx';
import { ScopeSaveActions } from './ScopeSaveActions.jsx';
import { createAccountController } from './privateAccount.js';
const entry = { id: 'saved', scope_id: 'scope', scope: { id: 'scope', raw_label: 'Liste publiée' }, race: { name: 'Course fictive' } };
const item = { change_id: 'change', scope_id: 'scope', kind: 'presence', entry, created_at: '2026-11-17T08:00:00Z', read_at: null, delta: { before: { source_presence: 'present' }, after: { source_presence: 'to_verify' } }, provenance: { checked_at: '2026-11-17T07:00:00Z', source_url: 'https://example.test/calendar' } };
const notifications = { status: 'ready', unreadCount: 87, items: [item], nextCursor: 'opaque.' + 'a'.repeat(43), hasMore: true, error: null, message: null };
afterEach(cleanup);
test('section has global count and exact actions, source uncertainty and safe links', () => {
  const controller = { loadNotifications: vi.fn(), markNotificationsRead: vi.fn() };
  render(<NotificationsPanel account={{ notifications, busy: false }} controller={controller} />);
  expect(screen.getByText('87 nouveautés')).toBeTruthy(); expect(screen.getByText('Liste publiée')).toBeTruthy();
  expect(screen.getByText('Non lue')).toBeTruthy(); expect(screen.getByText(/Après : Présence à vérifier/)).toBeTruthy();
  expect(screen.getByText(/ne déterminent pas votre admissibilité/)).toBeTruthy();
  expect(screen.getByRole('link').rel).toContain('noreferrer');
  fireEvent.click(screen.getByRole('button', { name: 'Marquer comme lues' })); expect(controller.markNotificationsRead).toHaveBeenCalledOnce();
  fireEvent.click(screen.getByRole('button', { name: 'Charger la suite' })); expect(controller.loadNotifications).toHaveBeenCalledWith({ more: true });
});
test('unknown refresh after confirmed ACK never claims zero and requires explicit GET', () => {
  const controller = { loadNotifications: vi.fn(), markNotificationsRead: vi.fn() };
  render(<NotificationsPanel account={{ notifications: { ...notifications, status: 'error', unreadCount: null, message: 'Lecture enregistrée. Actualisez pour vérifier les nouveautés.', error: { code: 'network' }, items: [] } }} controller={controller} />);
  expect(screen.getByText('Compteur à actualiser')).toBeTruthy(); expect(screen.queryByText('0 nouveauté')).toBeNull();
  expect(screen.getByRole('button', { name: 'Marquer comme lues' }).disabled).toBe(true);
  fireEvent.click(screen.getByRole('button', { name: 'Actualiser les changements' })); expect(controller.loadNotifications).toHaveBeenCalledOnce();
});
test('simultaneous mounted scope action and season coalesce without a request loop', async () => {
  const reply = data => ({ status: 200, ok: true, json: async () => data });
  const fetcher = vi.fn(async path => path.endsWith('/csrf') ? reply({ csrf_token: 'a'.repeat(64) }) : path === '/api/v1/me' ? reply({ account: { id: 'alice' } }) : path.endsWith('/saved-entries') ? reply({ items: [entry] }) : reply({ items: [item], unread_count: 87, has_more: false, next_cursor: null }));
  const controller = createAccountController(fetcher); await controller.refresh();
  function Mounted() {
    const account = useSyncExternalStore(controller.subscribe, controller.getSnapshot);
    return <><ScopeSaveActions scopeId="scope" account={account} controller={controller} /><dialog open><SeasonPanel account={account} controller={controller} /></dialog></>;
  }
  render(<Mounted />);
  await vi.waitFor(() => expect(controller.getSnapshot().notifications.status).toBe('ready'));
  expect(within(screen.getByRole('dialog')).getByText('87 nouveautés')).toBeTruthy();
  expect(fetcher.mock.calls.filter(([path]) => path.endsWith('/saved-entries'))).toHaveLength(1);
  expect(fetcher.mock.calls.filter(([path]) => path.startsWith('/api/v1/me/notifications?'))).toHaveLength(1);
});
