import { useEffect, useRef } from 'react';
import type { MapObject } from '../domain/mapObject';

interface ObjectCardProps {
  object: MapObject;
  onClose: () => void;
}

export function ObjectCard({ object, onClose }: ObjectCardProps) {
  const closeButton = useRef<HTMLButtonElement>(null);
  useEffect(() => { closeButton.current?.focus({ preventScroll: true }); }, [object.id]);

  return <aside className="object-card" aria-labelledby="object-title" onKeyDown={(event) => {
    if (event.key === 'Escape') onClose();
  }}>
    <div className="card-heading">
      <p className="eyebrow">ДЕМОНСТРАЦИОННАЯ ТОЧКА</p>
      <button ref={closeButton} className="close-card" onClick={onClose} aria-label="Закрыть карточку">×</button>
    </div>
    <h2 id="object-title">{object.properties.name}</h2>
    <dl>
      <div><dt>Категория</dt><dd>{object.properties.category}</dd></div>
      <div><dt>ID</dt><dd>{object.id}</dd></div>
    </dl>
    <p className="card-description">{object.properties.description}</p>
  </aside>;
}
