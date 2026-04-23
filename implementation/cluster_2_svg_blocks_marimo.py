import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    from sklearn.neighbors import BallTree

    return BallTree, mo, np, pd


@app.cell
def _(BallTree, np, pd):

    def classify_weighted_knn(df, k=5, max_radius_km=1.0, epsilon=0.001):
        # 1. Split data
        df_comm = df[df['zone'].isin(['commercial', 'residential'])].reset_index(drop=True)
        df_targets = df[df['zone'].isin(['tourism', 'industrial'])].reset_index(drop=True)
    
        if df_comm.empty or df_targets.empty:
            return pd.DataFrame()

        # 2. Build Tree and Query
        comm_rad = np.radians(df_comm[['lat', 'lon']])
        target_rad = np.radians(df_targets[['lat', 'lon']])
        tree = BallTree(target_rad, metric='haversine')
    
        earth_radius_km = 6371.0
        radius_rad = max_radius_km / earth_radius_km
        distances, indices = tree.query(comm_rad, k=k, return_distance=True)
    
        # 3. Collect Valid Neighbors and Calculate Inverse Distance Weight
        results = []
        for i, (dist_array, idx_array) in enumerate(zip(distances, indices)):
            for dist, idx in zip(dist_array, idx_array):
                if dist <= radius_rad:
                    dist_km = dist * earth_radius_km
                    weight = 1.0 / (dist_km + epsilon) # Add epsilon to avoid zero division
                
                    results.append({
                        'commercial_id': df_comm.iloc[i]['place_id'],
                        'target_zone': df_targets.iloc[idx]['zone'],
                        'weight': weight
                    })
                
        df_neighbors = pd.DataFrame(results)
        if df_neighbors.empty:
            return pd.DataFrame(columns=['commercial_id', 'predicted_zone', 'weighted_score'])

        # 4. Sum the weights grouped by commercial_id and target_zone
        weighted_scores = (df_neighbors.groupby(['commercial_id', 'target_zone'])['weight']
                                       .sum()
                                       .reset_index(name='weighted_score'))
    
        # 5. Sort by highest weighted score to determine majority
        df_majority = (weighted_scores.sort_values(['commercial_id', 'weighted_score'], ascending=[True, False])
                                      .drop_duplicates(subset=['commercial_id'], keep='first')
                                      .rename(columns={'target_zone': 'predicted_zone'}))
                              
        return df_majority.reset_index(drop=True)

    return (classify_weighted_knn,)


@app.cell
def _(mo, pd):
    # places_edited = duckdb.sql("""
    #     select place_id, 
    #            case when zone = 'residential' and name = 'Paakland Elementary' then 'tourism'
    #                 when zone = 'residential' and name in ('Waveside Townhomes', 'Tidewater Flats') then 'industrial'
    #                 when name = 'Tropics Environmental Hub' then 'tourism'
    #                 else zone end as zone, lat, lon
    #     from database_jour.places
    # """).to_df()

    # places_edited.to_json("places_edited.json", index=False)

    try:
        places_edited = pd.read_json(str(mo.notebook_location() / "data" / "places_edited.json"))
    except:
        places_edited = pd.read_json("https://raw.githubusercontent.com/tvakul/dataviz1/refs/heads/main/data/places_edited.json")
    places_edited
    return (places_edited,)


@app.cell
def _(
    classify_weighted_knn,
    knn_dist_slider,
    knn_num_slider,
    pd,
    places_edited,
):
    remapped_location = pd.concat([places_edited.loc[places_edited['zone'].isin(['industrial', 'tourism'])],
    classify_weighted_knn(places_edited, max_radius_km=knn_dist_slider.value, k=knn_num_slider.value).rename(
        columns={'predicted_zone': 'zone', 'commercial_id': 'place_id'}
    )
    ], ignore_index=True).drop_duplicates(subset=['place_id'], keep='first')[['place_id', 'zone']]

    remapped_location
    return (remapped_location,)


