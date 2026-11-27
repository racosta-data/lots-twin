# 0001. Design decisions D1 to D8, F1 to F6 and S1 to S8

Date: 26 Nov 2026. Maintainer: `racosta-data`.
Decisions marked "delegated" were taken by the assistant after the maintainer asked it to resolve every pending point. Any of them can be reversed by pull request, which should add a new numbered record instead of editing this one.

| ID | Decision | Alternatives considered | Reason |
|---|---|---|---|
| D1 | 4 audit points (ingestion, maze, persistence, publication) | Keep 8 points | P0 and P1 are the same exchange with the catalog; P7 is deferred; fewer points answer the same questions |
| D2 | No hash chain in v1 | Hash-chained log | One user, and git already gives tamper evidence. Revisit if an external party asks |
| D3 | 5 tables; rules in YAML in git; metrics as SQL views | Rules and metrics as tables | git already versions, authors and dates rules; views avoid duplicated state |
| D4 | One abstract class (`Rule`) | Interfaces for source, repository and publisher | The rule of three: only `Rule` has several real variants today |
| D5 | No audit decorator on rules | Decorator logging each call | The `evaluation` row already stores input, output and version |
| D6 | Vector track of 3 checks in v1 | Keep the 5-check track | One polygon has nothing to overlap with; layer effectiveness folds into V4 |
| D7 | Catalog reduced to codes in use (16) | Keep reserved codes | Unused codes are decisions made without evidence |
| D8 | Integer rule versions (`C3@2`) | Semantic versions | Internal rules gain nothing from MAJOR and MINOR |
| F1 | `DQ-510` = CRS present but invalid or incoherent; absent is `UNKNOWN / DQ-506` | Treat absent CRS as FAIL | Keeps one null policy for every cell |
| F2 | Vector-blocked scenes carry the layer check code | Use `DQ-506` | The real cause is the layer, and the code names it |
| F3 | Keep strict 100% for B3, add a near-miss view | Allow a tolerance now | A tolerance without data is a guess; the view measures how often it matters |
| F4 | Merge `DQ-521` into `DQ-520` | Two codes with a NoData limit | NoData is already excluded from observed pixels, so one number covers both |
| F5 | Always 9 evaluation rows per scene | Rows only up to the stop | Uniform counts keep conservation and views simple |
| F6 | C2 compares the metadata offset to the baseline and bounds DN at 32767 | Fixed reflectance range | ESA documents the offset by baseline (-1000 from 04.00), DN 0 as NoData and DN up to 32767; the offset is read from metadata, not hard-coded |
| S1 | Source: Copernicus Data Space Ecosystem, STAC for discovery and OData for checksum and download | Public COG mirrors | The mirrors may not publish a checksum, which A2 needs. Verify in probe PR1 |
| S2 | Supported baselines 04.00, 05.00, 05.09, 05.10, 05.11 | Accept any version | An unseen baseline could change the radiometry; failing it forces a deliberate review |
| S3 | Required bands B02, B03, B04, B08, SCL | All bands | Enough for true colour, vegetation index and the cloud mask |
| S5 | Viewer: MapLibre GL JS with PMTiles on static storage | Mapbox tilesets | No account, token or quota; the round-trip check becomes a hash and count comparison. The publisher stays swappable |
| S6 | Publish mask, footprints with zone and code, monthly coverage; no imagery | Publish imagery tiles | Imagery tiles are resampled data, which conflicts with the project principle |
| S7 | C3 value pending; calibration protocol in contract section 6.2 | Fix 80% now | A threshold chosen without data violates the project's own rule |
| S8 | Contract owner: `racosta-data` | Unnamed | Every change needs an approver |

## Facts used (verified 26 Nov 2026)

- From processing baseline 04.00 (25 Jan 2022), L2A values carry `BOA_ADD_OFFSET`, read from the product metadata and set to -1000 for all bands. DN 0 is NoData and valid DN run from 1 to 32767. Reflectance is (DN + BOA_ADD_OFFSET) / 10000. Source: ESA Sentinel-2 MSI technical guide, Level-2A processing; ESA STEP forum FAQ listing baselines 04.00, 05.00, 05.09, 05.10 and 05.11 with the same formula.
- Copernicus Data Space serves STAC search and OData download, and third-party clients report MD5 checksums through OData. This needs confirming against the official documentation in probe PR1.
