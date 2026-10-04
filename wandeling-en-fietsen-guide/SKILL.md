---
name: wandeling-en-fietsen-guide
description: Build verified Dutch walking and cycling routes.
version: 0.1.0
author: Rogério, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [netherlands, walking, cycling, knooppunten, gpx, openstreetmap]
    category: productivity
    requires_toolsets: [terminal, file_operations]
---

# Wandeling en Fietsen Guide

Create Dutch walking and cycling routes from live OpenStreetMap data rather than plausible-sounding prose. It can discover mapped walking (`rwn_ref`) and cycling (`rcn_ref`) knooppunten, find real POIs, call the appropriate OSM router, and write a GPX track with the returned geometry.

This skill is deliberately evidence-first. It does not claim a route, a node number, a scenic feature, distance, duration, ferry, surface, or accessibility condition unless the live query returned it. A route engine result proves that a traversable route was returned at query time; it does not prove current closures, works, weather, opening hours, or signage condition.

## When to Use

- The user wants a Dutch walk, hike, bike ride, day trip, route around a town, or GPX file.
- The user asks for walking or cycling knooppunten / route nodes.
- The user wants actual nearby nature, water, windmills, castles, cafés, or museums as route anchors.
- The user wants to check or reproduce a route by coordinates.

Do not use it for public-transport itineraries, real-time closure advice, or routes outside the Netherlands.

## Prerequisites

- Python 3.8+; the helper has no third-party dependencies.
- Network access to Nominatim, Overpass, and `routing.openstreetmap.de`.
- Resolve the installed folder before invoking the helper:

  `GUIDE="${HERMES_SKILL_DIR}/scripts/nl_route.py"`

The helper uses:

- Nominatim: Dutch geocoding, restricted to NL.
- Overpass + current OSM tags: node and POI evidence.
- OSM routed-foot / routed-bike: actual track geometry and length/duration estimates.

All APIs are community services. Query only for real requests, keep result sets small, and never bulk-scrape them.

## Evidence Rules

1. Start with live evidence. Run `geocode`, `nodes`, or `pois` before proposing anchors. Do not make up landmarks or knooppunt references from model knowledge.
2. Present the source and query time. Treat the tool's JSON as the source of truth for coordinates, distance, duration, and names.
3. A listed knooppunt is a live OSM-mapped node, not a promise that every sign is intact. State the exact tag: `rwn_ref` for walking or `rcn_ref` for cycling.
4. A GPX is only deliverable after `route` succeeds, writes a non-empty file, and the XML parses. Never construct GPX coordinates yourself.
5. If a service fails, returns no suitable evidence, or a point is outside NL, say so and stop. Offer a narrower search or exact start point; never substitute an invented route.
6. Do not say a route "follows the knooppunten network" merely because its waypoint coordinates are mapped nodes. Say it is *routed via verified mapped node locations*. Claim signed-network continuity only when the user independently provides a verified node sequence or another source proves it.

## How to Run

All helper calls print JSON. Invoke them with `terminal` and inspect the returned values before using them in the response.

### Resolve a start point

```
terminal(command="python3 \"$GUIDE\" geocode 'Station Utrecht Centraal'")
```

This returns one geocoded Dutch coordinate; retain its exact `lat` and `lon`.

### Discover knooppunten near a place

```
terminal(command="python3 \"$GUIDE\" nodes --mode bike --near 'Utrecht Centraal' --radius 15000 --limit 12")
terminal(command="python3 \"$GUIDE\" nodes --mode walk --near 'Nationaal Park Zuid-Kennemerland' --radius 15000 --limit 12")
```

Use only references and coordinates returned in the `nodes` array. Note that repeated node references can occur across regions; identify nodes by their returned coordinate and OSM URL, never by bare number alone.

### Discover factual route anchors

```
terminal(command="python3 \"$GUIDE\" pois --near 'Leiden Centraal' --kind windmill --radius 12000 --limit 8")
terminal(command="python3 \"$GUIDE\" pois --near 'Amersfoort' --kind nature --radius 20000 --limit 8")
```