@app.cell(hide_code=True)
def _(mo, pd):
    # time_trip_spend = duckdb.sql("\""
    #     select a.*, b.*, c.*, d.people_id 
    #     from 
    #       database_jour.trips a,
    #      database_jour.trip_places b,
    #         database_jour.places c,
    #         database_jour.trip_people d
    #         where a.trip_id = b.trip_id and b.place_id = c.place_id and a.trip_id = d.trip_id
    #     order by a.trip_id, time
    # "\"").to_df()

    # # Create index column by trip_id and time
    # time_trip_spend["index"] = time_trip_spend.groupby("trip_id").cumcount()
    # time_trip_spend["index_lead"] = time_trip_spend.groupby("trip_id")["index"].shift(-1).fillna(9999).astype(int)

    # # Convert start_time, end_time, time to datetime
    # time_trip_spend["date"] = time_trip_spend["date"].str.replace("0040","2040")
    # time_trip_spend["start_time"] = pd.to_datetime(time_trip_spend["date"] + " " + time_trip_spend["start_time"])
    # time_trip_spend["end_time"] = pd.to_datetime(time_trip_spend["date"] + " " + time_trip_spend["end_time"])
    # time_trip_spend["time"] = pd.to_datetime(time_trip_spend["time"].str.replace("0040","2040"))
    # time_trip_spend["time_lead"] = time_trip_spend.groupby("trip_id")["time"].shift(-1).fillna(time_trip_spend["time"])

    # #  1. Shift to get adjacent location times
    # time_trip_spend["time_prev"] = time_trip_spend.groupby("trip_id")["time"].shift(1)
    # time_trip_spend["time_lead"] = time_trip_spend.groupby("trip_id")["time"].shift(-1)

    # # 2. Calculate the bounding time intervals
    # # Divided by 2 for the shared transit times
    # gap_start = time_trip_spend["time"] - time_trip_spend["start_time"]
    # gap_prev = (time_trip_spend["time"] - time_trip_spend["time_prev"]) / 2

    # gap_end = time_trip_spend["end_time"] - time_trip_spend["time"]
    # gap_lead = (time_trip_spend["time_lead"] - time_trip_spend["time"]) / 2

    # # Handle overnight boundary for the end gap if your times cross midnight
    # gap_end = gap_end.mask(gap_end < pd.Timedelta(0), gap_end + pd.Timedelta(days=1))

    # # 3. Allocate the time halves
    # # If gap_prev is NaT (first row), it falls back to the full gap_start
    # time_trip_spend["half_before"] = gap_prev.fillna(gap_start)

    # # If gap_lead is NaT (last row), it falls back to the full gap_end
    # time_trip_spend["half_after"] = gap_lead.fillna(gap_end)

    # # 4. Final Calculation
    # time_trip_spend["time_spend"] = time_trip_spend["half_before"] + time_trip_spend["half_after"]

    # # Clean up intermediate columns
    # time_trip_spend = time_trip_spend.drop(columns=["time_prev", "time_lead", "half_before", "half_after"])
    # time_trip_spend[["trip_id", "people_id", "place_id", "name", "time", "time_spend", "zone", "zone_detail"]]


    _dtypes_tts = {
        "trip_id": "object",
        "date": "object",
        "start_time": "datetime64[ns]",
        "end_time": "datetime64[ns]",
        "trip_id_1": "object",
        "place_id": "object",
        "time": "datetime64[ns]",
        "place_id_1": "object",
        "name": "object",
        "lat": "float64",
        "lon": "float64",
        "zone": "object",
        "zone_detail": "object",
        "people_id": "object",
        "index": "int64",
        "index_lead": "int64",
        "time_spend": "timedelta64[ns]"
    }
    try:
        time_trip_spend = pd.read_json(str(mo.notebook_location() / "data" / "time_trip_spend.json"), dtype=_dtypes_tts)
    except:
        time_trip_spend = pd.read_json("https://raw.githubusercontent.com/tvakul/dataviz1/refs/heads/main/data/time_trip_spend.json", dtype=_dtypes_tts)
    time_trip_spend
    return (time_trip_spend,)


@app.cell
def _(pd, remapped_location, time_trip_spend):
    time_location_remapped = pd.merge(time_trip_spend[["trip_id", "date", "people_id", "place_id", "name", "time", "time_spend", "zone", 'lat', 'lon']], remapped_location.rename(columns={"zone": "zone_remapped"}),
                on="place_id", how="left").fillna({"zone_remapped": "other"})
    time_location_remapped
    return (time_location_remapped,)


@app.cell(hide_code=True)
def _(time_location_remapped):
    # Group by people_id and zone_remapped to calculate total visits by trip_id and place_id
    _tmp = time_location_remapped.copy()
    _tmp['visit_id'] = _tmp['trip_id'].astype(str) + '_' + _tmp['place_id'].astype(str) + '_' + _tmp['place_id'].astype(str)
    people_zone_summary = _tmp.groupby(['people_id', 'zone_remapped']).agg(
        total_visits=('visit_id', 'nunique'),   
    ).reset_index()

    people_zone_summary = people_zone_summary[people_zone_summary['zone_remapped'].isin(['industrial', 'tourism'])]


    people_zone_summary_delta = people_zone_summary.pivot(index='people_id', columns='zone_remapped', values='total_visits').fillna(0).reset_index()
    people_zone_summary_delta['delta'] = people_zone_summary_delta['industrial'] - people_zone_summary_delta['tourism']
    people_zone_summary_delta.sort_values('delta', ascending=False)
    return (people_zone_summary_delta,)


