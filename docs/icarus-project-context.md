# Icarus — Project Context

## 1. Project summary

Icarus is a Canada-first, mobile-first wildfire and heat situational-awareness application. It combines active wildfire information, weather, smoke, air quality, official alerts, local news, shelters, and user location into one interactive map.

The product should answer four questions quickly:

1. What is happening near me?
2. Am I currently at risk?
3. Where is the danger likely to move?
4. Where can I safely go, and how do I get there?

Icarus is named after the mythological warning against flying too close to the sun. The name reinforces the product's purpose: understand heat and fire, recognize approaching danger, and keep a safe distance. Icarus is not an emergency authority. It supports awareness and navigation while directing users to official evacuation instructions.

## 2. Product vision

Build the clearest and most useful Canada-first wildfire map for ordinary people—not a technical forestry dashboard. Information should be geographically connected, easy to scan, timestamped, sourced, and honest about uncertainty.

Initial launch area: Ontario.

Expansion path: all Canadian provinces and territories, followed by cross-border fire and smoke conditions affecting Canada.

## 3. Target users

- Residents near active wildfires
- People monitoring family members or saved locations
- Travellers and drivers entering affected regions
- People sensitive to smoke or poor air quality
- Community organizations and local volunteers
- Journalists and researchers needing a consolidated overview

## 4. Core product principles

- **Location first:** translate regional information into personal relevance.
- **Official sources first:** emergency and government information outranks media reporting.
- **Timestamp everything:** users need to know how fresh each layer is.
- **Never hide uncertainty:** observed, reported, modelled, and predicted data must look different.
- **Safety over engagement:** no sensational language, gamification, or attention traps.
- **Accessible under stress:** large touch targets, plain language, strong contrast, and limited cognitive load.
- **Useful under weak connectivity:** cache the last known map, alerts, and saved locations.

## 5. MVP scope

### 5.1 Interactive map

- Ontario base map with pan, zoom, search, and geolocation
- Active fire ignition points and official fire perimeters
- Satellite hotspots with confidence and observation time
- Fire danger and Fire Weather Index layers
- Wind direction and speed
- Smoke coverage
- AQI, AQHI, PM2.5, and health-risk layer
- Evacuation zones and emergency alert boundaries
- Road closures and major route disruptions when available
- Shelter and reception-centre locations
- Layer visibility controls and a timestamp legend

### 5.2 Fire incident window

Selecting a fire opens a focused panel containing:

- Official incident name and identifier
- Status: not under control, being held, under control, or observed
- Current estimated area
- Discovery time and latest update
- Official perimeter and hotspot history
- Nearby communities and infrastructure
- Wind, humidity, precipitation, temperature, and fire-weather conditions
- Official alerts, evacuation notices, and closures
- Related regional news
- Data sources and last-updated times
- An estimated movement corridor clearly labelled as a model output

### 5.3 Personal safety status

- Determine the user’s current position with permission
- Allow manually entered and saved locations
- Calculate distance to active perimeters, hotspots, evacuation zones, and smoke
- Display a simple status: **Normal, Monitor, Prepare, or Follow evacuation order**
- Explain which signals caused the status
- Never issue an independent evacuation command
- Link directly to the responsible authority

### 5.4 Air quality and smoke

- AQI and Canadian AQHI
- PM2.5 concentration
- Smoke plume or smoke forecast layer
- Current wind speed and direction
- Health guidance adjusted to current risk
- Additional guidance for asthma, cardiovascular conditions, children, older adults, pregnancy, and outdoor workers
- Indoor-air actions: close windows, run filtration, avoid indoor smoke sources
- Outdoor guidance: activity reduction and N95 recommendations

### 5.5 Shelters and safer destinations

- Use official municipal, provincial, First Nations, emergency-management, Red Cross, and public 211 information
- Show whether a location is confirmed open, reported, full, closed, or awaiting verification
- Display source and last verification time
- Rank shelters by **safety and travel feasibility**, not distance alone
- Exclude or strongly warn against locations inside:
  - active fire perimeters
  - evacuation or restricted zones
  - projected movement corridors
  - impassable or closed-route areas
  - severe smoke zones when safer alternatives exist
- Show route distance, estimated travel time, route hazards, accessibility, pet policy, capacity, and contact details when available
- Require users to confirm operational status before travel when the feed is not authoritative and current
- Provide one-tap directions and 211/emergency contact links

### 5.6 News and updates

- Match articles and official updates to incidents using fire IDs, place names, and geographic proximity
- Prioritize sources in this order:
  1. Emergency alerts and evacuation orders
  2. Provincial and municipal authorities
  3. First Nations and local emergency-management offices
  4. Fire agencies and transportation authorities
  5. Reputable regional and national news
