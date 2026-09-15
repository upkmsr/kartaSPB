import type { Feature, Point } from 'geojson';

export interface ObjectProperties {
  id: string;
  name: string;
  category: string;
  description: string;
}

// Application data uses GeoJSON, with no dependency on MapLibre types.
export type MapObject = Feature<Point, ObjectProperties> & { id: string };
export type SelectedObject = MapObject | null;
