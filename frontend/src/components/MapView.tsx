import { useEffect, useRef, useState } from 'react';
import 'maplibre-gl/dist/maplibre-gl.css';
import { mapConfig } from '../config/map';
import type { Category, MapObject } from '../domain/mapObject';
import { districtFeatureCollection } from '../data/districts';
import type { DistrictId } from '../domain/district';
import type { LayerRegistry } from '../domain/layers';
import type { MapTarget } from '../domain/search';
import { createMap } from '../map/mapLibreAdapter';

interface MapViewProps {
  onObjectClick: (id: string) => void;
  onDistrictClick: (id: DistrictId) => void;
  selectedDistrictIds: readonly DistrictId[];
  layers: LayerRegistry;
  objects?: MapObject[];
  categories?: Category[];
  visibleCategoryIds?: string[];
  mapTarget?: MapTarget;
}

export function MapView({ onObjectClick, onDistrictClick, selectedDistrictIds, layers, objects = [], categories = [], visibleCategoryIds = [], mapTarget }: MapViewProps) {
  const container = useRef<HTMLDivElement>(null);
  const onClick = useRef(onObjectClick);
  const onDistrict = useRef(onDistrictClick);
  const adapter = useRef<ReturnType<typeof createMap> | undefined>(undefined);
  const initialSelection = useRef(selectedDistrictIds);
  const initialLayers = useRef(layers);
  const initialObjects = useRef(objects);
  const initialCategories = useRef({ categories, visibleCategoryIds });
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');

  useEffect(() => { onClick.current = onObjectClick; }, [onObjectClick]);
  useEffect(() => { onDistrict.current = onDistrictClick; }, [onDistrictClick]);
  useEffect(() => { adapter.current?.setSelectedDistricts(selectedDistrictIds); }, [selectedDistrictIds]);
  useEffect(() => { adapter.current?.setLayers(layers); }, [layers]);
  useEffect(() => { adapter.current?.setObjects(objects); }, [objects]);
  useEffect(() => { adapter.current?.setCategories(categories, visibleCategoryIds); }, [categories, visibleCategoryIds]);
  useEffect(() => { if (mapTarget) adapter.current?.focus(mapTarget); }, [mapTarget]);
  useEffect(() => {
    if (!container.current) return;
    let mapAdapter: ReturnType<typeof createMap> | undefined;
    let observer: ResizeObserver | undefined;
    let active = true;
    const timeout = window.setTimeout(() => setStatus('error'), 20000);
    try {
      mapAdapter = createMap(container.current, mapConfig, initialObjects.current, districtFeatureCollection, {
        onObjectClick: (id) => { if (active) onClick.current(id); },
        onDistrictClick: (id) => { if (active) onDistrict.current(id); },
        onReady: () => {
          window.clearTimeout(timeout);
          if (active) setStatus('ready');
        },
        onError: () => {
          window.clearTimeout(timeout);
          if (active) setStatus('error');
        },
      });
      adapter.current = mapAdapter;
      mapAdapter.setSelectedDistricts(initialSelection.current);
      mapAdapter.setLayers(initialLayers.current);
      mapAdapter.setCategories(initialCategories.current.categories, initialCategories.current.visibleCategoryIds);
      observer = new ResizeObserver(() => mapAdapter?.resize());
      observer.observe(container.current);
    } catch {
      window.clearTimeout(timeout);
      queueMicrotask(() => { if (active) setStatus('error'); });
    }
    return () => {
      active = false;
      window.clearTimeout(timeout);
      observer?.disconnect();
      mapAdapter?.remove();
      adapter.current = undefined;
    };
  }, []);

  return <div className="map-pane">
    <div ref={container} className="map-container" role="region" aria-label="Карта Санкт-Петербурга" />
    {status !== 'ready' && <p className="map-notice" role="status">
      {status === 'loading'
        ? 'Загружаем карту…'
        : 'Карта загружена не полностью. Проверьте соединение и поддержку WebGL в браузере, затем обновите страницу.'}
    </p>}
  </div>;
}
