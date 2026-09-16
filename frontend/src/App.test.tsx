// @vitest-environment jsdom
import { StrictMode } from 'react';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { App } from './App';
import { MapView } from './components/MapView';
import { ObjectCard } from './components/ObjectCard';
import { mapConfig } from './config/map';
import { demoObjects } from './data/demo';
import { districts } from './data/districts';
import { initialLayerRegistry } from './domain/layers';
import { toGeoJSON } from './domain/mapObject';
import rawPoint from './data/demo/point.json';

// Only mock the WebGL boundary. Real adapter, ID resolution, React state and card run.
const { maps, MockMap } = vi.hoisted(() => {
  interface ClickEvent { point?: { x: number; y: number } }
  interface RenderedFeature { id?: string; layer: { id: string }; properties: Record<string, string> }
  class MockMap {
    handlers = new globalThis.Map<string, (event: ClickEvent) => void>();
    addSource = vi.fn();
    addLayer = vi.fn();
    addControl = vi.fn();
    setFilter = vi.fn();
    setPaintProperty = vi.fn();
    setLayoutProperty = vi.fn();
    renderedFeatures: RenderedFeature[] = [];
    queryRenderedFeatures = vi.fn(() => this.renderedFeatures);
    remove = vi.fn();
    resize = vi.fn();
    touchZoomRotate = { disableRotation: vi.fn() };
    getSource = () => ({ setData: vi.fn() });
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
  setWorkerUrl: vi.fn(),
  Map: MockMap,
  NavigationControl: class {},
  AttributionControl: class {},
}));

beforeEach(() => {
  maps.length = 0;
  vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() {} });
  vi.stubGlobal('fetch', vi.fn(async (url: string) => new Response(JSON.stringify(url === '/api/objects' ? demoObjects : url === '/api/categories' ? [{ id: 'demo', name: 'Демонстрационные', description: '', color: '#77dfcc', defaultVisible: true }, { id: 'other', name: 'Прочее', description: '', color: '#ffc078', defaultVisible: true }] : { status: 'ok' }))));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

async function renderApp() {
  const view = render(<App />);
  await screen.findByText('Система готова');
  act(() => maps[0].emit('style.load'));
  return view;
}

it('mounts a map container and supplies one separate GeoJSON source with a stable ID', async () => {
  await renderApp();
  expect(screen.getByRole('region', { name: 'Карта Санкт-Петербурга' })).toBeTruthy();
  expect(maps[0].options).toMatchObject({ center: mapConfig.center, zoom: mapConfig.zoom, style: mapConfig.style.url });
  expect(maps[0].addSource).toHaveBeenCalledWith('demo-objects', {
    type: 'geojson', data: toGeoJSON(demoObjects),
  });
  expect(maps[0].addSource).toHaveBeenCalledWith('districts', expect.objectContaining({ type: 'geojson' }));
  expect(maps[0].addLayer).toHaveBeenCalledTimes(4);
  expect(districts).toHaveLength(18);
  expect(demoObjects).toHaveLength(1);
  expect(rawPoint.type).toBe('Feature');
  expect(rawPoint.geometry.type).toBe('Point');
  expect(rawPoint.id).toBe(rawPoint.properties.id);
  expect(rawPoint.geometry.coordinates).toEqual([30.3158, 59.9391]);
  expect(screen.queryByRole('complementary', { name: 'Тестовый объект' })).toBeNull();
});

it('resolves a map click by ID into React state, closes and reopens the real card', async () => {
  await renderApp();
  const click = () => {
    act(() => maps[0].emit('style.load'));
  maps[0].renderedFeatures = [{ id: 'demo-object-1', layer: { id: 'demo-points' }, properties: { name: 'Untrusted map property' } }];
    maps[0].emit('click', { point: { x: 0, y: 0 } });
  };
  act(click);
  expect(screen.getByRole('complementary', { name: 'Тестовый объект' })).toBeTruthy();
  expect(screen.getByText('demo-object-1')).toBeTruthy();
  expect(screen.getByText('Демонстрационные', { selector: 'dd' })).toBeTruthy();
  expect(screen.getByText(demoObjects[0].description)).toBeTruthy();
  expect(screen.queryByText('Untrusted map property')).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Закрыть карточку' }));
  expect(screen.queryByRole('complementary', { name: 'Тестовый объект' })).toBeNull();
  act(click);
  expect(screen.getByRole('complementary', { name: 'Тестовый объект' })).toBeTruthy();
  expect(maps).toHaveLength(1);
});

