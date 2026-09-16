import { useEffect, useRef } from 'react';
import type { MapObject } from '../domain/mapObject';

interface ObjectCardProps {
  object: MapObject;
  categoryName?: string;
  onClose: () => void;
}

export function ObjectCard({ object, categoryName = 'Нет данных', onClose }: ObjectCardProps) {
  const closeButton = useRef<HTMLButtonElement>(null);
  useEffect(() => { closeButton.current?.focus({ preventScroll: true }); }, [object.id]);

  return <aside className="object-card" aria-labelledby="object-title" onKeyDown={(event) => {
    if (event.key === 'Escape') onClose();
  }}>
    <div className="card-heading">
      <p className="eyebrow">{object.properties.demo ? 'ДЕМОНСТРАЦИОННЫЙ ОБЪЕКТ' : 'ОБЪЕКТ ПРОЕКТА'}</p>
      <button ref={closeButton} className="close-card" onClick={onClose} aria-label="Закрыть карточку">×</button>
    </div>
    <h2 id="object-title">{object.name}</h2>
    <dl>
      <div><dt>Категория</dt><dd>{categoryName}</dd></div>
      <div><dt>ID</dt><dd>{object.id}</dd></div>
      <div><dt>Источник</dt><dd>{object.source || 'Нет данных'}</dd></div>
    </dl>
    <p className="card-description">{object.description || 'Нет данных'}</p>
  </aside>;
}
