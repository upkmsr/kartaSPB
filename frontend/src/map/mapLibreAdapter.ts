import { AttributionControl, Map, NavigationControl } from 'maplibre-gl';
import type { AddLayerObject, ExpressionSpecification, FilterSpecification } from 'maplibre-gl';
import type { FeatureCollection, MultiPolygon, Polygon } from 'geojson';
import type { MapConfig } from '../config/map';
import type { DistrictId, DistrictProperties } from '../domain/district';
import type { LayerRegistry, ProjectLayerId } from '../domain/layers';
import { orderedLayers } from '../domain/layers';
import type { MapObject } from '../domain/mapObject';

const SOURCES = { districts: 'districts', 'demo-object': 'demo-objects' } as const;
const DISTRICT_FILL = 'district-fill';
const DISTRICT_OUTLINE = 'district-outline';
const DISTRICT_SELECTED = 'district-selected';
const OBJECT_LAYER = 'demo-points';
const MAP_LAYERS: Record<ProjectLayerId, readonly string[]> = {
  districts: [DISTRICT_FILL, DISTRICT_OUTLINE, DISTRICT_SELECTED],
  'demo-object': [OBJECT_LAYER],
};

interface MapCallbacks {
  onObjectClick: (id: string) => void;
  onDistrictClick: (id: DistrictId) => void;
  onReady: () => void;
  onError: () => void;
}

export function createMap(
  container: HTMLDivElement,
  config: MapConfig,
  objects: MapObject[],
  districtData: FeatureCollection<Polygon | MultiPolygon, DistrictProperties>,
  callbacks: MapCallbacks,
) {
  const map = new Map({
    container, style: config.style.url, center: config.center, zoom: config.zoom,
    attributionControl: false, dragRotate: false, pitchWithRotate: false, touchPitch: false,
    locale: {
      'NavigationControl.ZoomIn': 'Приблизить', 'NavigationControl.ZoomOut': 'Отдалить',
      'AttributionControl.ToggleAttribution': 'Источники карты', 'Map.Title': 'Карта Санкт-Петербурга',
    },
  });
  let loaded = false;
  let selectedIds: readonly DistrictId[] = [];
  let registry: LayerRegistry | undefined;

  const selectionFilter = (): FilterSpecification => ['in', ['get', 'id'], ['literal', [...selectedIds]]];
  const applySelection = () => {
    if (!loaded) return;
    map.setFilter(DISTRICT_SELECTED, selectionFilter());
    const selected = selectionFilter() as ExpressionSpecification;
    map.setPaintProperty(DISTRICT_FILL, 'fill-color', selectedIds.length
      ? ['case', selected, '#77dfcc', '#07111a'] : '#17343c');
    const opacity = registry?.districts.opacity ?? 0.7;
    map.setPaintProperty(DISTRICT_FILL, 'fill-opacity', selectedIds.length
      ? ['case', selected, 0.24 * opacity, 0.68 * opacity] : 0.2 * opacity);
  };
  const applyLayers = () => {
    if (!loaded || !registry) return;
    for (const layer of orderedLayers(registry)) {
      for (const mapLayer of MAP_LAYERS[layer.id]) {
        map.setLayoutProperty(mapLayer, 'visibility', layer.visible ? 'visible' : 'none');
      }
    }
    map.setPaintProperty(DISTRICT_OUTLINE, 'line-opacity', registry.districts.opacity);
    map.setPaintProperty(DISTRICT_SELECTED, 'line-opacity', registry.districts.opacity);
    map.setPaintProperty(OBJECT_LAYER, 'circle-opacity', registry['demo-object'].opacity);
    map.setPaintProperty(OBJECT_LAYER, 'circle-stroke-opacity', registry['demo-object'].opacity);
    applySelection();
  };

  map.touchZoomRotate.disableRotation();
  map.addControl(new NavigationControl({ showCompass: false }), 'top-right');
  map.addControl(new AttributionControl({
    compact: false,
    customAttribution: `${config.style.attribution} · District boundaries © <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap contributors</a>`,
  }), 'bottom-left');

  map.on('style.load', () => {
    map.addSource(SOURCES.districts, { type: 'geojson', data: districtData });
    map.addSource(SOURCES['demo-object'], { type: 'geojson', data: { type: 'FeatureCollection', features: objects } });
    const definitions: AddLayerObject[] = [
      { id: DISTRICT_FILL, type: 'fill', source: SOURCES.districts, paint: { 'fill-color': '#17343c', 'fill-opacity': 0.14 } },
      { id: DISTRICT_OUTLINE, type: 'line', source: SOURCES.districts, paint: { 'line-color': '#76a9ad', 'line-width': 1.2, 'line-opacity': 0.7 } },
      { id: OBJECT_LAYER, type: 'circle', source: SOURCES['demo-object'], paint: { 'circle-radius': 13, 'circle-color': '#77dfcc', 'circle-stroke-width': 4, 'circle-stroke-color': '#163e42' } },
      { id: DISTRICT_SELECTED, type: 'line', source: SOURCES.districts, filter: ['in', ['get', 'id'], ['literal', []]], paint: { 'line-color': '#b8fff2', 'line-width': 3, 'line-opacity': 0.7 } },
    ];
    for (const definition of definitions) map.addLayer(definition);
    loaded = true;
    applyLayers();
    applySelection();
    callbacks.onReady();
  });
  map.on('click', (event) => {
    const features = map.queryRenderedFeatures(event.point, { layers: [OBJECT_LAYER, DISTRICT_FILL] });
    const object = features.find((feature) => feature.layer.id === OBJECT_LAYER);
    if (typeof object?.id === 'string') { callbacks.onObjectClick(object.id); return; }
    const district = features.find((feature) => feature.layer.id === DISTRICT_FILL);
    const id = district?.properties.id;
    if (typeof id === 'string' && id.startsWith('district-osm-relation-')) callbacks.onDistrictClick(id as DistrictId);
  });
  map.on('mousemove', (event) => {
    map.getCanvas().style.cursor = map.queryRenderedFeatures(event.point, { layers: [OBJECT_LAYER, DISTRICT_FILL] }).length ? 'pointer' : '';
  });
  map.on('error', () => { if (!loaded) callbacks.onError(); });

  return {
    resize: () => map.resize(), remove: () => map.remove(),
    setSelectedDistricts: (ids: readonly DistrictId[]) => { selectedIds = ids; applySelection(); },
    setLayers: (layers: LayerRegistry) => { registry = layers; applyLayers(); },
  };
}
