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
import type { DrawingDraft, UserGeometry } from '../domain/userGeometry';
import { draftPreview, toUserGeoJSON } from '../domain/userGeometry';

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
const KINDERGARTEN_POINTS = 'kindergarten-points';
const MEDICAL_POINTS = 'medical-points';
const PHARMACY_SOURCE = 'pharmacies';
const PHARMACY_CLUSTERS = 'pharmacy-clusters';
const PHARMACY_POINTS = 'pharmacy-points';
const ROADS_SOURCE = 'roads';
const ROAD_MAJOR = 'road-major-lines';
const ROAD_KAD = 'road-kad-lines';
const ROAD_ZSD = 'road-zsd-lines';
const ROAD_RAMPS = 'road-ramp-lines';
const ROAD_INTERCHANGES = 'road-interchange-points';
const NOISE_SOURCE = 'noise';
const NOISE_ROAD = 'noise-road-lines';
const NOISE_RAILWAY = 'noise-railway-lines';
const NOISE_AVIATION = 'noise-aviation-fill';
const NOISE_HELICOPTER = 'noise-helicopter-lines';
const USER_SOURCE = 'user-geometries';
const DRAFT_SOURCE = 'drawing-preview';
const USER_POINTS = 'user-points';
const USER_LINES = 'user-lines';
const USER_AREAS = 'user-areas';
const DRAFT_FILL = 'drawing-fill';
const DRAFT_LINE = 'drawing-line';
const DRAFT_VERTICES = 'drawing-vertices';
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
  kindergartens: [KINDERGARTEN_POINTS],
  medical: [MEDICAL_POINTS],
  pharmacies: [PHARMACY_CLUSTERS, PHARMACY_POINTS],
  'road-major': [ROAD_MAJOR],
  'road-kad': [ROAD_KAD],
  'road-zsd': [ROAD_ZSD],
  'road-interchanges': [ROAD_RAMPS, ROAD_INTERCHANGES],
  'noise-road': [NOISE_ROAD],
  'noise-railway': [NOISE_RAILWAY],
  'noise-aviation': [NOISE_AVIATION],
  'noise-helicopter': [NOISE_HELICOPTER],
  'user-points': [USER_POINTS],
  'user-lines': [USER_LINES],
  'user-areas': [USER_AREAS],
};

