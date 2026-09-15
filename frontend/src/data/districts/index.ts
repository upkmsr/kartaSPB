import rawDistricts from './spb-districts.json';
import type { District } from '../../domain/district';

export const districts = rawDistricts.features as District[];

export const districtFeatureCollection = {
  type: 'FeatureCollection' as const,
  features: districts,
};