@app.cell
def _(pd, time_location_remapped):
    people_timespend_summary = time_location_remapped.groupby(["people_id", "zone_remapped"]).agg({"time_spend": "sum", "trip_id": "nunique"}).reset_index()

    # Filter out zone_remapped = 'other'
    people_timespend_summary_filtered = people_timespend_summary[people_timespend_summary['zone_remapped'].isin(['industrial', 'tourism'])].copy()

    # Get the delta time spend between different zones for each people_id
    delta_time_spend = people_timespend_summary_filtered.pivot(index='people_id', columns='zone_remapped', values='time_spend').fillna(pd.Timedelta(0))
    delta_time_spend['delta'] = delta_time_spend.get('industrial', pd.Timedelta(0)) - delta_time_spend.get('tourism', pd.Timedelta(0))

    delta_time_spend
    return (people_timespend_summary_filtered,)


@app.cell
def _(mo):
    knn_dist_slider = mo.ui.slider(start=0, stop=5, step=0.1, value = 1.5, show_value=True)
    knn_num_slider = mo.ui.slider(start=0, stop=10, step=1, value = 5, show_value=True)
    mode_dropdown = mo.ui.dropdown(options=['time_spend', 'visits'], value='visits')
    mo.vstack([
        mo.hstack([
            mo.md("Remapper: max distance limit for reference (in km)"),
            knn_dist_slider
        ], align="start", justify="start"),
        mo.hstack([
            mo.md("Remapper: number of nearnest reference locations"),
            knn_num_slider
        ], align="start", justify="start") ,
        mo.hstack([
            mo.md("Comparison mode"),
            mode_dropdown,
        ], align="start", justify="start")     
    ])


    return knn_dist_slider, knn_num_slider, mode_dropdown


@app.cell
def _(time_location_remapped):
    time_location_remappd2 = time_location_remapped.copy();
    time_location_remappd2.groupby(['people_id', 'lat', 'lon', 'trip_id']).agg({'time_spend': 'sum'}).reset_index().rename(columns={'place_id': 'time_spend'})
    return


@app.cell
def _(
    mode_dropdown,
    people_timespend_summary_filtered,
    people_zone_summary_delta,
    time_location_remapped,
):
    if mode_dropdown.value == 'visits':
        graph_2_1_data = people_zone_summary_delta
        graph_2_2_data = time_location_remapped.groupby(['people_id', 'date', 'zone_remapped', 'trip_id']).agg({'place_id': 'count'}).reset_index().rename(columns={'place_id': 'num_visits'})
    else:
        graph_2_1_data = people_timespend_summary_filtered
        graph_2_2_data = time_location_remapped.groupby(['people_id', 'date', 'zone_remapped', 'trip_id']).agg({'time_spend': 'sum'}).reset_index().rename(columns={'place_id': 'time_spend'})
    return


@app.cell
def _(graph_2_3_data):
    graph_2_3_data
    return

# Interactive Cluster 2 SVG cells build on the exact Graph 2 preprocessing above.


@app.cell
def _(time_location_remapped):
    graph_2_3_data = (
        time_location_remapped.copy()
        .groupby(['people_id', 'lat', 'lon', 'trip_id'])
        .agg({'time_spend': 'sum'})
        .reset_index()
    )
    return (graph_2_3_data,)


@app.cell
def _():
    import json
    import math
    from collections import defaultdict
    from html import escape
    from pathlib import Path

    return Path, defaultdict, escape, json, math


@app.cell
def _(math):
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
        "other": "#d9d9d9",
        "unknown": "#d9d9d9",
    }

    def category_from_zone(zone):
        zone = str(zone or "").strip().lower()
        if zone == "tourism":
            return "Tourism"
        if zone == "industrial":
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
        CATEGORY_COLORS,
        CATEGORY_ORDER,
        CATEGORY_STROKES,
        ZONE_COLORS,
        category_from_zone,
        dominant_time_category,
        summarize_category_hours,
    )