- Group duplicate reports into one developing story
- Show publication time, event time, source, and affected region
- Avoid placing rumours or social posts in the same visual category as verified alerts

### 5.7 Notifications

- Fire detected within a user-defined radius
- Existing fire grows toward the user or a saved place
- New evacuation order or emergency alert
- Shelter status changes
- Planned route enters a danger or closure zone
- AQHI/AQI or PM2.5 crosses a health threshold
- Major change in wind or smoke direction
- Significant official incident update
- Quiet hours with emergency alerts allowed to override
- Location tracking must be opt-in and privacy-conscious

## 6. Prediction scope

The first version should show an **estimated movement corridor**, not claim to predict the exact future perimeter.

Inputs may include:

- Recent perimeter changes
- Time-sequenced satellite hotspots
- Wind direction and speed
- Temperature, humidity, and precipitation
- Fire Weather Index components
- Elevation, slope, and aspect
- Vegetation and fuel type
- Natural and artificial firebreaks
- Suppression activity when reported

Outputs:

- Direction of likely movement
- 6-, 12-, and 24-hour estimated corridors
- Low, medium, or high confidence
- Model generation time
- Input freshness
- A permanent statement that the estimate is not an evacuation order

Do not begin with custom machine learning. Start with explainable rules and historical perimeter comparison. Validate predictions before increasing their prominence.

## 7. Data-source plan

Preferred sources:

- Natural Resources Canada Canadian Wildland Fire Information System (CWFIS)
- Ontario Aviation, Forest Fire and Emergency Services
- Ontario Open Data fire perimeters
- Environment and Climate Change Canada GeoMet weather services
- Environment Canada AQHI and public weather alerts
- NASA FIRMS/VIIRS satellite hotspots
- Provincial emergency alerts and municipal evacuation notices
- Ontario 511 and municipal road-closure sources
- Ontario 211, official reception-centre listings, and recognized relief organizations
- Reputable regional news feeds

Every normalized record should retain:

- Original source
- Source URL
- Source record identifier
- Observation/event time
- Publication time
- Ingestion time
- Geometry
- Confidence or verification status
- Expiry time where relevant

## 8. Recommended technical architecture

### Frontend

- Next.js with TypeScript
- Tailwind CSS or CSS modules
- MapLibre GL JS for the interactive map
- deck.gl for larger geospatial overlays if needed
- Installable Progressive Web App first
- Native mobile application later through Expo/React Native if background location becomes essential

### Backend

- FastAPI or NestJS
- PostgreSQL with PostGIS
- Scheduled workers for data ingestion and normalization
- Redis for caching and short-lived alert state if required
- REST endpoints initially; WebSockets or server-sent events only for genuinely urgent live updates

### Services

- Firebase Cloud Messaging or equivalent for notifications
- Sentry for errors and feed failures
- Privacy-friendly analytics
- Map tile provider with Canadian coverage and acceptable emergency-use reliability

### Suggested internal API resources

- `GET /fires`
- `GET /fires/:id`
- `GET /fires/:id/timeline`
- `GET /conditions?lat=&lng=`
- `GET /air-quality?lat=&lng=`
- `GET /alerts?bounds=`
- `GET /shelters?lat=&lng=`
- `GET /news?fire_id=`
- `POST /risk/evaluate`
- `POST /notification-subscriptions`

## 9. Visual direction: green and orange

The visual identity should feel like a modern environmental safety product: grounded, calm, outdoors-oriented, and trustworthy. It should not resemble a military command centre, cryptocurrency dashboard, or dark cyberpunk interface.

### Palette

- Deep forest: `#12372A` — navigation, strong text, map controls
- Evergreen: `#1F5C45` — primary brand colour
- Fresh green: `#49A078` — safe status, active controls, supportive information
- Pale sage: `#E8F1EA` — page background and quiet surfaces
- Warm cream: `#FFF9EF` — cards and content panels
- Ember orange: `#F26A2E` — fire activity and primary urgency accent
- Amber orange: `#F5A33B` — warning state
- Deep ember: `#A83E19` — severe danger and evacuation information
- Charcoal: `#213029` — body text
- Muted green-grey: `#718078` — secondary labels

Orange communicates fire, heat, alerts, and urgent actions. Green communicates environment, safety, verified shelters, navigation, and normal conditions. Do not use green to soften genuine danger.

### Interface style

- Light-first interface with optional dark map mode
- Cream and pale-sage surfaces rather than pure white or black
- Rounded cards, approximately 12–16 px radius
- Fine green-grey borders
- Moderate shadows, never glowing neon effects
- Map remains visually dominant
- Use orange sparingly so urgent information remains meaningful
- Use warm off-white space to make dense emergency data easier to scan
- Charts and legends must use colour plus icons, labels, or patterns for accessibility

