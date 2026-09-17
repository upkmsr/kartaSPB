import type { MapObject } from './mapObject';

export interface GeocodingResult {
  id: string;
  label: string;
  coordinates: [number, number];
  type: string;
  provider: string;
}

export interface GeocoderProvider {
  search(query: string, signal?: AbortSignal): Promise<GeocodingResult[]>;
}

async function read<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal });
  if (!response.ok) throw new Error(`Search HTTP ${response.status}`);
  return response.json() as Promise<T>;
}

export const projectSearch = (query: string, signal?: AbortSignal) =>
  read<MapObject[]>(`/api/search/objects?q=${encodeURIComponent(query)}`, signal);

export const geocoderProvider: GeocoderProvider = {
  search: (query, signal) => read<GeocodingResult[]>(
    `/api/search/geocode?q=${encodeURIComponent(query)}`, signal),
};

export interface MapTarget {
  coordinates: [number, number];
  token: number;
  showMarker: boolean;
}

export function geometryCenter(object: Pick<MapObject, 'geometry'>): [number, number] {
  const points: number[][] = [];
  const visit = (coordinates: unknown): void => {
    if (Array.isArray(coordinates) && coordinates.length >= 2 &&
      typeof coordinates[0] === 'number' && typeof coordinates[1] === 'number') {
      points.push(coordinates as number[]);
    } else if (Array.isArray(coordinates)) coordinates.forEach(visit);
  };
  if ('coordinates' in object.geometry) visit(object.geometry.coordinates);
  if (!points.length) return [30.3158, 59.9391];
  const longitudes = points.map((point) => point[0]);
  const latitudes = points.map((point) => point[1]);
  return [(Math.min(...longitudes) + Math.max(...longitudes)) / 2,
    (Math.min(...latitudes) + Math.max(...latitudes)) / 2];
}
