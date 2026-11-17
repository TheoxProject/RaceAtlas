import { SPORTS, TYPES } from './catalog.js';
import { formatDate } from './RaceDetails.jsx';
import { opaqueSegment } from './season.js';

const BASE = '/api/v1/me/notifications';
const cursorValid = value => typeof value === 'string' && value.length <= 1024 && /^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]{43}$/.test(value);
const invalid = () => Object.assign(new Error('Réponse de notifications indisponible.'), { code: 'invalid_response' });
export const notificationKey = item => JSON.stringify([item.change_id, item.scope_id]);
export function notificationPath(cursor = null) {
  if (cursor !== null && !cursorValid(cursor)) throw invalid();
  const query = new URLSearchParams({ limit: '50' });
  if (cursor !== null) query.set('cursor', cursor);
  return BASE + '?' + query;
}
export function allowedNotificationPath(path) {
  if (typeof path !== 'string' || !path.startsWith(BASE + '?')) return false;
  const parts = path.split('?');
  if (parts.length !== 2) return false;
  const query = new URLSearchParams(parts[1]);
  if (query.get('limit') !== '50' || [...query.keys()].some(key => !['limit', 'cursor'].includes(key) || query.getAll(key).length !== 1)) return false;
  try { return path === notificationPath(query.get('cursor')); } catch { return false; }
}
export function notificationPage(data) {
  try {
    if (!data || !Array.isArray(data.items) || data.items.length > 50 || !Number.isSafeInteger(data.unread_count) || data.unread_count < 0 || typeof data.has_more !== 'boolean' || (data.has_more ? !cursorValid(data.next_cursor) : data.next_cursor !== null)) throw invalid();
    const text = new TextEncoder();
    function bounded(value) {
      if (typeof value === 'string' && text.encode(value).length > 16384) throw invalid();
      if (Array.isArray(value)) value.forEach(bounded);
      else if (value && typeof value === 'object') Object.values(value).forEach(bounded);
    }
    bounded(data);
    if (text.encode(JSON.stringify(data)).length > 2 * 1024 * 1024) throw invalid();
    const keys = new Set();
    for (const item of data.items) {
      opaqueSegment(item.change_id); opaqueSegment(item.scope_id);
      if (!['business', 'presence'].includes(item.kind) || typeof item.created_at !== 'string' || !Number.isFinite(Date.parse(item.created_at)) || (item.read_at !== null && (typeof item.read_at !== 'string' || !Number.isFinite(Date.parse(item.read_at)))) || !item.delta?.before || typeof item.delta.before !== 'object' || !item.delta?.after || typeof item.delta.after !== 'object' || Array.isArray(item.delta.before) || Array.isArray(item.delta.after) || item.entry?.scope_id !== item.scope_id || item.entry?.scope?.id !== item.scope_id || typeof item.entry?.race?.name !== 'string' || typeof item.provenance?.source_url !== 'string') throw invalid();
      if (keys.has(notificationKey(item))) throw invalid();
      keys.add(notificationKey(item));
    }
    return { items: data.items, unreadCount: data.unread_count, nextCursor: data.next_cursor, hasMore: data.has_more };
  } catch { throw invalid(); }
}

const normalized = value => Array.isArray(value) ? value.map(normalized) : value && typeof value === 'object' ? Object.fromEntries(Object.keys(value).sort().map(key => [key, normalized(value[key])])) : value;
const same = (a, b) => JSON.stringify(normalized(a)) === JSON.stringify(normalized(b));
const plain = value => typeof value === 'string' && value ? value : 'Non précisé';
const status = { scheduled: 'Programmée selon la source', postponed: 'Reportée selon la source', cancelled: 'Annulée selon la source', unknown: 'Statut à vérifier' };
const presence = { present: 'Présente dans la source', to_verify: 'Présence à vérifier (absence ne signifie pas annulation)' };
const labels = { name: 'Nom', start_date: 'Début', end_date: 'Fin', status: 'Statut publié', source_presence: 'Présence source', discipline: 'Discipline', types: 'Type', organizer: 'Organisateur', commune: 'Commune', raw_label: 'Libellé de cette liste', eligibility: 'Conditions publiées', competition: 'Regroupement' };
function conditions(value) {
  if (!value || typeof value !== 'object') return 'Conditions non précisées';
  const lines = [({ confirmed: 'Conditions confirmées par la source', unknown: 'Conditions non confirmées', ambiguous: 'Conditions ambiguës, à vérifier' })[value.status] || 'Conditions à vérifier'];
  if (value.identity_status !== 'verified') lines.push('Identité de liste à vérifier');
  for (const rule of Array.isArray(value.rules) ? value.rules : []) {
    if (!rule || typeof rule !== 'object') continue;
    const r = rule.restrictions || {};
    const category = (Array.isArray(rule.categories) ? rule.categories : []).filter(code => typeof code === 'string').map(code => code.replaceAll('_', ' ')).join(' · ') || 'Catégories non précisées';
    const parts = [plain(rule.raw_label), category];
    if (r.sex !== 'any') parts.push(({ men: 'Hommes', women: 'Femmes', unknown: 'Sexe non précisé' })[r.sex] || 'Sexe non précisé');
    if (r.min_age != null || r.max_age != null) parts.push(`Âge : ${r.min_age ?? 'non précisé'} à ${r.max_age ?? 'non précisé'} ans${r.age_reference === 'season_end' ? ` en fin de saison ${r.age_season ?? ''}` : r.age_reference === 'event_date' ? ' le jour de la course' : ' · référence à vérifier'}`);
    if (Array.isArray(r.engagers) && r.engagers.length) parts.push('Engagement : ' + r.engagers.join(', '));
    if (r.other_text) parts.push(r.other_text);
    lines.push(parts.join(' · '));
  }
  return lines.join('\n');
}
function describe(key, value) {
  if (['start_date', 'end_date'].includes(key)) return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(value)) ? formatDate(value) : 'Date à vérifier';
  if (key === 'status') return status[value] || 'Statut à vérifier';
  if (key === 'source_presence') return presence[value] || 'Présence à vérifier';
  if (key === 'discipline') return SPORTS[value] || 'Discipline non précisée';
  if (key === 'types') return Array.isArray(value) ? value.map(code => TYPES[code]?.[1] || 'Type à vérifier').join(', ') || 'Non précisé' : 'Non précisé';
  if (key === 'commune') return value ? [plain(value.name), value.department && `Département ${value.department}`, value.insee_code && `INSEE ${value.insee_code}`].filter(Boolean).join(' · ') : 'Commune à préciser';
  if (key === 'eligibility') return conditions(value);
  return plain(value);
}
export function notificationChanges(delta) {
  return Object.keys(labels).filter(key => !same(delta?.before?.[key], delta?.after?.[key])).map(key => key === 'competition' ? { label: labels[key], text: 'Le regroupement publié a changé. Consultez la source pour les épreuves concernées.' } : { label: labels[key], before: describe(key, delta.before[key]), after: describe(key, delta.after[key]) });
}
export function observedDate(value) {
  const date = new Date(value);
  return Number.isFinite(+date) ? date.toLocaleString('fr-FR', { timeZone: 'Europe/Paris', dateStyle: 'medium', timeStyle: 'short' }) : 'Date à vérifier';
}
export function sourceLink(value) {
  try { const url = new URL(value); return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password ? url.href : null; } catch { return null; }
}
