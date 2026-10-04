#!/usr/bin/env python3
"""Evidence-first Dutch walking/cycling route helper (stdlib only)."""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

USER_AGENT = "Hermes-Dutch-Routing-Skill/0.1 (+https://github.com/rogerogert/hermes-skills)"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
OVERPASS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)
ROUTERS = {
    "walk": "https://routing.openstreetmap.de/routed-foot/route/v1/driving/",
    "bike": "https://routing.openstreetmap.de/routed-bike/route/v1/driving/",
}
# Broadly the Netherlands, including its islands. This is a guardrail, not a border test.
NL_BOUNDS = (50.70, 53.65, 3.10, 7.35)  # south, north, west, east


def request_json(url: str, *, data: bytes | None = None, timeout: int = 45) -> dict[str, Any]:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded; charset=utf-8"
    req = Request(url, data=data, headers=headers)
    try:
        with urlopen(req, timeout=timeout) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"request failed: {exc}") from exc


def geocode(query: str) -> dict[str, Any]:
    params = urlencode({"q": query, "format": "jsonv2", "limit": "1", "countrycodes": "nl"})
    data = request_json(f"{NOMINATIM}?{params}")
    if not data:
        raise RuntimeError(f"No Dutch geocoding result for: {query!r}")
    item = data[0]
    lat, lon = float(item["lat"]), float(item["lon"])
    assert_netherlands(lat, lon)
    return {"name": item["display_name"], "lat": lat, "lon": lon, "osm_type": item.get("osm_type"), "osm_id": item.get("osm_id")}


def assert_netherlands(lat: float, lon: float) -> None:
    south, north, west, east = NL_BOUNDS
    if not (south <= lat <= north and west <= lon <= east):
        raise RuntimeError(f"Point {lat:.6f},{lon:.6f} is outside the Netherlands guardrail")


def overpass(query: str) -> dict[str, Any]:
    errors: list[str] = []
    for endpoint in OVERPASS:
        try:
            return request_json(endpoint, data=query.encode(), timeout=75)
        except RuntimeError as exc:
            errors.append(str(exc))
    raise RuntimeError("All Overpass endpoints failed: " + " | ".join(errors))


def lookup_nodes(near: str, mode: str, radius: int, limit: int) -> dict[str, Any]:
    centre = geocode(near)
    ref_key = "rwn_ref" if mode == "walk" else "rcn_ref"
    query = f'''[out:json][timeout:50];node["{ref_key}"](around:{radius},{centre["lat"]},{centre["lon"]});out body;'''
    elements = overpass(query).get("elements", [])
    records = []
    for element in elements:
        ref = element.get("tags", {}).get(ref_key)
        if ref is None:
            continue
        lat, lon = float(element["lat"]), float(element["lon"])
        records.append({
            "ref": ref,
            "lat": lat,
            "lon": lon,
            "osm_url": f"https://www.openstreetmap.org/node/{element['id']}",
            "distance_km": round(haversine_km(centre["lat"], centre["lon"], lat, lon), 2),
        })
    records.sort(key=lambda item: item["distance_km"])
    return {"source": "OpenStreetMap via Overpass", "queried_at": utc_now(), "mode": mode, "ref_key": ref_key, "centre": centre, "nodes": records[:limit]}


def lookup_pois(near: str, kind: str, radius: int, limit: int) -> dict[str, Any]:
    centre = geocode(near)
    selectors = {
        "nature": 'nwr["leisure"="nature_reserve"](around:{r},{lat},{lon});nwr["natural"="wood"](around:{r},{lat},{lon});',
        "water": 'nwr["natural"="water"](around:{r},{lat},{lon});nwr["waterway"="riverbank"](around:{r},{lat},{lon});',
        "windmill": 'nwr["man_made"="windmill"](around:{r},{lat},{lon});',
        "castle": 'nwr["historic"="castle"](around:{r},{lat},{lon});',
        "cafe": 'nwr["amenity"="cafe"](around:{r},{lat},{lon});',
        "museum": 'nwr["tourism"="museum"](around:{r},{lat},{lon});',
    }
    if kind not in selectors:
        raise RuntimeError(f"Unknown POI kind {kind!r}")
    query = "[out:json][timeout:50];(" + selectors[kind].format(r=radius, lat=centre["lat"], lon=centre["lon"]) + ");out center;"
    records = []
    for element in overpass(query).get("elements", []):
        tags = element.get("tags", {})
        point = element.get("center", element)
        if "lat" not in point or "lon" not in point:
            continue
        lat, lon = float(point["lat"]), float(point["lon"])
        records.append({
            "name": tags.get("name", f"Unnamed {kind}"),
            "lat": lat,
            "lon": lon,
            "osm_url": f"https://www.openstreetmap.org/{element['type']}/{element['id']}",
            "distance_km": round(haversine_km(centre["lat"], centre["lon"], lat, lon), 2),
        })
    records.sort(key=lambda item: item["distance_km"])
    return {"source": "OpenStreetMap via Overpass", "queried_at": utc_now(), "kind": kind, "centre": centre, "pois": records[:limit]}


