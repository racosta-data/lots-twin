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
