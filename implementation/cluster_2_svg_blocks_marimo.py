import marimo

__generated_with = "0.17.6"
app = marimo.App(width="wide")


@app.cell
def _():
    import csv
    import json
    import math
    from collections import Counter, defaultdict
    from datetime import datetime, timedelta
    from html import escape
    from pathlib import Path

    import marimo as mo
    return (
        Counter,
        Path,
        csv,
        datetime,
        defaultdict,
        escape,
        json,
        math,
        mo,
        timedelta,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Cluster 2 SVG Notebook

    This notebook contains the Cluster 2 visuals directly as marimo cells:

    - `fishing full`: the fishing-boat vs tourist-shore scene
    - `block 8`: the board visit map
    - `block 9`: the trip-time summary
    """)
    return


@app.cell
def _(Path):
    DEFAULT_ROOT = Path("/Users/bouns/g0r72a_data_peiyang_2526")

    SOURCE_NAMES = ("Journalist", "Government")
    CATEGORY_ORDER = ("Fishing", "Tourism", "Hybrid", "Neutral")

    CATEGORY_COLORS = {
        "Fishing": "#1f5aa6",
        "Tourism": "#d17a22",
        "Hybrid": "#6f6f6f",
        "Neutral": "#cfcfcf",
    }

    CATEGORY_STROKES = {
        "Fishing": "#123d73",
        "Tourism": "#9b5515",
        "Hybrid": "#4d4d4d",
        "Neutral": "#8f8f8f",
    }

    ZONE_COLORS = {
        "industrial": "#355c7d",
        "tourism": "#f08a5d",
        "government": "#7b6d8d",
        "residential": "#7fb069",
        "commercial": "#e9c46a",
        "connector": "#8ecae6",
        "unknown": "#d9d9d9",
    }

    FISHING_TOPICS = {
        "deep_fishing_dock",
        "fish_vacuum",
        "new_crane_lomark",
        "low_volume_crane",
        "affordable_housing",
        "name_inspection_office",
    }

    TOURISM_TOPICS = {
        "expanding_tourist_wharf",
        "heritage_walking_tour",
        "marine_life_deck",
        "waterfront_market",
        "name_harbor_area",
        "statue_john_smoth",
        "concert",
        "renaming_park_himark",
    }

    HYBRID_TOPICS = {"seafood_festival"}

    FISHING_KEYWORDS = (
        "fish",
        "fishing",
        "harvest",
        "dock",
        "crane",
        "shipping",
        "wharf",
        "marine",
    )

    TOURISM_KEYWORDS = (
        "tour",
        "tourist",
        "restaurant",
        "market",
        "grill",
        "hall of fame",
        "bait",
        "festival",
        "park",
        "harbor area",
    )
    return (
        CATEGORY_COLORS,
        CATEGORY_ORDER,
        CATEGORY_STROKES,
        DEFAULT_ROOT,
        FISHING_TOPICS,
        HYBRID_TOPICS,
        SOURCE_NAMES,
        TOURISM_TOPICS,
        ZONE_COLORS,
    )


@app.cell
def _(
    CATEGORY_ORDER,
    Counter,
    FISHING_TOPICS,
    HYBRID_TOPICS,
    TOURISM_TOPICS,
    csv,
    datetime,
    defaultdict,
    math,
    timedelta,
):
    def normalize_year(date_text):
        if date_text.startswith("0040-"):
            return "2040" + date_text[4:]
        return date_text

    def parse_stamp(date_text, time_text=None):
        if time_text is None:
            return datetime.strptime(normalize_year(date_text), "%Y-%m-%d %H:%M:%S")
        return datetime.strptime(
            f"{normalize_year(date_text)} {time_text}",
            "%Y-%m-%d %H:%M:%S",
        )

    def read_rows(path):
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def classify_topic(topic_id):
        if topic_id in FISHING_TOPICS:
            return "Fishing"
        if topic_id in TOURISM_TOPICS:
            return "Tourism"
        if topic_id in HYBRID_TOPICS:
            return "Hybrid"
        return "Neutral"

    def dominant_category(labels):
        focused = [label for label in labels if label in {"Fishing", "Tourism", "Hybrid"}]
        if not focused:
            return None
        counts = Counter(focused).most_common()
        if len(counts) > 1 and counts[0][1] == counts[1][1]:
            return "Hybrid"
        return counts[0][0]

    def category_from_zone(zone):
        zone = (zone or "").strip().lower()
        if zone == "tourism":
            return "Tourism"
        if zone == "industrial":
            return "Fishing"
        return "Neutral"


    def apply_manual_zone_override(row):
        zone = (row.get("zone") or "unknown").strip().lower()
        name = (row.get("name") or "").strip()

        if zone == "residential" and name == "Paakland Elementary":
            return "tourism", "manual override"
        if zone == "residential" and name in {"Waveside Townhomes", "Tidewater Flats"}:
            return "industrial", "manual override"
        if name == "Tropics Environmental Hub":
            return "tourism", "manual override"
        return zone, "native zone"


    def haversine_km(lat_a, lon_a, lat_b, lon_b):
        lat_a_rad, lon_a_rad = math.radians(lat_a), math.radians(lon_a)
        lat_b_rad, lon_b_rad = math.radians(lat_b), math.radians(lon_b)
        delta_lat = lat_b_rad - lat_a_rad
        delta_lon = lon_b_rad - lon_a_rad
        value = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat_a_rad) * math.cos(lat_b_rad) * math.sin(delta_lon / 2) ** 2
        )
        return 6371.0 * 2 * math.asin(min(1.0, math.sqrt(value)))


    def classify_weighted_knn_places(places, k=5, max_radius_km=1.5, epsilon=0.001):
        targets = [
            place
            for place in places
            if place["zone_remapped"] in {"industrial", "tourism"}
        ]
        candidates = [
            place
            for place in places
            if place["zone"] in {"commercial", "residential"}
            and place["zone_remapped"] not in {"industrial", "tourism"}
        ]

        predictions = {}
        if not targets or not candidates or k <= 0 or max_radius_km <= 0:
            return predictions

        for candidate in candidates:
            neighbors = []
            for target in targets:
                distance_km = haversine_km(
                    candidate["lat"],
                    candidate["lon"],
                    target["lat"],
                    target["lon"],
                )
                neighbors.append((distance_km, target["zone_remapped"]))

            scores = defaultdict(float)
            for distance_km, target_zone in sorted(neighbors, key=lambda item: item[0])[:k]:
                if distance_km <= max_radius_km:
                    scores[target_zone] += 1.0 / (distance_km + epsilon)

            if scores:
                predicted_zone, weighted_score = sorted(
                    scores.items(),
                    key=lambda item: (-item[1], item[0]),
                )[0]
                predictions[candidate["place_id"]] = {
                    "zone": predicted_zone,
                    "score": weighted_score,
                }

        return predictions


    def prepare_places(place_rows, remap_k, remap_radius_km):
        places = []
        for row in place_rows:
            zone = (row.get("zone") or "unknown").strip().lower()
            zone_remapped, remap_method = apply_manual_zone_override(row)
            place_record = {
                "place_id": str(row["place_id"]),
                "name": row["name"],
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "x": float(row["lat"]),
                "y": float(row["lon"]),
                "zone": zone,
                "zone_remapped": zone_remapped,
                "zone_detail": row["zone_detail"] or "",
                "remap_method": remap_method,
                "remap_score": None,
            }
            place_record["category"] = category_from_zone(zone_remapped)
            places.append(place_record)

        predictions = classify_weighted_knn_places(
            places,
            k=remap_k,
            max_radius_km=remap_radius_km,
        )

        for place in places:
            prediction = predictions.get(place["place_id"])
            if prediction is None:
                continue
            place["zone_remapped"] = prediction["zone"]
            place["category"] = category_from_zone(prediction["zone"])
            place["remap_method"] = "weighted nearest neighbors"
            place["remap_score"] = prediction["score"]

        return places

    def summarize_category_hours(visit_rows):
        totals = {label: 0.0 for label in CATEGORY_ORDER}
        for row in visit_rows:
            category = str(row["category"])
            totals[category] = totals.get(category, 0.0) + float(row["duration_hours"])
        return totals

    def dominant_time_category(category_hours):
        focus = {
            label: hours
            for label, hours in category_hours.items()
            if label in {"Fishing", "Tourism", "Hybrid"} and hours > 0
        }
        if focus:
            ordered = sorted(focus.items(), key=lambda item: (-item[1], item[0]))
            if len(ordered) > 1 and math.isclose(ordered[0][1], ordered[1][1]):
                return "Hybrid"
            return ordered[0][0]
        return "Neutral"

    def allocate_stop_hours(stops, start_dt, end_dt):
        stop_rows = []
        for index, stop in enumerate(stops):
            previous_time = stops[index - 1]["time"] if index > 0 else None
            next_time = stops[index + 1]["time"] if index < len(stops) - 1 else None

            if previous_time is None:
                before = stop["time"] - start_dt
            else:
                before = (stop["time"] - previous_time) / 2

            if next_time is None:
                after = end_dt - stop["time"]
            else:
                after = (next_time - stop["time"]) / 2

            enriched = dict(stop)
            enriched["duration_hours"] = max(before.total_seconds(), 0.0) / 3600.0
            enriched["duration_hours"] += max(after.total_seconds(), 0.0) / 3600.0
            stop_rows.append(enriched)

        return stop_rows


    def load_source(root, source_name, remap_k=5, remap_radius_km=1.5):
        source_dir = root / f"Collected_by_the_{source_name}"

        place_rows = read_rows(source_dir / "places.csv")
        trip_rows = read_rows(source_dir / "trips.csv")
        trip_people_rows = read_rows(source_dir / "trip_people.csv")
        trip_place_rows = read_rows(source_dir / "trip_places.csv")
        people_rows = read_rows(source_dir / "people.csv")

        place_lookup = {}
        all_places = prepare_places(place_rows, remap_k, remap_radius_km)

        for place_record in all_places:
            place_lookup[place_record["place_id"]] = place_record
            place_lookup[place_record["name"]] = place_record

        people_names = sorted({row["name"] for row in people_rows})

        trip_meta = {}
        for row in trip_rows:
            start_dt = parse_stamp(row["date"], row["start_time"])
            end_dt = parse_stamp(row["date"], row["end_time"])

            if end_dt < start_dt:
                end_dt += timedelta(days=1)

            trip_meta[row["trip_id"]] = {
                "trip_id": row["trip_id"],
                "date": normalize_year(row["date"]),
                "start_dt": start_dt,
                "end_dt": end_dt,
            }

        trip_members = defaultdict(list)
        for row in trip_people_rows:
            trip_members[row["trip_id"]].append(row["people_id"])

        trip_stops = defaultdict(list)
        for row in trip_place_rows:
            place = place_lookup.get(str(row["place_id"]))
            if place is None:
                continue

            trip_stops[row["trip_id"]].append(
                {
                    "trip_id": row["trip_id"],
                    "place_id": place["place_id"],
                    "name": place["name"],
                    "x": place["x"],
                    "y": place["y"],
                    "zone": place["zone"],
                    "zone_remapped": place["zone_remapped"],
                    "zone_detail": place["zone_detail"],
                    "category": place["category"],
                    "remap_method": place["remap_method"],
                    "remap_score": place["remap_score"],
                    "time": parse_stamp(row["time"]),
                }
            )

        visit_rows = []
        for trip_id, meta in trip_meta.items():
            stops = sorted(trip_stops.get(trip_id, []), key=lambda item: item["time"])
            if not stops:
                continue

            members = sorted(set(trip_members.get(trip_id, []))) or ["Unknown"]
            stop_rows = allocate_stop_hours(stops, meta["start_dt"], meta["end_dt"])

            for member in members:
                for stop in stop_rows:
                    visit_rows.append(
                        {
                            "source": source_name,
                            "trip_id": trip_id,
                            "date": meta["date"],
                            "start_dt": meta["start_dt"],
                            "end_dt": meta["end_dt"],
                            "member": member,
                            "place_id": stop["place_id"],
                            "name": stop["name"],
                            "x": stop["x"],
                            "y": stop["y"],
                            "zone": stop["zone"],
                            "zone_remapped": stop["zone_remapped"],
                            "zone_detail": stop["zone_detail"],
                            "category": stop["category"],
                            "remap_method": stop["remap_method"],
                            "remap_score": stop["remap_score"],
                            "duration_hours": float(stop["duration_hours"]),
                        }
                    )

        return {
            "name": source_name,
            "people_names": people_names,
            "places": all_places,
            "visit_rows": visit_rows,
        }
    return dominant_time_category, load_source, summarize_category_hours


@app.cell
def _(mo):
    remap_distance_widget = mo.ui.slider(
        start=0,
        stop=5,
        step=0.1,
        value=1.5,
        show_value=True,
        label="Remap radius (km)",
    )
    remap_neighbor_widget = mo.ui.slider(
        start=1,
        stop=10,
        step=1,
        value=5,
        show_value=True,
        label="Nearest references",
    )
    return remap_distance_widget, remap_neighbor_widget


@app.cell
def _(
    DEFAULT_ROOT,
    SOURCE_NAMES,
    load_source,
    remap_distance_widget,
    remap_neighbor_widget,
):
    source_data = {
        source_name: load_source(
            DEFAULT_ROOT,
            source_name,
            remap_k=remap_neighbor_widget.value,
            remap_radius_km=remap_distance_widget.value,
        )
        for source_name in SOURCE_NAMES
    }

    all_members = sorted(
        {
            member
            for dataset in source_data.values()
            for member in dataset["people_names"]
        }
    )
    return all_members, source_data


@app.cell
def _(all_members, mo):
    source_widget = mo.ui.dropdown(
        options=["Journalist", "Government"],
        value="Journalist",
        label="Source",
    )

    member_widget = mo.ui.multiselect(
        options=["All members"] + all_members,
        value=["All members"],
        label="Board member filter",
        full_width=True,
    )

    neutral_widget = mo.ui.checkbox(
        value=True,
        label="Include uncoded or admin stops",
    )
    return member_widget, neutral_widget, source_widget


@app.cell
def _(
    member_widget,
    mo,
    neutral_widget,
    remap_distance_widget,
    remap_neighbor_widget,
    source_widget,
):
    mo.vstack(
        [
            source_widget,
            member_widget,
            neutral_widget,
            remap_distance_widget,
            remap_neighbor_widget,
        ]
    )
    return


@app.cell
def _(member_widget, neutral_widget, source_data, source_widget):
    c2_selected_source = source_widget.value
    c2_source_members = set(source_data[c2_selected_source]["people_names"])

    c2_raw_selected_members = member_widget.value or ["All members"]

    if "All members" in c2_raw_selected_members or not c2_raw_selected_members:
        c2_selected_members = c2_source_members
    else:
        c2_selected_members = set(c2_raw_selected_members) & c2_source_members

    c2_include_neutral = neutral_widget.value

    c2_filtered_visits = [
        row
        for row in source_data[c2_selected_source]["visit_rows"]
        if row["member"] in c2_selected_members
        and (c2_include_neutral or row["category"] != "Neutral")
    ]

    c2_member_label = (
        "all board members"
        if c2_selected_members == c2_source_members
        else ", ".join(sorted(c2_selected_members))
    )
    return (
        c2_filtered_visits,
        c2_include_neutral,
        c2_member_label,
        c2_selected_source,
    )


@app.cell(hide_code=True)
def _(
    c2_filtered_visits,
    c2_member_label,
    c2_selected_source,
    mo,
    remap_distance_widget,
    remap_neighbor_widget,
):
    mo.md(f"""
    **Current filter**

    - source: `{c2_selected_source}`
    - members: `{c2_member_label}`
    - remapper: `{remap_neighbor_widget.value}` nearest references within `{remap_distance_widget.value:.1f}` km
    - filtered visit rows: `{len(c2_filtered_visits)}`
    """)
    return


@app.cell
def _(
    CATEGORY_COLORS,
    c2_filtered_visits,
    c2_member_label,
    c2_selected_source,
    escape,
):
    def render_fishing_full():
        scene_width = 980
        scene_height = 620

        member_summary = {}
        for visit in c2_filtered_visits:
            member_name = visit["member"]
            if member_name not in member_summary:
                member_summary[member_name] = {
                    "member": member_name,
                    "Fishing": 0.0,
                    "Tourism": 0.0,
                    "Hybrid": 0.0,
                    "Neutral": 0.0,
                }
            member_summary[member_name][visit["category"]] += float(visit["duration_hours"])

        people = []
        for summary in member_summary.values():
            fishing_value = summary["Fishing"] + 0.5 * summary["Hybrid"]
            tourism_value = summary["Tourism"] + 0.5 * summary["Hybrid"]
            people.append(
                {
                    "member": summary["member"],
                    "bias_gap": tourism_value - fishing_value,
                }
            )

        if people:
            bias_min = min(person["bias_gap"] for person in people)
            bias_max = max(person["bias_gap"] for person in people)
        else:
            bias_min = -1.0
            bias_max = 1.0

        def sx(x_ratio):
            return round(x_ratio * scene_width, 1)

        def sy(y_ratio):
            return round((1 - y_ratio) * scene_height, 1)

        def bias_to_x(value):
            if abs(bias_max - bias_min) < 1e-9:
                return 0.54
            return 0.26 + (value - bias_min) * (0.82 - 0.26) / (bias_max - bias_min)

        def blend_hex(color_a, color_b, t):
            t = max(0.0, min(1.0, t))
            a = color_a.lstrip("#")
            b = color_b.lstrip("#")
            ar, ag, ab = int(a[0:2], 16), int(a[2:4], 16), int(a[4:6], 16)
            br, bg, bb = int(b[0:2], 16), int(b[2:4], 16), int(b[4:6], 16)
            rr = round(ar + (br - ar) * t)
            rg = round(ag + (bg - ag) * t)
            rb = round(ab + (bb - ab) * t)
            return f"#{rr:02x}{rg:02x}{rb:02x}"

        max_abs_bias = max([abs(person["bias_gap"]) for person in people] + [0.25])
        for person in people:
            if max_abs_bias <= 1e-9:
                person["color"] = "#6f6f6f"
            elif person["bias_gap"] < 0:
                person["color"] = blend_hex("#6f6f6f", CATEGORY_COLORS["Fishing"], abs(person["bias_gap"]) / max_abs_bias)
            else:
                person["color"] = blend_hex("#6f6f6f", CATEGORY_COLORS["Tourism"], abs(person["bias_gap"]) / max_abs_bias)

            person["scene_x"] = bias_to_x(person["bias_gap"])
            if person["scene_x"] <= 0.31:
                person["foot_y"] = 0.37
                person["label_x"] = person["scene_x"] - 0.02
                person["label_y"] = 0.60
                person["label_anchor"] = "end"
            elif person["scene_x"] >= 0.74:
                person["foot_y"] = 0.32
                person["label_x"] = person["scene_x"] + 0.02
                person["label_y"] = 0.56
                person["label_anchor"] = "start"
            else:
                person["foot_y"] = 0.27
                person["label_x"] = person["scene_x"]
                person["label_y"] = 0.54
                person["label_anchor"] = "middle"
            person["head_y"] = person["foot_y"] + 0.10

        people.sort(key=lambda person: person["bias_gap"])

        def draw_person(svg_parts, x_ratio, foot_y_ratio, stroke_color):
            x = sx(x_ratio)
            foot_y = sy(foot_y_ratio)
            knee_y = sy(foot_y_ratio + 0.07)
            arm_y = sy(foot_y_ratio + 0.045)
            left_hand_x = sx(x_ratio - 0.045)
            right_hand_x = sx(x_ratio + 0.045)
            left_foot_x = sx(x_ratio - 0.035)
            right_foot_x = sx(x_ratio + 0.035)
            head_y = sy(foot_y_ratio + 0.10)

            svg_parts.append(f'<line x1="{x}" y1="{foot_y}" x2="{x}" y2="{knee_y}" stroke="{stroke_color}" stroke-width="2.2" stroke-linecap="round"/>')
            svg_parts.append(f'<line x1="{left_hand_x}" y1="{arm_y}" x2="{right_hand_x}" y2="{arm_y}" stroke="{stroke_color}" stroke-width="2.2" stroke-linecap="round"/>')
            svg_parts.append(f'<line x1="{x}" y1="{foot_y}" x2="{left_foot_x}" y2="{sy(foot_y_ratio - 0.035)}" stroke="{stroke_color}" stroke-width="2.2" stroke-linecap="round"/>')
            svg_parts.append(f'<line x1="{x}" y1="{foot_y}" x2="{right_foot_x}" y2="{sy(foot_y_ratio - 0.035)}" stroke="{stroke_color}" stroke-width="2.2" stroke-linecap="round"/>')
            svg_parts.append(f'<circle cx="{x}" cy="{head_y}" r="7.5" fill="none" stroke="{stroke_color}" stroke-width="2.2"/>')

        svg = []
        svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{scene_width}" height="{scene_height}" viewBox="0 0 {scene_width} {scene_height}">')
        svg.append(f'<rect x="0" y="0" width="{scene_width}" height="{scene_height}" fill="#fbfaf7" rx="20" ry="20"/>')
        svg.append(f'<rect x="{sx(0.05)}" y="{sy(0.95)}" width="{sx(0.95) - sx(0.05)}" height="{sy(0.52) - sy(0.95)}" fill="#fbf4e8"/>')
        svg.append(f'<rect x="{sx(0.05)}" y="{sy(0.28)}" width="{sx(0.67) - sx(0.05)}" height="{sy(0.05) - sy(0.28)}" fill="#cfe2ec"/>')
        svg.append(f'<polygon points="{sx(0.67)},{sy(0.05)} {sx(0.95)},{sy(0.05)} {sx(0.95)},{sy(0.34)} {sx(0.81)},{sy(0.34)} {sx(0.76)},{sy(0.32)} {sx(0.73)},{sy(0.30)} {sx(0.67)},{sy(0.28)}" fill="#ead8ab"/>')
        svg.append(f'<line x1="{sx(0.05)}" y1="{sy(0.28)}" x2="{sx(0.95)}" y2="{sy(0.28)}" stroke="#403d39" stroke-width="1.4"/>')
        svg.append(f'<polygon points="{sx(0.11)},{sy(0.39)} {sx(0.28)},{sy(0.39)} {sx(0.245)},{sy(0.28)} {sx(0.165)},{sy(0.28)}" fill="#97633e" stroke="#4b3a30" stroke-width="2"/>')
        svg.append(f'<line x1="{sx(0.16)}" y1="{sy(0.39)}" x2="{sx(0.16)}" y2="{sy(0.59)}" stroke="#4b3a30" stroke-width="2.2"/>')
        svg.append(f'<line x1="{sx(0.16)}" y1="{sy(0.59)}" x2="{sx(0.20)}" y2="{sy(0.58)}" stroke="#4b3a30" stroke-width="1.8"/>')
        svg.append(f'<path d="M {sx(0.16)} {sy(0.59)} Q {sx(0.10)} {sy(0.45)} {sx(0.09)} {sy(0.26)}" fill="none" stroke="#4b3a30" stroke-width="1.8"/>')
        svg.append(f'<line x1="{sx(0.11)}" y1="{sy(0.39)}" x2="{sx(0.30)}" y2="{sy(0.39)}" stroke="#4b3a30" stroke-width="1.8"/>')

        for person in people:
            if 0.31 < person["scene_x"] < 0.74:
                svg.append(f'<rect x="{sx(person["scene_x"] - 0.035)}" y="{sy(person["foot_y"] - 0.002)}" width="{sx(0.07) - sx(0)}" height="7" fill="#9a7a54" stroke="#4b3a30" stroke-width="1"/>')
            draw_person(svg, person["scene_x"], person["foot_y"], person["color"])
            svg.append(f'<line x1="{sx(person["scene_x"])}" y1="{sy(person["head_y"] + 0.02)}" x2="{sx(person["label_x"])}" y2="{sy(person["label_y"] - 0.02)}" stroke="#8d877d" stroke-width="1" stroke-dasharray="4,4"/>')
            svg.append(f'<text x="{sx(person["label_x"])}" y="{sy(person["label_y"])}" font-size="14" font-weight="700" text-anchor="{person["label_anchor"]}" fill="{person["color"]}">{escape(person["member"])}</text>')
            svg.append(f'<text x="{sx(person["label_x"])}" y="{sy(person["label_y"]) + 18}" font-size="12" text-anchor="{person["label_anchor"]}" fill="{person["color"]}">{person["bias_gap"]:+.2f}</text>')

        svg.append(f'<line x1="{sx(0.29)}" y1="{sy(0.64)}" x2="{sx(0.82)}" y2="{sy(0.64)}" stroke="#403d39" stroke-width="2"/>')
        svg.append(f'<polygon points="{sx(0.29)},{sy(0.64)} {sx(0.305)},{sy(0.648)} {sx(0.305)},{sy(0.632)}" fill="#403d39"/>')
        svg.append(f'<polygon points="{sx(0.82)},{sy(0.64)} {sx(0.805)},{sy(0.648)} {sx(0.805)},{sy(0.632)}" fill="#403d39"/>')
        svg.append(f'<text x="{sx(0.555)}" y="{sy(0.68)}" font-size="15" font-weight="700" text-anchor="middle" fill="#403d39">Bias gap = Tourism sentiment minus Fishing sentiment</text>')
        svg.append(f'<text x="{sx(0.17)}" y="{sy(0.58)}" font-size="13" fill="{CATEGORY_COLORS["Fishing"]}">warmer to fishing</text>')
        svg.append(f'<text x="{sx(0.79)}" y="{sy(0.58)}" font-size="13" fill="{CATEGORY_COLORS["Tourism"]}">warmer to tourism</text>')
        svg.append(f'<text x="{sx(0.055)}" y="{sy(0.94)}" font-size="30" font-weight="700" fill="#202020">From Boat to Beach: Where Members Lean</text>')
        svg.append(f'<text x="{sx(0.055)}" y="{sy(0.89)}" font-size="17" fill="#202020">Source: {escape(c2_selected_source)} | Filter: {escape(c2_member_label)}</text>')
        svg.append(f'<rect x="{sx(0.11)}" y="{sy(0.145)}" width="110" height="30" rx="8" ry="8" fill="{CATEGORY_COLORS["Fishing"]}"/>')
        svg.append(f'<text x="{sx(0.165)}" y="{sy(0.125)}" font-size="13" font-weight="700" text-anchor="middle" fill="white">Fishing boat</text>')
        svg.append(f'<rect x="{sx(0.82)}" y="{sy(0.145)}" width="120" height="30" rx="8" ry="8" fill="{CATEGORY_COLORS["Tourism"]}"/>')
        svg.append(f'<text x="{sx(0.88)}" y="{sy(0.125)}" font-size="13" font-weight="700" text-anchor="middle" fill="white">Tourist shore</text>')
        svg.append(f'<text x="{sx(0.055)}" y="{sy(0.02)}" font-size="11" fill="#2c2c2c">Placement uses tourism minus fishing allocated hours from the filtered trip data. Hybrid time contributes half to each side.</text>')
        if not people:
            svg.append(f'<text x="{scene_width / 2:.1f}" y="{scene_height / 2:.1f}" text-anchor="middle" font-size="22" fill="#6b7280">No member data after current filters</text>')
        svg.append("</svg>")
        return "".join(svg)
    return


@app.cell
def _(
    CATEGORY_COLORS,
    CATEGORY_ORDER,
    CATEGORY_STROKES,
    ZONE_COLORS,
    c2_filtered_visits,
    c2_member_label,
    c2_selected_source,
    escape,
    math,
    source_data,
):
    def render_visit_map():
        map_width = 980
        map_height = 620
        margin = 70

        all_places = source_data[c2_selected_source]["places"]
        x_min = min(place["x"] for place in all_places)
        x_max = max(place["x"] for place in all_places)
        y_min = min(place["y"] for place in all_places)
        y_max = max(place["y"] for place in all_places)

        def to_screen(x_value, y_value):
            if x_max == x_min:
                screen_x = map_width / 2
            else:
                screen_x = margin + ((x_value - x_min) / (x_max - x_min)) * (map_width - 2 * margin)

            if y_max == y_min:
                screen_y = map_height / 2
            else:
                screen_y = map_height - margin - ((y_value - y_min) / (y_max - y_min)) * (map_height - 2 * margin)

            return screen_x, screen_y

        grouped_places = {}
        for visit in c2_filtered_visits:
            place_id = str(visit["place_id"])
            if place_id not in grouped_places:
                grouped_places[place_id] = {
                    "name": visit["name"],
                    "x": visit["x"],
                    "y": visit["y"],
                    "zone": visit["zone"],
                    "zone_remapped": visit["zone_remapped"],
                    "category": visit["category"],
                    "visits": 0,
                    "hours": 0.0,
                    "members": set(),
                    "trips": set(),
                }
            grouped_places[place_id]["visits"] += 1
            grouped_places[place_id]["hours"] += float(visit["duration_hours"])
            grouped_places[place_id]["members"].add(visit["member"])
            grouped_places[place_id]["trips"].add(visit["trip_id"])

        short_label = c2_member_label if len(c2_member_label) <= 80 else c2_member_label[:77] + "..."
        svg = []
        svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{map_width}" height="{map_height}" viewBox="0 0 {map_width} {map_height}">')
        svg.append(f'<rect x="0" y="0" width="{map_width}" height="{map_height}" fill="#faf7f2" rx="18" ry="18"/>')
        svg.append('<text x="36" y="42" font-size="28" font-weight="700" fill="#203040">Board visit map</text>')
        svg.append(f'<text x="36" y="68" font-size="14" fill="#5f6b76">Source: {escape(c2_selected_source)} | Filter: {escape(short_label)}</text>')
        svg.append('<text x="36" y="90" font-size="13" fill="#6d6d6d">Faint dots show raw place zones. Larger colored circles use the remapped fishing/tourism categories.</text>')

        for place in all_places:
            sx, sy = to_screen(place["x"], place["y"])
            zone_fill = ZONE_COLORS.get(place["zone"], ZONE_COLORS["unknown"])
            place_title = escape(
                f'{place["name"]}\n'
                f'Raw zone: {place["zone"]}\n'
                f'Remapped zone: {place["zone_remapped"]}\n'
                f'Category: {place["category"]}\n'
                f'Method: {place["remap_method"]}'
            )
            svg.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="3.5" fill="{zone_fill}" opacity="0.25"><title>{place_title}</title></circle>')

        for category_name in CATEGORY_ORDER:
            category_places = [place for place in grouped_places.values() if place["category"] == category_name]
            for place in sorted(category_places, key=lambda item: item["visits"]):
                sx, sy = to_screen(place["x"], place["y"])
                radius = 6 + math.sqrt(place["visits"]) * 3.0
                fill_color = CATEGORY_COLORS[category_name]
                stroke_color = CATEGORY_STROKES[category_name]
                opacity = "0.88" if category_name != "Neutral" else "0.48"
                members_text = ", ".join(sorted(place["members"]))
                hover_title = escape(
                    f'{place["name"]}\n'
                    f'Category: {category_name}\n'
                    f'Member-visits: {place["visits"]}\n'
                    f'Trips touching this place: {len(place["trips"])}\n'
                    f'Allocated hours: {place["hours"]:.2f}\n'
                    f'Raw zone: {place["zone"]}\n'
                    f'Remapped zone: {place.get("zone_remapped", place["zone"])}\n'
                    f'Members: {members_text}'
                )
                svg.append(
                    f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{radius:.1f}" fill="{fill_color}" fill-opacity="{opacity}" stroke="{stroke_color}" stroke-width="2"><title>{hover_title}</title></circle>'
                )
                if place["visits"] >= 4:
                    label = place["name"] if len(place["name"]) <= 18 else place["name"][:15] + "..."
                    svg.append(f'<text x="{sx:.1f}" y="{sy - radius - 8:.1f}" font-size="11" text-anchor="middle" fill="#334155">{escape(label)}</text>')

        legend_x = map_width - 190
        legend_y = 120
        svg.append(f'<rect x="{legend_x - 18}" y="{legend_y - 28}" width="170" height="150" rx="12" ry="12" fill="white" opacity="0.92" stroke="#d7d2c8"/>')
        svg.append(f'<text x="{legend_x}" y="{legend_y - 6}" font-size="14" font-weight="700" fill="#334155">Legend</text>')
        for index, category_name in enumerate(CATEGORY_ORDER):
            legend_row_y = legend_y + 24 + index * 24
            svg.append(f'<circle cx="{legend_x}" cy="{legend_row_y}" r="7" fill="{CATEGORY_COLORS[category_name]}" stroke="{CATEGORY_STROKES[category_name]}" stroke-width="1.5"/>')
            svg.append(f'<text x="{legend_x + 16}" y="{legend_row_y + 4}" font-size="12" fill="#475569">{category_name}</text>')
        svg.append(f'<text x="{legend_x}" y="{legend_y + 126}" font-size="11" fill="#6b7280">circle size = repeated visits</text>')

        if not c2_filtered_visits:
            svg.append(f'<text x="{map_width / 2:.1f}" y="{map_height / 2:.1f}" text-anchor="middle" font-size="20" fill="#6b7280">No visit records after current filters</text>')

        svg.append("</svg>")
        return "".join(svg)
    return


@app.cell
def _(
    CATEGORY_COLORS,
    CATEGORY_ORDER,
    CATEGORY_STROKES,
    c2_filtered_visits,
    c2_include_neutral,
    c2_member_label,
    c2_selected_source,
    defaultdict,
    dominant_time_category,
    escape,
    math,
    summarize_category_hours,
):
    def render_trip_summary():
        width = 980
        height = 620
        trip_center_x = 690
        trip_center_y = 330
        trip_outer_radius = 170
        trip_inner_radius = 70

        total_hours = summarize_category_hours(c2_filtered_visits)
        summary_labels = [
            category_name
            for category_name in CATEGORY_ORDER
            if total_hours.get(category_name, 0.0) > 0 and (c2_include_neutral or category_name != "Neutral")
        ]
        if not summary_labels:
            summary_labels = ["Neutral"]

        summary_values = [total_hours.get(category_name, 0.0) for category_name in summary_labels]
        if sum(summary_values) <= 0:
            summary_values = [1.0 for _ in summary_labels]

        trip_rollup = {}
        for visit in c2_filtered_visits:
            key = (str(visit["member"]), str(visit["trip_id"]))
            if key not in trip_rollup:
                trip_rollup[key] = {
                    "member": visit["member"],
                    "trip_id": visit["trip_id"],
                    "date": visit["date"],
                    "start_dt": visit["start_dt"],
                    "hours": 0.0,
                    "category_hours": defaultdict(float),
                    "places": set(),
                }
            trip_rollup[key]["hours"] += float(visit["duration_hours"])
            trip_rollup[key]["category_hours"][str(visit["category"])] += float(visit["duration_hours"])
            trip_rollup[key]["places"].add(str(visit["name"]))

        trip_records = []
        for record in trip_rollup.values():
            trip_records.append(
                {
                    "member": str(record["member"]),
                    "trip_id": str(record["trip_id"]),
                    "date": str(record["date"]),
                    "start_dt": record["start_dt"],
                    "hours": float(record["hours"]),
                    "category": dominant_time_category(dict(record["category_hours"])),
                    "places": ", ".join(sorted(record["places"])),
                }
            )
        trip_records.sort(key=lambda record: (record["start_dt"], record["member"], record["trip_id"]))

        def polar_point(cx, cy, radius, angle_deg):
            angle_rad = math.radians(angle_deg - 90)
            return cx + radius * math.cos(angle_rad), cy + radius * math.sin(angle_rad)

        def arc_wedge_path(cx, cy, r_outer, r_inner, start_angle, end_angle):
            x1, y1 = polar_point(cx, cy, r_outer, start_angle)
            x2, y2 = polar_point(cx, cy, r_outer, end_angle)
            x3, y3 = polar_point(cx, cy, r_inner, end_angle)
            x4, y4 = polar_point(cx, cy, r_inner, start_angle)
            large_arc = 1 if (end_angle - start_angle) > 180 else 0
            return (
                f"M {x1:.2f} {y1:.2f} "
                f"A {r_outer:.2f} {r_outer:.2f} 0 {large_arc} 1 {x2:.2f} {y2:.2f} "
                f"L {x3:.2f} {y3:.2f} "
                f"A {r_inner:.2f} {r_inner:.2f} 0 {large_arc} 0 {x4:.2f} {y4:.2f} Z"
            )

        svg = []
        svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
        svg.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fbfaf7" rx="20" ry="20"/>')
        svg.append('<text x="36" y="42" font-size="28" font-weight="700" fill="#203040">Trip-time summary</text>')
        svg.append(f'<text x="36" y="68" font-size="14" fill="#5f6b76">Source: {escape(c2_selected_source)} | Filter: {escape(c2_member_label)}</text>')
        svg.append('<text x="36" y="90" font-size="13" fill="#6d6d6d">Left: overall time split. Right: each member-trip shown as a clockwise wedge.</text>')

        pie_center_x = 220
        pie_center_y = 330
        pie_outer = 120
        pie_inner = 58
        total_sum = sum(summary_values)
        current_angle = 0.0
        for label, value in zip(summary_labels, summary_values):
            width_angle = 360.0 * value / total_sum
            path = arc_wedge_path(pie_center_x, pie_center_y, pie_outer, pie_inner, current_angle, current_angle + width_angle)
            svg.append(f'<path d="{path}" fill="{CATEGORY_COLORS[label]}" stroke="white" stroke-width="2"/>')
            mid_angle = current_angle + width_angle / 2.0
            label_x, label_y = polar_point(pie_center_x, pie_center_y, 145, mid_angle)
            pct = 100.0 * value / total_sum
            svg.append(f'<text x="{label_x:.1f}" y="{label_y:.1f}" font-size="12" text-anchor="middle" fill="#334155">{label}</text>')
            svg.append(f'<text x="{label_x:.1f}" y="{label_y + 15:.1f}" font-size="11" text-anchor="middle" fill="#64748b">{pct:.0f}%</text>')
            current_angle += width_angle
        svg.append(f'<text x="{pie_center_x}" y="{pie_center_y - 6}" font-size="16" font-weight="700" text-anchor="middle" fill="#334155">total</text>')
        svg.append(f'<text x="{pie_center_x}" y="{pie_center_y + 16}" font-size="13" text-anchor="middle" fill="#64748b">allocated hours</text>')

        trip_total_hours = sum(record["hours"] for record in trip_records) or 1.0
        ring_angle = 0.0
        for record in trip_records:
            width_angle = max(record["hours"] / trip_total_hours * 360.0, 2.0)
            path = arc_wedge_path(trip_center_x, trip_center_y, trip_outer_radius, trip_inner_radius, ring_angle, ring_angle + width_angle)
            fill_color = CATEGORY_COLORS.get(record["category"], CATEGORY_COLORS["Neutral"])
            hover_title = escape(
                f'{record["trip_id"]}\n'
                f'Member: {record["member"]}\n'
                f'Date: {record["date"]}\n'
                f'Hours: {record["hours"]:.2f}\n'
                f'Category: {record["category"]}\n'
                f'Places: {record["places"]}'
            )
            svg.append(f'<path d="{path}" fill="{fill_color}" fill-opacity="0.88" stroke="white" stroke-width="2"><title>{hover_title}</title></path>')
            if width_angle >= 12:
                mid_angle = ring_angle + width_angle / 2.0
                text_x, text_y = polar_point(
                    trip_center_x,
                    trip_center_y,
                    (trip_outer_radius + trip_inner_radius) / 2.0,
                    mid_angle,
                )
                svg.append(f'<text x="{text_x:.1f}" y="{text_y:.1f}" font-size="10" text-anchor="middle" fill="white">{escape(record["trip_id"])}</text>')
            ring_angle += width_angle

        svg.append(f'<circle cx="{trip_center_x}" cy="{trip_center_y}" r="{trip_inner_radius - 8}" fill="#fbfaf7" stroke="#e5ded1" stroke-width="1.5"/>')
        svg.append(f'<text x="{trip_center_x}" y="{trip_center_y - 5}" font-size="16" font-weight="700" text-anchor="middle" fill="#334155">member-</text>')
        svg.append(f'<text x="{trip_center_x}" y="{trip_center_y + 15}" font-size="16" font-weight="700" text-anchor="middle" fill="#334155">trips</text>')

        legend_x = 835
        legend_y = 150
        svg.append(f'<rect x="{legend_x - 20}" y="{legend_y - 30}" width="145" height="140" rx="12" ry="12" fill="white" opacity="0.92" stroke="#d7d2c8"/>')
        svg.append(f'<text x="{legend_x}" y="{legend_y - 8}" font-size="14" font-weight="700" fill="#334155">Legend</text>')
        for index, category_name in enumerate(CATEGORY_ORDER):
            legend_row_y = legend_y + 20 + index * 24
            svg.append(f'<circle cx="{legend_x}" cy="{legend_row_y}" r="7" fill="{CATEGORY_COLORS[category_name]}" stroke="{CATEGORY_STROKES[category_name]}" stroke-width="1.5"/>')
            svg.append(f'<text x="{legend_x + 16}" y="{legend_row_y + 4}" font-size="12" fill="#475569">{category_name}</text>')
        svg.append('<text x="36" y="586" font-size="11" fill="#6b7280">Each wedge on the right is one member-trip ordered clockwise by trip start time.</text>')

        if not trip_records:
            svg.append(f'<text x="{width / 2:.1f}" y="{height / 2:.1f}" text-anchor="middle" font-size="22" fill="#6b7280">No trip data after current filters</text>')

        svg.append("</svg>")
        return "".join(svg)
    return


@app.cell
def _(
    CATEGORY_COLORS,
    CATEGORY_ORDER,
    CATEGORY_STROKES,
    Path,
    c2_filtered_visits,
    c2_include_neutral,
    c2_member_label,
    c2_selected_source,
    defaultdict,
    dominant_time_category,
    escape,
    json,
    math,
    mo,
    source_data,
    summarize_category_hours,
):
    def render_cluster2_merged():
        width = 1180
        height = 820
        paper = "#eef4f8"
        ink = "#2f2f2f"
        soft_ink = "#53606b"
        sea = "url(#c2-sea-grad)"
        sand = "url(#c2-sand-grad)"

        def clip(value, low, high):
            return max(low, min(high, value))

        def blend_hex(color_a, color_b, t):
            t = clip(t, 0.0, 1.0)
            a = color_a.lstrip("#")
            b = color_b.lstrip("#")
            ar, ag, ab = int(a[0:2], 16), int(a[2:4], 16), int(a[4:6], 16)
            br, bg, bb = int(b[0:2], 16), int(b[2:4], 16), int(b[4:6], 16)
            return f"#{round(ar + (br - ar) * t):02x}{round(ag + (bg - ag) * t):02x}{round(ab + (bb - ab) * t):02x}"

        def short_label(text, max_len=16):
            text = str(text or "")
            return text if len(text) <= max_len else text[: max_len - 3] + "..."

        def slug(text):
            cleaned = []
            for char in str(text or "").lower():
                if char.isalnum():
                    cleaned.append(char)
                else:
                    cleaned.append("-")
            return "-".join(part for part in "".join(cleaned).split("-") if part)

        def draw_panel(svg, x, y, w, h, label, title):
            svg.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" ry="6" '
                f'fill="#ffffff" stroke="#c8d4df" stroke-width="1.3"/>'
            )
            svg.append(
                f'<text x="{x + 14}" y="{y + 24}" font-size="13" font-weight="700" fill="{soft_ink}">{label}</text>'
            )
            svg.append(
                f'<text x="{x + 54}" y="{y + 24}" font-size="15" font-weight="700" fill="{ink}">{title}</text>'
            )

        def draw_person(svg, x, y, color, scale=1.0):
            skin = "#d69a72"
            pants = "#2f4154"
            shoes = "#2a2a2a"
            shirt = color
            svg.append(
                f'<ellipse cx="{x:.1f}" cy="{y + 5 * scale:.1f}" rx="{16 * scale:.1f}" ry="{4 * scale:.1f}" fill="#1f2933" opacity="0.18"/>'
            )
            svg.append(
                f'<circle cx="{x:.1f}" cy="{y - 42 * scale:.1f}" r="{7 * scale:.1f}" fill="{skin}" stroke="#7a5845" stroke-width="{0.8 * scale:.1f}"/>'
            )
            svg.append(
                f'<path d="M {x - 4 * scale:.1f} {y - 48 * scale:.1f} C {x - 2 * scale:.1f} {y - 55 * scale:.1f}, '
                f'{x + 8 * scale:.1f} {y - 54 * scale:.1f}, {x + 9 * scale:.1f} {y - 45 * scale:.1f}" '
                f'fill="#3f2f29" opacity="0.86"/>'
            )
            svg.append(
                f'<rect x="{x - 3 * scale:.1f}" y="{y - 36 * scale:.1f}" width="{6 * scale:.1f}" height="{5 * scale:.1f}" fill="{skin}"/>'
            )
            svg.append(
                f'<path d="M {x - 13 * scale:.1f} {y - 31 * scale:.1f} Q {x:.1f} {y - 40 * scale:.1f} '
                f'{x + 13 * scale:.1f} {y - 31 * scale:.1f} L {x + 10 * scale:.1f} {y - 10 * scale:.1f} '
                f'L {x - 10 * scale:.1f} {y - 10 * scale:.1f} Z" fill="{shirt}" stroke="#26313a" stroke-width="{0.8 * scale:.1f}"/>'
            )
            svg.append(
                f'<line x1="{x - 12 * scale:.1f}" y1="{y - 28 * scale:.1f}" x2="{x - 22 * scale:.1f}" y2="{y - 17 * scale:.1f}" '
                f'stroke="{skin}" stroke-width="{4 * scale:.1f}" stroke-linecap="round"/>'
            )
            svg.append(
                f'<line x1="{x + 12 * scale:.1f}" y1="{y - 28 * scale:.1f}" x2="{x + 21 * scale:.1f}" y2="{y - 18 * scale:.1f}" '
                f'stroke="{skin}" stroke-width="{4 * scale:.1f}" stroke-linecap="round"/>'
            )
            svg.append(
                f'<path d="M {x - 8 * scale:.1f} {y - 10 * scale:.1f} L {x - 13 * scale:.1f} {y + 2 * scale:.1f} '
                f'L {x - 5 * scale:.1f} {y + 2 * scale:.1f} L {x:.1f} {y - 10 * scale:.1f} Z" fill="{pants}"/>'
            )
            svg.append(
                f'<path d="M {x + 8 * scale:.1f} {y - 10 * scale:.1f} L {x + 13 * scale:.1f} {y + 2 * scale:.1f} '
                f'L {x + 5 * scale:.1f} {y + 2 * scale:.1f} L {x:.1f} {y - 10 * scale:.1f} Z" fill="{pants}"/>'
            )
            svg.append(
                f'<ellipse cx="{x - 10 * scale:.1f}" cy="{y + 4 * scale:.1f}" rx="{6 * scale:.1f}" ry="{2.2 * scale:.1f}" fill="{shoes}"/>'
            )
            svg.append(
                f'<ellipse cx="{x + 10 * scale:.1f}" cy="{y + 4 * scale:.1f}" rx="{6 * scale:.1f}" ry="{2.2 * scale:.1f}" fill="{shoes}"/>'
            )

        def draw_boat_person(svg, x, y, color, scale=1.0):
            skin = "#d69a72"
            pants = "#27394c"
            svg.append(
                f'<circle cx="{x:.1f}" cy="{y - 31 * scale:.1f}" r="{6.2 * scale:.1f}" fill="{skin}" '
                f'stroke="#7a5845" stroke-width="{0.8 * scale:.1f}"/>'
            )
            svg.append(
                f'<path d="M {x - 5 * scale:.1f} {y - 36 * scale:.1f} C {x - 2 * scale:.1f} {y - 42 * scale:.1f}, '
                f'{x + 7 * scale:.1f} {y - 40 * scale:.1f}, {x + 7 * scale:.1f} {y - 31 * scale:.1f}" '
                'fill="#3f2f29" opacity="0.88"/>'
            )
            svg.append(
                f'<rect x="{x - 2.5 * scale:.1f}" y="{y - 25 * scale:.1f}" width="{5 * scale:.1f}" height="{4 * scale:.1f}" fill="{skin}"/>'
            )
            svg.append(
                f'<path d="M {x - 9 * scale:.1f} {y - 21 * scale:.1f} Q {x:.1f} {y - 28 * scale:.1f} '
                f'{x + 9 * scale:.1f} {y - 21 * scale:.1f} L {x + 7 * scale:.1f} {y - 5 * scale:.1f} '
                f'L {x - 7 * scale:.1f} {y - 5 * scale:.1f} Z" fill="{color}" stroke="#26313a" stroke-width="{0.7 * scale:.1f}"/>'
            )
            svg.append(
                f'<line x1="{x - 8 * scale:.1f}" y1="{y - 18 * scale:.1f}" x2="{x - 16 * scale:.1f}" y2="{y - 8 * scale:.1f}" '
                f'stroke="{skin}" stroke-width="{3 * scale:.1f}" stroke-linecap="round"/>'
            )
            svg.append(
                f'<line x1="{x + 8 * scale:.1f}" y1="{y - 18 * scale:.1f}" x2="{x + 16 * scale:.1f}" y2="{y - 8 * scale:.1f}" '
                f'stroke="{skin}" stroke-width="{3 * scale:.1f}" stroke-linecap="round"/>'
            )
            svg.append(
                f'<path d="M {x - 7 * scale:.1f} {y - 5 * scale:.1f} L {x - 13 * scale:.1f} {y + 2 * scale:.1f} '
                f'L {x + 13 * scale:.1f} {y + 2 * scale:.1f} L {x + 7 * scale:.1f} {y - 5 * scale:.1f} Z" fill="{pants}"/>'
            )

        def draw_small_fishing_boat(svg, center_x, waterline_y, occupant_count, scale=1.0):
            boat_w = (78 + max(0, occupant_count - 1) * 27) * scale
            left = center_x - boat_w / 2
            right = center_x + boat_w / 2
            svg.append(
                f'<path d="M {left:.1f} {waterline_y:.1f} L {right:.1f} {waterline_y:.1f} '
                f'C {right - 11 * scale:.1f} {waterline_y + 20 * scale:.1f}, '
                f'{left + 15 * scale:.1f} {waterline_y + 22 * scale:.1f}, {left:.1f} {waterline_y:.1f} Z" '
                'fill="#174864" stroke="#0f2c3f" stroke-width="1.2"/>'
            )
            svg.append(
                f'<path d="M {left + 8 * scale:.1f} {waterline_y + 4 * scale:.1f} '
                f'L {right - 8 * scale:.1f} {waterline_y + 4 * scale:.1f}" '
                'fill="none" stroke="#f6f1df" stroke-width="3" stroke-linecap="round"/>'
            )
            svg.append(
                f'<path d="M {left + 15 * scale:.1f} {waterline_y + 11 * scale:.1f} '
                f'L {right - 15 * scale:.1f} {waterline_y + 11 * scale:.1f}" '
                'fill="none" stroke="#c79a58" stroke-width="2.4" stroke-linecap="round"/>'
            )
            svg.append(
                f'<line x1="{center_x - 6 * scale:.1f}" y1="{waterline_y + 8 * scale:.1f}" '
                f'x2="{center_x + 55 * scale:.1f}" y2="{waterline_y - 15 * scale:.1f}" '
                'stroke="#7a5335" stroke-width="2.3" stroke-linecap="round"/>'
            )
            svg.append(
                f'<circle cx="{right - 18 * scale:.1f}" cy="{waterline_y + 4 * scale:.1f}" r="{4.2 * scale:.1f}" '
                'fill="#ef4444" stroke="#8f1d1d" stroke-width="0.9"/>'
            )
            svg.append(
                f'<path d="M {left - 10 * scale:.1f} {waterline_y + 16 * scale:.1f} '
                f'C {center_x - 20 * scale:.1f} {waterline_y + 24 * scale:.1f}, '
                f'{center_x + 25 * scale:.1f} {waterline_y + 23 * scale:.1f}, '
                f'{right + 12 * scale:.1f} {waterline_y + 16 * scale:.1f}" '
                'fill="none" stroke="#d9f2ff" stroke-width="3" opacity="0.9" stroke-linecap="round"/>'
            )
            return boat_w

        def polar_point(cx, cy, radius, angle_deg):
            angle_rad = math.radians(angle_deg - 90)
            return cx + radius * math.cos(angle_rad), cy + radius * math.sin(angle_rad)

        def arc_wedge_path(cx, cy, r_outer, r_inner, start_angle, end_angle):
            x1, y1 = polar_point(cx, cy, r_outer, start_angle)
            x2, y2 = polar_point(cx, cy, r_outer, end_angle)
            x3, y3 = polar_point(cx, cy, r_inner, end_angle)
            x4, y4 = polar_point(cx, cy, r_inner, start_angle)
            large_arc = 1 if (end_angle - start_angle) > 180 else 0
            return (
                f"M {x1:.2f} {y1:.2f} "
                f"A {r_outer:.2f} {r_outer:.2f} 0 {large_arc} 1 {x2:.2f} {y2:.2f} "
                f"L {x3:.2f} {y3:.2f} "
                f"A {r_inner:.2f} {r_inner:.2f} 0 {large_arc} 0 {x4:.2f} {y4:.2f} Z"
            )

        member_summary = {}
        for visit in c2_filtered_visits:
            member_name = str(visit["member"])
            if member_name not in member_summary:
                member_summary[member_name] = {
                    "member": member_name,
                    "Fishing": 0.0,
                    "Tourism": 0.0,
                    "Hybrid": 0.0,
                    "Neutral": 0.0,
                }
            member_summary[member_name][str(visit["category"])] += float(
                visit["duration_hours"]
            )

        people = []
        for summary in member_summary.values():
            fishing_value = summary["Fishing"] + 0.5 * summary["Hybrid"]
            tourism_value = summary["Tourism"] + 0.5 * summary["Hybrid"]
            bias_gap = tourism_value - fishing_value
            total_focus = fishing_value + tourism_value
            people.append(
                {
                    "member": summary["member"],
                    "bias_gap": bias_gap,
                    "total_focus": total_focus,
                }
            )
        people.sort(key=lambda item: item["bias_gap"])

        bias_min = min([person["bias_gap"] for person in people] + [-1.0])
        bias_max = max([person["bias_gap"] for person in people] + [1.0])
        max_abs_bias = max([abs(person["bias_gap"]) for person in people] + [1.0])

        grouped_places = {}
        for visit in c2_filtered_visits:
            place_id = str(visit["place_id"])
            if place_id not in grouped_places:
                grouped_places[place_id] = {
                    "name": visit["name"],
                    "x": visit["x"],
                    "y": visit["y"],
                    "zone": visit["zone"],
                    "zone_remapped": visit["zone_remapped"],
                    "category": visit["category"],
                    "visits": 0,
                    "hours": 0.0,
                    "members": set(),
                    "trips": set(),
                }
            grouped_places[place_id]["visits"] += 1
            grouped_places[place_id]["hours"] += float(visit["duration_hours"])
            grouped_places[place_id]["members"].add(str(visit["member"]))
            grouped_places[place_id]["trips"].add(str(visit["trip_id"]))

        trip_rollup = {}
        for visit in c2_filtered_visits:
            trip_key = (str(visit["member"]), str(visit["trip_id"]))
            if trip_key not in trip_rollup:
                trip_rollup[trip_key] = {
                    "member": str(visit["member"]),
                    "trip_id": str(visit["trip_id"]),
                    "date": str(visit["date"]),
                    "start_dt": visit["start_dt"],
                    "hours": 0.0,
                    "category_hours": defaultdict(float),
                    "places": set(),
                }
            trip_rollup[trip_key]["hours"] += float(visit["duration_hours"])
            trip_rollup[trip_key]["category_hours"][str(visit["category"])] += float(
                visit["duration_hours"]
            )
            if visit["name"]:
                trip_rollup[trip_key]["places"].add(str(visit["name"]))

        trip_records = []
        for record in trip_rollup.values():
            trip_records.append(
                {
                    "member": record["member"],
                    "trip_id": record["trip_id"],
                    "date": record["date"],
                    "start_dt": record["start_dt"],
                    "hours": float(record["hours"]),
                    "category": dominant_time_category(dict(record["category_hours"])),
                    "places": ", ".join(sorted(record["places"])),
                }
            )
        trip_records.sort(key=lambda item: (item["start_dt"], item["member"], item["trip_id"]))

        total_hours = summarize_category_hours(c2_filtered_visits)
        summary_labels = [
            category_name
            for category_name in CATEGORY_ORDER
            if total_hours.get(category_name, 0.0) > 0
            and (c2_include_neutral or category_name != "Neutral")
        ]
        if not summary_labels:
            summary_labels = ["Neutral"]
        summary_values = [total_hours.get(category_name, 0.0) for category_name in summary_labels]
        if sum(summary_values) <= 0:
            summary_values = [1.0 for _ in summary_labels]

        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            """
            <defs>
              <linearGradient id="c2-sky-grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#dceffd"/>
                <stop offset="100%" stop-color="#f8fbff"/>
              </linearGradient>
              <linearGradient id="c2-sea-grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#5fa7d8"/>
                <stop offset="100%" stop-color="#2e78aa"/>
              </linearGradient>
              <linearGradient id="c2-sand-grad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#d6bd8f"/>
                <stop offset="100%" stop-color="#b89361"/>
              </linearGradient>
              <linearGradient id="c2-hull-grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#e8f0f7"/>
                <stop offset="52%" stop-color="#f8fbff"/>
                <stop offset="53%" stop-color="#24465f"/>
                <stop offset="100%" stop-color="#132f43"/>
              </linearGradient>
              <linearGradient id="c2-cabin-grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#ffffff"/>
                <stop offset="100%" stop-color="#dbe7ef"/>
              </linearGradient>
              <filter id="c2-soft-shadow" x="-20%" y="-20%" width="140%" height="150%">
                <feDropShadow dx="0" dy="3" stdDeviation="3" flood-color="#1f2933" flood-opacity="0.24"/>
              </filter>
            </defs>
            """,
            """
            <style>
              .c2-mark { cursor: pointer; transition: opacity 140ms ease, stroke-width 140ms ease, filter 140ms ease; }
              .c2-control { cursor: pointer; }
              .c2-control:hover { text-decoration: underline; }
              .c2-mark:hover { stroke-width: 3 !important; filter: drop-shadow(0 0 4px rgba(47,47,47,0.35)); }
              .c2-muted { opacity: 0.16 !important; }
              .c2-active { stroke-width: 3 !important; filter: drop-shadow(0 0 4px rgba(47,47,47,0.35)); }
              .c2-note { opacity: 0; transition: opacity 120ms ease; }
              .c2-note-active { opacity: 1; }
            </style>
            <script><![CDATA[
              (function () {
                const svg = document.currentScript.parentNode;
                let activeType = null;
                let activeValue = null;

                function setActive(type, value) {
                  activeType = type;
                  activeValue = value;
                  const marks = svg.querySelectorAll(".c2-mark");
                  marks.forEach((mark) => {
                    const sameMember = type === "member" && (mark.dataset.member || "").split(" ").includes(value);
                    const sameCategory = type === "category" && mark.dataset.category === value;
                    const active = sameMember || sameCategory;
                    mark.classList.toggle("c2-active", active);
                    mark.classList.toggle("c2-muted", type !== null && !active);
                  });
                  const notes = svg.querySelectorAll(".c2-note");
                  notes.forEach((note) => note.classList.toggle("c2-note-active", type !== null));
                  const status = svg.querySelector("#c2-status");
                  if (status) {
                    status.textContent = type ? "filtered: " + value.replaceAll("-", " ") : "click a person or legend item to highlight";
                  }
                }

                svg.addEventListener("click", (event) => {
                  const target = event.target.closest("[data-filter-type]");
                  if (!target) {
                    setActive(null, null);
                    return;
                  }
                  const type = target.dataset.filterType;
                  const value = target.dataset.filterValue;
                  if (activeType === type && activeValue === value) {
                    setActive(null, null);
                  } else {
                    setActive(type, value);
                  }
                  event.stopPropagation();
                });
              })();
            ]]></script>
            """,
            f'<rect x="0" y="0" width="{width}" height="{height}" fill="{paper}"/>',
            '<path d="M 26 26 L 1155 20 L 1148 795 L 31 790 Z" fill="none" stroke="#c3d1dc" stroke-width="1.2"/>',
            '<text x="50" y="34" font-size="18" font-weight="700" fill="#293241">Cluster 2 interactive scene</text>',
            f'<text x="246" y="34" font-size="12" fill="#606060">Source: {escape(c2_selected_source)} | Filter: {escape(c2_member_label)}</text>',
        ]
        hover_rules = []
        for person in people:
            member_slug = slug(person["member"])
            hover_rules.append(
                f'svg:has([data-filter-value="{member_slug}"]:hover) .c2-mark:not([data-member~="{member_slug}"]) {{ opacity: 0.16 !important; }}'
            )
            hover_rules.append(
                f'svg:has([data-filter-value="{member_slug}"]:hover) .c2-mark[data-member~="{member_slug}"] {{ stroke-width: 3 !important; filter: drop-shadow(0 0 4px rgba(47,47,47,0.35)); }}'
            )
        for category_name in CATEGORY_ORDER:
            category_slug = slug(category_name)
            hover_rules.append(
                f'svg:has([data-filter-value="{category_slug}"]:hover) .c2-mark:not([data-category="{category_slug}"]) {{ opacity: 0.16 !important; }}'
            )
            hover_rules.append(
                f'svg:has([data-filter-value="{category_slug}"]:hover) .c2-mark[data-category="{category_slug}"] {{ stroke-width: 3 !important; filter: drop-shadow(0 0 4px rgba(47,47,47,0.35)); }}'
            )
        svg.append("<style>" + "\n".join(hover_rules) + "</style>")

        # C5: shoreline bias panel.
        top_x, top_y, top_w, top_h = 55, 50, 1070, 250
        draw_panel(svg, top_x, top_y, top_w, top_h, "C5", "shoreline bias")
        water_y = top_y + 182
        shoreline_x = top_x + 680

        def shore_ground_y(x):
            flat_shore_y = top_y + 124
            if x >= shoreline_x + 92:
                return flat_shore_y
            if x <= shoreline_x:
                return water_y
            progress = (x - shoreline_x) / 92
            eased = progress * progress * (3 - 2 * progress)
            return water_y + (flat_shore_y - water_y) * eased

        svg.append(
            f'<rect x="{top_x + 1}" y="{top_y + 32}" width="{top_w - 2}" height="{top_h - 33}" fill="url(#c2-sky-grad)" opacity="0.96"/>'
        )
        svg.append(
            f'<circle cx="{top_x + top_w - 98}" cy="{top_y + 76}" r="28" fill="#ffd36f" opacity="0.55"/>'
        )
        svg.append(
            f'<path d="M {top_x + 18} {water_y} L {shoreline_x} {water_y} L {shoreline_x + 92} {top_y + 124} '
            f'L {top_x + top_w - 20} {top_y + 124} L {top_x + top_w - 18} {top_y + top_h - 34} '
            f'L {top_x + 18} {top_y + top_h - 34} Z" fill="{sand}" opacity="0.86"/>'
        )
        svg.append(
            f'<path d="M {top_x + 18} {water_y} L {shoreline_x} {water_y} L {shoreline_x + 92} {top_y + 124} '
            f'L {top_x + 18} {top_y + 124} Z" fill="{sea}" opacity="0.9"/>'
        )
        for offset in (0, 18, 36):
            svg.append(
                f'<path d="M {top_x + 34} {water_y - 18 + offset} C {top_x + 170} {water_y - 30 + offset}, '
                f'{top_x + 335} {water_y - 6 + offset}, {top_x + 520} {water_y - 16 + offset}" '
                'fill="none" stroke="#4b8ec0" stroke-width="1" opacity="0.55"/>'
            )
        svg.append(
            f'<path d="M {shoreline_x} {water_y} C {shoreline_x + 30} {water_y - 28}, '
            f'{shoreline_x + 56} {water_y - 64}, {shoreline_x + 92} {top_y + 124}" '
            'fill="none" stroke="#4b4b4b" stroke-width="1.5"/>'
        )
        svg.append(
            f'<g filter="url(#c2-soft-shadow)">'
            f'<path d="M {top_x + 95} {water_y - 31} L {top_x + 285} {water_y - 31} '
            f'C {top_x + 268} {water_y + 5}, {top_x + 147} {water_y + 8}, {top_x + 115} {water_y - 2} Z" '
            'fill="url(#c2-hull-grad)" stroke="#102d40" stroke-width="1.5"/>'
            f'<path d="M {top_x + 143} {water_y - 66} L {top_x + 226} {water_y - 66} '
            f'L {top_x + 248} {water_y - 32} L {top_x + 126} {water_y - 32} Z" '
            'fill="url(#c2-cabin-grad)" stroke="#60727f" stroke-width="1.2"/>'
            f'<rect x="{top_x + 155}" y="{water_y - 57}" width="22" height="13" rx="2" fill="#7eb7da" stroke="#456577" stroke-width="0.8"/>'
            f'<rect x="{top_x + 187}" y="{water_y - 57}" width="24" height="13" rx="2" fill="#7eb7da" stroke="#456577" stroke-width="0.8"/>'
            f'<line x1="{top_x + 118}" y1="{water_y - 38}" x2="{top_x + 275}" y2="{water_y - 38}" stroke="#ffffff" stroke-width="2" opacity="0.9"/>'
            f'<path d="M {top_x + 98} {water_y - 1} C {top_x + 150} {water_y + 7}, {top_x + 220} {water_y + 6}, {top_x + 292} {water_y - 1}" '
            'fill="none" stroke="#d9f2ff" stroke-width="3" opacity="0.88"/>'
            f'<line x1="{top_x + 134}" y1="{water_y - 72}" x2="{top_x + 134}" y2="{water_y - 119}" stroke="#263746" stroke-width="2"/>'
            f'<path d="M {top_x + 134} {water_y - 116} C {top_x + 169} {water_y - 105}, {top_x + 179} {water_y - 82}, {top_x + 139} {water_y - 80} Z" fill="#f3f6f8" stroke="#263746" stroke-width="1"/>'
            f'<line x1="{top_x + 228}" y1="{water_y - 65}" x2="{top_x + 270}" y2="{water_y - 94}" stroke="#263746" stroke-width="2"/>'
            f'<line x1="{top_x + 270}" y1="{water_y - 94}" x2="{top_x + 290}" y2="{water_y - 77}" stroke="#263746" stroke-width="1.4"/>'
            f'<circle cx="{top_x + 247}" cy="{water_y - 19}" r="5" fill="#ef4444" stroke="#8f1d1d" stroke-width="1"/>'
            '</g>'
        )
        svg.append(
            f'<g filter="url(#c2-soft-shadow)">'
            f'<path d="M {top_x + top_w - 215} {top_y + 138} C {top_x + top_w - 187} {top_y + 80}, '
            f'{top_x + top_w - 118} {top_y + 80}, {top_x + top_w - 91} {top_y + 138} Z" '
            'fill="#ef5350" stroke="#8b2b29" stroke-width="1.2"/>'
            f'<path d="M {top_x + top_w - 153} {top_y + 138} C {top_x + top_w - 155} {top_y + 104}, '
            f'{top_x + top_w - 154} {top_y + 87}, {top_x + top_w - 153} {top_y + 82}" '
            'fill="none" stroke="#8b2b29" stroke-width="1"/>'
            f'<line x1="{top_x + top_w - 153}" y1="{top_y + 138}" x2="{top_x + top_w - 153}" y2="{top_y + 178}" stroke="#8a6f3f" stroke-width="2"/>'
            f'<rect x="{top_x + top_w - 194}" y="{top_y + 178}" width="76" height="9" rx="4" fill="#f0f5f7" stroke="#8ea0aa" stroke-width="1"/>'
            '</g>'
        )
        svg.append(
            f'<line x1="{top_x + 150}" y1="{top_y + top_h - 48}" x2="{top_x + top_w - 160}" y2="{top_y + top_h - 48}" '
            f'stroke="{ink}" stroke-width="1.5"/>'
        )
        svg.append(
            f'<text x="{top_x + 60}" y="{top_y + top_h - 43}" font-size="12" fill="{CATEGORY_COLORS["Fishing"]}">fishing side</text>'
        )
        svg.append(
            f'<text x="{top_x + top_w - 126}" y="{top_y + top_h - 43}" font-size="12" text-anchor="end" fill="{CATEGORY_COLORS["Tourism"]}">tourism side</text>'
        )

        positioned_people = []
        for index, person in enumerate(people):
            if abs(bias_max - bias_min) < 1e-9:
                x = top_x + top_w * 0.53
            else:
                x = top_x + 185 + (person["bias_gap"] - bias_min) * (top_w - 355) / (bias_max - bias_min)
            x = clip(x, top_x + 145, top_x + top_w - 145)
            y = top_y + 104 - (index % 3) * 8
            if x >= shoreline_x + 18:
                y = shore_ground_y(x) - 6
            if person["bias_gap"] < 0:
                color = blend_hex("#6e6e6e", CATEGORY_COLORS["Fishing"], abs(person["bias_gap"]) / max_abs_bias)
            else:
                color = blend_hex("#6e6e6e", CATEGORY_COLORS["Tourism"], abs(person["bias_gap"]) / max_abs_bias)
            member_slug = slug(person["member"])
            category_slug = "Fishing" if person["bias_gap"] < 0 else "Tourism"
            positioned_people.append(
                {
                    "index": index,
                    "member": person["member"],
                    "bias_gap": person["bias_gap"],
                    "x": x,
                    "y": y,
                    "color": color,
                    "member_slug": member_slug,
                    "category": category_slug,
                    "category_slug": slug(category_slug),
                    "label_y": top_y + 48 + (index % 3) * 15,
                }
            )

        member_top_points = {}
        water_people = [
            person for person in positioned_people if person["x"] < shoreline_x + 18
        ]
        land_people = [
            person for person in positioned_people if person["x"] >= shoreline_x + 18
        ]
        water_groups = []
        for person in sorted(water_people, key=lambda item: item["x"]):
            if (
                not water_groups
                or person["x"] - water_groups[-1][-1]["x"] > 95
                or len(water_groups[-1]) >= 3
            ):
                water_groups.append([person])
            else:
                water_groups[-1].append(person)

        for group_index, group in enumerate(water_groups):
            boat_center_x = clip(
                sum(person["x"] for person in group) / len(group),
                top_x + 120,
                shoreline_x - 52,
            )
            boat_y = water_y - 24 - (group_index % 2) * 11
            group_members = " ".join(person["member_slug"] for person in group)
            group_categories = {person["category_slug"] for person in group}
            group_category = (
                next(iter(group_categories)) if len(group_categories) == 1 else slug("Hybrid")
            )
            svg.append(
                f'<g class="c2-mark c2-control" data-filter-type="category" data-filter-value="{group_category}" '
                f'data-member="{group_members}" data-category="{group_category}">'
            )
            boat_w = draw_small_fishing_boat(svg, boat_center_x, boat_y, len(group), scale=0.96)
            if len(group) == 1:
                seat_offsets = [0]
            else:
                seat_gap = min(29, (boat_w - 42) / (len(group) - 1))
                seat_offsets = [
                    (seat_index - (len(group) - 1) / 2) * seat_gap
                    for seat_index in range(len(group))
                ]
            for person, seat_offset in zip(sorted(group, key=lambda item: item["x"]), seat_offsets):
                seat_x = boat_center_x + seat_offset
                seat_y = boat_y - 2
                svg.append(
                    f'<g class="c2-mark c2-control" data-filter-type="member" data-filter-value="{person["member_slug"]}" '
                    f'data-member="{person["member_slug"]}" data-category="{person["category_slug"]}">'
                )
                draw_boat_person(svg, seat_x, seat_y, person["color"], scale=0.74)
                svg.append(
                    f'<path d="M {seat_x:.1f} {seat_y - 34:.1f} L {seat_x:.1f} {person["label_y"] + 5}" '
                    'fill="none" stroke="#817b6a" stroke-width="0.9" stroke-dasharray="4,4"/>'
                )
                svg.append(
                    f'<text x="{seat_x:.1f}" y="{person["label_y"]}" font-size="11" font-weight="700" '
                    f'text-anchor="middle" fill="{person["color"]}">{escape(short_label(person["member"], 14))}</text>'
                )
                svg.append(
                    f'<title>{escape(person["member"])}\nBias gap: {person["bias_gap"]:+.2f} hours\nClick to highlight this member across panels.</title>'
                )
                svg.append("</g>")
                member_top_points[person["member"]] = (
                    seat_x,
                    seat_y,
                    person["color"],
                    person["member_slug"],
                )
            svg.append(
                f'<title>Small fishing boat: {escape(", ".join(person["member"] for person in group))}</title>'
            )
            svg.append("</g>")

        for person in land_people:
            x = person["x"]
            y = person["y"]
            svg.append(
                f'<g class="c2-mark c2-control" data-filter-type="member" data-filter-value="{person["member_slug"]}" '
                f'data-member="{person["member_slug"]}" data-category="{person["category_slug"]}">'
            )
            draw_person(svg, x, y, person["color"], scale=0.9)
            svg.append(
                f'<path d="M {x:.1f} {y - 34:.1f} L {x:.1f} {person["label_y"] + 5}" fill="none" stroke="#817b6a" '
                'stroke-width="0.9" stroke-dasharray="4,4"/>'
            )
            svg.append(
                f'<text x="{x:.1f}" y="{person["label_y"]}" font-size="11" font-weight="700" text-anchor="middle" '
                f'fill="{person["color"]}">{escape(short_label(person["member"], 14))}</text>'
            )
            svg.append(
                f'<title>{escape(person["member"])}\nBias gap: {person["bias_gap"]:+.2f} hours\nClick to highlight this member across panels.</title>'
            )
            svg.append("</g>")
            member_top_points[person["member"]] = (
                x,
                y,
                person["color"],
                person["member_slug"],
            )

        svg.append(
            f'<text x="{top_x + 34}" y="{top_y + top_h - 16}" font-size="11" fill="{soft_ink}">position = tourism time minus fishing time; member selection updates all panels</text>'
        )
        svg.append(
            f'<text id="c2-status" x="{top_x + top_w - 34}" y="{top_y + top_h - 16}" font-size="11" text-anchor="end" fill="{soft_ink}">click a person or legend item to highlight</text>'
        )
        if not people:
            svg.append(
                f'<text x="{top_x + top_w / 2:.1f}" y="{top_y + 140}" font-size="18" text-anchor="middle" fill="{soft_ink}">No member data after current filters</text>'
            )

        # C6: board visit map.
        map_x, map_y, map_w, map_h = 55, 335, 535, 420
        draw_panel(svg, map_x, map_y, map_w, map_h, "C6", "board visit map")
        all_places = source_data[c2_selected_source]["places"]

        def load_oceanus_map():
            candidates = []
            try:
                candidates.append(Path(__file__).parent / "data" / "oceanus_map.geojson")
            except NameError:
                pass
            candidates.append(Path.cwd() / "data" / "oceanus_map.geojson")
            candidates.append(Path.cwd().parent / "data" / "oceanus_map.geojson")
            for candidate in candidates:
                if candidate.exists():
                    return json.loads(candidate.read_text(encoding="utf-8"))
            return {"type": "FeatureCollection", "features": []}

        oceanus_map = load_oceanus_map()

        def iter_geo_points(coords):
            if (
                isinstance(coords, list)
                and len(coords) >= 2
                and isinstance(coords[0], (int, float))
                and isinstance(coords[1], (int, float))
            ):
                yield float(coords[0]), float(coords[1])
            elif isinstance(coords, list):
                for item in coords:
                    yield from iter_geo_points(item)

        geo_points = [
            point
            for feature in oceanus_map.get("features", [])
            for point in iter_geo_points(feature.get("geometry", {}).get("coordinates", []))
        ]
        place_points = [(place["x"], place["y"]) for place in all_places]
        bounds_points = geo_points + place_points
        x_min = min(point[0] for point in bounds_points)
        x_max = max(point[0] for point in bounds_points)
        y_min = min(point[1] for point in bounds_points)
        y_max = max(point[1] for point in bounds_points)

        def map_screen(x_value, y_value):
            px = map_x + 38 + ((x_value - x_min) / (x_max - x_min)) * (map_w - 76)
            py = map_y + map_h - 48 - ((y_value - y_min) / (y_max - y_min)) * (map_h - 96)
            return px, py

        svg.append(
            f'<rect x="{map_x + 18}" y="{map_y + 44}" width="{map_w - 36}" height="{map_h - 84}" rx="4" fill="#d8eef9" stroke="#c7dbe7" stroke-width="1"/>'
        )

        def polygon_path(ring):
            commands = []
            for index, (lon, lat) in enumerate(ring):
                px, py = map_screen(lon, lat)
                prefix = "M" if index == 0 else "L"
                commands.append(f"{prefix} {px:.1f} {py:.1f}")
            if commands:
                commands.append("Z")
            return " ".join(commands)

        def map_feature_style(feature):
            props = feature.get("properties", {})
            kind = props.get("Kind", "")
            activities = " ".join(props.get("Activities", []) or [])
            if "Fishing Ground" in kind or "fishing" in activities.lower():
                return "#b7d4ee", "#3f78a6", "0.46"
            if "Ecological Preserve" in kind or "Research" in activities or "Tourism" in activities:
                return "#bfe2c8", "#4e8a63", "0.58"
            if "Island" in kind:
                return "#e1d3b7", "#9b855d", "0.88"
            return "#d7e1e8", "#8798a6", "0.7"

        for feature in oceanus_map.get("features", []):
            geometry = feature.get("geometry", {})
            props = feature.get("properties", {})
            name = props.get("Name", "")
            fill, stroke, opacity = map_feature_style(feature)
            if geometry.get("type") == "Polygon":
                for ring_index, ring in enumerate(geometry.get("coordinates", [])):
                    path = polygon_path(ring)
                    if not path:
                        continue
                    width_value = "1.2" if ring_index == 0 else "0.8"
                    svg.append(
                        f'<path d="{path}" fill="{fill}" fill-opacity="{opacity}" stroke="{stroke}" stroke-width="{width_value}">'
                        f'<title>{escape(name)}</title></path>'
                    )
            elif geometry.get("type") == "Point":
                lon, lat = geometry.get("coordinates", [None, None])[:2]
                if lon is None or lat is None:
                    continue
                px, py = map_screen(float(lon), float(lat))
                svg.append(
                    f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.4" fill="#ffffff" stroke="#667788" stroke-width="1"><title>{escape(name)}</title></circle>'
                )
                if name in {"Himark", "Lomark", "Paackland", "Port Grove"}:
                    svg.append(
                        f'<text x="{px + 5:.1f}" y="{py - 5:.1f}" font-size="9" fill="#51606c">{escape(name)}</text>'
                    )

        for place in all_places:
            px, py = map_screen(place["x"], place["y"])
            svg.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.3" fill="#9b9b9b" opacity="0.28"/>'
            )

        for category_name in CATEGORY_ORDER:
            places = [
                place
                for place in grouped_places.values()
                if place["category"] == category_name
            ]
            for place in sorted(places, key=lambda item: item["visits"]):
                px, py = map_screen(place["x"], place["y"])
                radius = min(19, 3.5 + math.sqrt(place["visits"]) * 2.1)
                opacity = "0.86" if category_name != "Neutral" else "0.42"
                title = escape(
                    f'{place["name"]}\n'
                    f'Category: {category_name}\n'
                    f'Member-visits: {place["visits"]}\n'
                    f'Hours: {place["hours"]:.2f}\n'
                    f'Raw zone: {place["zone"]}\n'
                    f'Remapped zone: {place["zone_remapped"]}'
                )
                member_values = " ".join(slug(member) for member in sorted(place["members"]))
                svg.append(
                    f'<circle class="c2-mark c2-control" data-filter-type="category" data-filter-value="{slug(category_name)}" '
                    f'data-member="{member_values}" data-category="{slug(category_name)}" cx="{px:.1f}" cy="{py:.1f}" '
                    f'r="{radius:.1f}" fill="{CATEGORY_COLORS[category_name]}" fill-opacity="{opacity}" '
                    f'stroke="{CATEGORY_STROKES[category_name]}" stroke-width="1.4"><title>{title}\nClick to highlight {category_name}.</title></circle>'
                )

        top_places = sorted(
            grouped_places.values(),
            key=lambda item: (-item["visits"], -item["hours"], str(item["name"])),
        )[:4]
        for index, place in enumerate(top_places):
            px, py = map_screen(place["x"], place["y"])
            lx = map_x + 78 + index * 112
            ly = map_y + map_h - 40
            svg.append(
                f'<path d="M {px:.1f} {py:.1f} C {px:.1f} {py + 44:.1f}, {lx:.1f} {ly - 28:.1f}, {lx:.1f} {ly - 12:.1f}" '
                'fill="none" stroke="#777" stroke-width="0.8" stroke-dasharray="3,4"/>'
            )
            svg.append(
                f'<text x="{lx}" y="{ly}" font-size="10" text-anchor="middle" fill="{soft_ink}">{escape(short_label(place["name"], 18))}</text>'
            )

        svg.append(
            f'<text x="{map_x + 24}" y="{map_y + 56}" font-size="11" fill="{soft_ink}">circle size = repeated visits; color = remapped place type</text>'
        )

        # C7: trip-time summary.
        time_x, time_y, time_w, time_h = 625, 335, 500, 420
        draw_panel(svg, time_x, time_y, time_w, time_h, "C7", "trip time split")
        line_y = time_y + 82
        svg.append(
            f'<line x1="{time_x + 58}" y1="{line_y}" x2="{time_x + time_w - 52}" y2="{line_y}" stroke="{ink}" stroke-width="1.2"/>'
        )
        if trip_records:
            tick_records = trip_records
            step = max(1, len(tick_records) // 28)
            visible_ticks = tick_records[::step][:29]
            for index, record in enumerate(visible_ticks):
                tx = time_x + 58 + index * (time_w - 110) / max(1, len(visible_ticks) - 1)
                color = CATEGORY_COLORS.get(record["category"], CATEGORY_COLORS["Neutral"])
                tick_h = 10 + min(24, record["hours"] * 1.3)
                svg.append(
                    f'<line class="c2-mark c2-control" data-filter-type="member" data-filter-value="{slug(record["member"])}" '
                    f'data-member="{slug(record["member"])}" data-category="{slug(record["category"])}" '
                    f'x1="{tx:.1f}" y1="{line_y - tick_h:.1f}" x2="{tx:.1f}" y2="{line_y + tick_h:.1f}" '
                    f'stroke="{color}" stroke-width="2" stroke-linecap="round">'
                    f'<title>{escape(record["trip_id"] + " | " + record["member"] + " | " + record["category"])}\nClick to highlight this member.</title></line>'
                )
            svg.append(
                f'<text x="{time_x + 60}" y="{line_y - 34}" font-size="10" fill="{soft_ink}">trip order</text>'
            )

        donut_cx, donut_cy = time_x + 250, time_y + 255
        inner_outer = 82
        inner_hole = 34
        total_sum = sum(summary_values) or 1.0
        current_angle = 0.0
        for category_name, value in zip(summary_labels, summary_values):
            angle_width = 360.0 * value / total_sum
            color = CATEGORY_COLORS.get(category_name, CATEGORY_COLORS["Neutral"])
            if angle_width >= 359.9:
                svg.append(
                    f'<circle cx="{donut_cx}" cy="{donut_cy}" r="{inner_outer}" fill="{color}" opacity="0.9"/>'
                )
            else:
                path = arc_wedge_path(
                    donut_cx,
                    donut_cy,
                    inner_outer,
                    inner_hole,
                    current_angle,
                    current_angle + angle_width,
                )
                svg.append(
                    f'<path d="{path}" fill="{color}" fill-opacity="0.9" stroke="{paper}" stroke-width="1.6"/>'
                )
            current_angle += angle_width
        svg.append(
            f'<circle cx="{donut_cx}" cy="{donut_cy}" r="{inner_hole}" fill="#ffffff" stroke="#8ea0aa" stroke-width="1"/>'
        )

        trip_total_hours = sum(record["hours"] for record in trip_records) or 1.0
        outer_angle = 0.0
        for record in trip_records:
            angle_width = 360.0 * record["hours"] / trip_total_hours
            if angle_width <= 0:
                continue
            color = CATEGORY_COLORS.get(record["category"], CATEGORY_COLORS["Neutral"])
            path = arc_wedge_path(
                donut_cx,
                donut_cy,
                inner_outer + 31,
                inner_outer + 19,
                outer_angle,
                outer_angle + max(angle_width, 0.25),
            )
            svg.append(
                f'<path class="c2-mark c2-control" data-filter-type="member" data-filter-value="{slug(record["member"])}" '
                f'data-member="{slug(record["member"])}" data-category="{slug(record["category"])}" d="{path}" '
                f'fill="{color}" fill-opacity="0.72" stroke="#ffffff" stroke-width="0.5">'
                f'<title>{escape(record["trip_id"] + " | " + record["member"] + " | " + record["category"])}\nClick to highlight this member.</title></path>'
            )
            outer_angle += angle_width

        svg.append(
            f'<text x="{donut_cx}" y="{donut_cy - 4}" font-size="13" font-weight="700" text-anchor="middle" fill="{ink}">time</text>'
        )
        svg.append(
            f'<text x="{donut_cx}" y="{donut_cy + 14}" font-size="10" text-anchor="middle" fill="{soft_ink}">{sum(summary_values):.0f} hours</text>'
        )
        legend_x = time_x + 55
        legend_y = time_y + time_h - 78
        for index, category_name in enumerate(CATEGORY_ORDER):
            lx = legend_x + index * 98
            svg.append(
                f'<circle class="c2-mark c2-control" data-filter-type="category" data-filter-value="{slug(category_name)}" '
                f'data-category="{slug(category_name)}" cx="{lx}" cy="{legend_y}" r="6" fill="{CATEGORY_COLORS[category_name]}" '
                f'stroke="{CATEGORY_STROKES[category_name]}" stroke-width="1"><title>Click to highlight {category_name}.</title></circle>'
            )
            svg.append(
                f'<text class="c2-control" data-filter-type="category" data-filter-value="{slug(category_name)}" '
                f'x="{lx + 10}" y="{legend_y + 4}" font-size="10" fill="{soft_ink}">{category_name}</text>'
            )
        svg.append(
            f'<text x="{time_x + 24}" y="{time_y + 56}" font-size="11" fill="{soft_ink}">inner = total time split; outer = each member-trip in order</text>'
        )

        # Linking marks between the top sketch and the two lower sketches.
        svg.append(
            f'<path d="M {top_x + 308} {top_y + top_h - 2} C {top_x + 248} {map_y - 10}, {map_x + 270} {map_y - 8}, {map_x + 270} {map_y}" '
            'fill="none" stroke="#79746a" stroke-width="1.1" stroke-dasharray="5,6"/>'
        )
        svg.append(
            f'<path d="M {top_x + 778} {top_y + top_h - 2} C {top_x + 840} {time_y - 12}, {time_x + 250} {time_y - 10}, {time_x + 250} {time_y}" '
            'fill="none" stroke="#79746a" stroke-width="1.1" stroke-dasharray="5,6"/>'
        )
        svg.append(
            f'<text x="{width - 52}" y="{height - 28}" font-size="10" text-anchor="end" fill="#777">interactive C5 + C6 + C7 view</text>'
        )
        svg.append("</svg>")
        return "".join(svg)

    mo.Html(render_cluster2_merged())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Notes

    - Place labels use the Graph 2 preparation: manual zone fixes first, then weighted nearest-neighbor remapping for commercial/residential places.
    - Remapped `industrial` places are shown as Fishing; remapped `tourism` places are shown as Tourism.
    - Trip time is allocated with half the gap before and half the gap after each timestamp in `trip_places.csv`.
    - The first and last stops receive the remaining gap to the trip start/end.
    """)
    return


if __name__ == "__main__":
    app.run()
