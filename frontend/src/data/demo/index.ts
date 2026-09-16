import type { MapObject } from '../../domain/mapObject';
import point from './point.json';

const demoObject: MapObject = {
  id: point.id,
  name: point.properties.name,
  categoryId: point.properties.category,
  description: point.properties.description,
  properties: { demo: true },
  geometry: { ...point.geometry, type: 'Point' },
};

export const demoObjects: MapObject[] = [demoObject];
