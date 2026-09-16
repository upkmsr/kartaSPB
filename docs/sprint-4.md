# SPRINT 4 — Search & Geocoding

Project Search uses `GET /api/search/objects?q=...&limit=...` and the canonical
PostGIS object model. It searches name, description and category display name,
returns stable IDs, escapes wildcard input, and caps results at 50.

Address search uses the provider-independent frontend `GeocoderProvider` contract
and backend `NominatimProvider`. The proxy normalizes results, identifies the app,
serializes external calls to at most one per second, caches repeated requests, and
limits each response. URL and User-Agent are replaceable via environment variables.

The shared UI separates KARTASPB objects from addresses. It debounces project
search by 500 ms and runs public geocoding only after explicit button/Enter submit
(public Nominatim forbids autocomplete). It requires two characters for project
search and three for geocoding, cancels old
requests, rejects stale responses, reports independent errors, and closes with
Escape. Selecting a project object opens the existing Object Card and centers the
map. Selecting a geographic result centers the map and replaces one temporary
marker without persisting it.
