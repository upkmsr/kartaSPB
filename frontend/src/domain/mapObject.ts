import type { FeatureCollection, Geometry } from 'geojson';

export interface MapObject {
  id: string;
  name: string;
  categoryId: string;
  description: string;
  geometry: Geometry;
  properties: Record<string, unknown>;
  source?: string | null;
  sourceId?: string | null;
}

// Application data uses GeoJSON, with no dependency on MapLibre types.
export type SelectedObject = MapObject | null;

export interface Category {
  id: string;
  name: string;
  description: string;
  color: string;
  defaultVisible: boolean;
}

export function toGeoJSON(objects: readonly MapObject[]): FeatureCollection {
  return { type: 'FeatureCollection', features: objects.map((object) => ({
    type: 'Feature', id: object.id, geometry: object.geometry,
    properties: { ...object.properties, id: object.id, name: object.name, categoryId: object.categoryId },
  })) };
}
