import { useEffect, useRef, useState } from 'react';
import type { GeocoderProvider, GeocodingResult } from '../domain/search';
import { projectSearch } from '../domain/search';
import type { MapObject } from '../domain/mapObject';

interface Props {
  geocoder: GeocoderProvider;
  onObjectSelect: (object: MapObject) => void;
  onGeographicSelect: (result: GeocodingResult) => void;
}

export function SearchPanel({ geocoder, onObjectSelect, onGeographicSelect }: Props) {
  const [query, setQuery] = useState('');
  const [objects, setObjects] = useState<MapObject[]>([]);
  const [places, setPlaces] = useState<GeocodingResult[]>([]);
  const [status, setStatus] = useState<'idle' | 'loading' | 'ready'>('idle');
  const [geoStatus, setGeoStatus] = useState<'idle' | 'loading' | 'ready'>('idle');
  const [geocoderError, setGeocoderError] = useState(false);
  const [open, setOpen] = useState(false);
  const sequence = useRef(0);
  const geocodeSequence = useRef(0);
  const geocodeController = useRef<AbortController | undefined>(undefined);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) return;
    const current = ++sequence.current;
    const controller = new AbortController();
    const timeout = window.setTimeout(async () => {
      setStatus('loading'); setOpen(true); setGeocoderError(false);
      const requests = await Promise.allSettled([projectSearch(trimmed, controller.signal)]);
      if (current !== sequence.current || controller.signal.aborted) return;
      setObjects(requests[0].status === 'fulfilled' ? requests[0].value : []);
      setStatus('ready');
    }, 500);
    return () => { window.clearTimeout(timeout); controller.abort(); };
  }, [query, geocoder]);

  useEffect(() => () => geocodeController.current?.abort(), []);

  const runGeocoder = async () => {
    const trimmed = query.trim();
    if (trimmed.length < 3) return;
    const current = ++geocodeSequence.current;
    geocodeController.current?.abort();
    const controller = new AbortController();
    geocodeController.current = controller;
    setGeoStatus('loading'); setGeocoderError(false); setOpen(true);
    try {
      const result = await geocoder.search(trimmed, controller.signal);
      if (current === geocodeSequence.current && !controller.signal.aborted) {
        setPlaces(result); setGeoStatus('ready');
      }
    } catch {
      if (current === geocodeSequence.current && !controller.signal.aborted) {
        setPlaces([]); setGeocoderError(true); setGeoStatus('ready');
      }
    }
  };

  const choose = (action: () => void) => { action(); setOpen(false); };
  return <section className="search-panel" onKeyDown={(event) => {
    if (event.key === 'Escape') setOpen(false);
  }}>
    <form onSubmit={(event) => { event.preventDefault(); void runGeocoder(); }}>
    <label htmlFor="map-search">Поиск объектов и адресов</label>
    <div className="search-row"><input id="map-search" type="search" value={query} placeholder="Название объекта или адрес"
      onFocus={() => { if (query.trim().length >= 2) setOpen(true); }}
      onChange={(event) => {
        const value = event.target.value;
        setQuery(value);
        if (value.trim().length < 2) {
          setObjects([]); setPlaces([]); setStatus('idle'); setOpen(false); setGeocoderError(false);
        }
      }} aria-expanded={open} /><button type="submit" disabled={query.trim().length < 3}>Найти адрес</button></div>
    </form>
    {open && <div className="search-results" role="region" aria-label="Результаты поиска" aria-live="polite">
      {status === 'loading' && <p>Ищем…</p>}
      {status === 'ready' && <>
        <h2>Объекты KARTASPB</h2>
        {objects.length ? objects.map((object) => <button key={object.id}
          onClick={() => choose(() => onObjectSelect(object))}>{object.name}</button>) : <p>Ничего не найдено</p>}
        <h2>Адреса и места</h2>
        {geoStatus === 'idle' ? <p>Нажмите «Найти адрес»</p> : geoStatus === 'loading' ? <p>Ищем адрес…</p> : geocoderError ? <p>Геокодер временно недоступен</p> : places.length ? places.map((place) =>
          <button key={place.id} onClick={() => choose(() => onGeographicSelect(place))}>{place.label}</button>
        ) : <p>Ничего не найдено</p>}
        <small>Адресные данные © OpenStreetMap contributors, ODbL</small>
      </>}
    </div>}
  </section>;
}
