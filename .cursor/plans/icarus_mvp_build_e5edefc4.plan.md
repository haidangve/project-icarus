---
name: Icarus MVP Build
overview: Greenfield build of Icarus as a monorepo with a Next.js PWA frontend and FastAPI/PostGIS backend, delivering the full MVP (Phases 1–4 plus rule-based movement corridors) for Ontario wildfire situational awareness through public-testing acceptance criteria.
todos:
  - id: foundation
    content: "Scaffold monorepo at D:/project-icarus: Next.js PWA, FastAPI, Docker (PostGIS+Redis), design tokens, app shell, copy brief to docs/"
    status: pending
  - id: phase1-fires
    content: Implement LIO+CWFIS fire ingestion, PostGIS schema, map fire layers, incident drawer, geolocation/search, saved places
    status: pending
  - id: phase2-environment
    content: Add GeoMet weather/AQHI/alerts ingest, smoke/FWI layers, source timestamps, degraded-feed UI, air quality guidance panel
    status: pending
  - id: phase3-shelters
    content: Build shelter ingest (211 API + seed fallback), PostGIS danger screening, ranking, 511 closures, directions integration
    status: pending
  - id: phase4-risk-notify
    content: Implement risk engine + safety pill, news/timeline matching, FCM notifications, PWA offline cache
    status: pending
  - id: phase5-corridor
    content: Add fire observation history and rule-based movement corridor with explicit non-official labelling
    status: pending
  - id: mvp-qa
    content: "Run acceptance testing: feed failures, accessibility (WCAG 2.2 AA), mobile layout, safety disclaimer audit"
    status: pending
isProject: false
---

# Icarus MVP Implementation Plan

## Scope and success criteria

This plan covers the **full MVP** through [section 13 acceptance criteria](C:\Users\Admin\Downloads\icarus-project-context.md): Ontario fires on a working map, sourced/timestamped data, personal location context, environmental layers, screened shelters, resilient feed failures, accessible UI, and model outputs clearly distinguished from official instructions.

**Out of scope for v1** (per brief section 14): ML prediction, guaranteed evacuation routing, autonomous evacuation orders, global coverage, and property-loss modeling. Movement corridors use **explainable rules only** (brief section 6).

**Backend choice:** FastAPI + PostgreSQL/PostGIS + Redis (your selection).

**Project location:** `D:/project-icarus` (existing git repo). Canonical brief lives at `docs/icarus-project-context.md`.

---

## Architecture

```mermaid
flowchart TB
  subgraph clients [Clients]
    PWA[Next.js PWA]
  end

  subgraph api [FastAPI Service]
    REST[REST API]
    Risk[Risk Engine]
    Cache[Redis Cache]
  end

  subgraph workers [Ingestion Workers]
    FireJob[Fire Ingest]
    EnvJob[Weather/AQ Ingest]
    AlertJob[Alerts Ingest]
    ShelterJob[Shelter Ingest]
    NewsJob[News Ingest]
    NotifyJob[Notification Dispatcher]
  end

  subgraph storage [Storage]
    PG[(PostgreSQL + PostGIS)]
  end

  subgraph external [External Feeds]
    LIO[LIO Ontario Fire Perimeters]
    CWFIS[CWFIS WFS]
    GeoMet[MSC GeoMet OGC API]
    FIRMS[NASA FIRMS VIIRS]
    ON511[Ontario 511 Events]
    ON211[Ontario 211 API]
    NewsRSS[Regional News RSS]
  end

  PWA --> REST
  REST --> Cache
  REST --> PG
  REST --> Risk
  Risk --> PG
  FireJob --> LIO
  FireJob --> CWFIS
  EnvJob --> GeoMet
  EnvJob --> CWFIS
  AlertJob --> GeoMet
  ShelterJob --> ON211
  ShelterJob --> ON511
  NewsJob --> NewsRSS
  workers --> PG
  NotifyJob --> PG
```

### Monorepo layout

```
icarus/
├── apps/web/                 # Next.js 15, TypeScript, Tailwind, MapLibre, PWA
├── services/api/             # FastAPI, SQLAlchemy, Alembic, APScheduler workers
├── packages/shared/          # OpenAPI-generated TS types + shared constants
├── infra/
│   ├── docker-compose.yml    # postgres+postgis, redis
│   └── .env.example
└── docs/icarus-project-context.md
```

