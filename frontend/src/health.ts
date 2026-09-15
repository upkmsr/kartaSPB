export async function fetchHealth(signal?: AbortSignal): Promise<boolean> {
  const response = await fetch('/api/health/ready', { signal });
  if (!response.ok) return false;
  const body: unknown = await response.json();
  return typeof body === 'object' && body !== null && 'status' in body && body.status === 'ok';
}
