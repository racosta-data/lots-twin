# Data Contract v0.4: Geospatial Quality Maze

> Project: `lots-twin`. Territory v1: Barranquilla (DANE `08001`), then Atlántico (`08`), then Colombia (`00`).
> Status: draft v0.4. Code has started: the pure domain and the 20 simulation cases run as tests. All artifacts are in English. Values copied from official sources (for example "Barranquilla") are kept exactly as published.

## 0. Decision status

Items marked "delegated" were decided by the assistant on 26 Nov 2026 under the maintainer's instruction to resolve every pending point. The maintainer can reverse any of them by pull request. Rationale is in `docs/decisions/0001-design-decisions.md`.

| ID | Decision | Status |
|---|---|---|
| P7 | Viewer consumption event deferred to v2 | Approved |
| B3 | Strict 100% territory coverage in v1 | Approved, revisit with probe PR2 |
| C1 | Required bands stays a cell in row C | Approved |
| A2/A3 | Stay separate cells | Approved |
| D1 | 4 audit points instead of 8 | Approved |
| D2 | No hash chain on the audit log in v1 | Approved |
| D6 | Vector track limited to 3 checks in v1 | Approved |
| D3, D4, D5, D7, D8 | 5 tables, one abstract class, no audit decorator, reduced error catalog, integer rule versions | Approved (delegated) |
| F1 | `DQ-510` means CRS present but invalid or incoherent; absent is `UNKNOWN / DQ-506` | Approved (delegated) |
| F2 | Vector-blocked scenes carry the layer check code in `dq_code` | Approved (delegated) |
| F3 | Keep strict B3 and add a near-miss view | Approved (delegated) |
| F4 | `DQ-521` merged into `DQ-520` | Approved (delegated) |
| F5 | Always 9 evaluation rows per scene | Approved (delegated) |
| F6 | C2 defined from the product metadata offset (section 6.5) | Approved (delegated) |
| S1 | Source: Copernicus Data Space Ecosystem (STAC + OData) | Decided (delegated), verify in PR1 |
| S2 | Supported baselines: 04.00, 05.00, 05.09, 05.10, 05.11 | Decided (delegated) |
| S3 | Required bands: B02, B03, B04, B08, SCL | Decided (delegated) |
| S5 | Viewer: MapLibre GL JS with PMTiles on static storage | Decided (delegated) |
| S6 | Publication scope: mask, footprints with zone and code, monthly coverage. No imagery in v1 | Decided (delegated) |
| S7 | C3 threshold: calibration protocol defined (section 6.2); the value needs real data | Pending data (PR4) |
| S8 | Contract owner: repository maintainer `racosta-data` | Decided |
| M1 | No `audit_event` table; the path is rebuilt from `evaluation`, `run` and the `publication` manifest | Approved |
| M2 | No DuckDB registry in v1: A1 checks `data/raw/<scene_id>`; evaluations are Parquet files per run, queried with DuckDB | Approved |
| M3 | Code in two packages (`domain`, `pipeline`) until there is a concrete reason to split | Approved |
| M4 | Build order: pure rules for all 9 cells and the 20 case tests first, then real measurement for A1, A2, B3, C3, then B1, B2, C1, C2 | Approved, step 1 done |
| M5 | New documents are frozen until real data exists | Approved |
| M6 | Add drift alert, `cell_memory`, threshold suggestion, deterministic hash, always-produced mask and minimal CI | Approved, drift, memory, suggestion, hash and CI done |
| M7 | Probe PR7 (PMTiles) moves after L4 | Approved |
| M8 | C3 stays a gate in v1; reopen as a measure with a partial zone after PR4 | Open until PR4 |


## 1. Purpose and scope

The contract defines what enters, what is guaranteed on output, how decisions are made and how they are proven.

