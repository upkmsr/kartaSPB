import { AttributionControl, Map, NavigationControl } from 'maplibre-gl';
import type { MapConfig } from '../config/map';
import type { MapObject } from '../domain/mapObject';

const OBJECT_SOURCE = 'demo-objects';
const OBJECT_LAYER = 'demo-points';

interface MapCallbacks {
  onObjectClick: (id: string) => void;
  onReady: () => void;
  onError: () => void;
}

export function createMap(
  container: HTMLDivElement,
  config: MapConfig,
  objects: MapObject[],
  callbacks: MapCallbacks,
) {
  const map = new Map({
    container,
    style: config.style.url,
    center: config.center,
    zoom: config.zoom,
    attributionControl: false,
    dragRotate: false,
    pitchWithRotate: false,
    touchPitch: false,
    locale: {
      'NavigationControl.ZoomIn': 'Приблизить',
      'NavigationControl.ZoomOut': 'Отдалить',
      'AttributionControl.ToggleAttribution': 'Источники карты',
      'Map.Title': 'Карта Санкт-Петербурга',
    },
  });
  map.touchZoomRotate.disableRotation();
  map.addControl(new NavigationControl({ showCompass: false }), 'top-right');
  map.addControl(new AttributionControl({
    compact: false,
    customAttribution: config.style.attribution,
  }), 'bottom-left');

  map.on('load', () => {
    map.addSource(OBJECT_SOURCE, {
      type: 'geojson',
      data: { type: 'FeatureCollection', features: objects },
    });
    map.addLayer({
      id: OBJECT_LAYER,
      type: 'circle',
      source: OBJECT_SOURCE,
      paint: {
        'circle-radius': 13,
        'circle-color': '#77dfcc',
        'circle-stroke-width': 4,
        'circle-stroke-color': '#163e42',
      },
    });
    callbacks.onReady();
  });
  map.on('click', OBJECT_LAYER, (event) => {
    const id = event.features?.[0]?.id;
    if (typeof id === 'string') callbacks.onObjectClick(id);
  });
  map.on('mouseenter', OBJECT_LAYER, () => { map.getCanvas().style.cursor = 'pointer'; });
  map.on('mouseleave', OBJECT_LAYER, () => { map.getCanvas().style.cursor = ''; });
  map.on('error', () => callbacks.onError());

  return {
    resize: () => map.resize(),
    remove: () => map.remove(),
  };
}
