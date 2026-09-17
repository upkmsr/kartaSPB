import type { UserGeometry } from '../domain/userGeometry';

interface Props {
  item: UserGeometry;
  deleting: boolean;
  confirmDelete: boolean;
  error: string | null;
  onEdit: () => void;
  onDelete: () => void;
  onClose: () => void;
}

export function UserGeometryCard({ item, deleting, confirmDelete, error, onEdit, onDelete, onClose }: Props) {
  return <aside className="object-card user-geometry-card" aria-label="Пользовательская геометрия">
    <div className="card-heading"><p className="eyebrow">МОЯ ГЕОМЕТРИЯ</p>
      <button className="close-card" onClick={onClose} aria-label="Закрыть карточку">×</button></div>
    <h2>{item.name}</h2>
    <dl>
      <div><dt>Тип</dt><dd>{item.geometryType}</dd></div>
      <div><dt>Создано</dt><dd>{new Date(item.createdAt).toLocaleString('ru-RU')}</dd></div>
      <div><dt>Обновлено</dt><dd>{new Date(item.updatedAt).toLocaleString('ru-RU')}</dd></div>
    </dl>
    <p className="card-description">{item.description || 'Описание не задано'}</p>
    <div className="drawing-actions">
      <button type="button" onClick={onEdit}>Редактировать</button>
      <button type="button" onClick={onDelete} disabled={deleting}>{confirmDelete ? 'Подтвердить удаление' : 'Удалить'}</button>
    </div>
    {error && <p role="alert">{error}</p>}
  </aside>;
}
