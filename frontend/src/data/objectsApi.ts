import type { Category, MapObject } from '../domain/mapObject';

async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, { signal });
  if (!response.ok) throw new Error(`Project API HTTP ${response.status}`);
  return response.json() as Promise<T>;
}

export const objectsApi = {
  getObjects: (signal?: AbortSignal, categoryIds?: string[]) => get<MapObject[]>(
    `/api/objects${categoryIds ? `?category=${encodeURIComponent(categoryIds.join(','))}` : '?excludeCategory=medical-pharmacy&excludeCategoryPrefix=road-,noise-'}`, signal),
  getObject: (id: string, signal?: AbortSignal) => get<MapObject>(`/api/objects/${encodeURIComponent(id)}`, signal),
  getCategories: (signal?: AbortSignal) => get<Category[]>('/api/categories', signal),
};

export function getCategoryById(categories: readonly Category[], id: string): Category | undefined {
  return categories.find((category) => category.id === id);
}
