# Data Visualization: Cluster 2

This repository contains the final marimo SVG implementation for Cluster 2 of the Data Visualization assignment. The notebook builds on the preprocessing in `graph2.py` from `tvakul/dataviz1`.

## Files

- `implementation/graph2.py` - original Graph 2 preprocessing notebook copied unchanged from `tvakul/dataviz1`.
- `implementation/cluster_2_svg_blocks_marimo.py` - final interactive marimo notebook; it starts with the Graph 2 preprocessing cells unchanged, then adds the SVG visualization cells.
- `implementation/cluster_2_svg_blocks_marimo.html` - exported HTML version of the notebook.
- `implementation/data/places_edited.json` - Graph 2 prepared place zones.
- `implementation/data/time_trip_spend.json` - Graph 2 prepared trip-place time allocation.
- `implementation/data/oceanus_map.geojson` - Oceanus map data used in the board visit map panel.

## Run

```bash
cd implementation
marimo edit cluster_2_svg_blocks_marimo.py
```
