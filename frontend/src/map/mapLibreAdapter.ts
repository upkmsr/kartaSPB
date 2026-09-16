import { AttributionControl, Map, NavigationControl, setWorkerUrl } from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import type { AddLayerObject, ExpressionSpecification, FilterSpecification, GeoJSONSource } from 'maplibre-gl';
import type { FeatureCollection, MultiPolygon, Polygon } from 'geojson';
import type { MapConfig } from '../config/map';
import type { DistrictId, DistrictProperties } from '../domain/district';
import type { LayerRegistry, ProjectLayerId } from '../domain/layers';
import { orderedLayers } from '../domain/layers';
import type { Category, MapObject } from '../domain/mapObject';
import { toGeoJSON } from '../domain/mapObject';
import type { MapTarget } from '../domain/search';

const SOURCES = { districts: 'districts', 'demo-object': 'demo-objects' } as const;
const DISTRICT_FILL = 'district-fill';
const DISTRICT_OUTLINE = 'district-outline';
const DISTRICT_SELECTED = 'district-selected';
const OBJECT_LAYER = 'demo-points';
const GREEN_FILL = 'nature-green-fill';
const GREEN_LINE = 'nature-green-line';
const WATER_FILL = 'nature-water-fill';
const WATER_LINE = 'nature-water-line';
const METRO_LINE = 'metro-lines';
const METRO_STATION = 'metro-stations';
const METRO_ENTRANCE = 'metro-entrances';
const BUS_ROUTES = 'transport-bus-routes';
const TRAM_ROUTES = 'transport-tram-routes';
const TROLLEYBUS_ROUTES = 'transport-trolleybus-routes';
const TRANSPORT_STOPS = 'transport-stops';
const SCHOOL_POINTS = 'school-points';
const SCHOOL_CATCHMENTS = 'school-catchments';
const SEARCH_SOURCE = 'search-result';
const SEARCH_LAYER = 'search-result-marker';
const MAP_LAYERS: Record<ProjectLayerId, readonly string[]> = {
  districts: [DISTRICT_FILL, DISTRICT_OUTLINE, DISTRICT_SELECTED],
  'demo-object': [OBJECT_LAYER],
  'nature-green': [GREEN_FILL, GREEN_LINE],
  'nature-water': [WATER_FILL, WATER_LINE],
  'metro-lines': [METRO_LINE],
  'metro-stations': [METRO_STATION],
  'metro-entrances': [METRO_ENTRANCE],
  'transport-bus': [BUS_ROUTES],
  'transport-tram': [TRAM_ROUTES],
  'transport-trolleybus': [TROLLEYBUS_ROUTES],
  'transport-stops': [TRANSPORT_STOPS],
  schools: [SCHOOL_POINTS],
  'school-catchments': [SCHOOL_CATCHMENTS],
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
  setWorkerUrl(workerUrl);
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
  let currentObjects = objects;
  let categories: Category[] = [];
  let visibleCategories: string[] = [];
  const applyCategories = () => {
    if (!loaded) return;
    const visible: FilterSpecification = ['in', ['get', 'categoryId'], ['literal', visibleCategories]];
    map.setFilter(OBJECT_LAYER, ['all', visible, ['==', ['geometry-type'], 'Point'], [
      '!', ['in', ['get', 'categoryId'], ['literal', [
        'metro-station', 'metro-entrance', 'transport-stop', 'school',
      ]]],
    ]]);
    for (const [layer, category] of [
      [GREEN_FILL, 'nature-green'], [GREEN_LINE, 'nature-green'],
      [WATER_FILL, 'nature-water'], [WATER_LINE, 'nature-water'],
    ] as const) {
      map.setFilter(layer, ['all', visible, ['==', ['get', 'categoryId'], category]]);
    }
    map.setFilter(SCHOOL_POINTS, ['all', visible, ['==', ['get', 'categoryId'], 'school']]);
    map.setFilter(METRO_LINE, ['all', visible, ['==', ['get', 'categoryId'], 'metro-line']]);
    map.setFilter(METRO_STATION, ['all', visible, ['==', ['get', 'categoryId'], 'metro-station']]);
    map.setFilter(METRO_ENTRANCE, ['all', visible, ['==', ['get', 'categoryId'], 'metro-entrance']]);
    for (const [layer, category] of [
      [BUS_ROUTES, 'transport-bus'], [TRAM_ROUTES, 'transport-tram'],
      [TROLLEYBUS_ROUTES, 'transport-trolleybus'], [TRANSPORT_STOPS, 'transport-stop'],
    ] as const) {
      map.setFilter(layer, ['all', visible, ['==', ['get', 'categoryId'], category]]);
    }
    const color: ExpressionSpecification = categories.length
      ? ['match', ['get', 'categoryId'], ...categories.flatMap((category) => [category.id, category.color]), '#a4b5c5'] as unknown as ExpressionSpecification
      : ['literal', '#a4b5c5'];
    map.setPaintProperty(OBJECT_LAYER, 'circle-color', color);
  };

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
    map.setPaintProperty(GREEN_FILL, 'fill-opacity', 0.5 * registry['nature-green'].opacity);
    map.setPaintProperty(GREEN_LINE, 'line-opacity', registry['nature-green'].opacity);
    map.setPaintProperty(WATER_FILL, 'fill-opacity', 0.55 * registry['nature-water'].opacity);
    map.setPaintProperty(WATER_LINE, 'line-opacity', registry['nature-water'].opacity);
    map.setPaintProperty(METRO_LINE, 'line-opacity', registry['metro-lines'].opacity);
    map.setPaintProperty(METRO_STATION, 'circle-opacity', registry['metro-stations'].opacity);
    map.setPaintProperty(METRO_ENTRANCE, 'circle-opacity', registry['metro-entrances'].opacity);
    map.setPaintProperty(BUS_ROUTES, 'line-opacity', registry['transport-bus'].opacity);
    map.setPaintProperty(TRAM_ROUTES, 'line-opacity', registry['transport-tram'].opacity);
    map.setPaintProperty(TROLLEYBUS_ROUTES, 'line-opacity', registry['transport-trolleybus'].opacity);
    map.setPaintProperty(TRANSPORT_STOPS, 'circle-opacity', registry['transport-stops'].opacity);
    map.setPaintProperty(SCHOOL_POINTS, 'circle-opacity', registry.schools.opacity);
    map.setPaintProperty(SCHOOL_CATCHMENTS, 'fill-opacity', registry['school-catchments'].opacity);
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
    map.addSource(SOURCES['demo-object'], { type: 'geojson', data: toGeoJSON(currentObjects) });
    map.addSource(SEARCH_SOURCE, { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addSource(SCHOOL_CATCHMENTS, { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    const definitions: AddLayerObject[] = [
      { id: DISTRICT_FILL, type: 'fill', source: SOURCES.districts, paint: { 'fill-color': '#17343c', 'fill-opacity': 0.14 } },
      { id: DISTRICT_OUTLINE, type: 'line', source: SOURCES.districts, paint: { 'line-color': '#76a9ad', 'line-width': 1.2, 'line-opacity': 0.7 } },
      { id: GREEN_FILL, type: 'fill', source: SOURCES['demo-object'], filter: ['==', ['get', 'categoryId'], 'nature-green'], paint: { 'fill-color': '#55b978', 'fill-opacity': 0.38 } },
      { id: WATER_FILL, type: 'fill', source: SOURCES['demo-object'], filter: ['==', ['get', 'categoryId'], 'nature-water'], paint: { 'fill-color': '#4ba3d3', 'fill-opacity': 0.44 } },
      { id: GREEN_LINE, type: 'line', source: SOURCES['demo-object'], filter: ['==', ['get', 'categoryId'], 'nature-green'], paint: { 'line-color': '#78d696', 'line-width': 3 } },
      { id: WATER_LINE, type: 'line', source: SOURCES['demo-object'], filter: ['==', ['get', 'categoryId'], 'nature-water'], paint: { 'line-color': '#66c4ef', 'line-width': 3 } },
      { id: METRO_LINE, type: 'line', source: SOURCES['demo-object'], filter: ['==', ['get', 'categoryId'], 'metro-line'], paint: {
        'line-color': ['match', ['get', 'lineColor'], 'red', '#d6083b', 'blue', '#0078c9', 'green', '#009a49', 'orange', '#ea7125', 'purple', '#702785', 'brown', '#8d5b2d', '#d7dce2'],
        'line-width': 4,
      } },
      { id: METRO_STATION, type: 'circle', source: SOURCES['demo-object'], filter: ['==', ['get', 'categoryId'], 'metro-station'], paint: { 'circle-radius': 6, 'circle-color': '#ffffff', 'circle-stroke-width': 3, 'circle-stroke-color': '#202b35' } },
      { id: METRO_ENTRANCE, type: 'circle', source: SOURCES['demo-object'], filter: ['==', ['get', 'categoryId'], 'metro-entrance'], paint: { 'circle-radius': 3, 'circle-color': '#9aa8b5', 'circle-stroke-width': 1, 'circle-stroke-color': '#202b35' } },
      { id: BUS_ROUTES, type: 'line', source: SOURCES['demo-object'], filter: ['==', ['get', 'categoryId'], 'transport-bus'], paint: { 'line-color': '#3f9adb', 'line-width': 3 } },
      { id: TRAM_ROUTES, type: 'line', source: SOURCES['demo-object'], filter: ['==', ['get', 'categoryId'], 'transport-tram'], paint: { 'line-color': '#e25353', 'line-width': 3 } },
      { id: TROLLEYBUS_ROUTES, type: 'line', source: SOURCES['demo-object'], filter: ['==', ['get', 'categoryId'], 'transport-trolleybus'], paint: { 'line-color': '#58b9ad', 'line-width': 3 } },
      { id: TRANSPORT_STOPS, type: 'circle', source: SOURCES['demo-object'], filter: ['==', ['get', 'categoryId'], 'transport-stop'], paint: { 'circle-radius': 4, 'circle-color': '#f5d06f', 'circle-stroke-width': 1.5, 'circle-stroke-color': '#42371b' } },
      { id: SCHOOL_CATCHMENTS, type: 'fill', source: SCHOOL_CATCHMENTS, paint: { 'fill-color': '#e2b45e', 'fill-opacity': 0.25 } },
      { id: SCHOOL_POINTS, type: 'circle', source: SOURCES['demo-object'], filter: ['==', ['get', 'categoryId'], 'school'], paint: { 'circle-radius': 6, 'circle-color': '#e2b45e', 'circle-stroke-width': 2, 'circle-stroke-color': '#513b16' } },
      { id: OBJECT_LAYER, type: 'circle', source: SOURCES['demo-object'], paint: { 'circle-radius': 13, 'circle-color': '#77dfcc', 'circle-stroke-width': 4, 'circle-stroke-color': '#163e42' } },
      { id: DISTRICT_SELECTED, type: 'line', source: SOURCES.districts, filter: ['in', ['get', 'id'], ['literal', []]], paint: { 'line-color': '#b8fff2', 'line-width': 3, 'line-opacity': 0.7 } },
      { id: SEARCH_LAYER, type: 'circle', source: SEARCH_SOURCE, paint: { 'circle-radius': 10, 'circle-color': '#ffc078', 'circle-stroke-width': 4, 'circle-stroke-color': '#402d19' } },
    ];
    for (const definition of definitions) map.addLayer(definition);
    loaded = true;
    applyLayers();
    applySelection();
    applyCategories();
    callbacks.onReady();
  });
  map.on('click', (event) => {
    if (!loaded) return;
    const objectLayers = [
      OBJECT_LAYER, GREEN_FILL, GREEN_LINE, WATER_FILL, WATER_LINE,
      METRO_LINE, METRO_STATION, METRO_ENTRANCE,
      BUS_ROUTES, TRAM_ROUTES, TROLLEYBUS_ROUTES, TRANSPORT_STOPS,
      SCHOOL_POINTS,
    ];
    const features = map.queryRenderedFeatures(event.point, { layers: [...objectLayers, DISTRICT_FILL] });
    const object = features.find((feature) => objectLayers.includes(feature.layer.id));
    const objectId = object?.properties.id ?? object?.id;
    if (typeof objectId === 'string') { callbacks.onObjectClick(objectId); return; }
    const district = features.find((feature) => feature.layer.id === DISTRICT_FILL);
    const id = district?.properties.id;
    if (typeof id === 'string' && id.startsWith('district-osm-relation-')) callbacks.onDistrictClick(id as DistrictId);
  });
  map.on('mousemove', (event) => {
    if (!loaded) return;
    map.getCanvas().style.cursor = map.queryRenderedFeatures(event.point, {
      layers: [
        OBJECT_LAYER, GREEN_FILL, GREEN_LINE, WATER_FILL, WATER_LINE,
        METRO_LINE, METRO_STATION, METRO_ENTRANCE, DISTRICT_FILL,
        BUS_ROUTES, TRAM_ROUTES, TROLLEYBUS_ROUTES, TRANSPORT_STOPS,
        SCHOOL_POINTS,
      ],
    }).length ? 'pointer' : '';
  });
  map.on('error', () => { if (!loaded) callbacks.onError(); });

  return {
    resize: () => map.resize(), remove: () => map.remove(),
    setSelectedDistricts: (ids: readonly DistrictId[]) => { selectedIds = ids; applySelection(); },
    setLayers: (layers: LayerRegistry) => { registry = layers; applyLayers(); },
    setObjects: (data: MapObject[]) => {
      currentObjects = data;
      if (loaded) (map.getSource(SOURCES['demo-object']) as GeoJSONSource).setData(toGeoJSON(data));
    },
    setCategories: (definitions: Category[], ids: string[]) => {
      categories = definitions; visibleCategories = ids; applyCategories();
    },
    focus: (target: MapTarget) => {
      if (!loaded) return;
      const source = map.getSource(SEARCH_SOURCE) as GeoJSONSource;
      source.setData({ type: 'FeatureCollection', features: target.showMarker ? [{
        type: 'Feature', properties: {}, geometry: { type: 'Point', coordinates: target.coordinates },
      }] : [] });
      map.flyTo({ center: target.coordinates, zoom: Math.max(map.getZoom(), 14) });
    },
  };
}
