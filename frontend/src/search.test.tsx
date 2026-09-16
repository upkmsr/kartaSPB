// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { SearchPanel } from './components/SearchPanel';
import { demoObjects } from './data/demo';
import type { GeocoderProvider } from './domain/search';

beforeEach(() => {
  vi.useFakeTimers();
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(demoObjects))));
});
afterEach(() => { cleanup(); vi.useRealTimers(); vi.unstubAllGlobals(); });

const result = { id: 'nominatim-node-1', label: 'Дворцовая площадь', coordinates: [30.328, 59.939] as [number, number], type: 'square', provider: 'nominatim' };

async function search(value: string) {
  fireEvent.change(screen.getByLabelText('Поиск объектов и адресов'), { target: { value } });
  await act(() => vi.advanceTimersByTimeAsync(500));
}

it('shows separate project and geographic results and selects both', async () => {
  const onObject = vi.fn();
  const onPlace = vi.fn();
  const geocoder: GeocoderProvider = { search: vi.fn().mockResolvedValue([result]) };
  render(<SearchPanel geocoder={geocoder} onObjectSelect={onObject} onGeographicSelect={onPlace} />);
  await search('Тестовый');
  fireEvent.click(screen.getByRole('button', { name: 'Найти адрес' }));
  await act(async () => {});
  expect(screen.getByText('Объекты KARTASPB')).toBeTruthy();
  expect(screen.getByText('Адреса и места')).toBeTruthy();
  fireEvent.click(screen.getByRole('button', { name: 'Тестовый объект' }));
  expect(onObject).toHaveBeenCalledWith(demoObjects[0]);
  fireEvent.focus(screen.getByLabelText('Поиск объектов и адресов'));
  fireEvent.click(screen.getByRole('button', { name: 'Дворцовая площадь' }));
  expect(onPlace).toHaveBeenCalledWith(result);
});

it('keeps project search available on geocoder error and closes with Escape', async () => {
  const geocoder: GeocoderProvider = { search: vi.fn().mockRejectedValue(new Error('offline')) };
  render(<SearchPanel geocoder={geocoder} onObjectSelect={vi.fn()} onGeographicSelect={vi.fn()} />);
  await search('Тестовый');
  fireEvent.click(screen.getByRole('button', { name: 'Найти адрес' }));
  await act(async () => {});
  expect(screen.getByRole('button', { name: 'Тестовый объект' })).toBeTruthy();
  expect(screen.getByText('Геокодер временно недоступен')).toBeTruthy();
  fireEvent.keyDown(screen.getByLabelText('Поиск объектов и адресов'), { key: 'Escape' });
  expect(screen.queryByRole('region', { name: 'Результаты поиска' })).toBeNull();
});

it('does not query for a short or empty value and handles empty results', async () => {
  vi.mocked(fetch).mockResolvedValue(new Response('[]'));
  const geocoder: GeocoderProvider = { search: vi.fn().mockResolvedValue([]) };
  render(<SearchPanel geocoder={geocoder} onObjectSelect={vi.fn()} onGeographicSelect={vi.fn()} />);
  await search('a');
  expect(fetch).not.toHaveBeenCalled();
  await search('unknown');
  fireEvent.click(screen.getByRole('button', { name: 'Найти адрес' }));
  await act(async () => {});
  expect(screen.getAllByText('Ничего не найдено')).toHaveLength(2);
});

it('ignores a stale geocoder response', async () => {
  vi.useRealTimers();
  let resolveFirst: (value: typeof result[]) => void = () => {};
  const first = new Promise<typeof result[]>((resolve) => { resolveFirst = resolve; });
  const geocoder: GeocoderProvider = { search: vi.fn()
    .mockReturnValueOnce(first).mockResolvedValueOnce([{ ...result, id: 'new', label: 'Новый результат' }]) };
  render(<SearchPanel geocoder={geocoder} onObjectSelect={vi.fn()} onGeographicSelect={vi.fn()} />);
  fireEvent.change(screen.getByLabelText('Поиск объектов и адресов'), { target: { value: 'first' } });
  fireEvent.click(screen.getByRole('button', { name: 'Найти адрес' }));
  fireEvent.change(screen.getByLabelText('Поиск объектов и адресов'), { target: { value: 'second' } });
  fireEvent.click(screen.getByRole('button', { name: 'Найти адрес' }));
  expect(await screen.findByText('Новый результат')).toBeTruthy();
  await act(async () => resolveFirst([result]));
  expect(screen.queryByText('Дворцовая площадь')).toBeNull();
});