| Contract | Question it answers |
|---|---|
| Input | What do we accept from the source, and in what form? |
| Output | What do we guarantee in the `validated`, `rejected` and `unknown` zones? |
| Rules | How are rules defined, versioned and changed? |
| Audit and publication | How is everything shown in the viewer reconstructed? |

Out of scope for v1: imputation, interpolation of gaps, silent correction, radar (Sentinel-1), Landsat, events or streaming, microservices, user-query logging (P7), hash-chained audit log.

## 2. Principles

1. **Never invent.** An absent, ambiguous or unevaluable value is rejected with a code or left `UNKNOWN`. It is never filled in.
2. **Rules do not tune themselves.** The system accumulates statistics; only the maintainer changes a threshold, and that creates a new rule version.
3. **Failing is a result, not an exception.** A cloudy scene returns `Result(state=FAIL, code=DQ-520)`. Exceptions are only for infrastructure and contract failures.
4. **Ascending cost.** Cells run from cheap (metadata) to expensive (pixels) and the maze stops at the first non-PASS cell.
5. **Resampling is inventing.** Rasters stay in their native CRS (UTM). The vector is reprojected, which is an exact coordinate transform.
6. **The viewer is derived.** Truth lives in the `validated` zone and the audit log.
7. **Territory is a parameter.** No territory code appears inside a rule.
8. **Eliminate with evidence.** A cell that never fires in 12 months of real data is a candidate for removal.

## 3. Conventions

### 3.1 States

| State | Meaning |
|---|---|
| `PASS` (1) | Evaluated and the rule holds |
| `FAIL` (0) | Evaluated and the rule is violated (a wall) |
| `UNKNOWN` | Not evaluated or not evaluable. Nothing is assumed |

### 3.2 Subreasons (required when the state is `UNKNOWN`)

| Subreason | When |
|---|---|
| `NOT_EVALUATED` | An earlier cell was not PASS, so the maze stopped |
| `MISSING_INPUT` | The data a rule needs is absent. Code `DQ-506` |
| `VECTOR_TRACK_FAILED` | The territory layer failed its checks, so no scene is evaluated against it |
| `RULE_NOT_EFFECTIVE` | No effective version of the rule exists for that date |

### 3.3 Identifiers

| Identifier | Format | Ties together |
|---|---|---|
| `run_id` | UUID | One full execution |
| `scene_id` | Exact product name from the source | One scene across its whole path |
| `territory_code` | DANE code (`00`, `08`, `08001`) | One territory |
| `rule_version` | `cell@integer` (for example `C3@2`) | Exact rule and version |
| `code_version` | Git commit hash | Code that ran |
| `publication_id` | UUID | One package sent to the viewer |

### 3.4 Time and units

UTC, ISO 8601. Percentages in [0, 100] with 2 decimals. Distances in meters, areas in m². Coordinates always travel with their EPSG code.

## 4. Input contract: scene

Source v1 (decision S1): Sentinel-2 level L2A from the Copernicus Data Space Ecosystem. Discovery uses its STAC catalogue; download and checksum use its OData service. An account is required and usage quotas apply. STAC item ids are product names and become `scene_id`. Terms of use, quotas and checksum availability are verified in probe PR1.

| Field | Type | Required | Notes |
|---|---|---|---|
| `scene_id` | text | Yes | Unique in the registry (A1) |
| `acquisition_date` | timestamp UTC | Yes | Validated at the ingestion gate by the STAC schema |
| `satellite` | text | Yes | For example Sentinel-2A, 2B, 2C |
| `processing_level` | text | Yes | Must be `L2A` in v1 |
| `baseline` | text | Yes | Processing version; defines the radiometric offset (A3) |
| `crs` | EPSG | Yes | Native (UTM); metadata vs file compared in B1 |
| `bbox` | 4 numbers | Yes | Coherent with the raster (B2) |
| `footprint` | polygon | Yes | Valid geometry (B2) |
| `resolution_m` | number | Yes | Product property, recorded, not a cell |
| `scene_cloud_pct` | % | No | Provider's global metadata. **Does not decide** |
| `territory_cloud_pct` | % | Computed | Clipped to the territory. Informative |
| `usable_coverage` | % | Computed | Observed pixels inside the territory. **Decides in C3** |
| `hash_published` | text | Yes | MD5 checksum declared by the source's OData service (A2). Availability verified in probe PR1 |
| `hash_received` | text | Computed | Hash of the downloaded file (A2) |
| `territory_code`, `territory_level` | text | Yes | Municipality, department or country |
| `zone` | enum | Computed | `validated`, `rejected`, `unknown` |

