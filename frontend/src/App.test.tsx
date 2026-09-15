// @vitest-environment jsdom
import { StrictMode } from 'react';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { App } from './App';
import { MapView } from './components/MapView';
import { ObjectCard } from './components/ObjectCard';
import { mapConfig } from './config/map';
import { demoObjects } from './data/demo';
import rawPoint from './data/demo/point.json';

// Only mock the WebGL boundary. Real adapter, ID resolution, React state and card run.
const { maps, MockMap } = vi.hoisted(() => {
  interface ClickEvent { features?: { id?: string; properties?: { name: string } }[] }
  class MockMap {
    handlers = new globalThis.Map<string, (event: ClickEvent) => void>();
    addSource = vi.fn();
    addLayer = vi.fn();
    addControl = vi.fn();
    remove = vi.fn();
    resize = vi.fn();
    touchZoomRotate = { disableRotation: vi.fn() };
    getCanvas = () => ({ style: { cursor: '' } });
    constructor(public options: unknown) { maps.push(this); }
    on(event: string, layerOrHandler: string | ((event: ClickEvent) => void), handler?: (event: ClickEvent) => void) {
      const callback = typeof layerOrHandler === 'string' ? handler : layerOrHandler;
      if (callback) this.handlers.set(event, callback);
    }
    emit(event: string, data: ClickEvent = {}) { this.handlers.get(event)?.(data); }
  }
  const maps: MockMap[] = [];
  return { maps, MockMap };
});

vi.mock('maplibre-gl', () => ({
  Map: MockMap,
  NavigationControl: class {},
  AttributionControl: class {},
}));

beforeEach(() => {
  maps.length = 0;
  vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() {} });
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{"status":"ok"}')));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

async function renderApp() {
  const view = render(<App />);
  await screen.findByText('Система готова');
  act(() => maps[0].emit('load'));
  return view;
}

it('mounts a map container and supplies one separate GeoJSON source with a stable ID', async () => {
  await renderApp();
  expect(screen.getByRole('region', { name: 'Карта Санкт-Петербурга' })).toBeTruthy();
  expect(maps[0].options).toMatchObject({ center: mapConfig.center, zoom: mapConfig.zoom, style: mapConfig.style.url });
  expect(maps[0].addSource).toHaveBeenCalledWith('demo-objects', {
    type: 'geojson', data: { type: 'FeatureCollection', features: demoObjects },
  });
  expect(maps[0].addLayer).toHaveBeenCalledTimes(1);
  expect(demoObjects).toHaveLength(1);
  expect(rawPoint.type).toBe('Feature');
  expect(rawPoint.geometry.type).toBe('Point');
  expect(rawPoint.id).toBe(rawPoint.properties.id);
  expect(rawPoint.geometry.coordinates).toEqual([30.3158, 59.9391]);
  expect(screen.queryByRole('complementary')).toBeNull();
});

it('resolves a map click by ID into React state, closes and reopens the real card', async () => {
  await renderApp();
  const click = () => maps[0].emit('click', { features: [{ id: 'demo-object-1', properties: { name: 'Untrusted map property' } }] });
  act(click);
  expect(screen.getByRole('complementary', { name: 'Тестовый объект' })).toBeTruthy();
  expect(screen.getByText('demo-object-1')).toBeTruthy();
  expect(screen.getByText('demo')).toBeTruthy();
  expect(screen.getByText(demoObjects[0].properties.description)).toBeTruthy();
  expect(screen.queryByText('Untrusted map property')).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Закрыть карточку' }));
  expect(screen.queryByRole('complementary')).toBeNull();
  act(click);
  expect(screen.getByRole('complementary')).toBeTruthy();
  expect(maps).toHaveLength(1);
});

it('does not create a card for unknown or absent feature IDs', async () => {
  await renderApp();
  act(() => maps[0].emit('click', { features: [{ id: 'unknown' }] }));
  expect(screen.queryByRole('complementary')).toBeNull();
  act(() => maps[0].emit('click'));
  expect(screen.queryByRole('complementary')).toBeNull();
});

it('updates callbacks without recreating the map and removes it on unmount', () => {
  const first = vi.fn();
  const second = vi.fn();
  const view = render(<MapView onObjectClick={first} />);
  view.rerender(<MapView onObjectClick={second} />);
  act(() => maps[0].emit('click', { features: [{ id: 'demo-object-1' }] }));
  expect(first).not.toHaveBeenCalled();
  expect(second).toHaveBeenCalledWith('demo-object-1');
  expect(maps).toHaveLength(1);
  view.unmount();
  expect(maps[0].remove).toHaveBeenCalledTimes(1);
});

it('balances creation and cleanup during StrictMode setup replay', () => {
  const view = render(<StrictMode><MapView onObjectClick={vi.fn()} /></StrictMode>);
  expect(maps).toHaveLength(2);
  expect(maps[0].remove).toHaveBeenCalledTimes(1);
  expect(maps[1].remove).not.toHaveBeenCalled();
  view.unmount();
  expect(maps[1].remove).toHaveBeenCalledTimes(1);
});

it('surfaces basemap errors instead of leaving a loading message', () => {
  render(<MapView onObjectClick={vi.fn()} />);
  act(() => maps[0].emit('error'));
  expect(screen.getByRole('status').textContent).toContain('Карта загружена не полностью');
});

it('renders a separate card component and supports keyboard closing', () => {
  const onClose = vi.fn();
  render(<ObjectCard object={demoObjects[0]} onClose={onClose} />);
  const close = screen.getByRole('button', { name: 'Закрыть карточку' });
  expect(document.activeElement).toBe(close);
  fireEvent.keyDown(close, { key: 'Escape' });
  expect(onClose).toHaveBeenCalledTimes(1);
});
