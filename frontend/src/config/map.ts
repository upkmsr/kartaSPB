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

// Development basemap. Replace URL and attribution together for another source.
// Local styles must also use local tiles, glyphs and sprites to work offline.
export const mapConfig: MapConfig = {
  center: [30.3158, 59.9391],
  zoom: 12,
  style: {
    url: 'https://tiles.openfreemap.org/styles/dark',
    attribution:
      '<a href="https://openfreemap.org">OpenFreeMap</a> ' +
      '<a href="https://www.openmaptiles.org/">&copy; OpenMapTiles</a> ' +
      'Data from <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  },
};
