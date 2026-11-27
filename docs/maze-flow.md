# Maze Flow — End-to-End Visual

> Status: draft v0.2. All project artifacts (code, docs, contract, UI) are in English.

## Glossary (contract ES → code EN)

| Contract (ES) | Code (EN) |
|---|---|
| escena | `scene` |
| casilla | `cell` |
| laberinto | `maze` |
| pista vectorial | `vector_track` |
| territorio | `territory` |
| evaluación | `evaluation` |
| zona | `zone` |
| cruda / validada / rechazada / unknown | `raw` / `validated` / `rejected` / `unknown` |
| umbral | `threshold` |
| regla | `rule` |
| vigente | `effective` |
| submotivo | `subreason` |
| huella | `footprint` |
| cobertura útil | `usable_coverage` |
| píxel observado | `observed_pixel` |
| corrida / ejecución | `run` |
| publicación | `publication` |
| manifiesto | `manifest` |
| evento de auditoría | `audit_event` |

## 1. High-level pipeline
```mermaid
flowchart LR
  STAC[(STAC catalog)] --> ING[INGEST<br/>P0-P2<br/>download + hash]
  ING --> MAZE[MAZE<br/>P3<br/>vector 3x1 + scene 3x3]
  MAZE --> ZONES[ZONES<br/>P4<br/>raw / validated /<br/>rejected / unknown]
  ZONES --> PUB[PUBLICATION<br/>P5-P6<br/>manifest + round-trip]
  PUB --> VIEW[Viewer<br/>derived<br/>MapLibre + PMTiles]
  ING -.-> AUDIT[AUDIT<br/>append-only log]
  MAZE -.-> AUDIT
  ZONES -.-> AUDIT
  PUB -.-> AUDIT
```

**Rule:** the viewer is *derived*. Truth lives in the `validated` zone + audit chain.

## 2. Vector track (3x1 in v1)
```mermaid
flowchart TD
  L[territory layer] --> V1{"V1<br/>geometry valid?"}
  V1 -- PASS --> V3{"V3<br/>attrs complete?"}
  V1 -- FAIL --> E1[DQ-541]
  V3 -- PASS --> V4{"V4<br/>DANE code in catalog<br/>and layer version effective?"}
  V3 -- FAIL --> E3[DQ-501]
  V4 -- PASS --> OPEN[TRACK OPEN]
  V4 -- FAIL --> E4[DQ-540 / DQ-544]
  E1 & E3 & E4 --> BLOCK[[TRACK BLOCKED<br/>scenes = UNKNOWN<br/>subreason=VECTOR_TRACK_FAILED]]
```

V2 (no overlaps) returns in v1.5, when 23 municipalities exist (decision D6).

## 3. Scene maze (3x3)
```mermaid
flowchart TD
  T([scene token]) --> A1{"A1<br/>identity unique?"}
  A1 -- PASS --> A2{"A2<br/>integrity: hash + opens?"}
  A1 -- FAIL --> R530[REJECTED DQ-530]
  A2 -- PASS --> A3{"A3<br/>baseline supported?"}
  A2 -- FAIL --> R550[REJECTED DQ-550]
  A3 -- PASS --> B1{"B1<br/>CRS defined and coherent?"}
  A3 -- FAIL --> R531[REJECTED DQ-531]
  B1 -- PASS --> B2{"B2<br/>footprint and bbox coherent?"}
  B1 -- FAIL --> R510[REJECTED DQ-510]
  B2 -- PASS --> B3{"B3<br/>territory inside footprint?"}
  B2 -- FAIL --> R511[REJECTED DQ-511]
  B3 -- PASS --> C1{"C1<br/>required bands?"}
  B3 -- FAIL --> R512[REJECTED DQ-512]
  C1 -- PASS --> C2{"C2<br/>values in baseline range?"}
  C1 -- FAIL --> R522[REJECTED DQ-522]
  C2 -- PASS --> C3{"C3<br/>usable_coverage >= threshold?"}
  C2 -- FAIL --> R523[REJECTED DQ-523]
  C3 -- PASS --> OK[[VALIDATED]]
  C3 -- FAIL --> R520[REJECTED DQ-520]
  A2 -. missing input .-> U506[UNKNOWN DQ-506]
  A3 -. missing input .-> U506
  B1 -. missing input .-> U506
  B2 -. missing input .-> U506
  B3 -. missing input .-> U506
  C1 -. missing input .-> U506
  C2 -. missing input .-> U506
  C3 -. missing input .-> U506
```

Rule shown by the dotted edges: a cell whose input is absent returns `UNKNOWN` with subreason `MISSING_INPUT`. After any non-PASS cell (a wall or a missing input) the remaining cells are `UNKNOWN / NOT_EVALUATED`. Nothing is guessed.

