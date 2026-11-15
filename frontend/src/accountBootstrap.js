// Called once by main, before React/StrictMode effects. Proofs stay only in RAM.
export function captureAccountAction(location, history) {
  const fragment = location.hash;
  if (!fragment) return null;
  history.replaceState(history.state, '', `${location.pathname}${location.search}`);
  const match = /^#(confirm-email|reset-password)=([A-Za-z0-9_-]{43})$/.exec(fragment);
  return match ? { kind: match[1] === 'confirm-email' ? 'confirm' : 'reset', proof: match[2] } : { kind: 'invalid' };
}

export function newPasswordError(value) {
  const characters = Array.from(value);
  if (characters.some(character => { const code = character.codePointAt(0); return code >= 0xD800 && code <= 0xDFFF; })) return 'Le mot de passe contient un caractère Unicode invalide.';
  if (characters.length < 15 || characters.length > 128 || new TextEncoder().encode(value).length > 512) return 'Utilisez 15 à 128 caractères Unicode, au plus 512 octets UTF-8. Les espaces comptent.';
  return null;
}

export function asciiEmailError(value) {
  const normalized = value.trim().toLowerCase();
  const parts = normalized.split('@');
  if (normalized.length < 3 || normalized.length > 254 || parts.length !== 2 || parts[0].length > 64 || !/^[a-z0-9.!#$%&'*+/=?^_`{|}~-]+$/.test(parts[0]) || !parts[1].split('.').every(label => /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/.test(label)) || parts[1].length > 253 || !parts[1].includes('.')) return 'Indiquez une adresse email ASCII valide. Les adresses internationales ne sont pas prises en charge pour cette demande.';
  return null;
}

// The same envelope can remain referenced by main/React props; erase ITS proof too.
// This releases our references, not a promise of JS string or browser-buffer zeroisation.
export function clearAccountAction(action) {
  if (action && Object.hasOwn(action, 'proof')) action.proof = null;
}
