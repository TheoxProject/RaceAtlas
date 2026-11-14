export const SAVED_LABELS = { interested: 'Intéressé', planned: 'Prévue', registered: 'Inscrit', completed: 'Terminée' };
export function opaqueSegment(value) {
  if (typeof value !== 'string' || Array.from(value).length < 1 || Array.from(value).length > 64 || value.includes('\0') || Array.from(value).some(c => c.codePointAt(0) >= 0xD800 && c.codePointAt(0) <= 0xDFFF)) throw new Error('Identifiant indisponible.');
  return encodeURIComponent(value);
}
export function seasonError(error) {
  if (error?.code === 'context_changed') return 'Le compte actif a changé. Vérifiez-le puis actualisez votre saison.';
  if (error?.status === 401) return 'Votre connexion doit être vérifiée. Connectez-vous à nouveau.';
  if (error?.status === 403) return 'Le contexte a changé ou la demande a été refusée. Actualisez votre saison avant une nouvelle action.';
  if (error?.status === 404) return 'Cette sauvegarde ou cette liste n’est plus disponible. Actualisez votre saison.';
  if (error?.status === 413) return 'La sélection dépasse une limite du service. Aucune liste tronquée n’est affichée.';
  if (error?.status === 429) return 'Trop de demandes. Patientez puis réessayez explicitement.';
  return 'La demande n’a pas pu être confirmée. Une modification peut avoir déjà été traitée : actualisez votre saison pour vérifier, sans la renvoyer automatiquement.';
}
