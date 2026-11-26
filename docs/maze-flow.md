# Maze Flow — End-to-End Visual

> Status: draft v0.1 — technical artifact (English). Business contract stays in Spanish.
> Source of truth for `evaluate(context) -> Result` and the zone router.

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

## 1. High-level pipeline (backend -> viewer)

```mermaid
flowchart LR
  STAC[(STAC catalog)] --> ING[INGEST<br/>P0-P2<br/>download + hash]
  ING --> MAZE[MAZE<br/>P3<br/>vector 5x1 + scene 3x3]
  MAZE --> ZONES[ZONES<br/>P4<br/>raw / validated /<br/>rejected / unknown]
  ZONES --> AUDIT[AUDIT<br/>P0-P7<br/>hash chain<br/>append-only]
  AUDIT --> PUB[PUBLICATION<br/>P5-P7<br/>manifest + round-trip]
  PUB --> VIEW[Mapbox viewer<br/>derived]

---

**BLOQUE 2:**
```markdown
## 2. Vector track (5x1) — once per layer version

```mermaid
flowchart TD
  L[territory layer] --> V1{V1<br/>geometry valid?}
  V1 -- PASS --> V2{V2<br/>no overlaps?}
  V1 -- FAIL --> E1[DQ-541]
  V2 -- PASS --> V3{V3<br/>attrs complete?}
  V2 -- FAIL --> E2[DQ-542]
  V3 -- PASS --> V4{V4<br/>DANE code in catalog?}
  V3 -- FAIL --> E3[DQ-501]
  V4 -- PASS --> V5{V5<br/>layer effective?}
  V4 -- FAIL --> E4[DQ-540]
  V5 -- PASS --> OPEN[[TRACK OPEN]]
  V5 -- FAIL --> E5[DQ-544]
  E1 & E2 & E3 & E4 & E5 --> BLOCK[[TRACK BLOCKED<br/>scenes = UNKNOWN<br/>subreason=VECTOR_TRACK_FAILED]]
flowchart TD
  T([scene token]) --> A1{A1<br/>identity unique?}
  A1 -- PASS --> A2{A2<br/>integrity hash+opens?}
  A1 -- FAIL --> R530[REJECTED DQ-530]
  A2 -- PASS --> A3{A3<br/>baseline known?}
  A2 -- FAIL --> R550[REJECTED DQ-550]
  A3 -- PASS --> B1{B1<br/>CRS coherent?}
  A3 -- FAIL --> R531[REJECTED DQ-531]
  B1 -- PASS --> B2{B2<br/>footprint/bbox coherent?}
  B1 -- FAIL --> R510[REJECTED DQ-510]
  B2 -- PASS --> B3{B3<br/>territory inside footprint?}
  B2 -- FAIL --> R511[REJECTED DQ-511]
  B3 -- PASS --> C1{C1<br/>required bands?}
  B3 -- FAIL --> R512[REJECTED DQ-512]
  C1 -- PASS --> C2{C2<br/>values in baseline range?}
  C1 -- FAIL --> R522[REJECTED DQ-522]
  C2 -- PASS --> C3{C3<br/>usable_coverage >= thr?}
  C2 -- FAIL --> R523[REJECTED DQ-523]
  C3 -- PASS --> OK[[VALIDATED]]
  C3 -- FAIL --> R520[REJECTED DQ-520/521]


---

**BLOQUE 3:**
```markdown
## 4. Gate state machine (per cell)

```mermaid
stateDiagram-v2
  [*] --> EVALUATE
  EVALUATE --> PASS: rule holds
  EVALUATE --> FAIL: rule violated
  EVALUATE --> UNKNOWN: input missing / not evaluated
  PASS --> [*]: advance
  FAIL --> [*]: wall -> REJECTED
  UNKNOWN --> [*]: no advance (subreason)
flowchart TD
  RES[scene result] --> ROUTER{router<br/>precedence rule}
  ROUTER --> RAW[RAW<br/>immutable + hash]
  ROUTER --> VAL[VALIDATED<br/>9x PASS, 0 imputed]
  ROUTER --> REJ[REJECTED<br/>>=1 FAIL + DQ]
  ROUTER --> UNK[UNKNOWN<br/>no FAIL, any UNK]
  VAL --> MET[METRIC monthly<br/>series level]
flowchart LR
  P0[P0 request] --> P1[P1 catalog resp]
  P1 --> P2[P2 transport]
  P2 --> P3[P3 maze]
  P3 --> P4[P4 persist]
  P4 --> P5[P5 prep]
  P5 --> P6[P6 upload]
  P6 --> P7[P7 consume]
flowchart LR
  VAL[validated zone] --> PREP[PREP P5<br/>mask + metrics]
  PREP --> UP[UPLOAD P6<br/>tileset version<br/>no overwrite]
  UP --> RT{round-trip<br/>count + props}
  RT -- match --> ACT[active=true<br/>register P7]
  RT -- mismatch --> NO[DQ-570<br/>active=false]

flowchart TD
  S[STAC] --> ING[INGEST]
  ING --> VEC[VECTOR 5x1<br/>open/closed]
  VEC --> MAZE[MAZE 3x3<br/>A->B->C<br/>stop at first wall]
  MAZE --> Z{VALIDATED / REJECTED / UNKNOWN}
  Z --> AUD[AUDIT CHAIN<br/>P0-P7 hash-linked]
  AUD --> PUB[PUBLICATION<br/>manifest + round-trip]
  PUB --> MAP[Mapbox<br/>derived, UNKNOWN hatched]