@app.cell
def _(category_from_zone, pd, time_location_remapped):
    def clean(value, fallback=""):
        if pd.isna(value):
            return fallback
        return value

    def to_hours(value):
        if pd.isna(value):
            return 0.0
        if hasattr(value, "total_seconds"):
            return float(value.total_seconds()) / 3600.0
        return float(pd.to_timedelta(value).total_seconds()) / 3600.0

    working = time_location_remapped.copy()
    working["zone_remapped"] = working["zone_remapped"].fillna("other")

    place_rows = (
        working.sort_values(["name", "place_id"])
        .drop_duplicates(subset=["place_id"], keep="first")
        .to_dict("records")
    )
    places = []
    for row in place_rows:
        zone = str(clean(row.get("zone"), "unknown")).strip().lower()
        zone_remapped = str(clean(row.get("zone_remapped"), "other")).strip().lower()
        places.append(
            {
                "place_id": str(row["place_id"]),
                "name": str(clean(row.get("name"), row["place_id"])),
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "x": float(row["lat"]),
                "y": float(row["lon"]),
                "zone": zone,
                "zone_remapped": zone_remapped,
                "zone_detail": "",
                "category": category_from_zone(zone_remapped),
                "remap_method": "Graph 2 remapped_location merge",
                "remap_score": None,
            }
        )

    visit_rows = []
    for row in working.to_dict("records"):
        zone = str(clean(row.get("zone"), "unknown")).strip().lower()
        zone_remapped = str(clean(row.get("zone_remapped"), "other")).strip().lower()
        time_value = clean(row.get("time"), None)
        if time_value is None:
            start_dt = pd.to_datetime(row.get("date")).to_pydatetime()
        else:
            start_dt = pd.to_datetime(time_value).to_pydatetime()
        date_value = clean(row.get("date"), str(start_dt.date()))
        visit_rows.append(
            {
                "source": "Graph 2 preprocessing",
                "trip_id": str(row["trip_id"]),
                "date": str(date_value),
                "start_dt": start_dt,
                "end_dt": start_dt,
                "member": str(row.get("people_id") or "Unknown"),
                "place_id": str(row["place_id"]),
                "name": str(clean(row.get("name"), row["place_id"])),
                "x": float(row["lat"]),
                "y": float(row["lon"]),
                "zone": zone,
                "zone_remapped": zone_remapped,
                "zone_detail": "",
                "category": category_from_zone(zone_remapped),
                "remap_method": "Graph 2 remapped_location merge",
                "remap_score": None,
                "duration_hours": to_hours(row.get("time_spend")),
            }
        )

    c2_selected_source = "Graph 2 preprocessing"
    source_data = {
        c2_selected_source: {
            "name": c2_selected_source,
            "people_names": sorted({row["member"] for row in visit_rows}),
            "places": places,
            "visit_rows": visit_rows,
        }
    }
    all_members = source_data[c2_selected_source]["people_names"]
    return all_members, c2_selected_source, source_data


@app.cell
def _(all_members, mo):
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

    mo.vstack([member_widget, neutral_widget])
    return member_widget, neutral_widget


@app.cell
def _(c2_selected_source, member_widget, neutral_widget, source_data):
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
    return c2_filtered_visits, c2_include_neutral, c2_member_label


@app.cell(hide_code=True)
def _(
    c2_filtered_visits,
    c2_member_label,
    knn_dist_slider,
    knn_num_slider,
    mo,
    mode_dropdown,
):
    mo.md(f"""
    **Current filter**

    - preprocessing: `graph2.py` exact first block
    - members: `{c2_member_label}`
    - comparison mode: `{mode_dropdown.value}`
    - remapper: `{knn_num_slider.value}` nearest references within `{knn_dist_slider.value:.1f}` km
    - filtered visit rows: `{len(c2_filtered_visits)}`
    """)
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
        umbrella_cx = top_x + top_w - 153
        umbrella_ground_y = top_y + 184

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
            f'<path d="M {umbrella_cx - 48} {top_y + 136} C {umbrella_cx - 27} {top_y + 92}, '
            f'{umbrella_cx + 26} {top_y + 92}, {umbrella_cx + 48} {top_y + 136} Z" '
            'fill="#ef5350" stroke="#8b2b29" stroke-width="1.2"/>'
            f'<path d="M {umbrella_cx} {top_y + 136} C {umbrella_cx - 2} {top_y + 112}, '
            f'{umbrella_cx - 1} {top_y + 97}, {umbrella_cx} {top_y + 94}" '
            'fill="none" stroke="#8b2b29" stroke-width="1"/>'
            f'<line x1="{umbrella_cx}" y1="{top_y + 136}" x2="{umbrella_cx}" y2="{umbrella_ground_y}" stroke="#8a6f3f" stroke-width="2"/>'
            f'<rect x="{umbrella_cx - 38}" y="{umbrella_ground_y}" width="76" height="9" rx="4" fill="#f0f5f7" stroke="#8ea0aa" stroke-width="1"/>'
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
                x = umbrella_cx + (index % 3 - 1) * 22
                y = umbrella_ground_y - 6
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

    - Data loading builds on `graph2.py`: `places_edited.json` and `time_trip_spend.json` are loaded from `implementation/data`.
    - Place labels use the Graph 2 preparation: edited place zones first, then weighted nearest-neighbor remapping for commercial/residential places.
    - Remapped `industrial` places are shown as Fishing; remapped `tourism` places are shown as Tourism.
    - Trip duration comes from Graph 2's prepared `time_spend` column rather than being recalculated in this notebook.
    """)
    return

if __name__ == "__main__":
    app.run()
