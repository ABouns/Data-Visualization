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


@app.cell
def _():
    print("imports ok")
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
        FISHING_KEYWORDS,
        FISHING_TOPICS,
        HYBRID_TOPICS,
        SOURCE_NAMES,
        TOURISM_KEYWORDS,
        TOURISM_TOPICS,
        ZONE_COLORS,
    )


@app.cell
def _(CATEGORY_ORDER, DEFAULT_ROOT, SOURCE_NAMES):
    print(DEFAULT_ROOT)
    print(SOURCE_NAMES)
    print(CATEGORY_ORDER)
    return


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
    math,
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
    return (
        classify_topic,
        dominant_category,
        dominant_time_category,
        infer_place_category,
        normalize_year,
        parse_stamp,
        read_rows,
        summarize_category_hours,
    )


@app.cell
def _(classify_topic, normalize_year):
    print(normalize_year("0040-04-06"))
    print(classify_topic("deep_fishing_dock"))
    print(classify_topic("expanding_tourist_wharf"))
    print(classify_topic("seafood_festival"))
    return


@app.cell
def _(
    classify_topic,
    defaultdict,
    dominant_category,
    infer_place_category,
    normalize_year,
    parse_stamp,
    read_rows,
    timedelta,
):
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

    return (load_source,)


@app.cell
def _(DEFAULT_ROOT, load_source):
    journalist = load_source(DEFAULT_ROOT, "Journalist")
    print(journalist["name"])
    print(len(journalist["people_names"]))
    print(len(journalist["places"]))
    print(len(journalist["visit_rows"]))
    return


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

    print(source_data.keys())
    print(len(all_members))
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

    mo.vstack([
          source_widget,
          member_widget,
          neutral_widget,
      ])
    return member_widget, neutral_widget, source_widget


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

    print("source:", c2_selected_source)
    print("members:", c2_member_label)
    print("rows:", len(c2_filtered_visits))
    return (
        c2_filtered_visits,
        c2_include_neutral,
        c2_member_label,
        c2_selected_source,
    )


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
    mo,
    source_data,
):
    c2_map_width = 980
    c2_map_height = 620
    c2_margin = 70

    c2_all_places = source_data[c2_selected_source]["places"]

    c2_x_min = min(place["x"] for place in c2_all_places)
    c2_x_max = max(place["x"] for place in c2_all_places)
    c2_y_min = min(place["y"] for place in c2_all_places)
    c2_y_max = max(place["y"] for place in c2_all_places)


    def c2_to_screen(x_value, y_value):
        if c2_x_max == c2_x_min:
            screen_x = c2_map_width / 2
        else:
            screen_x = c2_margin + (
                (x_value - c2_x_min) / (c2_x_max - c2_x_min)
            ) * (c2_map_width - 2 * c2_margin)

        if c2_y_max == c2_y_min:
            screen_y = c2_map_height / 2
        else:
            screen_y = c2_map_height - c2_margin - (
                (y_value - c2_y_min) / (c2_y_max - c2_y_min)
            ) * (c2_map_height - 2 * c2_margin)

        return screen_x, screen_y


    c2_grouped_places = {}

    for row in c2_filtered_visits:
        place_id = str(row["place_id"])

        if place_id not in c2_grouped_places:
            c2_grouped_places[place_id] = {
                "name": row["name"],
                "x": row["x"],
                "y": row["y"],
                "zone": row["zone"],
                "category": row["category"],
                "visits": 0,
                "hours": 0.0,
                "members": set(),
                "trips": set(),
            }

        c2_grouped_places[place_id]["visits"] += 1
        c2_grouped_places[place_id]["hours"] += float(row["duration_hours"])
        c2_grouped_places[place_id]["members"].add(row["member"])
        c2_grouped_places[place_id]["trips"].add(row["trip_id"])


    c2_member_label_short = c2_member_label
    if len(c2_member_label_short) > 80:
        c2_member_label_short = c2_member_label_short[:77] + "..."


    c2_svg_parts = []
    c2_svg_parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{c2_map_width}" height="{c2_map_height}" viewBox="0 0 {c2_map_width} {c2_map_height}">'
    )
    c2_svg_parts.append(
        f'<rect x="0" y="0" width="{c2_map_width}" height="{c2_map_height}" fill="#faf7f2" rx="18" ry="18"/>'
    )

    c2_svg_parts.append(
        '<text x="36" y="42" font-size="28" font-weight="700" fill="#203040">Board visit map</text>'
    )
    c2_svg_parts.append(
        f'<text x="36" y="68" font-size="14" fill="#5f6b76">Source: {escape(c2_selected_source)} | Filter: {escape(c2_member_label_short)}</text>'
    )
    c2_svg_parts.append(
        '<text x="36" y="90" font-size="13" fill="#6d6d6d">Faint dots show all known places. Larger colored circles show repeated filtered member-visits.</text>'
    )

    for place in c2_all_places:
        c2_sx, c2_sy = c2_to_screen(place["x"], place["y"])
        c2_zone_fill = ZONE_COLORS.get(place["zone"], ZONE_COLORS["unknown"])
        c2_title = escape(
            f'{place["name"]}\nZone: {place["zone"]}\nCategory guess: {place["category"]}'
        )
        c2_svg_parts.append(
            f'<circle cx="{c2_sx:.1f}" cy="{c2_sy:.1f}" r="3.5" fill="{c2_zone_fill}" opacity="0.25"><title>{c2_title}</title></circle>'
        )

    for category in CATEGORY_ORDER:
        c2_rows = [
            row for row in c2_grouped_places.values()
            if row["category"] == category
        ]

        for row in sorted(c2_rows, key=lambda item: item["visits"]):
            c2_sx, c2_sy = c2_to_screen(row["x"], row["y"])
            c2_radius = 6 + math.sqrt(row["visits"]) * 3.0
            c2_fill = CATEGORY_COLORS[category]
            c2_stroke = CATEGORY_STROKES[category]
            c2_opacity = "0.88" if category != "Neutral" else "0.48"
            c2_members_text = ", ".join(sorted(row["members"]))

            c2_title = escape(
                f'{row["name"]}\n'
                f'Category: {category}\n'
                f'Member-visits: {row["visits"]}\n'
                f'Trips touching this place: {len(row["trips"])}\n'
                f'Allocated hours: {row["hours"]:.2f}\n'
                f'Zone: {row["zone"]}\n'
                f'Members: {c2_members_text}'
            )

            c2_svg_parts.append(
                f'<circle cx="{c2_sx:.1f}" cy="{c2_sy:.1f}" r="{c2_radius:.1f}" fill="{c2_fill}" fill-opacity="{c2_opacity}" stroke="{c2_stroke}" stroke-width="2"><title>{c2_title}</title></circle>'
            )

            if row["visits"] >= 4:
                c2_label = row["name"]
                if len(c2_label) > 18:
                    c2_label = c2_label[:15] + "..."
                c2_svg_parts.append(
                    f'<text x="{c2_sx:.1f}" y="{c2_sy - c2_radius - 8:.1f}" font-size="11" text-anchor="middle" fill="#334155">{escape(c2_label)}</text>'
                )

    c2_legend_x = c2_map_width - 190
    c2_legend_y = 120

    c2_svg_parts.append(
        f'<rect x="{c2_legend_x - 18}" y="{c2_legend_y - 28}" width="170" height="150" rx="12" ry="12" fill="white" opacity="0.92" stroke="#d7d2c8"/>'
    )
    c2_svg_parts.append(
        f'<text x="{c2_legend_x}" y="{c2_legend_y - 6}" font-size="14" font-weight="700" fill="#334155">Legend</text>'
    )

    for idx, category in enumerate(CATEGORY_ORDER):
        y = c2_legend_y + 24 + idx * 24
        c2_svg_parts.append(
            f'<circle cx="{c2_legend_x}" cy="{y}" r="7" fill="{CATEGORY_COLORS[category]}" stroke="{CATEGORY_STROKES[category]}" stroke-width="1.5"/>'
        )
        c2_svg_parts.append(
            f'<text x="{c2_legend_x + 16}" y="{y + 4}" font-size="12" fill="#475569">{category}</text>'
        )

    c2_svg_parts.append(
        f'<text x="{c2_legend_x}" y="{c2_legend_y + 126}" font-size="11" fill="#6b7280">circle size = repeated visits</text>'
    )

    if not c2_filtered_visits:
        c2_svg_parts.append(
            f'<text x="{c2_map_width / 2:.1f}" y="{c2_map_height / 2:.1f}" text-anchor="middle" font-size="20" fill="#6b7280">No visit records after current filters</text>'
        )

    c2_svg_parts.append("</svg>")

    c2_visit_map_svg = "".join(c2_svg_parts)

    mo.Html(c2_visit_map_svg)

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
    mo,
    summarize_category_hours,
):
    c2_trip_summary_width = 980
    c2_trip_summary_height = 620
    c2_trip_center_x = 690
    c2_trip_center_y = 330
    c2_trip_outer_radius = 170
    c2_trip_inner_radius = 70

    c2_total_hours = summarize_category_hours(c2_filtered_visits)

    c2_summary_labels = [
        category
        for category in CATEGORY_ORDER
        if c2_total_hours.get(category, 0.0) > 0 and (c2_include_neutral or category != "Neutral")
    ]

    if not c2_summary_labels:
        c2_summary_labels = ["Neutral"]

    c2_summary_values = [c2_total_hours.get(category, 0.0) for category in c2_summary_labels]
    if sum(c2_summary_values) <= 0:
        c2_summary_values = [1.0 for _ in c2_summary_labels]

    c2_trip_rollup = {}

    for row in c2_filtered_visits:
        c2_key = (str(row["member"]), str(row["trip_id"]))

        if c2_key not in c2_trip_rollup:
            c2_trip_rollup[c2_key] = {
                "member": row["member"],
                "trip_id": row["trip_id"],
                "date": row["date"],
                "start_dt": row["start_dt"],
                "hours": 0.0,
                "category_hours": defaultdict(float),
                "places": set(),
            }

        c2_trip_rollup[c2_key]["hours"] += float(row["duration_hours"])
        c2_trip_rollup[c2_key]["category_hours"][str(row["category"])] += float(row["duration_hours"])
        c2_trip_rollup[c2_key]["places"].add(str(row["name"]))

    c2_trip_records = []
    for record in c2_trip_rollup.values():
        c2_trip_records.append(
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

    c2_trip_records.sort(key=lambda item: (item["start_dt"], item["member"], item["trip_id"]))


    def c2_polar_point(cx, cy, radius, angle_deg):
        angle_rad = math.radians(angle_deg - 90)
        return (
            cx + radius * math.cos(angle_rad),
            cy + radius * math.sin(angle_rad),
        )


    def c2_arc_wedge_path(cx, cy, r_outer, r_inner, start_angle, end_angle):
        x1, y1 = c2_polar_point(cx, cy, r_outer, start_angle)
        x2, y2 = c2_polar_point(cx, cy, r_outer, end_angle)
        x3, y3 = c2_polar_point(cx, cy, r_inner, end_angle)
        x4, y4 = c2_polar_point(cx, cy, r_inner, start_angle)

        large_arc = 1 if (end_angle - start_angle) > 180 else 0

        return (
            f"M {x1:.2f} {y1:.2f} "
            f"A {r_outer:.2f} {r_outer:.2f} 0 {large_arc} 1 {x2:.2f} {y2:.2f} "
            f"L {x3:.2f} {y3:.2f} "
            f"A {r_inner:.2f} {r_inner:.2f} 0 {large_arc} 0 {x4:.2f} {y4:.2f} Z"
        )


    c2_trip_svg = []
    c2_trip_svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{c2_trip_summary_width}" height="{c2_trip_summary_height}" viewBox="0 0 {c2_trip_summary_width} {c2_trip_summary_height}">'
    )
    c2_trip_svg.append(
        f'<rect x="0" y="0" width="{c2_trip_summary_width}" height="{c2_trip_summary_height}" fill="#fbfaf7" rx="20" ry="20"/>'
    )

    c2_trip_svg.append(
        '<text x="36" y="42" font-size="28" font-weight="700" fill="#203040">Trip-time summary</text>'
    )
    c2_trip_svg.append(
        f'<text x="36" y="68" font-size="14" fill="#5f6b76">Source: {escape(c2_selected_source)} | Filter: {escape(c2_member_label)}</text>'
    )
    c2_trip_svg.append(
        '<text x="36" y="90" font-size="13" fill="#6d6d6d">Left: overall time split. Right: each member-trip shown as a clockwise wedge.</text>'
    )

    c2_pie_center_x = 220
    c2_pie_center_y = 330
    c2_pie_outer = 120
    c2_pie_inner = 58

    c2_total_sum = sum(c2_summary_values)
    c2_angle = 0.0

    for label, value in zip(c2_summary_labels, c2_summary_values):
        c2_width = 360.0 * value / c2_total_sum
        c2_path = c2_arc_wedge_path(
            c2_pie_center_x,
            c2_pie_center_y,
            c2_pie_outer,
            c2_pie_inner,
            c2_angle,
            c2_angle + c2_width,
        )
        c2_trip_svg.append(
            f'<path d="{c2_path}" fill="{CATEGORY_COLORS[label]}" stroke="white" stroke-width="2"/>'
        )

        c2_mid = c2_angle + c2_width / 2.0
        c2_label_x, c2_label_y = c2_polar_point(c2_pie_center_x, c2_pie_center_y, 145, c2_mid)
        c2_pct = 100.0 * value / c2_total_sum
        c2_trip_svg.append(
            f'<text x="{c2_label_x:.1f}" y="{c2_label_y:.1f}" font-size="12" text-anchor="middle" fill="#334155">{label}</text>'
        )
        c2_trip_svg.append(
            f'<text x="{c2_label_x:.1f}" y="{c2_label_y + 15:.1f}" font-size="11" text-anchor="middle" fill="#64748b">{c2_pct:.0f}%</text>'
        )

        c2_angle += c2_width

    c2_trip_svg.append(
        f'<text x="{c2_pie_center_x}" y="{c2_pie_center_y - 6}" font-size="16" font-weight="700" text-anchor="middle" fill="#334155">total</text>'
    )
    c2_trip_svg.append(
        f'<text x="{c2_pie_center_x}" y="{c2_pie_center_y + 16}" font-size="13" text-anchor="middle" fill="#64748b">allocated hours</text>'
    )

    c2_trip_total_hours = sum(record["hours"] for record in c2_trip_records) or 1.0
    c2_ring_angle = 0.0

    for record in c2_trip_records:
        c2_width = max(record["hours"] / c2_trip_total_hours * 360.0, 2.0)
        c2_path = c2_arc_wedge_path(
            c2_trip_center_x,
            c2_trip_center_y,
            c2_trip_outer_radius,
            c2_trip_inner_radius,
            c2_ring_angle,
            c2_ring_angle + c2_width,
        )

        c2_fill = CATEGORY_COLORS.get(record["category"], CATEGORY_COLORS["Neutral"])
        c2_title = escape(
            f'{record["trip_id"]}\n'
            f'Member: {record["member"]}\n'
            f'Date: {record["date"]}\n'
            f'Hours: {record["hours"]:.2f}\n'
            f'Category: {record["category"]}\n'
            f'Places: {record["places"]}'
        )

        c2_trip_svg.append(
            f'<path d="{c2_path}" fill="{c2_fill}" fill-opacity="0.88" stroke="white" stroke-width="2"><title>{c2_title}</title></path>'
        )

        if c2_width >= 12:
            c2_mid = c2_ring_angle + c2_width / 2.0
            c2_text_x, c2_text_y = c2_polar_point(
                c2_trip_center_x,
                c2_trip_center_y,
                (c2_trip_outer_radius + c2_trip_inner_radius) / 2.0,
                c2_mid,
            )
            c2_short = record["trip_id"]
            c2_trip_svg.append(
                f'<text x="{c2_text_x:.1f}" y="{c2_text_y:.1f}" font-size="10" text-anchor="middle" fill="white">{escape(c2_short)}</text>'
            )

        c2_ring_angle += c2_width

    c2_trip_svg.append(
        f'<circle cx="{c2_trip_center_x}" cy="{c2_trip_center_y}" r="{c2_trip_inner_radius - 8}" fill="#fbfaf7" stroke="#e5ded1" stroke-width="1.5"/>'
    )
    c2_trip_svg.append(
        f'<text x="{c2_trip_center_x}" y="{c2_trip_center_y - 5}" font-size="16" font-weight="700" text-anchor="middle" fill="#334155">member-</text>'
    )
    c2_trip_svg.append(
        f'<text x="{c2_trip_center_x}" y="{c2_trip_center_y + 15}" font-size="16" font-weight="700" text-anchor="middle" fill="#334155">trips</text>'
    )

    c2_leg_x = 835
    c2_leg_y = 150
    c2_trip_svg.append(
        f'<rect x="{c2_leg_x - 20}" y="{c2_leg_y - 30}" width="145" height="140" rx="12" ry="12" fill="white" opacity="0.92" stroke="#d7d2c8"/>'
    )
    c2_trip_svg.append(
        f'<text x="{c2_leg_x}" y="{c2_leg_y - 8}" font-size="14" font-weight="700" fill="#334155">Legend</text>'
    )

    for idx, category in enumerate(CATEGORY_ORDER):
        y = c2_leg_y + 20 + idx * 24
        c2_trip_svg.append(
            f'<circle cx="{c2_leg_x}" cy="{y}" r="7" fill="{CATEGORY_COLORS[category]}" stroke="{CATEGORY_STROKES[category]}" stroke-width="1.5"/>'
        )
        c2_trip_svg.append(
            f'<text x="{c2_leg_x + 16}" y="{y + 4}" font-size="12" fill="#475569">{category}</text>'
        )

    c2_trip_note = (
        "Each wedge on the right is one member-trip ordered clockwise by trip start time."
    )
    c2_trip_svg.append(
        f'<text x="36" y="586" font-size="11" fill="#6b7280">{escape(c2_trip_note)}</text>'
    )

    if not c2_trip_records:
        c2_trip_svg.append(
            f'<text x="{c2_trip_summary_width / 2:.1f}" y="{c2_trip_summary_height / 2:.1f}" text-anchor="middle" font-size="22" fill="#6b7280">No trip data after current filters</text>'
        )

    c2_trip_svg.append("</svg>")

    c2_trip_summary_svg = "".join(c2_trip_svg)

    mo.Html(c2_trip_summary_svg)

    return


if __name__ == "__main__":
    app.run()
