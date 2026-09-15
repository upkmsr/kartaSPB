import { useEffect, useRef, useState } from 'react';
import 'maplibre-gl/dist/maplibre-gl.css';
import { mapConfig } from '../config/map';
import { demoObjects } from '../data/demo';
import { createMap } from '../map/mapLibreAdapter';

interface MapViewProps {
  onObjectClick: (id: string) => void;
}

export function MapView({ onObjectClick }: MapViewProps) {
  const container = useRef<HTMLDivElement>(null);
  const onClick = useRef(onObjectClick);
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');

  useEffect(() => { onClick.current = onObjectClick; }, [onObjectClick]);
  useEffect(() => {
    if (!container.current) return;
    let adapter: ReturnType<typeof createMap> | undefined;
    let observer: ResizeObserver | undefined;
    let active = true;
    const timeout = window.setTimeout(() => setStatus('error'), 20000);
    try {
      adapter = createMap(container.current, mapConfig, demoObjects, {
        onObjectClick: (id) => { if (active) onClick.current(id); },
        onReady: () => {
          window.clearTimeout(timeout);
          if (active) setStatus('ready');
        },
        onError: () => {
          window.clearTimeout(timeout);
          if (active) setStatus('error');
        },
      });
      observer = new ResizeObserver(() => adapter?.resize());
      observer.observe(container.current);
    } catch {
      window.clearTimeout(timeout);
      queueMicrotask(() => { if (active) setStatus('error'); });
    }
    return () => {
      active = false;
      window.clearTimeout(timeout);
      observer?.disconnect();
      adapter?.remove();
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
