import { expect, test, vi } from 'vitest';
import { MAX_CALENDAR_BYTES, readCalendar, triggerCalendarDownload } from './calendarDownload.js';

function response(size, { status = 200, type = 'text/calendar', announced } = {}) {
  let sent = false;
  const cancel = vi.fn();
  const body = new ReadableStream({ pull(controller) { if (!sent) { sent = true; controller.enqueue(new Uint8Array(size)); } else controller.close(); }, cancel });
  return { response: new Response(body, { status, headers: { 'Content-Type': type, ...(announced ? { 'Content-Length': announced } : {}) } }), cancel };
}
test('actual stream limit accepts exactly 2 MiB and refuses excess despite small announced length', async () => {
  expect((await readCalendar(response(MAX_CALENDAR_BYTES).response, () => {})).size).toBe(MAX_CALENDAR_BYTES);
  const large = response(MAX_CALENDAR_BYTES + 1, { announced: '1' });
  await expect(readCalendar(large.response, () => {})).rejects.toMatchObject({ code: 'calendar_size' });
  expect(large.cancel).toHaveBeenCalledOnce();
});
test.each([{ status: 206 }, { type: 'application/json' }])('refuses partial or wrong MIME before download: %j', async options => {
  await expect(readCalendar(response(10, options).response, () => {})).rejects.toMatchObject({ code: 'calendar_format' });
});
test('context rejected after awaited chunk cancels stream', async () => {
  const source = response(10);
  await expect(readCalendar(source.response, () => { throw new Error('stale'); })).rejects.toThrow('stale');
  expect(source.cancel).toHaveBeenCalledOnce();
});
test('oversized announcement and empty stream cannot produce a download', async () => {
  const announced = response(1, { announced: String(MAX_CALENDAR_BYTES + 1) });
  await expect(readCalendar(announced.response, () => {})).rejects.toMatchObject({ code: 'calendar_size' });
  expect(announced.cancel).toHaveBeenCalledOnce();
  await expect(readCalendar(response(0).response, () => {})).rejects.toMatchObject({ code: 'calendar_format' });
});
function browser() {
  const anchor = { click: vi.fn(), remove: vi.fn() }, urls = { createObjectURL: vi.fn(() => 'blob:synthetic'), revokeObjectURL: vi.fn() };
  return { anchor, urls, document: { createElement: () => anchor, body: { append: vi.fn() } }, schedule: vi.fn(() => 1), unschedule: vi.fn() };
}
test('resolved result cannot download after switch/ABA; last check also covers URL creation', () => {
  const env = browser(), result = { blob: new Blob(['x']), context: { epoch: 1 } };
  expect(triggerCalendarDownload(result, () => false, env)).toBe(false);
  expect(env.urls.createObjectURL).not.toHaveBeenCalled();
  let valid = true;
  env.urls.createObjectURL.mockImplementation(() => { valid = false; return 'blob:synthetic'; });
  expect(triggerCalendarDownload(result, () => valid, env)).toBe(false);
  expect(env.anchor.click).not.toHaveBeenCalled();
  expect(env.urls.revokeObjectURL).toHaveBeenCalledOnce();
});
test('successful download is named, temporary and disposed only once', () => {
  const env = browser();
  expect(triggerCalendarDownload({ blob: new Blob(['x']), context: {} }, () => true, env)).toBe(true);
  expect(env.anchor.download).toBe('raceatlas-planning.ics');
  expect(env.anchor.click).toHaveBeenCalledOnce();
  const dispose = env.schedule.mock.calls[0][0]; dispose(); dispose();
  expect(env.urls.revokeObjectURL).toHaveBeenCalledOnce();
  expect(env.anchor.remove).toHaveBeenCalledOnce();
});