Source and license are constants per source and live once in `config/sources/`.

**Observed pixel:** not NoData, not saturated or defective, not cloud (medium or high probability), not cloud shadow and not cirrus. Water, vegetation, bare soil and urban areas count as observed. Water is not a defect.

**Inherited trust (must be declared):** clouds and shadows come from the provider's SCL mask, which is an estimate. The contract calls it "cloud according to SCL". It can fail over very bright surfaces or reflections on water.

**Radiometric trap:** since January 2022 (baseline 04.00) reflectance carries an offset of 1000. C2 reads its range according to the baseline checked in A3, which is why A3 runs before C2.

## 5. Territory and vector track

### 5.1 Entity `territory`

| Field | Type | Required | Notes |
|---|---|---|---|
| `territory_code` | text | Yes | `00`, `08`, `08001` |
| `level` | enum | Yes | `COUNTRY`, `DEPARTMENT`, `MUNICIPALITY` |
| `name` | text | Yes | As published by the source |
| `parent_code` | text | Yes* | Null only for the country |
| `geom` | (multi)polygon | Yes | Reprojected to the raster CRS; the raster is never touched |
| `source_crs` | EPSG | Yes | |
| `layer_version` | text | Yes | Version of the source layer (DANE or IGAC) |
| `updated_on` | date | Yes | |

### 5.2 Vector track (3x1 in v1, runs once per layer version)

If any check fails, no scene is evaluated against that territory and its scenes are `UNKNOWN / VECTOR_TRACK_FAILED`. Each such scene still writes the 9 evaluation rows, all `UNKNOWN / VECTOR_TRACK_FAILED`, carrying the layer check code (for example `DQ-541`) in `dq_code` (F2).

| Check | Logic | Error |
|---|---|---|
| **V1** | Geometry valid: no self-intersections, no empty geometry | `DQ-541` |
| **V3** | Required attributes complete | `DQ-501` |
| **V4** | DANE code exists in the catalog with a coherent parent, and the layer version is the effective one | `DQ-540` / `DQ-544` |

V2 (no overlaps between territories) returns in v1.5, when 23 municipalities exist and overlaps have something to be compared with.

## 6. Rules contract: scene maze 3x3

### 6.1 Structure

Rows are ordered by cost. The scene advances and stops at the first non-PASS cell. Later cells become `UNKNOWN / NOT_EVALUATED`.

| Row | Cell | Input | Logic | Error |
|---|---|---|---|---|
| **A. Admission** (metadata, file) | **A1** identity | `scene_id` | Not already in the registry | `DQ-530` |
| | **A2** integrity | file + published hash | Hash matches and the file opens | `DQ-550` |
| | **A3** baseline | `baseline` | In the supported list: 04.00, 05.00, 05.09, 05.10, 05.11. An unseen version fails until it is added on purpose | `DQ-531` |
| **B. Space** | **B1** CRS | metadata + file | Defined and coherent between both | `DQ-510` |
| | **B2** footprint | footprint, bbox, raster | Valid geometry and bbox matches the raster | `DQ-511` |
| | **B3** coverage | footprint + territory polygon | Polygon fully inside the footprint | `DQ-512` |
| **C. Content** (reads pixels) | **C1** bands | band list | B02, B03, B04, B08 and SCL present | `DQ-522` |
| | **C2** value range | clipped pixels | Metadata offset matches the baseline and no valid DN exceeds 32767 (section 6.5) | `DQ-523` |
| | **C3** usable coverage | clipped SCL mask | `usable_coverage` >= threshold | `DQ-520` |

