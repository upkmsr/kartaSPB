import type { MapObject } from '../../domain/mapObject';
import point from './point.json';

const demoObject: MapObject = {
  ...point,
  type: 'Feature',
  geometry: { ...point.geometry, type: 'Point' },
};

export const demoObjects: MapObject[] = [demoObject];
