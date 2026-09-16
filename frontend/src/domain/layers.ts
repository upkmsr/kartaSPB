export type ProjectLayerId =
  | 'districts' | 'demo-object' | 'nature-green' | 'nature-water'
  | 'metro-lines' | 'metro-stations' | 'metro-entrances'
  | 'transport-bus' | 'transport-tram' | 'transport-trolleybus' | 'transport-stops'
  | 'schools' | 'school-catchments';

export interface LayerDefinition {
  id: ProjectLayerId;
  name: string;
  visible: boolean;
  opacity: number;
  order: number;
}

export type LayerRegistry = Record<ProjectLayerId, LayerDefinition>;

export const initialLayerRegistry: LayerRegistry = {
  districts: { id: 'districts', name: 'Районы', visible: true, opacity: 0.7, order: 10 },
  'demo-object': { id: 'demo-object', name: 'Объекты проекта', visible: true, opacity: 1, order: 20 },
  'nature-green': { id: 'nature-green', name: 'Зелёные территории', visible: true, opacity: 0.75, order: 30 },
  'nature-water': { id: 'nature-water', name: 'Вода', visible: true, opacity: 0.8, order: 40 },
  'metro-lines': { id: 'metro-lines', name: 'Линии метро', visible: true, opacity: 0.9, order: 50 },
  'metro-stations': { id: 'metro-stations', name: 'Станции метро', visible: true, opacity: 1, order: 60 },
  'metro-entrances': { id: 'metro-entrances', name: 'Входы в метро', visible: false, opacity: 0.9, order: 70 },
  'transport-bus': { id: 'transport-bus', name: 'Автобусы', visible: false, opacity: 0.8, order: 80 },
  'transport-tram': { id: 'transport-tram', name: 'Трамваи', visible: false, opacity: 0.85, order: 90 },
  'transport-trolleybus': { id: 'transport-trolleybus', name: 'Троллейбусы', visible: false, opacity: 0.85, order: 100 },
  'transport-stops': { id: 'transport-stops', name: 'Остановки транспорта', visible: false, opacity: 1, order: 110 },
  schools: { id: 'schools', name: 'Школы', visible: true, opacity: 1, order: 120 },
  'school-catchments': { id: 'school-catchments', name: 'Закреплённые территории школ', visible: false, opacity: 0.5, order: 130 },
};

export function updateLayer(
  registry: LayerRegistry,
  id: ProjectLayerId,
  patch: Partial<Pick<LayerDefinition, 'visible' | 'opacity'>>,
): LayerRegistry {
  const opacity = patch.opacity === undefined
    ? registry[id].opacity
    : Math.min(1, Math.max(0, patch.opacity));
  return { ...registry, [id]: { ...registry[id], ...patch, opacity } };
}

export function orderedLayers(registry: LayerRegistry): LayerDefinition[] {
  return Object.values(registry).sort((left, right) => left.order - right.order);
}
