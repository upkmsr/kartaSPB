// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { DrawingPanel } from './components/DrawingPanel';
import { addDrawingPoint, draftGeometry, verticesFromGeometry } from './domain/userGeometry';
import type { DrawingDraft } from './domain/userGeometry';

afterEach(cleanup);

it('builds Point, LineString and closed Polygon without routing', () => {
  const point: DrawingDraft = { type: 'Point', vertices: [], name: 'A', description: '' };
  const one = addDrawingPoint(point, [30, 59]);
  expect(draftGeometry(one)).toEqual({ type: 'Point', coordinates: [30, 59] });
  const line = addDrawingPoint({ ...one, type: 'LineString' }, [31, 60]);
  expect(draftGeometry(line)).toEqual({ type: 'LineString', coordinates: [[30, 59], [31, 60]] });
  const polygon = addDrawingPoint({ ...line, type: 'Polygon' }, [32, 59]);
  expect(draftGeometry(polygon)).toEqual({ type: 'Polygon', coordinates: [
    [[30, 59], [31, 60], [32, 59], [30, 59]],
  ] });
  expect(verticesFromGeometry(draftGeometry(polygon)!)).toHaveLength(3);
  const moved = addDrawingPoint({ ...polygon, selectedVertex: 1 }, [31.5, 60.2]);
  expect(moved.vertices[1]).toEqual([31.5, 60.2]);
  expect(moved.selectedVertex).toBeUndefined();
});

it('shows tools, selected mode, cancel and save constraints', () => {
  const onStart = vi.fn(); const onCancel = vi.fn();
  const base = { items: [], busy: false, error: null, onStart, onChange: vi.fn(),
    onRemoveLast: vi.fn(), onClear: vi.fn(), onCancel, onSave: vi.fn(), onSelect: vi.fn() };
  const view = render(<DrawingPanel {...base} draft={null} />);
  fireEvent.click(screen.getByRole('button', { name: 'Добавить точку' }));
  fireEvent.click(screen.getByRole('button', { name: 'Нарисовать линию' }));
  fireEvent.click(screen.getByRole('button', { name: 'Нарисовать область' }));
  expect(onStart.mock.calls.map(([type]) => type)).toEqual(['Point', 'LineString', 'Polygon']);
  view.rerender(<DrawingPanel {...base} draft={{ type: 'Polygon', vertices: [], name: 'A', description: '' }} />);
  expect(screen.getByRole('status').textContent).toContain('Polygon');
  expect(screen.getByRole('button', { name: 'Сохранить' }).hasAttribute('disabled')).toBe(true);
  fireEvent.click(screen.getByRole('button', { name: 'Отменить рисование' }));
  expect(onCancel).toHaveBeenCalledTimes(1);
});
