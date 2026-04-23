import marimo

__generated_with = "0.17.6"
app = marimo.App(width="wide")


@app.cell
def _():
    import csv
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
        math,
        mo,
        timedelta,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Cluster 2 SVG Notebook

    This notebook rebuilds Cluster 2 from the `inperson_group5` design as
    marimo-driven SVG views.

    The workflow is split into two stages:

    1. load and filter trip-stop data
    2. draw the filtered results as SVG
    """)
    return


@app.cell
def _(Path):
    def resolve_default_root() -> Path:
        candidates = [
            Path("/Users/bouns/g0r72a_data_peiyang_2526"),
            Path.cwd() / "g0r72a_data_peiyang_2526",
            Path.cwd().parent / "g0r72a_data_peiyang_2526",
        ]
        for candidate in candidates:
            if (candidate / "Collected_by_the_Journalist").exists():
                return candidate
        return candidates[0]

    DEFAULT_ROOT = resolve_default_root()
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
        FISHING_KEYWORDS,
        FISHING_TOPICS,
        HYBRID_TOPICS,
        SOURCE_NAMES,
        TOURISM_KEYWORDS,
        TOURISM_TOPICS,
        ZONE_COLORS,
    )


@app.cell
def _(
    CATEGORY_ORDER,
    Counter,
    FISHING_KEYWORDS,
    FISHING_TOPICS,
    HYBRID_TOPICS,
    TOURISM_KEYWORDS,
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

    def infer_place_category(place, linked_category):
        if linked_category is not None:
            return linked_category

        zone = (place.get("zone") or "").strip().lower()
        text = " ".join(
            [
                (place.get("name") or "").lower(),
                (place.get("zone_detail") or "").lower(),
            ]
        )

        if zone == "tourism" or any(keyword in text for keyword in TOURISM_KEYWORDS):
            return "Tourism"
        if zone == "industrial" or any(keyword in text for keyword in FISHING_KEYWORDS):
            return "Fishing"
        return "Neutral"

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

    def load_source(root, source_name):
        source_dir = root / f"Collected_by_the_{source_name}"

        place_rows = read_rows(source_dir / "places.csv")
        plan_topic_rows = read_rows(source_dir / "plan_topics.csv")
        travel_link_rows = read_rows(source_dir / "travel_links.csv")
        trip_rows = read_rows(source_dir / "trips.csv")
        trip_people_rows = read_rows(source_dir / "trip_people.csv")
        trip_place_rows = read_rows(source_dir / "trip_places.csv")
        people_rows = read_rows(source_dir / "people.csv")

        topic_by_plan = {
            row["plan_id"]: classify_topic(row["topic_id"])
            for row in plan_topic_rows
        }

        place_link_categories = defaultdict(list)
        for row in travel_link_rows:
            category = topic_by_plan.get(row["plan_id"], "Neutral")
            place_link_categories[str(row["place_id"])].append(category)

        place_lookup = {}
        all_places = []
        for row in place_rows:
            place_id = str(row["place_id"])
            linked_category = dominant_category(place_link_categories[place_id])

            place_record = {
                "place_id": place_id,
                "name": row["name"],
                "x": float(row["lat"]),
                "y": float(row["lon"]),
                "zone": row["zone"] or "unknown",
                "zone_detail": row["zone_detail"] or "",
            }
            place_record["category"] = infer_place_category(row, linked_category)

            place_lookup[place_id] = place_record
            place_lookup[row["name"]] = place_record
            all_places.append(place_record)

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
                    "zone_detail": place["zone_detail"],
                    "category": place["category"],
                    "time": parse_stamp(row["time"]),
                }
            )

        visit_rows = []
        for trip_id, meta in trip_meta.items():
            stops = sorted(trip_stops.get(trip_id, []), key=lambda item: item["time"])
            if not stops:
                continue

            members = sorted(set(trip_members.get(trip_id, []))) or ["Unknown"]
            previous_time = meta["start_dt"]
            stop_rows = []

            for stop in stops:
                duration_hours = max(
                    (stop["time"] - previous_time).total_seconds() / 3600.0,
                    0.0,
                )
                enriched = dict(stop)
                enriched["duration_hours"] = duration_hours
                stop_rows.append(enriched)
                previous_time = stop["time"]

            tail_hours = max(
                (meta["end_dt"] - previous_time).total_seconds() / 3600.0,
                0.0,
            )
            stop_rows[-1]["duration_hours"] += tail_hours

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
                            "zone_detail": stop["zone_detail"],
                            "category": stop["category"],
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
def _(DEFAULT_ROOT, SOURCE_NAMES, load_source):
    source_data = {
        source_name: load_source(DEFAULT_ROOT, source_name)
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
def _(DEFAULT_ROOT, SOURCE_NAMES, all_members, mo):
    root_widget = mo.ui.text(
        value=str(DEFAULT_ROOT),
        label="Data root",
        disabled=True,
        full_width=True,
    )

    source_widget = mo.ui.dropdown(
        options=list(SOURCE_NAMES),
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
    return member_widget, neutral_widget, root_widget, source_widget


@app.cell
def _(member_widget, mo, neutral_widget, root_widget, source_widget):
    mo.vstack([root_widget, source_widget, member_widget, neutral_widget])
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

    if not c2_selected_members:
        c2_member_label = "no matching members"
    elif c2_selected_members == c2_source_members:
        c2_member_label = "all board members"
    else:
        c2_member_label = ", ".join(sorted(c2_selected_members))
    return (
        c2_filtered_visits,
        c2_include_neutral,
        c2_member_label,
        c2_selected_source,
    )


@app.cell(hide_code=True)
def _(c2_filtered_visits, c2_member_label, c2_selected_source, mo):
    mo.md(f"""
    **Current filter**

    - source: `{c2_selected_source}`
    - members: `{c2_member_label}`
    - filtered visit rows: `{len(c2_filtered_visits)}`
    """)
    return


@app.cell
def _(c2_filtered_visits):
    c2_member_summary = {}
    for visit in c2_filtered_visits:
        member_name = str(visit["member"])
        if member_name not in c2_member_summary:
            c2_member_summary[member_name] = {
                "member": member_name,
                "Fishing": 0.0,
                "Tourism": 0.0,
                "Hybrid": 0.0,
                "Neutral": 0.0,
            }
        c2_member_summary[member_name][str(visit["category"])] += float(
            visit["duration_hours"]
        )

    c2_bias_people = []
    for summary in c2_member_summary.values():
        fishing_value = summary["Fishing"] + 0.5 * summary["Hybrid"]
        tourism_value = summary["Tourism"] + 0.5 * summary["Hybrid"]
        c2_bias_people.append(
            {
                "member": summary["member"],
                "bias_gap": tourism_value - fishing_value,
            }
        )

    c2_bias_people.sort(key=lambda person: (person["bias_gap"], person["member"]))
    return (c2_bias_people,)


@app.cell
def _(c2_filtered_visits, c2_selected_source, source_data):
    def _():
        c2_all_places = source_data[c2_selected_source]["places"]
        c2_grouped_places = {}

        for visit in c2_filtered_visits:
            place_id = str(visit["place_id"])
            if place_id not in c2_grouped_places:
                c2_grouped_places[place_id] = {
                    "name": visit["name"],
                    "x": visit["x"],
                    "y": visit["y"],
                    "zone": visit["zone"],
                    "category": visit["category"],
                    "visits": 0,
                    "hours": 0.0,
                    "members": set(),
                    "trips": set(),
                }

            c2_grouped_places[place_id]["visits"] += 1
            c2_grouped_places[place_id]["hours"] += float(visit["duration_hours"])
            c2_grouped_places[place_id]["members"].add(str(visit["member"]))
        return c2_grouped_places[place_id]["trips"].add(str(visit["trip_id"]))

        if c2_all_places:
            c2_map_bounds = {
                "x_min": min(place["x"] for place in c2_all_places),
                "x_max": max(place["x"] for place in c2_all_places),
                "y_min": min(place["y"] for place in c2_all_places),
                "y_max": max(place["y"] for place in c2_all_places),
            }
        else:
            c2_map_bounds = {"x_min": 0.0, "x_max": 0.0, "y_min": 0.0, "y_max": 0.0}


    _()
    return


@app.cell
def _(
    CATEGORY_ORDER,
    c2_filtered_visits,
    c2_include_neutral,
    defaultdict,
    dominant_time_category,
    summarize_category_hours,
):
    def _():
        c2_total_hours = summarize_category_hours(c2_filtered_visits)
        c2_summary_labels = [
            category_name
            for category_name in CATEGORY_ORDER
            if c2_total_hours.get(category_name, 0.0) > 0
            and (c2_include_neutral or category_name != "Neutral")
        ]
        if not c2_summary_labels:
            c2_summary_labels = ["Neutral"]

        c2_summary_values = [
            c2_total_hours.get(category_name, 0.0) for category_name in c2_summary_labels
        ]
        if sum(c2_summary_values) <= 0:
            c2_summary_values = [1.0 for _ in c2_summary_labels]

        c2_trip_rollup = {}
        for visit in c2_filtered_visits:
            trip_key = (str(visit["member"]), str(visit["trip_id"]))
            if trip_key not in c2_trip_rollup:
                c2_trip_rollup[trip_key] = {
                    "member": str(visit["member"]),
                    "trip_id": str(visit["trip_id"]),
                    "date": str(visit["date"]),
                    "start_dt": visit["start_dt"],
                    "hours": 0.0,
                    "category_hours": defaultdict(float),
                    "places": set(),
                }

            c2_trip_rollup[trip_key]["hours"] += float(visit["duration_hours"])
            c2_trip_rollup[trip_key]["category_hours"][str(visit["category"])] += float(
                visit["duration_hours"]
            )
            c2_trip_rollup[trip_key]["places"].add(str(visit["name"]))

        c2_trip_records = []
        for record in c2_trip_rollup.values():
            c2_trip_records.append(
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
        return c2_trip_records.sort(
            key=lambda record: (record["start_dt"], record["member"], record["trip_id"])
        )


    _()
    return


@app.cell
def _(
    CATEGORY_COLORS,
    c2_bias_people,
    c2_member_label,
    c2_selected_source,
    escape,
):
    scene_width = 980
    scene_height = 620

    def sx(x_ratio):
        return round(x_ratio * scene_width, 1)

    def sy(y_ratio):
        return round((1 - y_ratio) * scene_height, 1)

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

    people = [dict(person) for person in c2_bias_people]
    if people:
        bias_min = min(person["bias_gap"] for person in people)
        bias_max = max(person["bias_gap"] for person in people)
    else:
        bias_min = -1.0
        bias_max = 1.0

    def bias_to_x(value):
        if abs(bias_max - bias_min) < 1e-9:
            return 0.54
        return 0.26 + (value - bias_min) * (0.82 - 0.26) / (bias_max - bias_min)

    max_abs_bias = max([abs(person["bias_gap"]) for person in people] + [0.25])
    for person in people:
        if max_abs_bias <= 1e-9:
            person["color"] = "#6f6f6f"
        elif person["bias_gap"] < 0:
            person["color"] = blend_hex(
                "#6f6f6f",
                CATEGORY_COLORS["Fishing"],
                abs(person["bias_gap"]) / max_abs_bias,
            )
        else:
            person["color"] = blend_hex(
                "#6f6f6f",
                CATEGORY_COLORS["Tourism"],
                abs(person["bias_gap"]) / max_abs_bias,
            )

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

        svg_parts.append(
            f'<line x1="{x}" y1="{foot_y}" x2="{x}" y2="{knee_y}" '
            f'stroke="{stroke_color}" stroke-width="2.2" stroke-linecap="round"/>'
        )
        svg_parts.append(
            f'<line x1="{left_hand_x}" y1="{arm_y}" x2="{right_hand_x}" y2="{arm_y}" '
            f'stroke="{stroke_color}" stroke-width="2.2" stroke-linecap="round"/>'
        )
        svg_parts.append(
            f'<line x1="{x}" y1="{foot_y}" x2="{left_foot_x}" '
            f'y2="{sy(foot_y_ratio - 0.035)}" stroke="{stroke_color}" '
            f'stroke-width="2.2" stroke-linecap="round"/>'
        )
        svg_parts.append(
            f'<line x1="{x}" y1="{foot_y}" x2="{right_foot_x}" '
            f'y2="{sy(foot_y_ratio - 0.035)}" stroke="{stroke_color}" '
            f'stroke-width="2.2" stroke-linecap="round"/>'
        )
        svg_parts.append(
            f'<circle cx="{x}" cy="{head_y}" r="7.5" fill="none" '
            f'stroke="{stroke_color}" stroke-width="2.2"/>'
        )

    c2_fishing_full_svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{scene_width}" '
        f'height="{scene_height}" viewBox="0 0 {scene_width} {scene_height}">'
    ]
    c2_fishing_full_svg.append(
        f'<rect x="0" y="0" width="{scene_width}" height="{scene_height}" '
        'fill="#fbfaf7" rx="20" ry="20"/>'
    )
    c2_fishing_full_svg.append(
        f'<rect x="{sx(0.05)}" y="{sy(0.95)}" width="{sx(0.95) - sx(0.05)}" '
        f'height="{sy(0.52) - sy(0.95)}" fill="#fbf4e8"/>'
    )
    c2_fishing_full_svg.append(
        f'<rect x="{sx(0.05)}" y="{sy(0.28)}" width="{sx(0.67) - sx(0.05)}" '
        f'height="{sy(0.05) - sy(0.28)}" fill="#cfe2ec"/>'
    )
    c2_fishing_full_svg.append(
        f'<polygon points="{sx(0.67)},{sy(0.05)} {sx(0.95)},{sy(0.05)} '
        f'{sx(0.95)},{sy(0.34)} {sx(0.81)},{sy(0.34)} {sx(0.76)},{sy(0.32)} '
        f'{sx(0.73)},{sy(0.30)} {sx(0.67)},{sy(0.28)}" fill="#ead8ab"/>'
    )
    c2_fishing_full_svg.append(
        f'<line x1="{sx(0.05)}" y1="{sy(0.28)}" x2="{sx(0.95)}" y2="{sy(0.28)}" '
        'stroke="#403d39" stroke-width="1.4"/>'
    )
    c2_fishing_full_svg.append(
        f'<polygon points="{sx(0.11)},{sy(0.39)} {sx(0.28)},{sy(0.39)} '
        f'{sx(0.245)},{sy(0.28)} {sx(0.165)},{sy(0.28)}" fill="#97633e" '
        'stroke="#4b3a30" stroke-width="2"/>'
    )
    c2_fishing_full_svg.append(
        f'<line x1="{sx(0.16)}" y1="{sy(0.39)}" x2="{sx(0.16)}" y2="{sy(0.59)}" '
        'stroke="#4b3a30" stroke-width="2.2"/>'
    )
    c2_fishing_full_svg.append(
        f'<line x1="{sx(0.16)}" y1="{sy(0.59)}" x2="{sx(0.20)}" y2="{sy(0.58)}" '
        'stroke="#4b3a30" stroke-width="1.8"/>'
    )
    c2_fishing_full_svg.append(
        f'<path d="M {sx(0.16)} {sy(0.59)} Q {sx(0.10)} {sy(0.45)} {sx(0.09)} '
        f'{sy(0.26)}" fill="none" stroke="#4b3a30" stroke-width="1.8"/>'
    )
    c2_fishing_full_svg.append(
        f'<line x1="{sx(0.11)}" y1="{sy(0.39)}" x2="{sx(0.30)}" y2="{sy(0.39)}" '
        'stroke="#4b3a30" stroke-width="1.8"/>'
    )

    for person in people:
        if 0.31 < person["scene_x"] < 0.74:
            c2_fishing_full_svg.append(
                f'<rect x="{sx(person["scene_x"] - 0.035)}" '
                f'y="{sy(person["foot_y"] - 0.002)}" width="{sx(0.07) - sx(0)}" '
                'height="7" fill="#9a7a54" stroke="#4b3a30" stroke-width="1"/>'
            )
        draw_person(
            c2_fishing_full_svg,
            person["scene_x"],
            person["foot_y"],
            person["color"],
        )
        c2_fishing_full_svg.append(
            f'<line x1="{sx(person["scene_x"])}" y1="{sy(person["head_y"] + 0.02)}" '
            f'x2="{sx(person["label_x"])}" y2="{sy(person["label_y"] - 0.02)}" '
            'stroke="#8d877d" stroke-width="1" stroke-dasharray="4,4"/>'
        )
        c2_fishing_full_svg.append(
            f'<text x="{sx(person["label_x"])}" y="{sy(person["label_y"])}" '
            f'font-size="14" font-weight="700" text-anchor="{person["label_anchor"]}" '
            f'fill="{person["color"]}">{escape(person["member"])}</text>'
        )
        c2_fishing_full_svg.append(
            f'<text x="{sx(person["label_x"])}" y="{sy(person["label_y"]) + 18}" '
            f'font-size="12" text-anchor="{person["label_anchor"]}" '
            f'fill="{person["color"]}">{person["bias_gap"]:+.2f}</text>'
        )

    c2_fishing_full_svg.append(
        f'<line x1="{sx(0.29)}" y1="{sy(0.64)}" x2="{sx(0.82)}" y2="{sy(0.64)}" '
        'stroke="#403d39" stroke-width="2"/>'
    )
    c2_fishing_full_svg.append(
        f'<polygon points="{sx(0.29)},{sy(0.64)} {sx(0.305)},{sy(0.648)} '
        f'{sx(0.305)},{sy(0.632)}" fill="#403d39"/>'
    )
    c2_fishing_full_svg.append(
        f'<polygon points="{sx(0.82)},{sy(0.64)} {sx(0.805)},{sy(0.648)} '
        f'{sx(0.805)},{sy(0.632)}" fill="#403d39"/>'
    )
    c2_fishing_full_svg.append(
        f'<text x="{sx(0.555)}" y="{sy(0.68)}" font-size="15" font-weight="700" '
        'text-anchor="middle" fill="#403d39">'
        "Bias gap = Tourism sentiment minus Fishing sentiment"
        "</text>"
    )
    c2_fishing_full_svg.append(
        f'<text x="{sx(0.17)}" y="{sy(0.58)}" font-size="13" '
        f'fill="{CATEGORY_COLORS["Fishing"]}">warmer to fishing</text>'
    )
    c2_fishing_full_svg.append(
        f'<text x="{sx(0.79)}" y="{sy(0.58)}" font-size="13" '
        f'fill="{CATEGORY_COLORS["Tourism"]}">warmer to tourism</text>'
    )
    c2_fishing_full_svg.append(
        f'<text x="{sx(0.055)}" y="{sy(0.94)}" font-size="30" font-weight="700" '
        'fill="#202020">From Boat to Beach: Where Members Lean</text>'
    )
    c2_fishing_full_svg.append(
        f'<text x="{sx(0.055)}" y="{sy(0.89)}" font-size="17" fill="#202020">'
        f'Source: {escape(c2_selected_source)} | Filter: {escape(c2_member_label)}</text>'
    )
    c2_fishing_full_svg.append(
        f'<rect x="{sx(0.11)}" y="{sy(0.145)}" width="110" height="30" rx="8" ry="8" '
        f'fill="{CATEGORY_COLORS["Fishing"]}"/>'
    )
    c2_fishing_full_svg.append(
        f'<text x="{sx(0.165)}" y="{sy(0.125)}" font-size="13" font-weight="700" '
        'text-anchor="middle" fill="white">Fishing boat</text>'
    )
    c2_fishing_full_svg.append(
        f'<rect x="{sx(0.82)}" y="{sy(0.145)}" width="120" height="30" rx="8" ry="8" '
        f'fill="{CATEGORY_COLORS["Tourism"]}"/>'
    )
    c2_fishing_full_svg.append(
        f'<text x="{sx(0.88)}" y="{sy(0.125)}" font-size="13" font-weight="700" '
        'text-anchor="middle" fill="white">Tourist shore</text>'
    )
    c2_fishing_full_svg.append(
        f'<text x="{sx(0.055)}" y="{sy(0.02)}" font-size="11" fill="#2c2c2c">'
        "Placement uses tourism minus fishing allocated hours from the filtered trip data. "
        "Hybrid time contributes half to each side.</text>"
    )

    if not people:
        c2_fishing_full_svg.append(
            f'<text x="{scene_width / 2:.1f}" y="{scene_height / 2:.1f}" '
            'text-anchor="middle" font-size="22" fill="#6b7280">'
            "No member data after current filters</text>"
        )

    c2_fishing_full_svg.append("</svg>")
    c2_fishing_full_svg = "".join(c2_fishing_full_svg)
    return (c2_fishing_full_svg,)


@app.cell
def _(c2_fishing_full_svg, mo):
    mo.Html(c2_fishing_full_svg)
    return


@app.cell
def _(
    CATEGORY_COLORS,
    CATEGORY_ORDER,
    CATEGORY_STROKES,
    ZONE_COLORS,
    c2_all_places,
    c2_filtered_visits,
    c2_grouped_places,
    c2_map_bounds,
    c2_member_label,
    c2_selected_source,
    escape,
    math,
):
    def _():
        map_width = 980
        map_height = 620
        margin = 70

        def to_screen(x_value, y_value):
            x_min = c2_map_bounds["x_min"]
            x_max = c2_map_bounds["x_max"]
            y_min = c2_map_bounds["y_min"]
            y_max = c2_map_bounds["y_max"]

            if x_max == x_min:
                screen_x = map_width / 2
            else:
                screen_x = margin + ((x_value - x_min) / (x_max - x_min)) * (
                    map_width - 2 * margin
                )

            if y_max == y_min:
                screen_y = map_height / 2
            else:
                screen_y = map_height - margin - ((y_value - y_min) / (y_max - y_min)) * (
                    map_height - 2 * margin
                )

            return screen_x, screen_y

        short_label = c2_member_label
        if len(short_label) > 80:
            short_label = short_label[:77] + "..."

        c2_visit_map_svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{map_width}" '
            f'height="{map_height}" viewBox="0 0 {map_width} {map_height}">'
        ]
        c2_visit_map_svg.append(
            f'<rect x="0" y="0" width="{map_width}" height="{map_height}" '
            'fill="#faf7f2" rx="18" ry="18"/>'
        )
        c2_visit_map_svg.append(
            '<text x="36" y="42" font-size="28" font-weight="700" '
            'fill="#203040">Board visit map</text>'
        )
        c2_visit_map_svg.append(
            f'<text x="36" y="68" font-size="14" fill="#5f6b76">Source: '
            f'{escape(c2_selected_source)} | Filter: {escape(short_label)}</text>'
        )
        c2_visit_map_svg.append(
            '<text x="36" y="90" font-size="13" fill="#6d6d6d">'
            "Faint dots show all known places. Larger colored circles show repeated "
            "filtered member-visits.</text>"
        )

        for place in c2_all_places:
            screen_x, screen_y = to_screen(place["x"], place["y"])
            zone_fill = ZONE_COLORS.get(place["zone"], ZONE_COLORS["unknown"])
            place_title = escape(
                f'{place["name"]}\nZone: {place["zone"]}\nCategory guess: {place["category"]}'
            )
            c2_visit_map_svg.append(
                f'<circle cx="{screen_x:.1f}" cy="{screen_y:.1f}" r="3.5" '
                f'fill="{zone_fill}" opacity="0.25"><title>{place_title}</title></circle>'
            )

        for category_name in CATEGORY_ORDER:
            category_places = [
                place
                for place in c2_grouped_places.values()
                if place["category"] == category_name
            ]

            for place in sorted(category_places, key=lambda item: item["visits"]):
                screen_x, screen_y = to_screen(place["x"], place["y"])
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
                    f'Zone: {place["zone"]}\n'
                    f'Members: {members_text}'
                )

                c2_visit_map_svg.append(
                    f'<circle cx="{screen_x:.1f}" cy="{screen_y:.1f}" r="{radius:.1f}" '
                    f'fill="{fill_color}" fill-opacity="{opacity}" '
                    f'stroke="{stroke_color}" stroke-width="2">'
                    f"<title>{hover_title}</title></circle>"
                )

                if place["visits"] >= 4:
                    label = place["name"]
                    if len(label) > 18:
                        label = label[:15] + "..."
                    c2_visit_map_svg.append(
                        f'<text x="{screen_x:.1f}" y="{screen_y - radius - 8:.1f}" '
                        'font-size="11" text-anchor="middle" fill="#334155">'
                        f"{escape(label)}</text>"
                    )

        legend_x = map_width - 190
        legend_y = 120
        c2_visit_map_svg.append(
            f'<rect x="{legend_x - 18}" y="{legend_y - 28}" width="170" height="150" '
            'rx="12" ry="12" fill="white" opacity="0.92" stroke="#d7d2c8"/>'
        )
        c2_visit_map_svg.append(
            f'<text x="{legend_x}" y="{legend_y - 6}" font-size="14" '
            'font-weight="700" fill="#334155">Legend</text>'
        )

        for index, category_name in enumerate(CATEGORY_ORDER):
            legend_row_y = legend_y + 24 + index * 24
            c2_visit_map_svg.append(
                f'<circle cx="{legend_x}" cy="{legend_row_y}" r="7" '
                f'fill="{CATEGORY_COLORS[category_name]}" '
                f'stroke="{CATEGORY_STROKES[category_name]}" stroke-width="1.5"/>'
            )
            c2_visit_map_svg.append(
                f'<text x="{legend_x + 16}" y="{legend_row_y + 4}" font-size="12" '
                f'fill="#475569">{category_name}</text>'
            )

        c2_visit_map_svg.append(
            f'<text x="{legend_x}" y="{legend_y + 126}" font-size="11" '
            'fill="#6b7280">circle size = repeated visits</text>'
        )

        if not c2_filtered_visits:
            c2_visit_map_svg.append(
                f'<text x="{map_width / 2:.1f}" y="{map_height / 2:.1f}" '
                'text-anchor="middle" font-size="20" fill="#6b7280">'
                "No visit records after current filters</text>"
            )
        return c2_visit_map_svg.append("</svg>")
        c2_visit_map_svg = "".join(c2_visit_map_svg)


    _()
    return


@app.cell
def _(c2_visit_map_svg, mo):
    mo.Html(c2_visit_map_svg)
    return


@app.cell
def _(
    CATEGORY_COLORS,
    CATEGORY_ORDER,
    CATEGORY_STROKES,
    c2_member_label,
    c2_selected_source,
    c2_summary_labels,
    c2_summary_values,
    c2_trip_records,
    escape,
    math,
):
    width = 980
    height = 620
    trip_center_x = 690
    trip_center_y = 330
    trip_outer_radius = 170
    trip_inner_radius = 70

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

    c2_trip_summary_svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">'
    ]
    c2_trip_summary_svg.append(
        f'<rect x="0" y="0" width="{width}" height="{height}" '
        'fill="#fbfaf7" rx="20" ry="20"/>'
    )
    c2_trip_summary_svg.append(
        '<text x="36" y="42" font-size="28" font-weight="700" '
        'fill="#203040">Trip-time summary</text>'
    )
    c2_trip_summary_svg.append(
        f'<text x="36" y="68" font-size="14" fill="#5f6b76">Source: '
        f'{escape(c2_selected_source)} | Filter: {escape(c2_member_label)}</text>'
    )
    c2_trip_summary_svg.append(
        '<text x="36" y="90" font-size="13" fill="#6d6d6d">'
        "Left: overall time split. Right: each member-trip shown as a clockwise "
        "wedge.</text>"
    )

    pie_center_x = 220
    pie_center_y = 330
    pie_outer = 120
    pie_inner = 58
    total_sum = sum(c2_summary_values)
    current_angle = 0.0

    for label, value in zip(c2_summary_labels, c2_summary_values):
        width_angle = 360.0 * value / total_sum
        path = arc_wedge_path(
            pie_center_x,
            pie_center_y,
            pie_outer,
            pie_inner,
            current_angle,
            current_angle + width_angle,
        )
        c2_trip_summary_svg.append(
            f'<path d="{path}" fill="{CATEGORY_COLORS[label]}" '
            'stroke="white" stroke-width="2"/>'
        )

        mid_angle = current_angle + width_angle / 2.0
        label_x, label_y = polar_point(pie_center_x, pie_center_y, 145, mid_angle)
        pct = 100.0 * value / total_sum
        c2_trip_summary_svg.append(
            f'<text x="{label_x:.1f}" y="{label_y:.1f}" font-size="12" '
            f'text-anchor="middle" fill="#334155">{label}</text>'
        )
        c2_trip_summary_svg.append(
            f'<text x="{label_x:.1f}" y="{label_y + 15:.1f}" font-size="11" '
            f'text-anchor="middle" fill="#64748b">{pct:.0f}%</text>'
        )
        current_angle += width_angle

    c2_trip_summary_svg.append(
        f'<text x="{pie_center_x}" y="{pie_center_y - 6}" font-size="16" '
        'font-weight="700" text-anchor="middle" fill="#334155">total</text>'
    )
    c2_trip_summary_svg.append(
        f'<text x="{pie_center_x}" y="{pie_center_y + 16}" font-size="13" '
        'text-anchor="middle" fill="#64748b">allocated hours</text>'
    )

    trip_total_hours = sum(record["hours"] for record in c2_trip_records) or 1.0
    ring_angle = 0.0
    for record in c2_trip_records:
        width_angle = max(record["hours"] / trip_total_hours * 360.0, 2.0)
        path = arc_wedge_path(
            trip_center_x,
            trip_center_y,
            trip_outer_radius,
            trip_inner_radius,
            ring_angle,
            ring_angle + width_angle,
        )
        fill_color = CATEGORY_COLORS.get(record["category"], CATEGORY_COLORS["Neutral"])
        hover_title = escape(
            f'{record["trip_id"]}\n'
            f'Member: {record["member"]}\n'
            f'Date: {record["date"]}\n'
            f'Hours: {record["hours"]:.2f}\n'
            f'Category: {record["category"]}\n'
            f'Places: {record["places"]}'
        )
        c2_trip_summary_svg.append(
            f'<path d="{path}" fill="{fill_color}" fill-opacity="0.88" '
            'stroke="white" stroke-width="2">'
            f"<title>{hover_title}</title></path>"
        )

        if width_angle >= 12:
            mid_angle = ring_angle + width_angle / 2.0
            text_x, text_y = polar_point(
                trip_center_x,
                trip_center_y,
                (trip_outer_radius + trip_inner_radius) / 2.0,
                mid_angle,
            )
            c2_trip_summary_svg.append(
                f'<text x="{text_x:.1f}" y="{text_y:.1f}" font-size="10" '
                'text-anchor="middle" fill="white">'
                f'{escape(record["trip_id"])}</text>'
            )
        ring_angle += width_angle

    c2_trip_summary_svg.append(
        f'<circle cx="{trip_center_x}" cy="{trip_center_y}" '
        f'r="{trip_inner_radius - 8}" fill="#fbfaf7" stroke="#e5ded1" '
        'stroke-width="1.5"/>'
    )
    c2_trip_summary_svg.append(
        f'<text x="{trip_center_x}" y="{trip_center_y - 5}" font-size="16" '
        'font-weight="700" text-anchor="middle" fill="#334155">member-</text>'
    )
    c2_trip_summary_svg.append(
        f'<text x="{trip_center_x}" y="{trip_center_y + 15}" font-size="16" '
        'font-weight="700" text-anchor="middle" fill="#334155">trips</text>'
    )

    legend_x = 835
    legend_y = 150
    c2_trip_summary_svg.append(
        f'<rect x="{legend_x - 20}" y="{legend_y - 30}" width="145" height="140" '
        'rx="12" ry="12" fill="white" opacity="0.92" stroke="#d7d2c8"/>'
    )
    c2_trip_summary_svg.append(
        f'<text x="{legend_x}" y="{legend_y - 8}" font-size="14" '
        'font-weight="700" fill="#334155">Legend</text>'
    )

    for index, category_name in enumerate(CATEGORY_ORDER):
        legend_row_y = legend_y + 20 + index * 24
        c2_trip_summary_svg.append(
            f'<circle cx="{legend_x}" cy="{legend_row_y}" r="7" '
            f'fill="{CATEGORY_COLORS[category_name]}" '
            f'stroke="{CATEGORY_STROKES[category_name]}" stroke-width="1.5"/>'
        )
        c2_trip_summary_svg.append(
            f'<text x="{legend_x + 16}" y="{legend_row_y + 4}" font-size="12" '
            f'fill="#475569">{category_name}</text>'
        )

    c2_trip_summary_svg.append(
        '<text x="36" y="586" font-size="11" fill="#6b7280">'
        "Each wedge on the right is one member-trip ordered clockwise by trip start "
        "time.</text>"
    )

    if not c2_trip_records:
        c2_trip_summary_svg.append(
            f'<text x="{width / 2:.1f}" y="{height / 2:.1f}" '
            'text-anchor="middle" font-size="22" fill="#6b7280">'
            "No trip data after current filters</text>"
        )

    c2_trip_summary_svg.append("</svg>")
    c2_trip_summary_svg = "".join(c2_trip_summary_svg)
    return (c2_trip_summary_svg,)


@app.cell
def _(c2_trip_summary_svg, mo):
    mo.Html(c2_trip_summary_svg)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Notes

    - Topic labels come from `plan_topics.csv` and `travel_links.csv`.
    - Filtering happens before the SVG rendering cells run.
    - Trip time is allocated between consecutive timestamps in `trip_places.csv`.
    - The last recorded stop receives any remaining time up to the trip end.
    """)
    return


if __name__ == "__main__":
    app.run()
