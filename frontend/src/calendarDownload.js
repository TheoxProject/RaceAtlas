export const MAX_CALENDAR_BYTES = 2 * 1024 * 1024;
export class CalendarDownloadError extends Error {
  constructor(code) { super('Le téléchargement n’a pas été confirmé.'); this.code = code; this.status = 0; }
}

export async function readCalendar(response, checkCurrent) {
  const mime = (response.headers.get('Content-Type') || '').split(';')[0].trim().toLowerCase();
  if (response.status !== 200 || mime !== 'text/calendar' || !response.body?.getReader) {
    await response.body?.cancel();
    throw new CalendarDownloadError('calendar_format');
  }
  const announced = response.headers.get('Content-Length');
  if (announced && /^\d+$/.test(announced) && Number(announced) > MAX_CALENDAR_BYTES) {
    await response.body.cancel();
    throw new CalendarDownloadError('calendar_size');
  }
  const reader = response.body.getReader(), chunks = [];
  let total = 0, done = false;
  try {
    while (!done) {
      const next = await reader.read();
      checkCurrent();
      done = next.done;
      if (!done) {
        total += next.value.byteLength;
        if (total > MAX_CALENDAR_BYTES) throw new CalendarDownloadError('calendar_size');
        chunks.push(next.value);
      }
    }
    if (!total) throw new CalendarDownloadError('calendar_format');
    checkCurrent();
    return new Blob(chunks, { type: 'text/calendar;charset=utf-8' });
  } finally {
    if (!done) { try { await reader.cancel(); } catch { /* no raw stream errors */ } }
    reader.releaseLock();
  }
}

// No await between the last context check and click. Cleanup remains idempotent.
export function triggerCalendarDownload(result, isCurrent, environment = {}) {
  const doc = environment.document || globalThis.document, urls = environment.urls || globalThis.URL;
  const schedule = environment.schedule || globalThis.setTimeout, unschedule = environment.unschedule || globalThis.clearTimeout;
  let href, anchor, timer, disposed = false, clicked = false;
  const dispose = () => {
    if (disposed) return;
    disposed = true;
    if (timer !== undefined) unschedule(timer);
    anchor?.remove();
    if (href) urls.revokeObjectURL(href);
    environment.unregister?.(dispose);
  };
  try {
    if (!result || !isCurrent(result.context)) return false;
    href = urls.createObjectURL(result.blob);
    environment.register?.(dispose);
    if (!isCurrent(result.context)) return false;
    anchor = doc.createElement('a');
    anchor.href = href; anchor.download = 'raceatlas-planning.ics';
    doc.body.append(anchor);
    if (!isCurrent(result.context)) return false;
    anchor.click(); clicked = true;
    timer = schedule(dispose, 1000);
    return true;
  } finally { if (!clicked) dispose(); }
}
