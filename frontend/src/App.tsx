import { useEffect, useState } from 'react';
import { fetchHealth } from './health';

export function App() {
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
  return <main>
    <header><span className="brand">KARTA<span>SPB</span></span><span className="region">Санкт-Петербург · Ленинградская область</span></header>
    <section>
      <p className="eyebrow">ПЕРСОНАЛЬНАЯ GIS-СИСТЕМА</p>
      <h1>Место для жизни.<br /><span>Начало исследования.</span></h1>
      <p className="intro">Основа приложения подготовлена. Карта и инструменты анализа появятся на следующих этапах.</p>
      <div className="status" role="status" aria-live="polite">
        <span className={`dot ${status}`} />
        {status === 'loading' ? 'Проверяем подключение…' : status === 'ready' ? 'Система готова' : 'Система временно недоступна'}
      </div>
      {status === 'error' && <button onClick={() => { setStatus('loading'); setAttempt(attempt + 1); }}>Повторить проверку</button>}
    </section>
    <footer>KARTASPB <span>Данные территории: нет данных</span></footer>
  </main>;
}