A cell whose input is absent returns `UNKNOWN / MISSING_INPUT / DQ-506`. "Value present but unsupported" is a FAIL; "value absent" is UNKNOWN.

### 6.2 Thresholds

| Cell | v1 value | Status |
|---|---|---|
| B3 | 100% of the polygon inside the footprint | Approved |
| A3 | Supported list: 04.00, 05.00, 05.09, 05.10, 05.11 | Decided |
| C1 | B02, B03, B04, B08, SCL | Decided |
| C2 | Offset by baseline (section 6.5) | Decided |
| C3 | `null` until calibrated | **Pending data** (probe PR4) |
| Others | Binary logic | No numeric threshold |

**C3 calibration protocol (S7).** (1) Compute `usable_coverage` for every Barranquilla scene of 12 months. (2) Plot the histogram. (3) Set the threshold at the lowest value where the distribution shows a clear valley between cloudy and clear scenes; if there is no valley, use the value that keeps at least 25% of scenes in `validated`, and record that choice. (4) The maintainer approves it, and it enters `config/rules/` as a new integer version. The 80% used in the L2 simulation is a placeholder, not a result.

A rule whose threshold is `null` or whose status is `pending_calibration` cannot become effective. The loader raises `ContractError` instead of guessing.

### 6.3 Rule files (`config/rules/`)

One YAML file per version, versioned in git. Fields per cell: `name`, `row`, `cost_rank`, `error_code`, `inputs`, `params`, `status` (`active` or `pending_calibration`). File-level fields: `version` (integer), `effective_from` (date or null), `approved_by`, `justification`.

Changing a threshold or logic creates a new file and a new integer version. Past evaluations keep the version they ran with and are never silently recomputed; reprocessing creates a new `run_id`.

### 6.5 C2 definition (F6)

Facts from the ESA product documentation: since processing baseline 04.00 (25 Jan 2022) Sentinel-2 L2A values carry an offset read from the product metadata (`BOA_ADD_OFFSET`, -1000 for all bands), DN 0 means NoData, valid DN run from 1 to 32767, and reflectance is (DN + BOA_ADD_OFFSET) / quantification value (10000). The offset is applied by baseline, not by acquisition date.

C2 passes only if both hold:

1. The offset in the product metadata equals the expected value for the baseline (-1000 for every supported baseline in S2).
2. No non-NoData DN exceeds 32767.

The offset and quantification value are read from the metadata and never hard-coded in the cell logic. An absent offset field is `UNKNOWN / MISSING_INPUT`.

### 6.4 Rule function contract

`evaluate(context) -> Result` is pure: it does not read disk, write, or touch the network. Everything it needs arrives measured in `context`. A `ContextBuilder` in `pipeline/` computes hashes, CRS, bbox and pixel statistics, and it is **lazy**: row C values are computed only when a cell asks for them, so a duplicate scene that dies in A1 never pays for pixel reads.

## 7. Output contract

### 7.1 Entity `evaluation` (one row per scene and cell)

| Field | Type | Notes |
|---|---|---|
| `run_id`, `scene_id`, `territory_code` | text | |
| `cell` | text | A1 to C3, V1, V3, V4 |
| `state` | enum | `PASS` / `FAIL` / `UNKNOWN` |
| `subreason` | text | Required if `UNKNOWN` |
| `measured_value` | number or text | What was measured, no hidden rounding |
| `threshold_applied` | JSON | Copy of the effective threshold |
| `rule_version` | text | For example `C3@2` |
| `dq_code` | text | Null only if `PASS` |
| `code_version` | text | |
| `evaluated_at` | timestamp UTC | |

