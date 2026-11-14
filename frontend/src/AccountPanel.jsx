import { useEffect, useRef, useState } from 'react';
import { asciiEmailError, newPasswordError } from './accountBootstrap.js';
import './account.css';

const TITLES = { login: 'Se connecter', register: 'Créer un compte', resend: 'Renvoyer la confirmation', forgot: 'Mot de passe oublié', confirm: 'Confirmer mon adresse', reset: 'Choisir un nouveau mot de passe', invalid: 'Lien invalide', member: 'Mon compte' };
function errorMessage(error, mode) {
  if (error.code === 'context_changed') return 'Le compte actif a changé. Vérifiez le compte affiché puis recommencez votre action.';
  if (error.code === 'invalid_proof') return 'Ce lien est invalide, expiré ou déjà utilisé. Demandez un nouveau message.';
  if (error.code === 'invalid_password') return 'Choisissez un mot de passe moins courant, de 15 à 128 caractères Unicode et au plus 512 octets UTF-8.';
  if (error.status === 401 && mode === 'login') return 'Email ou mot de passe incorrect. Le compte déjà connecté est conservé.';
  if (error.status === 403) return 'Le contexte de la demande a changé ou la demande a été refusée. Actualisez le compte puis recommencez explicitement.';
  if (error.status === 429) return 'Trop de demandes. Patientez avant de réessayer.';
  if (error.status === 400) return 'Vérifiez les champs de votre demande.';
  if (error.status === 503) return 'Les comptes sont temporairement indisponibles. Vous pouvez continuer à explorer les courses.';
  return 'La demande n’a pas pu être confirmée. Vérifiez votre connexion puis actualisez le compte ; une action peut avoir déjà été traitée. Aucun nouvel essai automatique.';
}

function AccountForm({ mode, proof, account, controller, onProofUsed }) {
  const [email, setEmail] = useState(''), [password, setPassword] = useState(''), [confirmation, setConfirmation] = useState('');
  const [validation, setValidation] = useState(null);
  const hasEmail = ['login', 'register', 'resend', 'forgot'].includes(mode);
  const hasPassword = ['login', 'register', 'reset'].includes(mode), isNew = ['register', 'reset'].includes(mode);
  const unavailable = account.status === 'unknown' || account.status === 'unavailable';
  async function submit(event) {
    event.preventDefault();
    controller.clearFeedback();
    const form = event.currentTarget;
    let error = null;
    if (hasEmail && !email) error = { field: 'email', text: 'Indiquez votre adresse email.' };
    else if (hasEmail && mode !== 'login' && asciiEmailError(email)) error = { field: 'email', text: asciiEmailError(email) };
    else if (hasPassword && !password) error = { field: 'password', text: 'Indiquez votre mot de passe.' };
    else if (isNew && newPasswordError(password)) error = { field: 'password', text: newPasswordError(password) };
    else if (isNew && confirmation !== password) error = { field: 'confirmation', text: 'Les deux mots de passe doivent être identiques, espaces compris.' };
    setValidation(error);
    if (error) { form.elements.namedItem(error.field)?.focus(); return; }
    const fields = { ...(hasEmail ? { email } : {}), ...(mode === 'login' || mode === 'register' ? { password } : {}), ...(mode === 'reset' ? { new_password: password } : {}) };
    const success = await controller.submit(mode, fields, proof);
    if (success) { setPassword(''); setConfirmation(''); if (mode === 'confirm' || mode === 'reset') onProofUsed(); }
    else if (controller.getSnapshot?.().error?.code === 'invalid_proof') onProofUsed();
  }
  return <form className="account-form" noValidate onSubmit={submit} aria-busy={account.busy}>
    {hasEmail && <label htmlFor="account-email">Adresse email<input id="account-email" data-account-focus name="email" type="text" inputMode="email" autoComplete={mode === 'login' ? 'username' : 'email'} value={email} onChange={event => setEmail(event.target.value)} aria-invalid={validation?.field === 'email'} aria-describedby={mode === 'login' ? 'account-validation' : 'account-email-hint account-validation'} required /></label>}
    {hasEmail && mode !== 'login' && <p id="account-email-hint" className="hint">Cette demande prend en charge les adresses email ASCII. Aucune vérification de livraison n’est présumée.</p>}
    {hasPassword && <label htmlFor="account-password">{isNew ? 'Nouveau mot de passe' : 'Mot de passe'}<input id="account-password" data-account-focus={!hasEmail || undefined} name="password" type="password" autoComplete={isNew ? 'new-password' : 'current-password'} value={password} onChange={event => setPassword(event.target.value)} aria-invalid={validation?.field === 'password'} aria-describedby={isNew ? 'account-password-policy account-validation' : 'account-validation'} required /></label>}
    {isNew && <><p id="account-password-policy" className="hint">15 à 128 caractères Unicode, au plus 512 octets UTF-8. Les espaces sont conservés. Évitez les mots de passe courants.</p><label htmlFor="account-confirmation">Confirmer le mot de passe<input id="account-confirmation" name="confirmation" type="password" autoComplete="new-password" value={confirmation} onChange={event => setConfirmation(event.target.value)} aria-invalid={validation?.field === 'confirmation'} aria-describedby="account-validation" required /></label></>}
    {mode === 'register' && <p className="hint">Un lien permet de confirmer votre adresse avant toute connexion. La création de compte ne vous connecte pas automatiquement.</p>}
    {mode === 'confirm' && <p>Confirmez explicitement votre adresse. L’ouverture du lien seule n’effectue aucune confirmation et ne vous connecte pas.</p>}
    {mode === 'reset' && <p>Choisissez votre nouveau mot de passe. Cette action révoque les sessions du compte concerné, sans vous connecter automatiquement.</p>}
    <p id="account-validation" className="account-error" role={validation ? 'alert' : undefined}>{validation?.text}</p>
    <button className="account-primary" type="submit" disabled={account.busy || unavailable}>{account.busy ? 'Demande en cours…' : TITLES[mode]}</button>
  </form>;
}