def parse_point(value: str) -> tuple[float, float]:
    try:
        lat_s, lon_s = (part.strip() for part in value.split(",", 1))
        lat, lon = float(lat_s), float(lon_s)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("point must be LAT,LON") from exc
    try:
        assert_netherlands(lat, lon)
    except RuntimeError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return lat, lon


def build_route(mode: str, points: list[tuple[float, float]], name: str, output: Path) -> dict[str, Any]:
    if len(points) < 2:
        raise RuntimeError("At least two --point LAT,LON values are required")
    # OSM routing API expects lon,lat and semicolon-separated coordinates.
    coordinate_path = ";".join(f"{lon:.7f},{lat:.7f}" for lat, lon in points)
    params = urlencode({"overview": "full", "geometries": "geojson", "steps": "true"})
    data = request_json(f"{ROUTERS[mode]}{coordinate_path}?{params}", timeout=90)
    if data.get("code") != "Ok" or not data.get("routes"):
        raise RuntimeError("Routing engine returned no route: " + json.dumps(data)[:500])
    route = data["routes"][0]
    coordinates = route.get("geometry", {}).get("coordinates", [])
    if len(coordinates) < 2:
        raise RuntimeError("Routing engine returned geometry with fewer than two points")
    output.parent.mkdir(parents=True, exist_ok=True)
    write_gpx(output, name, mode, points, coordinates)
    return {
        "source": "OpenStreetMap routing (routed-foot/routed-bike)",
        "queried_at": utc_now(),
        "mode": mode,
        "name": name,
        "distance_km": round(float(route["distance"]) / 1000, 2),
        "duration_minutes": round(float(route["duration"]) / 60),
        "input_waypoints": [{"lat": lat, "lon": lon} for lat, lon in points],
        "geometry_points": len(coordinates),
        "gpx": str(output.resolve()),
    }


def write_gpx(path: Path, name: str, mode: str, points: list[tuple[float, float]], coordinates: list[list[float]]) -> None:
    trkpts = "\n".join(f'      <trkpt lat="{lat:.7f}" lon="{lon:.7f}" />' for lon, lat, *_ in coordinates)
    wpts = "\n".join(f'  <wpt lat="{lat:.7f}" lon="{lon:.7f}"><name>Waypoint {idx}</name></wpt>' for idx, (lat, lon) in enumerate(points, 1))
    content = f'''<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Hermes Dutch Walking &amp; Cycling Guide" xmlns="http://www.topografix.com/GPX/1/1">
  <metadata><name>{escape(name)}</name><time>{utc_now()}</time><desc>Mode: {escape(mode)}; geometry fetched live from OpenStreetMap routing.</desc></metadata>
{wpts}
  <trk><name>{escape(name)}</name><type>{mode}</type><trkseg>
{trkpts}
  </trkseg></trk>
</gpx>
'''
    path.write_text(content, encoding="utf-8")


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_geo = sub.add_parser("geocode")
    p_geo.add_argument("query")
    for cmd in ("nodes", "pois"):
        p = sub.add_parser(cmd)
        p.add_argument("--near", required=True)
        p.add_argument("--radius", type=int, default=15000)
        p.add_argument("--limit", type=int, default=12)
    p_nodes = sub.choices["nodes"]
    p_nodes.add_argument("--mode", choices=("walk", "bike"), required=True)
    p_pois = sub.choices["pois"]
    p_pois.add_argument("--kind", choices=("nature", "water", "windmill", "castle", "cafe", "museum"), required=True)
    p_route = sub.add_parser("route")
    p_route.add_argument("--mode", choices=("walk", "bike"), required=True)
    p_route.add_argument("--point", type=parse_point, action="append", required=True, help="repeatable LAT,LON")
    p_route.add_argument("--name", required=True)
    p_route.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "geocode": result = geocode(args.query)
        elif args.command == "nodes": result = lookup_nodes(args.near, args.mode, args.radius, args.limit)
        elif args.command == "pois": result = lookup_pois(args.near, args.kind, args.radius, args.limit)
        else: result = build_route(args.mode, args.point, args.name, args.output)
    except RuntimeError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