**Row count rule (F5):** every scene writes exactly 9 evaluation rows, regardless of where the maze stopped or whether the vector track blocked it. Cells after the stop are `UNKNOWN / NOT_EVALUATED`. This keeps the conservation check and the metric views uniform.

### 7.2 Zones

| Zone | Content | Guarantee |
|---|---|---|
| `raw` | Original file as received | Immutable, hashed. Written at ingestion for every scene, before the maze |
| `validated` | Scenes with all 9 cells `PASS` | Zero imputed values |
| `rejected` | Scenes with a `FAIL`, with their code | Always has a reason |
| `unknown` | Scenes not evaluable | Always has a subreason |

Routing precedence: `FAIL` > `UNKNOWN` > validated. Partitioning: `zone/territory_code/year/month/`.

### 7.4 Mask always produced and deterministic hash (M6)

- The observation mask and the measured values are produced for every scene that reaches C3, even when C3 fails. If a partial zone is adopted later (M8), nothing has to be recomputed.
- Output hashes are computed over canonical content (rows sorted, canonical JSON, no timestamps, no run ids), never over raw file bytes that embed metadata. Acceptance criterion 3 depends on this.

### 7.3 Mask, metrics and conservation

- Observation mask: one COG per scene, clipped to the territory (1 observed, 0 not). It is the proof of "where we know".
- Monthly coverage, temporal gaps and per-cell pass rates are **SQL views** over `evaluation`, not tables. They read all three zones. A B3 near-miss view lists scenes rejected by B3 whose covered share is within 5 percentage points of 100% (F3); the 5 points are a view parameter, not a rule.
- **Conservation invariant:** scenes in = validated + rejected + unknown, checked at each handoff. A mismatch stops the run with `DQ-560`.

## 8. Audit contract

### 8.1 Audit points (D1)

| Point | Covers | Evidence |
|---|---|---|
| **Ingestion** (P0-P2) | Request parameters, catalog reply (count, ids), download (size, duration, retries, hash received vs published) | Stored query, list of ids, hash comparison |
| **Maze** (P3) | Full traversal per scene | `evaluation` rows |
| **Persistence** (P4) | What was written to each zone and how many rows | Counts and file hashes |
| **Publication** (P5-P6) | Layers built, transformations, upload, round-trip result | Manifest and remote status |

P7 (viewer consumption) is deferred to v2.

### 8.2 No separate event table (M1)

The audit points are rebuilt from three sources: the `evaluation` rows (maze), the `run` record (ingestion parameters, counts per zone, hashes of the files written) and the `publication` manifest (publication). Every file is written once per run and never modified (writing to an existing path is an error). The hash of the exported run manifest is committed to git (D2).

### 8.3 Entity `run`

`run_id`, `started_at`, `finished_at`, `status`, `code_version`, `dependencies_hash`, `rule_catalog_hash`, `environment`, `ingestion` (query parameters, counts, ids), `zone_counts`, `files` (name and canonical hash). If the repository has uncommitted changes, the run **refuses to start**.

### 8.4 Not audited

Per-pixel content at every step (the hash is stored, not a copy), performance metrics nobody reads, and debug logs (a separate channel).

### 8.5 Learning layer (M6)

The maze starts knowing nothing and fills its memory with every scene. The rule that makes this compatible with "never invent": **what is learned proposes, the rules decide.** Nothing learned changes a result without a new, approved rule version.

| Piece | What it does | Status |
|---|---|---|
| `cell_memory` view | Per cell and territory: PASS, FAIL and UNKNOWN counts, first seen, last seen, last non-PASS. The persistent switch of the Shannon metaphor | Implemented |
| Drift alert | Flags a cell that fails for more than 50% of the evaluated scenes of one run, with at least 5 scenes. Usual cause: the source changed, for example a new baseline | Implemented |
| Threshold suggestion | Proposes the C3 value from the observed distribution (valley method, fallback keeps 25% of scenes). A proposal, never applied automatically | Implemented |
| Learned cell order | Reorders cells of equal cost by failure rate | Not in v1: the order stays fixed and versioned |
| Predictive model | Predicts rejection from metadata before downloading | Not in v1: needs volume (Atlantico or Colombia) |

