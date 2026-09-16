# SPRINT 3 — Core Objects, Categories & Filters

Canonical project objects are stored in `project_objects` with PostGIS geometry
SRID 4326 and a GiST index. Controlled categories live in `categories` and are
referenced by stable ID. Migration head: `0002_objects`.

Read-only endpoints expose categories, objects, object details and comma-separated
category filtering. The frontend loads through `objectsApi`, converts domain
objects to GeoJSON at the map boundary, filters categories locally, and keeps
selection in the existing React and Layer Registry flow.

The original development point is available through the explicit idempotent
`python -m app.seed_demo` command. It is never inserted automatically by the
migration. Empty and unavailable APIs leave the map and districts operational.

Acceptance covered real PostGIS migration upgrade/downgrade/upgrade, geometry
constraints and indexes, Docker API requests, real WebGL rendering, object click,
card, category filters, district selection, and desktop/mobile layouts.
