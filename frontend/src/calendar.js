import { changePeriod, periodRange } from './catalog.js';

export const MIN_CALENDAR_YEAR = 1900;
export const MAX_CALENDAR_YEAR = 2200;
const DAY = 86400000;

function validMonth(year, month) {
  return Number.isInteger(year) && year >= MIN_CALENDAR_YEAR && year <= MAX_CALENDAR_YEAR && Number.isInteger(month) && month >= 1 && month <= 12;
}

export function selectCalendarMonth(period, year = period.year, month = period.month) {
  if (!validMonth(year, month)) return period;
  return changePeriod(period, { mode: 'month', year, month });
}

export function moveCalendarMonth(period, delta) {
  if (!validMonth(period.year, period.month) || !Number.isSafeInteger(delta)) return period;
  const index = period.year * 12 + period.month - 1 + delta;
  return selectCalendarMonth(period, Math.floor(index / 12), index % 12 + 1);
}

export function monthGrid(year, month) {
  if (!validMonth(year, month)) return [];
  const first = new Date(Date.UTC(year, month - 1, 1));
  const last = new Date(Date.UTC(year, month, 0));
  const start = +first - ((first.getUTCDay() + 6) % 7) * DAY;
  const end = +last + ((7 - last.getUTCDay()) % 7) * DAY;
  const days = [];
  for (let cursor = start; cursor <= end; cursor += DAY) {
    const date = new Date(cursor);
    days.push({ date: date.toISOString().slice(0, 10), day: date.getUTCDate(), inMonth: date.getUTCFullYear() === year && date.getUTCMonth() + 1 === month, items: [] });
  }
  return days;
}

export function projectCalendar(period, selection, { radius = false } = {}) {
  const days = monthGrid(period.year, period.month);
  if (!days.length) return { days, items: [], candidates: [], total: 0 };
  const range = periodRange({ ...period, mode: 'month' });
  const unique = new Map();
  for (const item of selection?.items || []) {
    if (item.race.start_date <= range.to && item.race.end_date >= range.from && !unique.has(item.race.id)) unique.set(item.race.id, item);
  }
  const excluded = new Set(radius ? selection?.unlocatedIds || [] : []);
  const items = [...unique.values()].filter(item => !excluded.has(item.race.id));
  const candidates = [...unique.values()].filter(item => excluded.has(item.race.id));
  return {
    days: days.map(day => ({ ...day, items: day.inMonth ? items.filter(item => item.race.start_date <= day.date && item.race.end_date >= day.date) : [] })),
    items,
    candidates,
    total: items.length,
  };
}
