import { useCallback, useEffect, useState } from 'react';
import { fetchHealth } from './health';
import { MapView } from './components/MapView';
import { ObjectCard } from './components/ObjectCard';
import { demoObjects } from './data/demo';
import type { SelectedObject } from './domain/mapObject';

export function App() {
  const [selectedObject, setSelectedObject] = useState<SelectedObject>(null);
  const selectObject = useCallback((id: string) => {
    setSelectedObject(demoObjects.find((object) => object.id === id) ?? null);
  }, []);
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
      <MapView onObjectClick={selectObject} />
      <div className="map-intro">
        <p className="eyebrow">ИССЛЕДОВАНИЕ ТЕРРИТОРИИ</p>
        <h1>Санкт-Петербург</h1>
        <p>Нажмите на мятную точку,<br />чтобы открыть её карточку.</p>
        <span className="demo-badge">DEMO · 1 тестовый объект</span>
      </div>
      {selectedObject && <ObjectCard object={selectedObject} onClose={() => setSelectedObject(null)} />}
    </section>
    <footer className="app-footer"><span>ПЕРСОНАЛЬНАЯ GIS-СИСТЕМА</span><span>Тестовая точка · не реальные данные</span></footer>
  </main>;
}
