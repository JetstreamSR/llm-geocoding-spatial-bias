# Data notes

`course_run_results.csv` contains the 4,590 completed records from the historical TUM course experiment. The addresses and reference locations were derived from public GeoNames and OpenStreetMap services. Model outputs were produced during the course project.

## Important limitation

The historical prompts included the reference bounding-box coordinates after rounding every coordinate to two decimal places. The file is preserved for transparency and for reproducing the figures, but it is not a blind benchmark dataset. Do not use its model comparison values as evidence of current model performance.

The experiment was designed and reported as using DeepSeek R1. At the time of the July 2025 experiment, the `deepseek-reasoner` endpoint corresponded to DeepSeek-R1-0528. The historical outputs nevertheless lack row-level model provenance: the original script tried `deepseek-chat` first and `deepseek-reasoner` only as a fallback. Those aliases then corresponded to DeepSeek-V3-0324 and DeepSeek-R1-0528, respectively, so the saved rows cannot now confirm the exact endpoint used for every response.

The cleaned `src/query_models.py` implementation sends only the `address` field during inference. Results from that implementation should be saved as a separate run.

## External source data

Large upstream files are not stored in this repository:

- GeoNames `cities15000.txt`: <https://download.geonames.org/export/dump/>
- GADM administrative boundaries: <https://gadm.org/data.html>
- OpenStreetMap data: <https://www.openstreetmap.org/copyright>
- Nominatim usage policy: <https://operations.osmfoundation.org/policies/nominatim/>

The original GADM GeoPackage was approximately 2.6 GB and is excluded from version control.

## Intermediate files

The original course folder also contained separate sampling, reference, and prediction CSV files. They are omitted because `course_run_results.csv` contains the combined records needed to reproduce the published figures. Development caches, IDE settings, archived project copies, exploratory test plots, and API credentials are not part of the public dataset.
