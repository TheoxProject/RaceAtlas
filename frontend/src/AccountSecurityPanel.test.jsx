import { afterEach, expect, test, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { AccountSecurityPanel } from './AccountSecurityPanel.jsx';
afterEach(cleanup);
const account = { account: { id: 'alice' }, busy: false, revalidating: false };
function client() { return { clearFeedback: vi.fn(), sensitive: vi.fn(async () => false), getSnapshot: () => account }; }
test('delete requires explicit confirmation and clears current secret after result', async () => {
  const controller = client(); render(<AccountSecurityPanel account={account} controller={controller} />);
  fireEvent.click(screen.getByRole('button', { name: 'Supprimer mon compte' }));
  const input = screen.getByLabelText('Mot de passe actuel');
  fireEvent.change(input, { target: { value: ' exact legacy ' } });
  fireEvent.click(screen.getByRole('button', { name: 'Supprimer mon compte' }));
  expect(controller.sensitive).not.toHaveBeenCalled();
  expect(document.activeElement).toBe(screen.getByRole('checkbox'));
  fireEvent.click(screen.getByRole('checkbox'));
  fireEvent.click(screen.getByRole('button', { name: 'Supprimer mon compte' }));
  await waitFor(() => expect(input.value).toBe(''));
  expect(controller.sensitive).toHaveBeenCalledWith('deleteAccount', { current_password: ' exact legacy ' });
  expect(screen.getByRole('checkbox').checked).toBe(false);
});
test('new password uses exact Unicode and spaces; abandonment discards fields', async () => {
  const controller = client(); render(<AccountSecurityPanel account={account} controller={controller} />);
  fireEvent.click(screen.getByRole('button', { name: 'Changer le mot de passe' }));
  const password = '  🔑🧭🚲 New exact password  ';
  fireEvent.change(screen.getByLabelText('Mot de passe actuel'), { target: { value: 'legacy' } });
  fireEvent.change(screen.getByLabelText('Nouveau mot de passe'), { target: { value: password } });
  fireEvent.change(screen.getByLabelText('Confirmer le nouveau mot de passe'), { target: { value: password } });
  fireEvent.click(screen.getByRole('button', { name: 'Changer le mot de passe' }));
  await waitFor(() => expect(screen.getByLabelText('Nouveau mot de passe').value).toBe(''));
  expect(controller.sensitive).toHaveBeenCalledWith('changePassword', { current_password: 'legacy', new_password: password });
  fireEvent.change(screen.getByLabelText('Mot de passe actuel'), { target: { value: 'abandoned' } });
  fireEvent.click(screen.getByRole('button', { name: 'Retour à la sécurité' }));
  fireEvent.click(screen.getByRole('button', { name: 'Changer le mot de passe' }));
  expect(screen.getByLabelText('Mot de passe actuel').value).toBe('');
});
