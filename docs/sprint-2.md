# SPRINT 2 — Districts & Layers

Реализованы 18 реальных административных районов Санкт-Петербурга из локального
OSM-derived GeoJSON, multi-select из React UI и кликом по карте, визуальное
выделение/затемнение и минимальный Layer Registry для районов и demo object.

Selection, visibility и opacity обновляются через MapLibre filter, paint и
layout properties без пересоздания карты. Backend schema/API не менялись.

Источник, лицензия, attribution и ограничения свежести описаны в
`docs/data-sources.md`.