function Contents({ action, account, controller, onProofUsed }) {
  const content = useRef(null);
  const [mode, setMode] = useState(action?.kind || (account.account ? 'member' : 'login'));
  useEffect(() => {
    const owner = content.current?.closest('dialog');
    if (owner?.open && !owner.contains(document.activeElement)) content.current.querySelector('[data-account-focus],button')?.focus();
  }, [mode]);
  const navigate = next => { controller.clearFeedback(); setMode(next); };
  const finishProof = () => { setMode(account.account ? 'member' : 'login'); onProofUsed(); };
  return <div ref={content}>
    <p className="eyebrow">Votre compte RaceAtlas</p><h2 id="account-title">{TITLES[mode]}</h2>
    <div className="account-context" aria-live="polite">{account.status === 'unknown' ? 'Vérification du compte…' : account.account ? <>Connecté comme <strong>{account.account.email}</strong>.</> : account.status === 'unavailable' ? 'Comptes indisponibles pour le moment.' : 'Vous n’êtes pas connecté.'}</div>
    {account.message && <p className="account-message" role="status">{account.message}</p>}
    {account.error && <div><p className="account-error" role="alert">{errorMessage(account.error, mode)}</p><button className="text-button" disabled={account.busy} onClick={() => controller.refresh()}>Actualiser le compte</button></div>}
    {mode === 'invalid' ? <p role="alert">Ce lien ne contient pas une preuve valide. Ouvrez un lien complet récent ou demandez un nouveau message.</p> : mode === 'member' ? <p>Votre connexion est active. Fermez ce panneau pour continuer à explorer les courses.</p> : <AccountForm key={mode} mode={mode} proof={mode === action?.kind ? action.proof : undefined} account={account} controller={controller} onProofUsed={finishProof} />}
    <nav className="account-navigation" aria-label="Actions du compte">
      {mode !== 'login' && <button className="text-button" disabled={account.busy} onClick={() => navigate('login')}>{account.account ? 'Utiliser un autre compte' : 'Déjà un compte ? Se connecter'}</button>}
      {mode !== 'register' && <button className="text-button" disabled={account.busy} onClick={() => navigate('register')}>Créer un compte</button>}
      {mode !== 'resend' && <button className="text-button" disabled={account.busy} onClick={() => navigate('resend')}>Renvoyer la confirmation</button>}
      {mode !== 'forgot' && <button className="text-button" disabled={account.busy} onClick={() => navigate('forgot')}>Mot de passe oublié</button>}
    </nav>
  </div>;
}

export function AccountPanel({ open, action, account, controller, onClose, onProofUsed }) {
  const dialog = useRef(null);
  useEffect(() => {
    if (open) {
      if (!dialog.current.open) dialog.current.showModal();
      if (!dialog.current.contains(document.activeElement)) dialog.current.querySelector('button')?.focus();
    } else if (dialog.current.open) dialog.current.close();
  }, [open, account.account?.id, action?.kind]);
  return <dialog ref={dialog} className="account-dialog" aria-labelledby="account-title" onCancel={event => { event.preventDefault(); onClose(); }} onClose={() => { if (open) onClose(); }}>
    {open && <><button className="account-close text-button" aria-label="Fermer le compte" onClick={onClose}>Fermer ✕</button><Contents key={action?.kind || account.account?.id || 'guest'} action={action} account={account} controller={controller} onProofUsed={onProofUsed} /></>}
  </dialog>;
}
