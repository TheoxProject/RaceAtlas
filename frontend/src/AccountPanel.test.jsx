import { StrictMode } from 'react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { AccountPanel } from './AccountPanel.jsx';
import { clearAccountAction } from './accountBootstrap.js';
const guest = { status: 'anonymous', account: null, busy: false, error: null, message: null };
const controller = () => ({ submit: vi.fn(async () => true), clearFeedback: vi.fn(), refresh: vi.fn() });
beforeEach(() => { HTMLDialogElement.prototype.showModal = function () { this.open = true; }; HTMLDialogElement.prototype.close = function () { this.open = false; }; });
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
test('StrictMode does not submit proof before explicit confirmation', async () => {
  const action = { kind: 'confirm', proof: 'a'.repeat(43) };
  const c = controller(), onProofUsed = vi.fn(() => clearAccountAction(action));
  render(<StrictMode><AccountPanel open action={action} account={guest} controller={c} onClose={vi.fn()} onProofUsed={onProofUsed} /></StrictMode>);
  expect(c.submit).not.toHaveBeenCalled();
  expect(action.proof).toBe('a'.repeat(43));
  expect(document.querySelector('dialog').open).toBe(true);
  fireEvent.click(screen.getByRole('button', { name: 'Confirmer mon adresse' }));
  await waitFor(() => expect(onProofUsed).toHaveBeenCalledTimes(1));
  expect(c.submit).toHaveBeenCalledWith('confirm', {}, 'a'.repeat(43));
  expect(document.body.textContent).not.toContain('a'.repeat(43));
  expect(action.proof).toBeNull();
  expect(screen.getByRole('button', { name: 'Se connecter', exact: true })).toBeTruthy();
});
test('registration mismatched confirmation focuses error and exact128 Unicode remains untruncated', async () => {
  const c = controller();
  render(<AccountPanel open account={guest} controller={c} onClose={vi.fn()} onProofUsed={vi.fn()} />);
  fireEvent.click(screen.getByRole('button', { name: 'Créer un compte' }));
  fireEvent.change(screen.getByLabelText('Adresse email'), { target: { value: 'alice@example.test' } });
  const password = '😀'.repeat(128);
  fireEvent.change(screen.getByLabelText('Nouveau mot de passe'), { target: { value: password } });
  fireEvent.change(screen.getByLabelText('Confirmer le mot de passe'), { target: { value: password + 'x' } });
  fireEvent.submit(document.querySelector('form'));
  expect(screen.getByRole('alert').textContent).toMatch(/identiques/);
  expect(document.activeElement).toBe(screen.getByLabelText('Confirmer le mot de passe'));
  expect(c.submit).not.toHaveBeenCalled();
  expect(screen.getByLabelText('Nouveau mot de passe').hasAttribute('maxlength')).toBe(false);
  fireEvent.change(screen.getByLabelText('Confirmer le mot de passe'), { target: { value: password } });
  fireEvent.submit(document.querySelector('form'));
  await waitFor(() => expect(c.submit).toHaveBeenCalledWith('register', { email: 'alice@example.test', password }, undefined));
});
test('wrong login keeps A visible, cancel works and unavailable does not trap dialog', () => {
  const c = controller(), close = vi.fn();
  const account = { ...guest, status: 'member', account: { id: 'a', email: 'alice@example.test' }, error: { status: 401, code: 'authentication_failed' } };
  const { rerender } = render(<AccountPanel open account={account} controller={c} onClose={close} onProofUsed={vi.fn()} />);
  fireEvent.click(screen.getByRole('button', { name: 'Utiliser un autre compte' }));
  expect(screen.getByText('alice@example.test')).toBeTruthy();
  expect(screen.getByRole('alert').textContent).toMatch(/conservé/);
  fireEvent(document.querySelector('dialog'), new Event('cancel', { bubbles: false, cancelable: true }));
  expect(close).toHaveBeenCalledOnce();
  rerender(<AccountPanel open account={{ ...guest, status: 'unavailable', error: { status: 503 } }} controller={c} onClose={close} onProofUsed={vi.fn()} />);
  expect(screen.getByRole('button', { name: 'Se connecter' }).disabled).toBe(true);
  expect(screen.getByRole('button', { name: 'Fermer le compte' }).disabled).toBe(false);
});

test('definitive invalid proof is discarded and proof form cannot be resubmitted', async () => {
  const action = { kind: 'confirm', proof: 'b'.repeat(43) };
  const c = { ...controller(), submit: vi.fn(async () => false), getSnapshot: () => ({ error: { code: 'invalid_proof' } }) };
  render(<AccountPanel open action={action} account={guest} controller={c} onClose={() => clearAccountAction(action)} onProofUsed={() => clearAccountAction(action)} />);
  fireEvent.click(screen.getByRole('button', { name: 'Confirmer mon adresse' }));
  await waitFor(() => expect(action.proof).toBeNull());
  expect(screen.queryByRole('button', { name: 'Confirmer mon adresse' })).toBeNull();
});

test('closing clears the shared initial proof envelope without submitting it', () => {
  const action = { kind: 'reset', proof: 'c'.repeat(43) }, c = controller();
  render(<AccountPanel open action={action} account={guest} controller={c} onClose={() => clearAccountAction(action)} onProofUsed={vi.fn()} />);
  fireEvent.click(screen.getByRole('button', { name: 'Fermer le compte' }));
  expect(action.proof).toBeNull();
  expect(c.submit).not.toHaveBeenCalled();
});
