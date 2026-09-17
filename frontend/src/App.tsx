import { useCallback, useEffect, useState } from 'react';
import { fetchHealth } from './health';
import { MapView } from './components/MapView';
import { ObjectCard } from './components/ObjectCard';
import { DrawingPanel } from './components/DrawingPanel';
import { UserGeometryCard } from './components/UserGeometryCard';
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
import type { DrawingDraft, UserGeometry, UserGeometryType } from './domain/userGeometry';
import { addDrawingPoint, draftGeometry, verticesFromGeometry } from './domain/userGeometry';
import { userGeometriesApi } from './data/userGeometriesApi';

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
  const [userGeometries, setUserGeometries] = useState<UserGeometry[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [drawingDraft, setDrawingDraft] = useState<DrawingDraft | null>(null);
  const [drawingBusy, setDrawingBusy] = useState(false);
  const [drawingError, setDrawingError] = useState<string | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const selectedUser = userGeometries.find((item) => item.id === selectedUserId);
  useEffect(() => {
    let active = true;
    userGeometriesApi.list().then((items) => { if (active) setUserGeometries(items); })
      .catch(() => { if (active) setDrawingError('Не удалось загрузить мои геометрии.'); });
    return () => { active = false; };
  }, []);
  const startDrawing = (type: UserGeometryType) => {
    setSelectedObject(null); setSelectedUserId(null); setDrawingError(null);
    setDrawingDraft({ type, vertices: [], name: '', description: '' });
  };
  const selectUser = (id: string) => {
    const item = userGeometries.find((candidate) => candidate.id === id);
    if (!item) return;
    setSelectedUserId(id); setSelectedObject(null); setDeleteConfirmId(null);
    setMapTarget({ coordinates: geometryCenter(item), token: Date.now(), showMarker: false });
  };
  const saveDrawing = async () => {
    if (!drawingDraft) return;
    const geometry = draftGeometry(drawingDraft);
    if (!geometry || !drawingDraft.name.trim()) return;
    setDrawingBusy(true); setDrawingError(null);
    try {
      const saved = drawingDraft.editingId
        ? await userGeometriesApi.update(drawingDraft.editingId, drawingDraft.name.trim(), drawingDraft.description, geometry)
        : await userGeometriesApi.create(drawingDraft.name.trim(), drawingDraft.description, geometry);
      setUserGeometries((current) => [...current.filter((item) => item.id !== saved.id), saved]);
      setDrawingDraft(null); setSelectedUserId(saved.id);
    } catch { setDrawingError('Не удалось сохранить геометрию. Проверьте форму и соединение.'); }
    finally { setDrawingBusy(false); }
  };
  const deleteUser = async () => {
    if (!selectedUserId) return;
    if (deleteConfirmId !== selectedUserId) { setDeleteConfirmId(selectedUserId); return; }
    setDrawingBusy(true); setDrawingError(null);
    try {
      await userGeometriesApi.remove(selectedUserId);
      setUserGeometries((current) => current.filter((item) => item.id !== selectedUserId));
      setSelectedUserId(null); setDeleteConfirmId(null);
    } catch { setDrawingError('Не удалось удалить геометрию.'); }
    finally { setDrawingBusy(false); }
  };
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
    const local = objects.find((object) => object.id === id);
    if (local) { setSelectedObject(local); return; }
    objectsApi.getObject(id).then(setSelectedObject).catch(() => setSelectedObject(null));
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
        userGeometries={userGeometries}
        drawingDraft={drawingDraft}
        onUserGeometryClick={selectUser}
        onDrawingClick={(coordinate) => setDrawingDraft((draft) => draft && addDrawingPoint(draft, coordinate))}
        onDrawingVertexClick={(index) => setDrawingDraft((draft) => draft && { ...draft, selectedVertex: index })}
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
        <DrawingPanel draft={drawingDraft} items={userGeometries} busy={drawingBusy} error={drawingError}
          onStart={startDrawing}
          onChange={(patch) => setDrawingDraft((draft) => draft && { ...draft, ...patch })}
          onRemoveLast={() => setDrawingDraft((draft) => draft && { ...draft, vertices: draft.vertices.slice(0, -1), selectedVertex: undefined })}
          onClear={() => setDrawingDraft((draft) => draft && { ...draft, vertices: [], selectedVertex: undefined })}
          onCancel={() => { setDrawingDraft(null); setDrawingError(null); }}
          onSave={saveDrawing} onSelect={selectUser} />
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
      {selectedUser && <UserGeometryCard item={selectedUser} deleting={drawingBusy}
        confirmDelete={deleteConfirmId === selectedUser.id} error={drawingError}
        onEdit={() => { setDrawingError(null); setDeleteConfirmId(null); setDrawingDraft({ type: selectedUser.geometryType,
          vertices: verticesFromGeometry(selectedUser.geometry), name: selectedUser.name,
          description: selectedUser.description, editingId: selectedUser.id }); setSelectedUserId(null); }}
        onDelete={deleteUser} onClose={() => { setSelectedUserId(null); setDeleteConfirmId(null); }} />}
    </section>
    <footer className="app-footer"><span>ПЕРСОНАЛЬНАЯ GIS-СИСТЕМА</span><span>Тестовая точка · не реальные данные</span></footer>
  </main>;
}
