import type { District } from '../domain/district';
import type { DistrictId } from '../domain/district';
import type { LayerRegistry, ProjectLayerId } from '../domain/layers';
import { orderedLayers } from '../domain/layers';

interface DistrictPanelProps {
  districts: readonly District[];
  selectedIds: readonly DistrictId[];
  layers: LayerRegistry;
  onDistrictToggle: (id: DistrictId) => void;
  onClearDistricts: () => void;
  onLayerVisibilityChange: (id: ProjectLayerId, visible: boolean) => void;
  onLayerOpacityChange: (id: ProjectLayerId, opacity: number) => void;
}

export function DistrictPanel(props: DistrictPanelProps) {
  return <aside className="district-panel" aria-label="Районы и слои">
    <details open>
      <summary>Районы <span>{props.selectedIds.length || 'все'}</span></summary>
      <div className="panel-section">
        <div className="panel-heading">
          <span>{props.selectedIds.length ? `Выбрано: ${props.selectedIds.length}` : 'Без ограничения'}</span>
          <button type="button" disabled={!props.selectedIds.length} onClick={props.onClearDistricts}>Сбросить</button>
        </div>
        <div className="district-list">
          {props.districts.map((district) => <label key={district.id}>
            <input
              type="checkbox"
              checked={props.selectedIds.includes(district.id)}
              onChange={() => props.onDistrictToggle(district.id)}
            />
            <span>{district.properties.name}</span>
          </label>)}
        </div>
      </div>
    </details>
    <details open>
      <summary>Слои</summary>
      <div className="panel-section layer-list">
        {orderedLayers(props.layers).map((layer) => <div className="layer-control" key={layer.id}>
          <label>
            <input
              type="checkbox"
              checked={layer.visible}
              onChange={(event) => props.onLayerVisibilityChange(layer.id, event.target.checked)}
            />
            <span>{layer.name}</span>
          </label>
          <label className="opacity-control">
            <span>Прозрачность {Math.round(layer.opacity * 100)}%</span>
            <input
              aria-label={`Прозрачность слоя «${layer.name}»`}
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={layer.opacity}
              disabled={!layer.visible}
              onChange={(event) => props.onLayerOpacityChange(layer.id, Number(event.target.value))}
            />
          </label>
        </div>)}
        <p>Закреплённые территории школ: официальные адресные списки, проверенных полигонов нет. Включение слоя не означает право зачисления.</p>
      </div>
    </details>
  </aside>;
}
