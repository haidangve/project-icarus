# Fire Source Spike

Evaluation of wildfire data sources before integrating them into Icarus.

## CWFIF active fires

- Provider: Natural Resources Canada

- Collection: `public:cwfif_national_activefires`

- Format: GeoJSON

- Geometry: `Point`

- Filter: current Ontario records

```text

agency_code='ON'

AND now()>=record_start

AND now()<=record_end

```

## Run

From `experiments/fire-source-spike`:

```powershell

.\.venv\Scripts\Activate.ps1

python -m src.fetch_cwfis

```

The script writes:

```text

fixtures/cwfis-active-fires.json

fixtures/cwfis-active-fires.metadata.json

```

## CWFIS Findings

- Retrieved 171 current Ontario records.
- All records use `Point` geometry.
- No records are missing national IDs, agency IDs or geometry.
- Status codes: `OC` out of control, `BH` being held, `UC` under control.
- Cause codes: `N` natural and `H` human.
- Response codes: `FUL` full, `MOD` modified and `MON` monitored.
- `percent_contained` is `-1` for all records and cannot be used.
- `national_fire_id` is the preferred cross-source identifier.
- This source provides fire locations, not official perimeters.
- Response is a valid GeoJSON `FeatureCollection`.

## LIO Findings

- Retrieved 121 in-year Ontario fire perimeters.
- Geometry includes 82 polygons and 39 multipolygons.
- No records are missing geometry or fire numbers.
- `FIRENUMB` maps to the CWFIF agency ID:
  - `COC008` → `COC_FIRE_008`
- 43 LIO perimeters matched current CWFIF incidents.
- Every matched perimeter has `STATUS = I`.
- Unmatched records include 67 `F` and 11 `I` perimeters.
- `F` represents a final perimeter.
- `I` represents an interim perimeter.
- CWFIF remains authoritative for active-fire status.
- LIO supplies perimeter geometry only after an exact identifier match.
- Final LIO perimeters must not cause inactive fires to appear active.
- One `OFR` record and `THUMB-N512ME` are excluded from automatic matching.

## Reference
- Fire locations use `Point` geometry.

- `agency_code = ON` identifies Ontario records.

- `national_fire_id` is the preferred cross-source identifier.

- `agency_fire_id` is the Ontario incident identifier.

- `fire_size` contains reported area; unit still needs confirmation.

- `stage_of_control_status = OC` means out of control.

- `percent_contained = -1` means unavailable, not negative containment.

- `national_fire_cause = N` means natural.

- Timestamps ending in `Z` are UTC.

- `record_end` is a database validity boundary, not the estimated end of a fire.

## Important fields


| Meaning | Property |

|---|---|

| National ID | `national_fire_id` |

| Ontario ID | `agency_fire_id` |

| Region | `region_code` |

| Size | `fire_size` |

| Status | `stage_of_control_status` |

| Cause | `national_fire_cause` |

| Status time | `status_date` |

| Situation report time | `situation_report_date` |

## Limitations

This source provides reported fire points, not official perimeters, evacuation zones, smoke or satellite hotspots.

## Next

Inspect unique code values, confirm the `fire_size` unit, and evaluate the Ontario/LIO perimeter source.
