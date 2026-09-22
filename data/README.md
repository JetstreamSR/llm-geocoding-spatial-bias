# Data notes

`course_run_results.csv` contains the 4,590 completed records from the historical TUM course experiment. The addresses and reference locations were derived from public GeoNames and OpenStreetMap services. Model outputs were produced during the course project.

## Important limitation

The historical prompts included a rounded reference bounding box. The file is preserved for transparency and for reproducing the figures, but it is not a blind benchmark dataset. Do not use its model comparison values as evidence of current model performance.

The cleaned `src/query_models.py` implementation sends only the `address` field during inference. Results from that implementation should be saved as a separate run.

## External source data

Large upstream files are not stored in this repository:

- GeoNames `cities15000.txt`: <https://download.geonames.org/export/dump/>
- GADM administrative boundaries: <https://gadm.org/data.html>
- OpenStreetMap data: <https://www.openstreetmap.org/copyright>
- Nominatim usage policy: <https://operations.osmfoundation.org/policies/nominatim/>

The original GADM GeoPackage was approximately 2.6 GB and is excluded from version control.