## 4. Gate state machine
```mermaid
stateDiagram-v2
  [*] --> EVALUATE
  EVALUATE --> PASS: rule holds
  EVALUATE --> FAIL: rule violated
  EVALUATE --> UNKNOWN: input missing
  PASS --> [*]: advance
  FAIL --> [*]: wall -> REJECTED
  UNKNOWN --> [*]: no advance
  [*] --> NOT_EVALUATED: an earlier cell stopped the scene
  NOT_EVALUATED --> [*]: no measurement, nothing guessed
```

## 5. Zones & partitioning
```mermaid
flowchart TD
  ING[ingest done] --> RAW[RAW<br/>immutable + hash<br/>every scene]
  RAW --> MZ[maze result]
  MZ --> ROUTER{router<br/>precedence rule}
  ROUTER --> VAL[VALIDATED<br/>9x PASS, 0 imputed]
  ROUTER --> REJ[REJECTED<br/>1+ FAIL + DQ code]
  ROUTER --> UNK[UNKNOWN<br/>no FAIL, any UNKNOWN]
  VAL --> MET[METRIC monthly<br/>series level]
  REJ --> MET
  UNK --> MET
```

RAW is written at ingestion, before the maze, for every scene. The router only chooses among `validated`, `rejected` and `unknown`. The monthly metric reads all three zones, because "where we know and where we do not" needs the rejected and unknown areas too.

## 6. Audit points
```mermaid
flowchart LR
  P0[P0 request] --> P1[P1 catalog resp]
  P1 --> P2[P2 transport]
  P2 --> P3[P3 maze]
  P3 --> P4[P4 persist]
  P4 --> P5[P5 prep]
  P5 --> P6[P6 upload]
  P6 -.-> P7[P7 consume<br/>deferred to v2]
```

Audit points (decision D1): ingestion = P0-P2, maze = P3, persistence = P4, publication = P5-P6. P7 is deferred to v2. The log is append-only with no hash chain in v1 (decision D2); tamper evidence comes from committing the exported log manifest to git.

## 7. Publication & viewer
```mermaid
flowchart LR
  VAL[validated zone] --> PREP[PREP P5<br/>mask + metrics]
  UNK[unknown zone] --> PREP
  PREP --> UP[UPLOAD P6<br/>tileset version<br/>no overwrite]
  UP --> RT{round-trip<br/>count + props}
  RT -- match --> ACT[Active=true]
  RT -- mismatch --> NO[DQ-570<br/>active=false]
  NO --> KEEP[previous version<br/>stays live]
```

UNKNOWN areas are published with their own visible style (hatched), never as empty space.

## 8. One-glance summary
```mermaid
flowchart TD
  S[STAC] --> ING[INGEST<br/>raw zone]
  ING --> VEC{VECTOR 3x1<br/>track open?}
  VEC -- open --> MAZE[MAZE 3x3<br/>A->B->C<br/>stop at first wall]
  VEC -- blocked --> UNKN[UNKNOWN<br/>VECTOR_TRACK_FAILED]
  MAZE --> Z{ROUTER}
  Z -- validated --> PUB[PUBLICATION<br/>manifest + round-trip]
  Z -- unknown --> PUB
  UNKN --> PUB
  Z -- rejected --> REJ[REJECTED<br/>audit log only]
  PUB --> MAP[Viewer<br/>derived]
  ING -.-> AUD[AUDIT<br/>append-only log]
  MAZE -.-> AUD
  Z -.-> AUD
  PUB -.-> AUD
```

## P0 decisions

- [x] Precedence FAIL > UNKNOWN. A scene that stops at a wall has FAIL on that cell and NOT_EVALUATED (UNKNOWN) on the rest, and is routed to `rejected`.
- [x] Layer effectiveness (V5, folded into V4 by D6) is part of the vector track gate: it runs once per layer version and blocks every scene of that territory. It is not a scene-level precondition.
- [x] B3 threshold: strict 100% in v1. Revisit with real tile metadata for Barranquilla.
- [x] C1 (required bands) stays a cell in row C. Revisit after the data access probe (STAC asset list vs opening the file).
- [x] A2 and A3 stay separate. If A3 never fails in 12 months of data, remove it instead of merging.
- [x] P7 is deferred to v2.
- [x] Publication scope and viewer (S5, S6): MapLibre GL JS with PMTiles on static storage; publish mask, footprints and monthly coverage, no imagery in v1.
- [x] D1: 4 audit points instead of 8 (ingestion P0-P2, maze P3, persistence P4, publication P5-P6). Approved.
- [x] D2: no hash chain on the audit log in v1; use git for tamper evidence. Approved.
- [x] D6: vector track limited to 3 checks in v1 (V1 geometry, V3 attributes, V4 code and layer version); V2 overlaps returns in v1.5. Approved.
- [x] D3, D4, D5, D7, D8: approved (delegated). See docs/decisions/0001-design-decisions.md.
- [x] F1 to F6 resolved: DQ-510 means CRS present but invalid; vector-blocked scenes carry the layer code; strict B3 plus a near-miss view; DQ-521 merged into DQ-520; 9 evaluation rows per scene; C2 uses the metadata offset.
- [ ] C3 threshold: pending real data (probe PR4, protocol in contract section 6.2).
