import type { Feature, MultiPolygon, Polygon } from 'geojson';

export type DistrictId = `district-osm-relation-${number}`;

export interface DistrictProperties {
  id: DistrictId;
  name: string;
  source: 'OpenStreetMap';
  sourceId: `relation/${number}`;
}

export type District = Feature<Polygon | MultiPolygon, DistrictProperties> & {
  id: DistrictId;
};

export function toggleDistrict(
  selectedIds: readonly DistrictId[],
  id: DistrictId,
): DistrictId[] {
  return selectedIds.includes(id)
    ? selectedIds.filter((selectedId) => selectedId !== id)
    : [...selectedIds, id];
}
