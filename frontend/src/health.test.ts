import { afterEach, expect, it, vi } from 'vitest';
import { fetchHealth } from './health';

afterEach(() => vi.unstubAllGlobals());
it('accepts only a successful readiness response', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{"status":"ok"}')));
  expect(await fetchHealth()).toBe(true);
});
it('reports unavailable backend', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{"status":"unavailable"}', { status: 503 })));
  expect(await fetchHealth()).toBe(false);
});
it('does not treat unexpected data as ready', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}')));
  expect(await fetchHealth()).toBe(false);
});
it('propagates network failure for the UI to handle', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));
  await expect(fetchHealth()).rejects.toThrow('offline');
});
