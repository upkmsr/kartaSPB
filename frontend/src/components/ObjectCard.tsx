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
      {object.categoryId === 'school' && <>
        <div><dt>Тип</dt><dd>{String(object.properties.schoolType || 'Нет данных')}</dd></div>
        <div><dt>Адрес</dt><dd>{String(object.properties.address || 'Нет данных')}</dd></div>
        <div><dt>Актуальность источника</dt><dd>{String(object.properties.sourceDataAt || 'Нет данных')}</dd></div>
        <div><dt>Уверенность данных</dt><dd>{typeof object.properties.confidence === 'number' ? `${Math.round(object.properties.confidence * 100)}%` : 'Нет данных'}</dd></div>
      </>}
      {object.categoryId.startsWith('kindergarten-') && <>
        <div><dt>Тип</dt><dd>{object.properties.operatorType === 'public' ? 'Государственный' : object.properties.operatorType === 'private' ? 'Частный' : 'Неизвестен'}</dd></div>
        <div><dt>Адрес</dt><dd>{String(object.properties.address || 'Нет данных')}</dd></div>
        <div><dt>Актуальность источника</dt><dd>{String(object.properties.sourceDataAt || 'Нет данных')}</dd></div>
        <div><dt>Уверенность данных</dt><dd>{typeof object.properties.confidence === 'number' ? `${Math.round(object.properties.confidence * 100)}%` : 'Нет данных'}</dd></div>
      </>}
      {object.categoryId.startsWith('medical-') && <>
        <div><dt>Форма собственности</dt><dd>{object.properties.ownershipType === 'public' ? 'Государственная' : object.properties.ownershipType === 'private' ? 'Частная' : 'Неизвестна'}</dd></div>
        <div><dt>Адрес</dt><dd>{String(object.properties.address || 'Нет данных')}</dd></div>
        {object.properties.organization && <div><dt>Организация / сеть</dt><dd>{String(object.properties.organization)}</dd></div>}
        {object.properties.openingHours && <div><dt>Часы работы</dt><dd>{String(object.properties.openingHours)}</dd></div>}
        {object.properties.is24h === true && <div><dt>Круглосуточно</dt><dd>Да</dd></div>}
        {object.properties.phone && <div><dt>Телефон</dt><dd>{String(object.properties.phone)}</dd></div>}
        {object.properties.website && <div><dt>Сайт</dt><dd>{String(object.properties.website)}</dd></div>}
        {Array.isArray(object.properties.services) && object.properties.services.length > 0 && <div><dt>Специализации</dt><dd>{object.properties.services.join(', ')}</dd></div>}
        <div><dt>Актуальность источника</dt><dd>{String(object.properties.sourceDataAt || 'Нет данных')}</dd></div>
        <div><dt>Уверенность данных</dt><dd>{typeof object.properties.confidence === 'number' ? `${Math.round(object.properties.confidence * 100)}%` : 'Нет данных'}</dd></div>
      </>}
      {object.categoryId.startsWith('road-') && <>
        <div><dt>Тип дороги</dt><dd>{String(object.properties.roadType || 'Нет данных')}</dd></div>
        {object.properties.corridor && object.properties.corridor !== 'other' && <div><dt>Коридор</dt><dd>{object.properties.corridor === 'kad' ? 'КАД' : 'ЗСД'}</dd></div>}
        {object.properties.ref && <div><dt>Номер</dt><dd>{String(object.properties.ref)}</dd></div>}
        {object.properties.roadClass && <div><dt>Класс OSM</dt><dd>{String(object.properties.roadClass)}</dd></div>}
        {object.properties.toll !== null && object.properties.toll !== undefined && <div><dt>Платная</dt><dd>{object.properties.toll ? 'Да' : 'Нет'}</dd></div>}
        {object.properties.lanes && <div><dt>Полосы</dt><dd>{String(object.properties.lanes)}</dd></div>}
        {object.properties.maxspeed && <div><dt>Ограничение скорости</dt><dd>{String(object.properties.maxspeed)}</dd></div>}
        <div><dt>Уверенность данных</dt><dd>{typeof object.properties.confidence === 'number' ? `${Math.round(object.properties.confidence * 100)}%` : 'Нет данных'}</dd></div>
      </>}
    </dl>
    <p className="card-description">{object.description || 'Нет данных'}</p>
  </aside>;
}