interface MapCallbacks {
  onObjectClick: (id: string) => void;
  onDistrictClick: (id: DistrictId) => void;
  onUserGeometryClick?: (id: string) => void;
  onDrawingClick?: (coordinate: [number, number]) => void;
  onDrawingVertexClick?: (index: number) => void;
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
  let currentUserGeometries: UserGeometry[] = [];
  let drawingDraft: DrawingDraft | null = null;
  let categories: Category[] = [];
  let visibleCategories: string[] = [];
  const applyCategories = () => {
    if (!loaded) return;
    const visible: FilterSpecification = ['in', ['get', 'categoryId'], ['literal', visibleCategories]];
    map.setFilter(OBJECT_LAYER, ['all', visible, ['==', ['geometry-type'], 'Point'], [
      '!', ['in', ['get', 'categoryId'], ['literal', [
        'metro-station', 'metro-entrance', 'transport-stop', 'school',
        'kindergarten-public', 'kindergarten-private', 'kindergarten-unknown',
        'medical-public_polyclinic', 'medical-children_polyclinic', 'medical-hospital',
        'medical-private_multispecialty_clinic', 'medical-diagnostic_center',
        'medical-laboratory', 'medical-dentistry', 'medical-womens_health',
        'medical-specialized_center', 'medical-trauma_center', 'medical-emergency_or_24h',
      ]]],
    ]]);
    for (const [layer, category] of [
      [GREEN_FILL, 'nature-green'], [GREEN_LINE, 'nature-green'],
      [WATER_FILL, 'nature-water'], [WATER_LINE, 'nature-water'],
    ] as const) {
      map.setFilter(layer, ['all', visible, ['==', ['get', 'categoryId'], category]]);
    }
    map.setFilter(SCHOOL_POINTS, ['all', visible, ['==', ['get', 'categoryId'], 'school']]);
    map.setFilter(KINDERGARTEN_POINTS, ['all', visible, ['in', ['get', 'categoryId'], [
      'literal', ['kindergarten-public', 'kindergarten-private', 'kindergarten-unknown'],
    ]]]);
    map.setFilter(MEDICAL_POINTS, ['all', visible, ['in', ['get', 'categoryId'], ['literal', [
      'medical-public_polyclinic', 'medical-children_polyclinic', 'medical-hospital',
      'medical-private_multispecialty_clinic', 'medical-diagnostic_center',
      'medical-laboratory', 'medical-dentistry', 'medical-womens_health',
      'medical-specialized_center', 'medical-trauma_center', 'medical-emergency_or_24h',
    ]]]]);
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
    const showPharmacies = Boolean(registry?.pharmacies.visible && visibleCategories.includes('medical-pharmacy'));
    for (const layer of MAP_LAYERS.pharmacies) map.setLayoutProperty(layer, 'visibility', showPharmacies ? 'visible' : 'none');
    for (const [layer, category] of [
      [ROAD_MAJOR, 'road-major'], [ROAD_KAD, 'road-kad'], [ROAD_ZSD, 'road-zsd'],
      [ROAD_RAMPS, 'road-ramp'], [ROAD_INTERCHANGES, 'road-interchange'],
    ] as const) map.setFilter(layer, ['all', visible, ['==', ['get', 'categoryId'], category]]);
    for (const [id, categoriesForLayer] of [
      ['road-major', ['road-major']], ['road-kad', ['road-kad']],
      ['road-zsd', ['road-zsd']], ['road-interchanges', ['road-ramp', 'road-interchange']],
    ] as const) {
      const show = Boolean(registry?.[id].visible && categoriesForLayer.some((category) => visibleCategories.includes(category)));
      for (const layer of MAP_LAYERS[id]) map.setLayoutProperty(layer, 'visibility', show ? 'visible' : 'none');
    }
    for (const [layer, category] of [
      [NOISE_ROAD, 'noise-road'], [NOISE_RAILWAY, 'noise-railway'],
      [NOISE_AVIATION, 'noise-aviation'], [NOISE_HELICOPTER, 'noise-helicopter'],
    ] as const) map.setFilter(layer, ['all', visible, ['==', ['get', 'categoryId'], category]]);
    for (const id of ['noise-road', 'noise-railway', 'noise-aviation', 'noise-helicopter'] as const) {
      map.setLayoutProperty(MAP_LAYERS[id][0], 'visibility', registry?.[id].visible && visibleCategories.includes(id) ? 'visible' : 'none');
    }
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
        const selected = layer.id === 'pharmacies' ? visibleCategories.includes('medical-pharmacy')
          : layer.id === 'road-interchanges' ? visibleCategories.includes('road-ramp') || visibleCategories.includes('road-interchange')
            : layer.id.startsWith('road-') || layer.id.startsWith('noise-') ? visibleCategories.includes(layer.id) : true;
        map.setLayoutProperty(mapLayer, 'visibility', layer.visible && selected ? 'visible' : 'none');
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
    map.setPaintProperty(KINDERGARTEN_POINTS, 'circle-opacity', registry.kindergartens.opacity);
    map.setPaintProperty(MEDICAL_POINTS, 'circle-opacity', registry.medical.opacity);
    map.setPaintProperty(PHARMACY_POINTS, 'circle-opacity', registry.pharmacies.opacity);
    map.setPaintProperty(PHARMACY_CLUSTERS, 'circle-opacity', registry.pharmacies.opacity);
    map.setPaintProperty(ROAD_MAJOR, 'line-opacity', registry['road-major'].opacity);
    map.setPaintProperty(ROAD_KAD, 'line-opacity', registry['road-kad'].opacity);
    map.setPaintProperty(ROAD_ZSD, 'line-opacity', registry['road-zsd'].opacity);
    map.setPaintProperty(ROAD_RAMPS, 'line-opacity', registry['road-interchanges'].opacity);
    map.setPaintProperty(ROAD_INTERCHANGES, 'circle-opacity', registry['road-interchanges'].opacity);
    map.setPaintProperty(NOISE_ROAD, 'line-opacity', registry['noise-road'].opacity);
    map.setPaintProperty(NOISE_RAILWAY, 'line-opacity', registry['noise-railway'].opacity);
    map.setPaintProperty(NOISE_AVIATION, 'fill-opacity', registry['noise-aviation'].opacity * 0.4);
    map.setPaintProperty(NOISE_HELICOPTER, 'line-opacity', registry['noise-helicopter'].opacity);
    map.setPaintProperty(USER_POINTS, 'circle-opacity', registry['user-points'].opacity);
    map.setPaintProperty(USER_LINES, 'line-opacity', registry['user-lines'].opacity);
    map.setPaintProperty(USER_AREAS, 'fill-opacity', 0.35 * registry['user-areas'].opacity);
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
    map.addSource(PHARMACY_SOURCE, { type: 'geojson', data: { type: 'FeatureCollection', features: [] }, cluster: true, clusterRadius: 45 });
    map.addSource(ROADS_SOURCE, { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addSource(NOISE_SOURCE, { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addSource(USER_SOURCE, { type: 'geojson', data: toUserGeoJSON(currentUserGeometries) });
    map.addSource(DRAFT_SOURCE, { type: 'geojson', data: draftPreview(drawingDraft) });
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
      { id: KINDERGARTEN_POINTS, type: 'circle', source: SOURCES['demo-object'], filter: ['in', ['get', 'categoryId'], ['literal', ['kindergarten-public', 'kindergarten-private', 'kindergarten-unknown']]], paint: {
        'circle-radius': 5,
        'circle-color': ['match', ['get', 'categoryId'], 'kindergarten-public', '#b178dc', 'kindergarten-private', '#d76caa', '#a8a3b6'],
        'circle-stroke-width': 2, 'circle-stroke-color': '#392448',
      } },
      { id: MEDICAL_POINTS, type: 'circle', source: SOURCES['demo-object'], filter: ['in', ['get', 'categoryId'], ['literal', []]], paint: {
        'circle-radius': 5, 'circle-color': '#57c6c2', 'circle-stroke-width': 1.5, 'circle-stroke-color': '#174d58',
      } },
      { id: PHARMACY_CLUSTERS, type: 'circle', source: PHARMACY_SOURCE, filter: ['has', 'point_count'], paint: {
        'circle-radius': ['step', ['get', 'point_count'], 12, 20, 17, 100, 22], 'circle-color': '#4fad73',
        'circle-stroke-width': 2, 'circle-stroke-color': '#1a5134',
      } },
      { id: PHARMACY_POINTS, type: 'circle', source: PHARMACY_SOURCE, filter: ['!', ['has', 'point_count']], paint: {
        'circle-radius': 4, 'circle-color': '#68bb87', 'circle-stroke-width': 1, 'circle-stroke-color': '#1a5134',
      } },
      { id: ROAD_MAJOR, type: 'line', source: ROADS_SOURCE, paint: { 'line-color': '#8795a4', 'line-width': 1.8 } },
      { id: ROAD_KAD, type: 'line', source: ROADS_SOURCE, paint: { 'line-color': '#d69d59', 'line-width': 2.3 } },
      { id: ROAD_ZSD, type: 'line', source: ROADS_SOURCE, paint: { 'line-color': '#7bb0d6', 'line-width': 2.3 } },
      { id: ROAD_RAMPS, type: 'line', source: ROADS_SOURCE, paint: { 'line-color': '#b4ad9c', 'line-width': 1.3 } },
      { id: ROAD_INTERCHANGES, type: 'circle', source: ROADS_SOURCE, paint: {
        'circle-radius': 3.5, 'circle-color': '#d8ba7e', 'circle-stroke-width': 1,
        'circle-stroke-color': '#514633',
      } },
      { id: NOISE_ROAD, type: 'line', source: NOISE_SOURCE, paint: {
        'line-color': ['match', ['get', 'influenceClass'], 'high', '#d56555', 'medium', '#d59b58', 'low', '#a6a773', '#87909c'],
        'line-width': 3,
      } },
      { id: NOISE_RAILWAY, type: 'line', source: NOISE_SOURCE, paint: { 'line-color': '#b48cca', 'line-width': 2.5, 'line-dasharray': [2, 1] } },
      { id: NOISE_AVIATION, type: 'fill', source: NOISE_SOURCE, paint: { 'fill-color': '#7697b7', 'fill-opacity': 0.35 } },
      { id: NOISE_HELICOPTER, type: 'line', source: NOISE_SOURCE, paint: { 'line-color': '#90a5b3', 'line-width': 2 } },
      { id: USER_AREAS, type: 'fill', source: USER_SOURCE, filter: ['==', ['get', 'geometryType'], 'Polygon'], paint: { 'fill-color': '#edcf75', 'fill-opacity': 0.3, 'fill-outline-color': '#f5d988' } },
      { id: USER_LINES, type: 'line', source: USER_SOURCE, filter: ['==', ['get', 'geometryType'], 'LineString'], paint: { 'line-color': '#f4cd69', 'line-width': 4 } },
      { id: USER_POINTS, type: 'circle', source: USER_SOURCE, filter: ['==', ['get', 'geometryType'], 'Point'], paint: { 'circle-radius': 7, 'circle-color': '#f5d988', 'circle-stroke-width': 2, 'circle-stroke-color': '#463d23' } },
      { id: DRAFT_FILL, type: 'fill', source: DRAFT_SOURCE, paint: { 'fill-color': '#f2dc8a', 'fill-opacity': 0.3 } },
      { id: DRAFT_LINE, type: 'line', source: DRAFT_SOURCE, paint: { 'line-color': '#ffedab', 'line-width': 3, 'line-dasharray': [2, 1] } },
      { id: DRAFT_VERTICES, type: 'circle', source: DRAFT_SOURCE, paint: { 'circle-radius': 7, 'circle-color': ['case', ['get', 'selected'], '#ff8359', '#fff0b7'], 'circle-stroke-width': 2, 'circle-stroke-color': '#503b20' } },
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
    refreshPharmacies();
    refreshRoads();
    refreshNoise();
  });
  const refreshPharmacies = () => {
    if (!loaded || !registry?.pharmacies.visible || !visibleCategories.includes('medical-pharmacy')) return;
    const bounds = map.getBounds();
    const bbox = [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()].join(',');
    (map.getSource(PHARMACY_SOURCE) as GeoJSONSource).setData(`/api/medical/pharmacies.geojson?bbox=${encodeURIComponent(bbox)}`);
  };
  map.on('moveend', refreshPharmacies);
  const refreshRoads = () => {
    if (!loaded || !registry) return;
    const activeCategories = [
      ...(registry['road-major'].visible ? ['road-major'] : []),
      ...(registry['road-kad'].visible ? ['road-kad'] : []),
      ...(registry['road-zsd'].visible ? ['road-zsd'] : []),
      ...(registry['road-interchanges'].visible ? ['road-ramp', 'road-interchange'] : []),
    ].filter((id) => visibleCategories.includes(id));
    if (!activeCategories.length) return;
    const bounds = map.getBounds();
    const bbox = [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()].join(',');
    (map.getSource(ROADS_SOURCE) as GeoJSONSource).setData(`/api/roads/viewport.geojson?bbox=${encodeURIComponent(bbox)}&category=${encodeURIComponent(activeCategories.join(','))}`);
  };
  map.on('moveend', refreshRoads);
  const refreshNoise = () => {
    if (!loaded || !registry) return;
    const active = ([
      ['noise-road', 'road_noise'], ['noise-railway', 'railway_noise'],
      ['noise-aviation', 'aviation_noise'], ['noise-helicopter', 'helicopter_noise'],
    ] as const).filter(([id]) => registry?.[id].visible && visibleCategories.includes(id)).map(([, kind]) => kind);
    const source = map.getSource(NOISE_SOURCE) as GeoJSONSource;
    if (!active.length) { source.setData({ type: 'FeatureCollection', features: [] }); return; }
    const bounds = map.getBounds();
    const bbox = [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()].join(',');
    source.setData(`/api/noise/viewport.geojson?bbox=${encodeURIComponent(bbox)}&type=${encodeURIComponent(active.join(','))}`);
  };
  map.on('moveend', refreshNoise);
  map.on('click', (event) => {
    if (!loaded) return;
    if (drawingDraft) {
      const vertex = map.queryRenderedFeatures(event.point, { layers: [DRAFT_VERTICES] })[0];
      const index = vertex?.properties?.vertexIndex;
      if (typeof index === 'number') callbacks.onDrawingVertexClick?.(index);
      else callbacks.onDrawingClick?.([event.lngLat.lng, event.lngLat.lat]);
      return;
    }
    const userFeature = map.queryRenderedFeatures(event.point, { layers: [USER_POINTS, USER_LINES, USER_AREAS] })[0];
    const userId = userFeature?.properties?.id;
    if (typeof userId === 'string' && [USER_POINTS, USER_LINES, USER_AREAS].includes(userFeature.layer.id)) {
      callbacks.onUserGeometryClick?.(userId); return;
    }
    const objectLayers = [
      OBJECT_LAYER, GREEN_FILL, GREEN_LINE, WATER_FILL, WATER_LINE,
      METRO_LINE, METRO_STATION, METRO_ENTRANCE,
      BUS_ROUTES, TRAM_ROUTES, TROLLEYBUS_ROUTES, TRANSPORT_STOPS,
      SCHOOL_POINTS,
      KINDERGARTEN_POINTS,
      MEDICAL_POINTS, PHARMACY_POINTS,
      ROAD_MAJOR, ROAD_KAD, ROAD_ZSD, ROAD_RAMPS, ROAD_INTERCHANGES,
      NOISE_ROAD, NOISE_RAILWAY, NOISE_AVIATION, NOISE_HELICOPTER,
    ];
    const features = map.queryRenderedFeatures(event.point, { layers: [...objectLayers, DISTRICT_FILL] });
    const object = features.find((feature) => objectLayers.includes(feature.layer.id));
    const objectId = object?.properties.id ?? object?.id;
    if (typeof objectId === 'string') { callbacks.onObjectClick(objectId); return; }
    const cluster = map.queryRenderedFeatures(event.point, { layers: [PHARMACY_CLUSTERS] })[0];
    if (cluster?.geometry?.type === 'Point') {
      map.easeTo({ center: cluster.geometry.coordinates as [number, number], zoom: map.getZoom() + 2 });
      return;
    }
    const district = features.find((feature) => feature.layer.id === DISTRICT_FILL);
    const id = district?.properties.id;
    if (typeof id === 'string' && id.startsWith('district-osm-relation-')) callbacks.onDistrictClick(id as DistrictId);
  });
  map.on('mousemove', (event) => {
    if (!loaded) return;
    if (drawingDraft) { map.getCanvas().style.cursor = 'crosshair'; return; }
    map.getCanvas().style.cursor = map.queryRenderedFeatures(event.point, {
      layers: [
        USER_POINTS, USER_LINES, USER_AREAS,
        OBJECT_LAYER, GREEN_FILL, GREEN_LINE, WATER_FILL, WATER_LINE,
        METRO_LINE, METRO_STATION, METRO_ENTRANCE, DISTRICT_FILL,
        BUS_ROUTES, TRAM_ROUTES, TROLLEYBUS_ROUTES, TRANSPORT_STOPS,
        SCHOOL_POINTS,
        KINDERGARTEN_POINTS,
        MEDICAL_POINTS, PHARMACY_POINTS, PHARMACY_CLUSTERS,
        ROAD_MAJOR, ROAD_KAD, ROAD_ZSD, ROAD_RAMPS, ROAD_INTERCHANGES,
        NOISE_ROAD, NOISE_RAILWAY, NOISE_AVIATION, NOISE_HELICOPTER,
      ],
    }).length ? 'pointer' : '';
  });
  map.on('error', () => { if (!loaded) callbacks.onError(); });

  return {
    resize: () => map.resize(), remove: () => map.remove(),
    setSelectedDistricts: (ids: readonly DistrictId[]) => { selectedIds = ids; applySelection(); },
    setLayers: (layers: LayerRegistry) => { registry = layers; applyLayers(); refreshPharmacies(); refreshRoads(); refreshNoise(); },
    setObjects: (data: MapObject[]) => {
      currentObjects = data;
      if (loaded) (map.getSource(SOURCES['demo-object']) as GeoJSONSource).setData(toGeoJSON(data));
    },
    setUserGeometries: (items: UserGeometry[]) => {
      currentUserGeometries = items;
      if (loaded) (map.getSource(USER_SOURCE) as GeoJSONSource).setData(toUserGeoJSON(items));
    },
    setDrawingDraft: (draft: DrawingDraft | null) => {
      drawingDraft = draft;
      if (loaded) (map.getSource(DRAFT_SOURCE) as GeoJSONSource).setData(draftPreview(draft));
    },
    setCategories: (definitions: Category[], ids: string[]) => {
      categories = definitions; visibleCategories = ids; applyCategories(); refreshPharmacies(); refreshRoads(); refreshNoise();
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