## 9. Publication contract

The viewer is a presentation layer, not a source of truth.

### 9.1 Entity `publication` (with embedded manifest)

`publication_id`, `run_id`, `rule_versions` (map cell to version), `files` (name, hash, entity count), `source_crs`, `transformations` (reprojection, simplification tolerance, tiling), `archive_id`, `archive_version`, `remote_status`, `active`.

### 9.2 Rules

1. **Round-trip check:** after upload, counts and key properties are compared against the manifest. On mismatch: `DQ-570` and `active = false`; the previous version stays live.
2. **Versioning:** each publication creates a new version and never overwrites.
3. **`UNKNOWN` is visible:** it has its own style (hatched), never transparent. Absence must not read as "no problem".
4. **On-screen statement:** the viewer states that it is derived, that geometries may be simplified, and that it is not for measuring.
5. **Credentials:** none in the client, since v1 serves static files. Any storage write key lives only in the publishing process, never in the repository or the browser.

**Viewer (S5):** MapLibre GL JS reading a PMTiles archive from static storage. It needs no account, token or quota, and the round-trip check reduces to comparing file hashes and feature counts. The publisher sits behind one concrete class so another viewer, including Mapbox, can be added when a second implementation is justified.

**Publication scope (S6):** vector layers for the observation mask, scene footprints with their zone and code, and monthly coverage. Imagery is not published in v1. Probe PR7 builds one archive and loads it before the publisher is written.

## 10. Error catalog

Own namespace `DQ-xxx`, separate from HTTP codes.

| Code | Meaning | Source |
|---|---|---|
| `DQ-501` | Required field null | V3 |
| `DQ-506` | Unknown state, nothing inferred | Any cell |
| `DQ-510` | CRS present but invalid or incoherent (absent is `DQ-506`) | B1 |
| `DQ-511` | Footprint or bbox invalid or incoherent | B2 |
| `DQ-512` | Territory not covered by the scene | B3 |
| `DQ-520` | Usable coverage below threshold (NoData counts as not observed) | C3 |
| `DQ-522` | Required bands missing | C1 |
| `DQ-523` | Values out of range for the baseline | C2 |
| `DQ-530` | Duplicate scene | A1 |
| `DQ-531` | Unsupported processing baseline | A3 |
| `DQ-540` | DANE code missing or hierarchy incoherent | V4 |
| `DQ-541` | Invalid geometry | V1 |
| `DQ-544` | Layer version not effective | V4 |
| `DQ-550` | Hash mismatch or unreadable file | A2 |
| `DQ-560` | Conservation broken | Run |
| `DQ-570` | Publication not verified | Publication |

16 codes. Removed from earlier drafts: `502` to `505` (no rule uses them), `521` (merged into `520`, since NoData is already excluded from observed pixels), `542` (V2 deferred), `561` (duplicates `550`) and `571` (no hash chain). Code `560` stays because the conservation invariant needs it.

**Exceptions (system failures only):** `InfrastructureError` (disk, network, database unreachable) and `ContractError` (corrupt catalog, invalid schema, rule pending calibration). A rule that fails never raises.

## 11. Null policy

| Situation | Result |
|---|---|
| Required source field absent | `FAIL` + `DQ-501` |
| Data a rule needs does not arrive | `UNKNOWN` + `MISSING_INPUT` + `DQ-506` |
| Cell after a non-PASS cell | `UNKNOWN` + `NOT_EVALUATED` |
| Cloud, shadow or NoData pixel | Not observed; never filled |
| Territory outside the footprint | Rejected; never completed from another scene |
| Any doubt about a value | `UNKNOWN`; never guessed |