### Core stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Frontend | Next.js App Router, MapLibre GL JS | Brief spec; strong PWA support |
| Styling | Tailwind + CSS variables for design tokens | Matches green-orange system |
| Map tiles | OpenMapTiles/Protomaps or MapTiler (env-configurable) | Canadian coverage; fallback tile URL in config |
| Routing/directions | OSRM (self-hosted or public demo initially) | Closure-aware routing layered in app logic |
| Backend | FastAPI + async SQLAlchemy + GeoAlchemy2 | Geospatial ingestion fit |
| DB | PostgreSQL 16 + PostGIS 3 | Spatial queries for risk/shelter screening |
| Cache | Redis | Feed snapshots, alert dedup, rate-limit buffers |
| Notifications | Firebase Cloud Messaging | Brief spec; Web Push via service worker |
| Observability | Sentry | Feed failure + API error tracking |

---

## Design system (first deliverable)

Implement tokens from brief section 9 as Tailwind theme extensions in [`apps/web/tailwind.config.ts`](apps/web/tailwind.config.ts):

- **Greens:** `#12372A`, `#1F5C45`, `#49A078`, `#E8F1EA`
- **Oranges:** `#F26A2E`, `#F5A33B`, `#A83E19`
- **Neutrals:** `#FFF9EF` (cards), `#213029` (text), `#718078` (labels)
- **Fonts:** Plus Jakarta Sans (headings), Inter (body), IBM Plex Mono (metrics)

Build the responsive shell per brief section 9:

- Desktop: top nav + ~70% map canvas + left layer/incident panel + right contextual drawer
- Mobile: map-first + bottom sheet for context
- Persistent **safety status pill** (placeholder until risk engine lands)
- Every data card includes **source + timestamp** slots from day one

Accessibility baseline: WCAG 2.2 AA — colour + icon + label for all status/layer states; keyboard trap-free drawers; 44px touch targets.

---

## Data model and PostGIS schema

Alembic migrations in [`services/api/migrations/`](services/api/migrations/) implementing brief section 10, with these additions:

**Normalized provenance fields on every record:** `source_name`, `source_url`, `source_record_id`, `observed_at`, `published_at`, `ingested_at`, `confidence`, `expires_at`.

**Key tables:**

- `fires` — id, agency_id, name, status, cause, ignition (Point), perimeter (Polygon), area_hectares, discovered_at, updated_at
- `fire_observations` — hotspot/perimeter history snapshots for movement rules
- `alerts` — severity, type, headline, instructions, geometry, communities, issued/expires
- `environmental_conditions` — point observations with AQI, AQHI, PM2.5, wind, FWI components
- `shelters` — coordinates, operational_status (`confirmed_open`, `reported`, `full`, `closed`, `awaiting_verification`), verification metadata, danger_screening JSON
- `news_items` — headline, url, published_at, matched_fire_ids[], dedup_group_id
- `user_places` — anonymous device_id, label, point, alert_radius, preferences (no auth v1; upgrade path to accounts)
- `notification_subscriptions` — place_id, trigger types, quiet_hours, fcm_token
- `feed_health` — source_id, last_success, last_error, degraded flag

**Spatial indexes** on all geometry columns; use `ST_DWithin`, `ST_Intersects`, `ST_Distance` for risk and shelter screening.

---

## Data ingestion map