### Typography

- Headings: Manrope, Sora, or Plus Jakarta Sans
- Body and interface: Inter
- Numeric measurements may use IBM Plex Mono sparingly
- Avoid tiny uppercase text as the primary information hierarchy

### Proposed desktop layout

- Top navigation: logo, search, saved locations, notifications, profile/settings
- Main canvas: map occupying roughly 65–75% of the viewport
- Left floating panel: layer filters and incident list
- Right contextual drawer: selected fire, safety status, air quality, shelters, and updates
- Bottom mobile sheet: replaces side drawers on smaller screens
- A persistent compact safety pill shows the user’s current location status

### Emotional target

The UI should feel like **a national park field guide combined with a modern weather app**: natural, clear, calm, and highly legible, with orange appearing where attention is truly required.

## 10. Core data models

### Fire

- id, agency_id, name, status, cause
- ignition point, current perimeter
- discovered_at, updated_at
- area_hectares
- containment or control information
- agency and source

### Observation

- fire_id, type, geometry
- observed_at, ingested_at
- confidence, source
- radiative power where available

### Alert

- id, severity, type, headline, instructions
- geometry and affected communities
- issued_at, updated_at, expires_at
- official source

### Shelter

- id, name, coordinates, address
- operational status and capacity
- accessibility, pets, services, contact
- verified_at, source, source URL
- danger-screening result

### Environmental conditions

- coordinates and timestamp
- AQI, AQHI, PM2.5
- wind speed and direction
- temperature, humidity, precipitation
- Fire Weather Index components

### User place

- user_id or anonymous device ID
- label and coordinates
- alert radius and notification preferences
- privacy and retention settings

## 11. Safety and legal requirements

- Never present model output as an official evacuation decision
- Never label an unverified facility as confirmed open
- Show source and timestamp near all safety-critical claims
- Preserve official wording for evacuation instructions
- Provide emergency contact guidance without impersonating emergency services
- Design for stale, conflicting, and unavailable feeds
- Display a visible degraded-data state when an important source fails
- Avoid claiming a person is safe solely because they are outside a distance radius
- Protect precise user locations and minimize retention
- Complete accessibility testing to WCAG 2.2 AA standards
- Obtain legal review before marketing the system as a safety or prediction product

## 12. Development phases

### Phase 1 — Functional map

- Create the project and map shell
- Add Ontario fire points/perimeters
- Add incident selection and detail drawer
- Add layer controls
- Add geolocation and saved location locally

### Phase 2 — Environmental intelligence

- Add wind and weather
- Add AQI, AQHI, PM2.5, and smoke
- Add official alerts
- Add timestamps, source labels, and degraded-feed states

### Phase 3 — Shelters and routing

- Ingest official/public shelter listings
- Build danger-zone screening
- Rank safer destinations
- Add directions and closure-aware routing

### Phase 4 — Updates and notifications

- Add fire-specific official updates and news
- Add subscriptions and push notifications
- Add saved places and preference controls

### Phase 5 — Movement estimates

- Store perimeter and hotspot history
- Implement explainable directional estimates
- Back-test and measure forecast error
- Add confidence-based display rules

## 13. MVP acceptance criteria

The MVP is ready for public testing when:

- Users can see active Ontario fires on a working map
- Every incident shows a source and updated time
- Users can locate themselves or enter a location manually
- The application shows nearby fire, air-quality, smoke, and official-alert context
- A selected shelter is screened against known fire and evacuation geometry
- Unverified shelter status is clearly disclosed
- Layer controls work on desktop and mobile
- Feed failures do not crash the application
- Prediction labels cannot be mistaken for official instructions
- The product is keyboard accessible and readable without colour alone

## 14. Out of scope for the first release

- Exact property-loss prediction
- Guaranteed evacuation routing
- Autonomous evacuation orders
- Firefighter dispatch or resource management
- Crowdsourced emergency claims without verification
- Insurance risk scoring
- Global wildfire coverage
- Complex machine-learning prediction before a validated baseline exists

## 15. Immediate build order

1. Establish the green–orange design tokens and responsive application shell.
2. Render a reliable Ontario map with MapLibre.
3. Normalize one authoritative fire feed into internal `Fire` objects.
4. Display fire points, perimeters, status, sources, and timestamps.
5. Add geolocation and manual place search.
6. Add live weather, wind, AQI/AQHI, PM2.5, and smoke.
7. Add official alerts and evacuation geometry.
8. Add shelter ingestion and danger-zone screening.
9. Add news matching and incident timelines.
10. Add notifications only after the risk logic and data-failure states are tested.

---

This document is the canonical project brief. Update it whenever product scope, safety rules, data sources, architecture, or the visual system changes.
