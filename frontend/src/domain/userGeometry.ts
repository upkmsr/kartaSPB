import type { FeatureCollection, Geometry, Position } from 'geojson';

export type UserGeometryType = 'Point' | 'LineString' | 'Polygon';

export interface UserGeometry {
  id: string;
  name: string;
  description: string;
  geometryType: UserGeometryType;
  geometry: Geometry;
  createdAt: string;
  updatedAt: string;
}

export interface DrawingDraft {
  type: UserGeometryType;
  vertices: Position[];
  name: string;
  description: string;
  editingId?: string;
  selectedVertex?: number;
}

export function verticesFromGeometry(geometry: Geometry): Position[] {
  if (geometry.type === 'Point') return [geometry.coordinates];
  if (geometry.type === 'LineString') return [...geometry.coordinates];
  if (geometry.type === 'Polygon') return geometry.coordinates[0]?.slice(0, -1) ?? [];
  return [];
}

export function addDrawingPoint(draft: DrawingDraft, point: Position): DrawingDraft {
  if (draft.selectedVertex !== undefined) {
    const vertices = [...draft.vertices];
    vertices[draft.selectedVertex] = point;
    return { ...draft, vertices, selectedVertex: undefined };
  }
  if (draft.type === 'Point') return { ...draft, vertices: [point] };
  if (draft.vertices.length >= 1000) return draft;
  return { ...draft, vertices: [...draft.vertices, point] };
}

export function draftGeometry(draft: DrawingDraft): Geometry | null {
  const points = draft.vertices;
  if (draft.type === 'Point') return points.length === 1 ? { type: 'Point', coordinates: points[0] } : null;
  if (draft.type === 'LineString') return points.length >= 2 ? { type: 'LineString', coordinates: points } : null;
  return points.length >= 3 ? { type: 'Polygon', coordinates: [[...points, points[0]]] } : null;
}

export function toUserGeoJSON(items: readonly UserGeometry[]): FeatureCollection {
  return { type: 'FeatureCollection', features: items.map((item) => ({
    type: 'Feature', id: item.id, geometry: item.geometry,
    properties: { id: item.id, name: item.name, geometryType: item.geometryType },
  })) };
}

export function draftPreview(draft: DrawingDraft | null): FeatureCollection {
  if (!draft) return { type: 'FeatureCollection', features: [] };
  const points = draft.vertices;
  const features: FeatureCollection['features'] = points.map((coordinates, index) => ({
    type: 'Feature', geometry: { type: 'Point', coordinates },
    properties: { vertexIndex: index, selected: draft.selectedVertex === index },
  }));
  if (points.length >= 2) features.unshift({
    type: 'Feature', geometry: draft.type === 'Polygon' && points.length >= 3
      ? { type: 'Polygon', coordinates: [[...points, points[0]]] }
      : { type: 'LineString', coordinates: points },
    properties: { preview: true },
  });
  return { type: 'FeatureCollection', features };
}