| Data | Primary source | Ingest approach | Refresh cadence |
|------|----------------|-----------------|-----------------|
| Ontario fire perimeters | [LIO layer 51](https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open09/MapServer/51) | ArcGIS `query?f=geojson&where=1=1&outSR=4326` | Every 1–4 hours |
| Active fire points + national context | [CWFIS WFS `activefires_current`](https://cwfis.cfs.nrcan.gc.ca/geoserver/public/ows) | WFS GetFeature GeoJSON; filter Ontario bbox | Hourly |
| Satellite hotspots | CWFIS `hotspots_last24hrs` + NASA FIRMS VIIRS (MAP_KEY) | WFS + CSV→GeoJSON; dedupe by proximity/time | Every 30–60 min |
| Fire danger / FWI | LIO layer 50 + CWFIS `fdr_current` / `firewx_stns_current` | WFS + ArcGIS layers | Every 1–4 hours |
| Weather + wind | GeoMet collections (e.g. `citypageweather-realtime`, grid layers) | OGC API `items?bbox=&f=json` | Every 15–30 min |
| AQHI / PM2.5 | GeoMet `aqhi-observations-realtime`, `aqhi-forecasts-realtime` | OGC API with Ontario bbox | Every 30 min |
| Official alerts | GeoMet `weather-alerts` | OGC API; store geometry + official wording verbatim | Every 5–15 min |
| Smoke | CWFIS WMS smoke layers (display) + optional raster cache | WMS tile proxy or pre-rendered overlay | Every 1–4 hours |
| Road disruptions | [Ontario 511 Events API](https://511on.ca/developers/doc) | REST; throttle 10 req/min | Every 15 min |
| Shelters | Ontario 211 API (requires access) | Authorized API; taxonomy filter for emergency shelter | Every 2–4 hours |
| News | CBC Ontario, CP24, municipal RSS | RSS/Atom ingest + geo/keyword matching | Every 30 min |

**Early parallel action:** Email `211data@211ontario.ca` for API access on day 1. Until approved, seed shelters from municipal emergency pages with `operational_status=awaiting_verification` and prominent UI disclosure.

**Feed resilience pattern** (required for acceptance):

1. Worker writes to PostGIS + updates `feed_health`
2. API serves last good snapshot from Redis/DB when fetch fails
3. UI shows **degraded-data banner** per source; app never crashes on empty/partial feeds

---

## API surface

Implement in [`services/api/app/routers/`](services/api/app/routers/) per brief section 8:

| Endpoint | Purpose |
|----------|---------|
| `GET /fires?bbox=` | Active fires with source, status, geometry, updated_at |
| `GET /fires/{id}` | Full incident detail for drawer |
| `GET /fires/{id}/timeline` | Perimeter/hotspot/alert history |
| `GET /conditions?lat=&lng=` | Weather, wind, FWI near point |
| `GET /air-quality?lat=&lng=` | AQHI, AQI, PM2.5 + health guidance tier |
| `GET /alerts?bbox=` | Official alerts intersecting viewport |
| `GET /shelters?lat=&lng=&radius_km=` | Screened + ranked shelters |
| `GET /news?fire_id=` | Matched articles, deduped |
| `POST /risk/evaluate` | Returns `Normal` / `Monitor` / `Prepare` / `Follow evacuation order` + explaining signals |
| `POST /notification-subscriptions` | Register place + triggers + FCM token |
| `GET /feeds/health` | Source freshness for UI degraded states |

OpenAPI spec drives `packages/shared` TypeScript client generation for the frontend.

---

## Frontend feature breakdown

### Phase 1 — Functional map (weeks 1–3)

1. Design tokens + app shell ([`apps/web/app/layout.tsx`](apps/web/app/layout.tsx), [`apps/web/components/shell/`](apps/web/components/shell/))
2. MapLibre map centered on Ontario with pan/zoom/search/geolocation
3. Fire layers: ignition points, official perimeters (distinct styles: official=solid, satellite=dashed)
4. Left panel: layer toggles + scrollable incident list
5. Right drawer / mobile sheet: fire detail with status, area, discovery/update times, source links
6. Saved places in `localStorage` + geolocation permission flow
7. Place search via Nominatim (Ontario-biased)

### Phase 2 — Environmental intelligence (weeks 3–5)

1. Wind, temperature, humidity, precipitation overlays/cards
2. AQHI, PM2.5, smoke layer with legend distinguishing observed vs modelled
3. Official alert polygons on map + alert list in drawer
4. Air quality panel with population-specific guidance (brief section 5.4)
5. Timestamp legend component showing freshness per active layer
6. `FeedDegradedBanner` tied to `GET /feeds/health`

### Phase 3 — Shelters and routing (weeks 5–7)

1. Shelter markers with status badges (`confirmed_open` vs `awaiting_verification`)
2. **Danger-zone screening** before display:

```mermaid
flowchart LR
  Shelter[Shelter candidate] --> CheckPerimeter{Inside fire perimeter?}
  CheckPerimeter -->|yes| Exclude[Exclude or strong warning]
  CheckPerimeter -->|no| CheckEvac{Inside evacuation zone?}
  CheckEvac -->|yes| Exclude
  CheckEvac -->|no| CheckCorridor{Inside movement corridor?}
  CheckCorridor -->|yes| Warn[Warn + deprioritize]
  CheckCorridor -->|no| CheckRoads{Route through closure?}
  CheckRoads --> Rank[Rank by safety + travel feasibility]
```

3. Ranking weighs: outside danger geometry > route feasibility > smoke exposure > distance
4. Route preview with hazards (511 closures); one-tap directions link (external maps)
5. Pre-travel confirmation modal when `operational_status != confirmed_open`

### Phase 4 — Updates, risk, notifications (weeks 7–9)

1. **Risk engine** (`POST /risk/evaluate`):

   - Inputs: user point, nearest perimeter distance, evacuation intersection, smoke/AQHI thresholds, alert severity, wind toward user
   - Output: status enum + human-readable signal list + authority link (never independent evacuation command)
   - Safety pill updates live

2. News feed matched to selected fire; developing-story grouping
3. Fire timeline in detail drawer
4. FCM push notifications for triggers in brief section 5.7
5. Quiet hours with emergency override
6. PWA service worker: cache last map state, alerts, saved places for offline read

### Phase 5 subset — Movement corridors (week 9, MVP-minimal)

1. Store perimeter + hotspot snapshots in `fire_observations`
2. Rule-based corridor: recent perimeter centroid shift + wind vector + 6/12/24h buffers
3. Render as **distinct dashed/hatched overlay** labelled "Estimated movement — not an evacuation order"
4. Show confidence (low/medium/high), model time, input freshness in fire detail panel only

---

## Key UI components to build

| Component | Location | Notes |
|-----------|----------|-------|
| `MapCanvas` | `apps/web/components/map/` | MapLibre wrapper, layer registry |
| `LayerPanel` | `apps/web/components/shell/` | Toggles + legend |
| `IncidentDrawer` | `apps/web/components/incident/` | Fire detail, timeline, corridor disclaimer |
| `SafetyPill` | `apps/web/components/safety/` | Risk status, always visible |
| `AirQualityCard` | `apps/web/components/environment/` | AQHI + vulnerable-group guidance |
| `ShelterList` | `apps/web/components/shelters/` | Status badges, screening warnings |
| `AlertBanner` | `apps/web/components/alerts/` | Official wording preserved |
| `SourceStamp` | `apps/web/components/common/` | Reusable source + timestamp |
| `DegradedFeedNotice` | `apps/web/components/common/` | Per-source stale state |

---

## Development phases and sequencing

Work follows brief section 15 immediate build order, grouped into implementable milestones:

**Milestone A — Foundation**
- Monorepo, Docker, DB migrations, design tokens, empty map shell, FastAPI health

**Milestone B — Fires on map (Phase 1 complete)**
- LIO + CWFIS ingest, fire layers, incident drawer, geolocation/search, saved places

**Milestone C — Environment (Phase 2 complete)**
- GeoMet weather/AQ/alerts, smoke/FWI layers, timestamps, degraded states

**Milestone D — Shelters (Phase 3 complete)**
- 211 ingest (or seed), screening, ranking, 511 closures, directions

**Milestone E — Risk + news + push (Phase 4 complete)**
- Risk engine, news matching, notifications, PWA offline cache

**Milestone F — Movement corridor (MVP-minimal Phase 5)**
- Observation history, rule-based corridor, disclaimer UX

---

## Testing and launch checklist

- **Spatial tests:** PostGIS queries for shelter screening and risk distance calculations
- **Feed failure tests:** Simulate 503/timeout per source; verify UI banners and last-known-good data
- **Safety copy review:** Corridor and risk labels include non-authoritative disclaimers
- **Accessibility:** axe-core CI + manual keyboard/screen-reader pass on map controls and drawers
- **Mobile:** Bottom sheet, touch targets, safety pill on small viewports
- **Performance:** Map remains responsive with Ontario bbox clipping; paginate large WFS responses

Map acceptance criteria from brief section 13 as the release gate.

---

## Environment variables

```env
# infra/.env.example
DATABASE_URL=postgresql+asyncpg://icarus:icarus@localhost:5432/icarus
REDIS_URL=redis://localhost:6379
FIRMS_MAP_KEY=           # NASA FIRMS registration
MAP_TILE_URL=            # MapLibre style/tiles
GEOMET_BASE=https://api.weather.gc.ca
FCM_PROJECT_ID=          # Firebase for push
SENTRY_DSN=
ONTARIO_511_API_KEY=     # if required by 511
ON211_API_KEY=           # after data agreement
```

---

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Ontario 211 API access delayed | Seed verified municipal shelter CSV; mark unverified; begin 211 outreach immediately |
| CWFIS/LIO schema changes | Store raw payload JSON alongside normalized fields; adapter layer per source |
| Ontario 511 rate limits (10/min) | Cache aggressively; ingest incrementally |
| Smoke raster complexity | Start with CWFIS WMS tile overlay; defer heavy raster processing |
| Legal/safety liability | Preserve official alert wording; disclaimers on all model output; legal review before marketing as safety product |
