import { useCallback, useEffect, useState } from 'react';
import { fetchHealth } from './health';
import { MapView } from './components/MapView';
import { ObjectCard } from './components/ObjectCard';
import { DistrictPanel } from './components/DistrictPanel';
import { objectsApi, getCategoryById } from './data/objectsApi';
import { CategoryPanel } from './components/CategoryPanel';
import { SearchPanel } from './components/SearchPanel';
import { geocoderProvider, geometryCenter } from './domain/search';
import type { MapTarget } from './domain/search';
import { districts } from './data/districts';
import type { DistrictId } from './domain/district';
import { toggleDistrict } from './domain/district';
import { initialLayerRegistry, updateLayer } from './domain/layers';
import type { ProjectLayerId } from './domain/layers';
import type { SelectedObject, MapObject, Category } from './domain/mapObject';

export function App() {
  const [selectedObject, setSelectedObject] = useState<SelectedObject>(null);
  const [selectedDistrictIds, setSelectedDistrictIds] = useState<DistrictId[]>([]);
  const [layers, setLayers] = useState(initialLayerRegistry);
  const [objects, setObjects] = useState<MapObject[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [visibleCategoryIds, setVisibleCategoryIds] = useState<string[]>([]);
  const [dataStatus, setDataStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [dataAttempt, setDataAttempt] = useState(0);
  const [mapTarget, setMapTarget] = useState<MapTarget>();
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    const timeout = window.setTimeout(() => controller.abort(), 10000);
    Promise.all([objectsApi.getObjects(controller.signal), objectsApi.getCategories(controller.signal)])
      .then(([items, definitions]) => {
        if (!active) return;
        setObjects(items); setCategories(definitions);
        setVisibleCategoryIds(definitions.filter((category) => category.defaultVisible).map((category) => category.id));
        setDataStatus('ready');
      }).catch(() => {
        if (active) { console.warn('Project data load failed'); setDataStatus('error'); }
      }).finally(() => window.clearTimeout(timeout));
    return () => { active = false; controller.abort(); window.clearTimeout(timeout); };
  }, [dataAttempt]);
  const selectObject = useCallback((id: string) => {
    setSelectedObject(objects.find((object) => object.id === id) ?? null);
  }, [objects]);
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 5000);
    fetchHealth(controller.signal)
      .then((ok) => { if (active) setStatus(ok ? 'ready' : 'error'); })
      .catch(() => { if (active) setStatus('error'); })
      .finally(() => window.clearTimeout(timeout));
    return () => { active = false; window.clearTimeout(timeout); controller.abort(); };
  }, [attempt]);
  return <main className="app-shell">
    <header className="app-header">
      <span className="brand">KARTA<span>SPB</span></span>
      <span className="region">Санкт-Петербург · Ленинградская область</span>
      <div className="status" role="status" aria-live="polite">
        <span className={`dot ${status}`} />
        {status === 'loading' ? 'Проверяем подключение…' : status === 'ready' ? 'Система готова' : 'Система временно недоступна'}
      </div>
      {status === 'error' && <button onClick={() => { setStatus('loading'); setAttempt(attempt + 1); }}>Повторить проверку</button>}
    </header>
    <section className="map-workspace" aria-label="Обзор территории">
      <MapView
        objects={objects}
        categories={categories}
        visibleCategoryIds={visibleCategoryIds}
        mapTarget={mapTarget}
        selectedDistrictIds={selectedDistrictIds}
        layers={layers}
        onDistrictClick={(id) => setSelectedDistrictIds((current) => toggleDistrict(current, id))}
        onObjectClick={selectObject}
      />
      <div className="map-intro">
        <SearchPanel geocoder={geocoderProvider}
          onObjectSelect={(object) => {
            setSelectedObject(object);
            setMapTarget({ coordinates: geometryCenter(object), token: Date.now(), showMarker: false });
          }}
          onGeographicSelect={(result) => {
            setSelectedObject(null);
            setMapTarget({ coordinates: result.coordinates, token: Date.now(), showMarker: true });
          }} />
        <p className="eyebrow">ИССЛЕДОВАНИЕ ТЕРРИТОРИИ</p>
        <h1>Санкт-Петербург</h1>
        <p>Выберите районы в панели или на карте.<br />Мятная точка открывает карточку.</p>
        <span className="demo-badge">Объектов загружено: {objects.length}</span>
        {dataStatus === 'loading' && <p role="status">Загружаем объекты…</p>}
        {dataStatus === 'error' && <div role="alert">Не удалось загрузить объекты.
          <button onClick={() => { setDataStatus('loading'); setDataAttempt((value) => value + 1); }}>Повторить загрузку объектов</button>
        </div>}
        {dataStatus === 'ready' && <>
          <CategoryPanel categories={categories} visibleIds={visibleCategoryIds} onChange={(ids) => { setVisibleCategoryIds(ids); setSelectedObject(null); }} />
          {!objects.some((object) => visibleCategoryIds.includes(object.categoryId)) && <p role="status">Нет объектов для выбранных категорий.</p>}
        </>}
      </div>
      <DistrictPanel
        districts={districts}
        selectedIds={selectedDistrictIds}
        layers={layers}
        onDistrictToggle={(id) => setSelectedDistrictIds((current) => toggleDistrict(current, id))}
        onClearDistricts={() => setSelectedDistrictIds([])}
        onLayerVisibilityChange={(id: ProjectLayerId, visible) => setLayers((current) => updateLayer(current, id, { visible }))}
        onLayerOpacityChange={(id: ProjectLayerId, opacity) => setLayers((current) => updateLayer(current, id, { opacity }))}
      />
      {selectedObject && <ObjectCard object={selectedObject} categoryName={getCategoryById(categories, selectedObject.categoryId)?.name} onClose={() => setSelectedObject(null)} />}
    </section>
    <footer className="app-footer"><span>ПЕРСОНАЛЬНАЯ GIS-СИСТЕМА</span><span>Тестовая точка · не реальные данные</span></footer>
  </main>;
}
