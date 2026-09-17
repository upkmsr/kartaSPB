import type { DrawingDraft, UserGeometry, UserGeometryType } from '../domain/userGeometry';
import { draftGeometry } from '../domain/userGeometry';

interface DrawingPanelProps {
  draft: DrawingDraft | null;
  items: readonly UserGeometry[];
  busy: boolean;
  error: string | null;
  onStart: (type: UserGeometryType) => void;
  onChange: (patch: Partial<Pick<DrawingDraft, 'name' | 'description'>>) => void;
  onRemoveLast: () => void;
  onClear: () => void;
  onCancel: () => void;
  onSave: () => void;
  onSelect: (id: string) => void;
}

export function DrawingPanel(props: DrawingPanelProps) {
  const { draft } = props;
  return <details className="drawing-panel" open={draft ? true : undefined}>
    <summary>Мои геометрии <span>{props.items.length}</span></summary>
    <div className="drawing-content">
      {!draft ? <>
        <p>Выберите инструмент и нажмите на карту. Линии и области создаются последовательными касаниями.</p>
        <div className="drawing-actions">
          <button type="button" onClick={() => props.onStart('Point')}>Добавить точку</button>
          <button type="button" onClick={() => props.onStart('LineString')}>Нарисовать линию</button>
          <button type="button" onClick={() => props.onStart('Polygon')}>Нарисовать область</button>
        </div>
      </> : <>
        <p role="status">{draft.editingId ? 'Редактирование' : 'Рисование'}: {draft.type} · вершин {draft.vertices.length}.
          {draft.selectedVertex !== undefined ? ' Нажмите новое место для выбранной вершины.' : ' Нажимайте на карту для добавления вершин.'}</p>
        <label>Название<input value={draft.name} maxLength={120} onChange={(event) => props.onChange({ name: event.target.value })} /></label>
        <label>Описание<textarea value={draft.description} maxLength={2000} onChange={(event) => props.onChange({ description: event.target.value })} /></label>
        <div className="drawing-actions">
          {draft.type !== 'Point' && <>
            <button type="button" onClick={props.onRemoveLast} disabled={!draft.vertices.length}>Убрать последнюю вершину</button>
            <button type="button" onClick={props.onClear} disabled={!draft.vertices.length}>Очистить вершины</button>
          </>}
          <button type="button" onClick={props.onSave} disabled={props.busy || !draft.name.trim() || !draftGeometry(draft)}>{props.busy ? 'Сохраняем…' : 'Сохранить'}</button>
          <button type="button" onClick={props.onCancel}>Отменить рисование</button>
        </div>
        {draft.type === 'Polygon' && <p>Для области нужны минимум 3 вершины. Для изменения вершины нажмите её маркер, затем новое место.</p>}
      </>}
      {props.error && <p role="alert">{props.error}</p>}
      <div className="user-geometry-list">
        {props.items.map((item) => <button key={item.id} type="button" onClick={() => props.onSelect(item.id)}>
          {item.name} · {item.geometryType}
        </button>)}
      </div>
    </div>
  </details>;
}