Allowed kinds: `nature`, `water`, `windmill`, `castle`, `cafe`, `museum`. A POI result is an anchor candidate, not a recommendation. Pick routes with a coherent shape: start → two or three anchors → start for a loop, or start → destination for a one-way route.

### Produce a verified GPX route

Pass every selected point exactly as `LAT,LON`; make a loop by repeating the start as the final point. The routing engine selects the track between anchors.

```
terminal(command="python3 \"$GUIDE\" route --mode bike --name 'Leiden windmill loop' --point '52.1665,4.4816' --point '52.1512,4.5000' --point '52.1665,4.4816' --output ./leiden-windmill-loop.gpx", timeout=120)
```

The output JSON contains the only authoritative route length, estimated duration, geometry point count, and absolute GPX path.

## Procedure

1. Establish the brief: mode, start, desired distance or time, one-way vs loop, and interests. If missing, default to a loop with no more than three anchors and say what you assumed. Completion: there is a concrete start and mode.
2. Fetch evidence using `geocode`, `nodes`, and/or `pois`. For a knooppunten request, use `nodes` in the matching mode. Completion: every planned anchor has live coordinates and an OSM URL or geocoding result.
3. Curate one route, not five random ones. Prefer two to three geographically coherent verified anchors; reject a point if it creates obvious backtracking. Completion: the exact ordered waypoint list is written as `LAT,LON` values.
4. Call `route` using the selected points and the correct mode. For a loop, repeat the first point last. Completion: JSON reports a positive `distance_km`, `geometry_points >= 2`, and a GPX path.
5. Verify the GPX locally:

   ```
   terminal(command="python3 -c \"import sys, xml.etree.ElementTree as E; p=sys.argv[1]; r=E.parse(p).getroot(); assert r.tag.endswith('gpx'); print('GPX valid:', p)\" /absolute/path/from-route-output.gpx")
   ```

   Completion: the command prints `GPX valid` and the file is non-empty.
6. Respond with mode, exact start/anchors, route-engine distance and duration, evidence caveat, source/query time, and the absolute GPX path. Do not fabricate turn-by-turn directions, surfaces, or scenic descriptions.

## Response Shape

```
Route: [name] — [walking/cycling], [loop/one-way]
Verified anchors: [start] → [anchor names or node refs] → [start/destination]
Route-engine result: [distance_km] km, about [duration_minutes] min
Evidence: OpenStreetMap [routing / Overpass], queried [timestamp]
Caveat: GPX geometry is live-routed; check closures, signs, weather, ferries, and access locally before leaving.
GPX: [absolute path]
```

If using nodes, write `Cycling node <rcn_ref>` or `Walking node <rwn_ref>` only for the exact records returned by the helper. Include the node's OSM URL when the user needs to inspect it.

## Pitfalls

- Dutch knooppunt references are not globally unique. Never route to "node 52" without first resolving a nearby node record.
- Public OSM endpoints can be rate-limited or temporarily unavailable. The helper tries two Overpass mirrors; do not retry aggressively.
- Foot and bike routers return an estimated duration, not a promise. Cycling estimates assume an ordinary bike, not an e-bike or a loaded touring bike.
- POI geometry may be a large area (forest, water) rather than a useful entrance. For those cases, choose a named nearby node or ask the user for a preferred entrance.
- Keep waypoints modest. Too many points can make a route artificial and can overwhelm public routing services.
- GPX has no live closure awareness. A successful file is a valid track, not a safety guarantee.

## Verification

Run this smoke test only when network access is available:

```
terminal(command="python3 \"$GUIDE\" route --mode walk --name 'Amsterdam smoke test' --point '52.370216,4.895168' --point '52.372000,4.900000' --output /tmp/hermes-nl-route-smoke.gpx", timeout=120)
terminal(command="python3 -c \"import xml.etree.ElementTree as E; E.parse('/tmp/hermes-nl-route-smoke.gpx'); print('GPX valid')\"")
```

Both commands must succeed. If either does not, do not represent the skill as ready for route generation.
