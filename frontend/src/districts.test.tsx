// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { DistrictPanel } from './components/DistrictPanel';
import { districts } from './data/districts';
import { toggleDistrict } from './domain/district';
import { initialLayerRegistry, orderedLayers, updateLayer } from './domain/layers';

afterEach(cleanup);

it('contains 18 real districts with stable source IDs and supported geometries', () => {
  expect(districts).toHaveLength(18);
  expect(new Set(districts.map((district) => district.id)).size).toBe(18);
  for (const district of districts) {
    expect(district.id).toMatch(/^district-osm-relation-\d+$/);
    expect(district.properties.source).toBe('OpenStreetMap');
    expect(['Polygon', 'MultiPolygon']).toContain(district.geometry.type);
  }
});

it('toggles one, multiple and empty district selections', () => {
  const first = districts[0].id;
  const second = districts[1].id;
  expect(toggleDistrict([], first)).toEqual([first]);
  expect(toggleDistrict([first], second)).toEqual([first, second]);
  expect(toggleDistrict([first], first)).toEqual([]);
});

it('renders labeled district controls that select and clear districts', () => {
  const onToggle = vi.fn();
  const onClear = vi.fn();
  render(<DistrictPanel
    districts={districts}
    selectedIds={[districts[0].id]}
    layers={initialLayerRegistry}
    onDistrictToggle={onToggle}
    onClearDistricts={onClear}
    onLayerVisibilityChange={vi.fn()}
    onLayerOpacityChange={vi.fn()}
  />);
  expect(screen.getAllByRole('checkbox')).toHaveLength(31);
  const district = screen.getByRole('checkbox', { name: districts[1].properties.name });
  fireEvent.click(district);
  expect(onToggle).toHaveBeenCalledWith(districts[1].id);
  fireEvent.click(screen.getByRole('button', { name: 'Сбросить' }));
  expect(onClear).toHaveBeenCalledTimes(1);
});

it('updates registry visibility and bounded opacity with stable ordered IDs', () => {
  const hidden = updateLayer(initialLayerRegistry, 'districts', { visible: false });
  const transparent = updateLayer(hidden, 'districts', { opacity: -1 });
  const opaque = updateLayer(transparent, 'districts', { opacity: 2 });
  expect(hidden.districts.visible).toBe(false);
  expect(transparent.districts.opacity).toBe(0);
  expect(opaque.districts.opacity).toBe(1);
  expect(orderedLayers(initialLayerRegistry).map((layer) => layer.id)).toEqual([
    'districts', 'demo-object', 'nature-green', 'nature-water',
    'metro-lines', 'metro-stations', 'metro-entrances',
    'transport-bus', 'transport-tram', 'transport-trolleybus', 'transport-stops',
    'schools', 'school-catchments',
  ]);
});
