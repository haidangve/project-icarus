# # Icarus

Icarus is a Canada-first wildfire and heat intelligence platform that combines active fires, smoke, air quality, weather, official alerts, regional updates, and safer shelter information on an interactive map.

> Icarus is a situational-awareness project, not an emergency authority. Users must follow instructions issued by official emergency-management organizations.

## Project status

Early development and data-source validation.

## Structure

- `apps/web` — Next.js web application

- `services/api` — FastAPI backend

- `packages/shared` — shared types and constants

- `experiments` — source and geospatial research

- `docs` — product, architecture, safety, and data documentation

## Local development

### Web

```bash

npm install

npm run dev:web
```
## Safety

Icarus is a situational-awareness project, not an emergency authority.

Official alert wording must be preserved. Modelled information must be identified as non-official and include its uncertainty, source, and generation time.

Users must follow evacuation orders and emergency instructions issued by the responsible authorities.