## 12. Versioning and change control

- Rules: integer version, one YAML file per version, immutable once effective.
- Contract and schema: this document is versioned in git (`docs/contract/`) and changes through pull requests.
- Every change needs evidence (statistics from real runs), an approver and an effective date.
- Contract owner: the repository maintainer (`racosta-data`), recorded in `docs/decisions/`.

## 13. Acceptance criteria

| # | Criterion | How it is tested |
|---|---|---|
| 1 | For anything visible on the map, one query returns its full path from request to publication | Traceability query |
| 2 | The conservation equation holds at every handoff | Automatic test per batch |
| 3 | Re-running a historical scene reproduces the same output hash | Reproducibility test |
| 4 | A publication with counts different from its manifest is not activated | Test with a tampered manifest |
| 5 | Editing an exported audit file is detected by the committed manifest hash | Git diff check |
| 6 | `UNKNOWN` areas are visible and distinguishable in the viewer | Visual review |
| 7 | Zero imputed values in the `validated` zone | Pixel-origin audit |
| 8 | The same maze processes Barranquilla and Atlántico without rule changes | Only `territory_code` changes |
| 9 | Every scene has exactly 9 evaluation rows | Count check per run |
| 10 | A run where one cell fails for more than half of the scenes raises a drift alert | Test with synthetic scenes (done) |
| 11 | CI runs the unit tests, the 20 case fixtures and the diagram check on every push | GitHub Actions |

## 14. Data model and code mapping

Four datasets stored as Parquet files per run: `scene`, `evaluation`, `run`, `publication` (M1). Territories load from `config/territories.yaml`. Rules load from `config/rules/`. Metrics are SQL views. Masks are COG files.

| Contract element | Code component |
|---|---|
| States and errors | `State`, `Subreason`, `DQCode` (enums), `Result` (immutable) |
| Cells | `Rule` (abstract) with one subclass per cell |
| Traversal | `Maze(rows, columns)`, `Traversal` in `domain/` |
| Routing | `domain/routing.py` (`FAIL` > `UNKNOWN` > validated) |
| Measurement | `ContextBuilder` (lazy) in `pipeline/` |
| Registry | Files under `data/raw/` (A1) and Parquet per run, queried with DuckDB (M2) |
| Audit | `evaluation` + `run` + manifest, no event table (M1) |
| Calculations | Pure functions: masks, clipping, statistics |

## 15. Probes before code (phase 1)

Empirical points cannot be decided from a desk. Each one has a success criterion and a cell it unblocks.

| # | Probe | Success criterion | Unblocks |
|---|---|---|---|
| PR1 | One STAC search for Barranquilla and one OData download | Item ids returned, MD5 checksum present and matching, quotas and terms noted | A2, source S1 |
| PR2 | Footprints of the scenes covering Barranquilla over 12 months | Share of scenes with the polygon fully inside; number of tiles involved | B3 |
| PR3 | Distinct baselines in 12 months of metadata | List matches S2, or the list is extended on purpose | A3 |
| PR4 | `usable_coverage` distribution (calibration protocol in 6.2) | Histogram and an approved threshold | C3 |
| PR5 | Visual review of 20 scenes against the SCL mask (water, Cienaga de Mallorquin, urban) | Notes on misclassified areas, recorded as inherited trust | Section 4 |
| PR6 | Current DANE layer version and terms of use | Version and license recorded in `config/territories.yaml` | V4 |
| PR7 (after L4) | Build one mask PMTiles archive and load it in MapLibre | Renders, and `UNKNOWN` shows hatched | Publication |

## 16. Remaining items

1. Per-band checks beyond the five required bands, if analysis needs them.
2. Extending the supported baseline list when a new version appears (a deliberate change, not automatic).
3. A second viewer implementation (for example Mapbox) only when there is a reason for it.
