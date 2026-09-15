export interface MapStyleConfig {
  /** MapLibre Style JSON URL, including a same-origin self-hosted style. */
  url: string;
  attribution: string;
}

export interface MapConfig {
  center: [longitude: number, latitude: number];
  zoom: number;
  style: MapStyleConfig;
}

// Development basemap. The style is same-origin; its vector source remains replaceable.
export const mapConfig: MapConfig = {
  center: [30.3158, 59.9391],
  zoom: 12,
  style: {
    url: '/basemap/openfreemap-dark.json',
    attribution:
      '<a href="https://openfreemap.org">OpenFreeMap</a> ' +
      '<a href="https://www.openmaptiles.org/">&copy; OpenMapTiles</a> ' +
      'Data from <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  },
};