it('does not create a card for unknown or absent feature IDs', async () => {
  await renderApp();
  maps[0].renderedFeatures = [{ id: 'unknown', layer: { id: 'demo-points' }, properties: {} }];
  act(() => maps[0].emit('click', { point: { x: 0, y: 0 } }));
  expect(screen.queryByRole('complementary', { name: 'Тестовый объект' })).toBeNull();
  maps[0].renderedFeatures = [];
  act(() => maps[0].emit('click', { point: { x: 0, y: 0 } }));
  expect(screen.queryByRole('complementary', { name: 'Тестовый объект' })).toBeNull();
});

it('routes a rendered district click into React selection and updates paint without recreating the map', async () => {
  await renderApp();
  maps[0].renderedFeatures = [{ layer: { id: 'district-fill' }, properties: { id: districts[0].id } }];
  act(() => maps[0].emit('click', { point: { x: 0, y: 0 } }));
  expect((screen.getByRole('checkbox', { name: districts[0].properties.name }) as HTMLInputElement).checked).toBe(true);
  expect(screen.getByText('Выбрано: 1')).toBeTruthy();
  expect(maps[0].setFilter).toHaveBeenCalledWith('district-selected', expect.any(Array));
  expect(maps[0].setPaintProperty).toHaveBeenCalledWith('district-fill', 'fill-opacity', expect.any(Array));
  expect(maps).toHaveLength(1);
});

it('updates callbacks without recreating the map and removes it on unmount', () => {
  const first = vi.fn();
  const second = vi.fn();
  const common = { onDistrictClick: vi.fn(), selectedDistrictIds: [], layers: initialLayerRegistry };
  const view = render(<MapView {...common} onObjectClick={first} />);
  view.rerender(<MapView {...common} onObjectClick={second} />);
  act(() => maps[0].emit('style.load'));
  maps[0].renderedFeatures = [{ id: 'demo-object-1', layer: { id: 'demo-points' }, properties: {} }];
  act(() => maps[0].emit('click', { point: { x: 0, y: 0 } }));
  expect(first).not.toHaveBeenCalled();
  expect(second).toHaveBeenCalledWith('demo-object-1');
  expect(maps).toHaveLength(1);
  view.unmount();
  expect(maps[0].remove).toHaveBeenCalledTimes(1);
});

it('balances creation and cleanup during StrictMode setup replay', () => {
  const view = render(<StrictMode><MapView onObjectClick={vi.fn()} onDistrictClick={vi.fn()} selectedDistrictIds={[]} layers={initialLayerRegistry} /></StrictMode>);
  expect(maps).toHaveLength(2);
  expect(maps[0].remove).toHaveBeenCalledTimes(1);
  expect(maps[1].remove).not.toHaveBeenCalled();
  view.unmount();
  expect(maps[1].remove).toHaveBeenCalledTimes(1);
});

it('surfaces basemap errors instead of leaving a loading message', () => {
  render(<MapView onObjectClick={vi.fn()} onDistrictClick={vi.fn()} selectedDistrictIds={[]} layers={initialLayerRegistry} />);
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

it('filters one and multiple categories locally and restores all without recreating the map', async () => {
  await renderApp();
  const demo = screen.getByRole('checkbox', { name: 'Демонстрационные' });
  const other = screen.getByRole('checkbox', { name: 'Прочее' });
  const requests = vi.mocked(fetch).mock.calls.length;
  fireEvent.click(other);
  expect(maps[0].setFilter).toHaveBeenLastCalledWith('demo-points', ['in', ['get', 'categoryId'], ['literal', ['demo']]]);
  fireEvent.click(demo);
  expect(screen.getByText('Нет объектов для выбранных категорий.')).toBeTruthy();
  fireEvent.click(screen.getByRole('button', { name: 'Показать все' }));
  expect((demo as HTMLInputElement).checked).toBe(true);
  expect((other as HTMLInputElement).checked).toBe(true);
  expect(vi.mocked(fetch).mock.calls.length).toBe(requests);
  expect(maps).toHaveLength(1);
});

it('keeps the district UI and map mounted when object API fails and allows retry', async () => {
  vi.mocked(fetch).mockImplementation(async (url) => new Response(JSON.stringify({ status: 'ok' }), { status: url === '/api/objects' ? 503 : 200 }));
  render(<App />);
  expect(await screen.findByRole('alert')).toBeTruthy();
  expect(screen.getByRole('checkbox', { name: districts[0].properties.name })).toBeTruthy();
  expect(screen.getByRole('button', { name: 'Повторить загрузку объектов' })).toBeTruthy();
  expect(maps).toHaveLength(1);
});

it('handles an empty API dataset', async () => {
  vi.mocked(fetch).mockImplementation(async (url) => new Response(JSON.stringify(url === '/api/health/ready' ? { status: 'ok' } : [])));
  render(<App />);
  expect(await screen.findByText('Нет объектов для выбранных категорий.')).toBeTruthy();
  expect(screen.queryByRole('complementary', { name: 'Тестовый объект' })).toBeNull();
});
