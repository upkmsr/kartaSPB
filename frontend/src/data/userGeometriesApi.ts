import type { Geometry } from 'geojson';
import type { UserGeometry } from '../domain/userGeometry';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) throw new Error(`User geometries API HTTP ${response.status}`);
  return response.status === 204 ? undefined as T : response.json() as Promise<T>;
}

const base = '/api/user/geometries';
export const userGeometriesApi = {
  list: async () => {
    const items = await request<unknown>(base);
    if (!Array.isArray(items)) throw new Error('Invalid user geometry list');
    return items as UserGeometry[];
  },
  create: (name: string, description: string, geometry: Geometry) => request<UserGeometry>(base, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description, geometry }),
  }),
  update: (id: string, name: string, description: string, geometry: Geometry) => request<UserGeometry>(`${base}/${encodeURIComponent(id)}`, {
    method: 'PATCH', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description, geometry }),
  }),
  remove: (id: string) => request<void>(`${base}/${encodeURIComponent(id)}`, { method: 'DELETE' }),
};
