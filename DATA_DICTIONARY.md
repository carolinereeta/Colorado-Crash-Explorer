# Data dictionary and transformations

## Source

CDOT, [Statewide Crash Data Listing, 2021–2026](https://www.codot.gov/safety/traffic-safety/data-analysis/crash-data). The supplied Excel files contain **110 source columns** each. The project selects the fields needed for reproducible descriptive analysis; no original rows are published in the GitHub data folder.

| Source field | Purpose | Handling |
|---|---|---|
| `CUID` | Source crash identifier | Duplicate values within the same annual file are detected before aggregation. May be blank. |
| `Crash Date` | Date of crash | Excel serial date, validated against filename year. Invalid dates excluded from day/month breakdowns. |
| `Crash Time` | Clock time | Parsed `HH:MM`; invalid or blank times excluded from hour breakdown. |
| `City`, `County` | Geography | City `COLORADO SPRINGS`, county `EL PASO` are matching values for local subsets. |
| `Latitude`, `Longitude` | Geospatial distribution | Only coordinates in a generous Colorado bounding box retained. El Paso cells rounded to 0.01°. |
| `Crash Type` | Crash classification | CDOT category, retained verbatim. |
| `Number Killed`, `Number Injured` | Outcomes | Used for mutually exclusive crash-level classifications. |
| `Road Condition`, `Lighting Conditions`, `Weather Condition` | Contextual labels | Values retained verbatim; blanks grouped under Unknown. |
| `School Zone` | Administrative school-zone flag | `1`/`true`/`yes` treated as flagged; `0`/`false`/`no` treated as not flagged. |
| `TU-1 NM Type`, `TU-2 NM Type` | Exploratory non-motorist classification | Text searched for pedestrian/cyclist/other. May miss cases; cannot prove absence. |
| `Record Status` | Data maturity | Audited, including 2026 New and In Progress rows. No records excluded solely because of this status. |
| `Road Description`, `Location`, `Total Vehicles` | Available in the importer | Reserved for follow-on location-specific work. |

## Derived outputs

| CSV / JSON | Row grain |
|---|---|
| `annual.csv` | Crash year × area |
| `county_year.csv` | Crash year × county × severity |
| `monthly.csv` | Crash year × area × month × severity |
| `time.csv` | Crash year × area × time dimension (weekday/hour) × value × severity |
| `conditions.csv` | Crash year × area × condition family × condition value × severity |
| `crash_types.csv` | Crash year × area × crash type × severity |
| `nonmotorist.csv` | Crash year × area × detected non-motorist type × severity |
| `school_zone.csv` | Crash year × area × school-zone flag × severity |
| `el_paso_grid.csv` | Crash year × rounded coordinate grid-cell center × severity |
| `data_quality.csv` | Crash year × quality metric |
| `summary.json` | Processing metadata and annual counts |

## Critical methodological notes

- The file's year is used for the annual summary; malformed/mismatched dates are separately audited.
- Each crash appears once per area layer if it belongs there: Colorado, El Paso County, and/or Colorado Springs. **Do not add those three area totals together.** The city is within the county, which is within the state.
- The source contains vehicle and non-motorist fields whose interpretations can evolve. Consult the **official 2021–2026 CDOT Data Dictionary** and verify definitions before publishing new claims.
- `Number Killed` and `Number Injured` count *people*, but this project deliberately **reports crash counts** by outcomes. To calculate numbers of affected people, explicitly sum the fields in a separate transformation.
- Spatial bin coordinates are **centers of quantized cells**, not source crash coordinates. A 0.01-degree square covers different real-world distances by latitude and orientation, so it should not be described as exactly 1 square kilometer.
- This is reported motor-vehicle crash data, not a sidewalk-condition inventory or a census of falls.
