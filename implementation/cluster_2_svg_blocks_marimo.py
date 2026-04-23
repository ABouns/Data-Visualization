import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    from sklearn.neighbors import BallTree
    import svg
    import math
    import json
    import os

    return BallTree, json, math, mo, np, pd, svg


@app.cell
def _(BallTree, np, pd):

    def classify_weighted_knn(df, k=5, max_radius_km=1.0, epsilon=0.001):
        # 1. Split data
        df_comm = df[df["zone"].isin(["commercial", "residential"])].reset_index(drop=True)
        df_targets = df[df["zone"].isin(["tourism", "industrial"])].reset_index(drop=True)

        if df_comm.empty or df_targets.empty:
            return pd.DataFrame()

        # 2. Build Tree and Query
        comm_rad = np.radians(df_comm[["lat", "lon"]])
        target_rad = np.radians(df_targets[["lat", "lon"]])
        tree = BallTree(target_rad, metric="haversine")

        earth_radius_km = 6371.0
        radius_rad = max_radius_km / earth_radius_km
        distances, indices = tree.query(comm_rad, k=k, return_distance=True)

        # 3. Collect Valid Neighbors and Calculate Inverse Distance Weight
        results = []
        for i, (dist_array, idx_array) in enumerate(zip(distances, indices)):
            for dist, idx in zip(dist_array, idx_array):
                if dist <= radius_rad:
                    dist_km = dist * earth_radius_km
                    weight = 1.0 / (dist_km + epsilon)  # Add epsilon to avoid zero division

                    results.append(
                        {
                            "commercial_id": df_comm.iloc[i]["place_id"],
                            "target_zone": df_targets.iloc[idx]["zone"],
                            "weight": weight,
                        }
                    )

        df_neighbors = pd.DataFrame(results)
        if df_neighbors.empty:
            return pd.DataFrame(columns=["commercial_id", "predicted_zone", "weighted_score"])

        # 4. Sum the weights grouped by commercial_id and target_zone
        weighted_scores = (
            df_neighbors.groupby(["commercial_id", "target_zone"])["weight"]
            .sum()
            .reset_index(name="weighted_score")
        )

        # 5. Sort by highest weighted score to determine majority
        df_majority = (
            weighted_scores.sort_values(["commercial_id", "weighted_score"], ascending=[True, False])
            .drop_duplicates(subset=["commercial_id"], keep="first")
            .rename(columns={"target_zone": "predicted_zone"})
        )

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
        places_edited = pd.read_json(
            "https://raw.githubusercontent.com/tvakul/dataviz1/refs/heads/main/data/places_edited.json"
        )
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
    remapped_location = pd.concat(
        [
            places_edited.loc[places_edited["zone"].isin(["industrial", "tourism"])],
            classify_weighted_knn(
                places_edited,
                max_radius_km=knn_dist_slider.value,
                k=knn_num_slider.value,
            ).rename(columns={"predicted_zone": "zone", "commercial_id": "place_id"}),
        ],
        ignore_index=True,
    ).drop_duplicates(subset=["place_id"], keep="first")[["place_id", "zone"]]

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
        "time_spend": "timedelta64[ns]",
    }
    try:
        time_trip_spend = pd.read_json(
            str(mo.notebook_location() / "data" / "time_trip_spend.json"),
            dtype=_dtypes_tts,
        )
    except:
        time_trip_spend = pd.read_json(
            "https://raw.githubusercontent.com/tvakul/dataviz1/refs/heads/main/data/time_trip_spend.json",
            dtype=_dtypes_tts,
        )
    time_trip_spend
    return (time_trip_spend,)


@app.cell
def _(pd, remapped_location, sel_end, sel_start, time_trip_spend):
    _col = pd.to_datetime(time_trip_spend["date"])
    _mask = (_col >= sel_start) & (_col <= sel_end)
    filtered_tts = time_trip_spend[_mask]

    time_location_remapped = pd.merge(
        filtered_tts[
            [
                "trip_id",
                "date",
                "people_id",
                "place_id",
                "name",
                "time",
                "time_spend",
                "zone",
                "lat",
                "lon",
            ]
        ],
        remapped_location.rename(columns={"zone": "zone_remapped"}),
        on="place_id",
        how="left",
    ).fillna({"zone_remapped": "other"})
    time_location_remapped
    return (time_location_remapped,)


@app.cell(hide_code=True)
def _(time_location_remapped):
    _tmp = time_location_remapped.copy()
    _tmp["visit_id"] = (
        _tmp["trip_id"].astype(str)
        + "_"
        + _tmp["place_id"].astype(str)
        + "_"
        + _tmp["place_id"].astype(str)
    )
    people_zone_summary = (
        _tmp.groupby(["people_id", "zone_remapped"])
        .agg(total_visits=("visit_id", "nunique"))
        .reset_index()
    )

    people_zone_summary = people_zone_summary[
        people_zone_summary["zone_remapped"].isin(["industrial", "tourism"])
    ]

    people_zone_summary_delta = (
        people_zone_summary.pivot(index="people_id", columns="zone_remapped", values="total_visits")
        .fillna(0)
        .reset_index()
    )
    people_zone_summary_delta["delta"] = (
        people_zone_summary_delta["industrial"] - people_zone_summary_delta["tourism"]
    )
    people_zone_summary_delta.sort_values("delta", ascending=False)
    return (people_zone_summary_delta,)


@app.cell
def _(pd, time_location_remapped):
    people_timespend_summary = (
        time_location_remapped.groupby(["people_id", "zone_remapped"])
        .agg({"time_spend": "sum", "trip_id": "nunique"})
        .reset_index()
    )

    people_timespend_summary_filtered = people_timespend_summary[
        people_timespend_summary["zone_remapped"].isin(["industrial", "tourism"])
    ].copy()

    delta_time_spend = (
        people_timespend_summary_filtered.pivot(
            index="people_id", columns="zone_remapped", values="time_spend"
        ).fillna(pd.Timedelta(0))
    )
    delta_time_spend["delta"] = delta_time_spend.get("industrial", pd.Timedelta(0)) - delta_time_spend.get(
        "tourism", pd.Timedelta(0)
    )

    delta_time_spend
    return (delta_time_spend,)


@app.cell
def _(mo, pd, time_trip_spend):
    unique_dates = pd.to_datetime(time_trip_spend["date"]).sort_values().unique()
    num_days = len(unique_dates)

    knn_dist_slider = mo.ui.slider(start=0, stop=5, step=0.1, value=1.5, show_value=True)
    knn_num_slider = mo.ui.slider(start=0, stop=10, step=1, value=5, show_value=True)
    mode_dropdown = mo.ui.dropdown(options=["time_spend", "visits"], value="visits")
    show_others = mo.ui.checkbox(value=False, label="Show 'Others'")

    date_slider = mo.ui.range_slider(
        start=0,
        stop=num_days - 1,
        step=1,
        value=(0, num_days - 1),
        label="Filter Date Range",
    )

    return (
        date_slider,
        knn_dist_slider,
        knn_num_slider,
        mode_dropdown,
        show_others,
        unique_dates,
    )


@app.cell
def _(date_slider, unique_dates):
    sel_start = unique_dates[int(date_slider.value[0])]
    sel_end = unique_dates[int(date_slider.value[1])]
    return sel_end, sel_start


@app.cell
def _(time_location_remapped):
    time_location_remappd2 = time_location_remapped.copy()
    time_location_remappd2.groupby(["people_id", "lat", "lon", "trip_id"]).agg({"time_spend": "sum"}).reset_index().rename(
        columns={"place_id": "time_spend"}
    )
    return


@app.cell
def _(
    delta_time_spend,
    mode_dropdown,
    people_zone_summary_delta,
    time_location_remapped,
):
    if mode_dropdown.value == "visits":
        graph_2_1_data = people_zone_summary_delta
        graph_2_2_data = (
            time_location_remapped.groupby(
                ["people_id", "date", "zone_remapped", "trip_id", "place_id"]
            )
            .size()
            .reset_index(name="num_visits")
        )
        graph_2_2_data["time_spend"] = 0
    else:
        graph_2_1_data = delta_time_spend.reset_index()
        temp_df = time_location_remapped.copy()
        if temp_df["time_spend"].dtype == "timedelta64[ns]":
            temp_df["time_hr"] = temp_df["time_spend"].dt.total_seconds() / 3600
        else:
            temp_df["time_hr"] = temp_df["time_spend"]

        graph_2_2_data = (
            temp_df.groupby(["people_id", "date", "zone_remapped", "trip_id", "place_id"])["time_hr"]
            .sum()
            .reset_index(name="time_spend")
        )
        graph_2_2_data["num_visits"] = 1
    return graph_2_1_data, graph_2_2_data


@app.cell
def _(graph_2_1_data):
    graph_2_1_data
    return


@app.cell
def _(graph_2_1_data):
    graph_2_1_data.to_json("data/graph_2_1_data.json")
    return


@app.cell
def _(json):
    try:
        with open("data/oceanus_map.geojson", "r") as f:
            oceanus_geojson = json.load(f)
    except:
        oceanus_geojson = None
    return (oceanus_geojson,)


@app.cell
def _(pd, time_location_remapped):
    visit_counts = (
        time_location_remapped.groupby(["place_id", "zone_remapped", "lat", "lon"])
        .size()
        .reset_index(name="count")
    )
    total_time = (
        time_location_remapped.groupby(["place_id", "zone_remapped", "lat", "lon"])["time_spend"]
        .sum()
        .dt.total_seconds()
        / 3600
    )
    visit_data = pd.merge(
        visit_counts,
        total_time.reset_index(name="hours"),
        on=["place_id", "zone_remapped", "lat", "lon"],
    )
    return (visit_data,)


@app.cell
def _(visit_data):
    visit_data
    return


@app.cell
def _(math, svg):
    def _member_slug(name):
        return str(name).replace(" ", "_")

    def draw_boat(x, y, scale=1.0):
        return svg.G(
            transform=f"translate({x}, {y}) scale({scale})",
            elements=[
                svg.Path(
                    d="M 0 0 C 32 -2 93 -2 123 0 L 108 20 C 94 28 26 28 12 20 Z",
                    fill="url(#big-boat-hull)",
                    stroke="#274760",
                    stroke_width=2,
                ),
                svg.Rect(
                    x=32,
                    y=-22,
                    width=42,
                    height=24,
                    rx=5,
                    fill="#fbfeff",
                    stroke="#708ea2",
                    stroke_width=1.4,
                ),
                svg.Rect(x=40, y=-16, width=11, height=8, rx=1.5, fill="#9cc8e5"),
                svg.Rect(x=55, y=-16, width=11, height=8, rx=1.5, fill="#9cc8e5"),
                svg.Line(
                    x1=75,
                    y1=-2,
                    x2=98,
                    y2=-40,
                    stroke="#567991",
                    stroke_width=2,
                    stroke_linecap="round",
                ),
                svg.Path(
                    d="M 99 -39 Q 108 -28 101 -14 L 92 -13 L 92 -34 Z",
                    fill="#f7fafc",
                    stroke="#7a94a6",
                    stroke_width=1.2,
                ),
                svg.Path(
                    d="M -8 16 Q 18 24 48 19 Q 86 14 133 18",
                    fill="none",
                    stroke="#d8f0ff",
                    stroke_width=3,
                    stroke_linecap="round",
                    opacity=0.85,
                ),
            ],
        )

    def draw_rowboat(x, y, scale=1.0, color="#2c7a7b", name=""):
        safe_name = _member_slug(name)
        return svg.G(
            id=f"boat_{safe_name}",
            class_="member-node",
            transform=f"translate({x}, {y}) scale({scale})",
            style="cursor:pointer",
            elements=[
                svg.Path(
                    d="M -42 0 C -28 21 28 21 42 0 L 36 0 C 24 10 -24 10 -36 0 Z",
                    fill="url(#rowboat-wood)",
                    stroke="#4e3317",
                    stroke_width=1.6,
                ),
                svg.Path(
                    d="M -28 2 L 28 2",
                    stroke="#f3e5c6",
                    stroke_width=3,
                    stroke_linecap="round",
                ),
                svg.Path(
                    d="M -18 8 L 18 8",
                    stroke="#ba8f56",
                    stroke_width=2,
                    stroke_linecap="round",
                ),
                svg.Line(
                    x1=-10,
                    y1=7,
                    x2=35,
                    y2=-12,
                    stroke="#7a5335",
                    stroke_width=2,
                    stroke_linecap="round",
                ),
                svg.Circle(
                    cx=-4,
                    cy=-16,
                    r=6,
                    fill="#d5a180",
                    stroke="#7a5845",
                    stroke_width=0.9,
                ),
                svg.Path(
                    d="M -8 -21 C -5 -26 3 -26 4 -20",
                    fill="none",
                    stroke="#3f2f29",
                    stroke_width=2,
                    stroke_linecap="round",
                ),
                svg.Path(
                    d="M -15 -9 Q -4 -17 7 -9 L 5 6 L -13 6 Z",
                    fill=color,
                    stroke="#274050",
                    stroke_width=1,
                ),
                svg.Line(
                    x1=-12,
                    y1=-7,
                    x2=-22,
                    y2=0,
                    stroke="#d5a180",
                    stroke_width=3,
                    stroke_linecap="round",
                ),
                svg.Line(
                    x1=4,
                    y1=-7,
                    x2=17,
                    y2=0,
                    stroke="#d5a180",
                    stroke_width=3,
                    stroke_linecap="round",
                ),
                svg.Path(
                    d="M -54 17 Q -17 24 16 20 Q 45 17 57 18",
                    fill="none",
                    stroke="#dff4ff",
                    stroke_width=3,
                    opacity=0.9,
                    stroke_linecap="round",
                ),
            ],
        )

    def draw_umbrella(x, y, scale=1.0, color="#ef8354", name=""):
        safe_name = _member_slug(name)
        return svg.G(
            id=f"beach_{safe_name}",
            class_="member-node",
            transform=f"translate({x}, {y}) scale({scale})",
            style="cursor:pointer",
            elements=[
                svg.Line(
                    x1=0,
                    y1=0,
                    x2=0,
                    y2=-56,
                    stroke="#72553d",
                    stroke_width=2.2,
                    stroke_linecap="round",
                ),
                svg.Path(
                    d="M -34 -30 Q -19 -58 0 -60 Q 19 -58 34 -30 Z",
                    fill="url(#umbrella-canopy)",
                    stroke="#9a5b42",
                    stroke_width=1.4,
                ),
                svg.Line(x1=-17, y1=-32, x2=-9, y2=-57, stroke="#f7e1b2", stroke_width=1.4),
                svg.Line(x1=0, y1=-31, x2=0, y2=-59, stroke="#f7e1b2", stroke_width=1.4),
                svg.Line(x1=17, y1=-32, x2=9, y2=-57, stroke="#f7e1b2", stroke_width=1.4),
                svg.Path(
                    d="M 0 -2 C 6 8 8 12 5 18",
                    fill="none",
                    stroke="#72553d",
                    stroke_width=2,
                    stroke_linecap="round",
                ),
                svg.Path(
                    d="M -22 9 Q 0 15 22 9",
                    fill="none",
                    stroke=color,
                    stroke_width=2.2,
                    opacity=0.55,
                    stroke_linecap="round",
                ),
            ],
        )

    def draw_person(x, y, scale=0.8, color="#2c3e50", name=""):
        safe_name = _member_slug(name)
        return svg.G(
            id=f"person_{safe_name}",
            class_="member-node",
            transform=f"translate({x}, {y}) scale({scale})",
            style="cursor:pointer",
            elements=[
                svg.Ellipse(cx=0, cy=4, rx=16, ry=4, fill="#25313d", opacity=0.16),
                svg.Circle(
                    cx=0,
                    cy=-42,
                    r=10,
                    fill="#d5a180",
                    stroke="#7a5845",
                    stroke_width=0.9,
                ),
                svg.Path(
                    d="M -5 -50 C -2 -56 6 -56 7 -48",
                    fill="none",
                    stroke="#3f2f29",
                    stroke_width=2.2,
                    stroke_linecap="round",
                ),
                svg.Path(
                    d="M -15 -29 Q 0 -39 15 -29 L 12 -4 L -12 -4 Z",
                    fill=color,
                    stroke="#26313a",
                    stroke_width=1.1,
                ),
                svg.Line(
                    x1=-11,
                    y1=-24,
                    x2=-20,
                    y2=-13,
                    stroke="#d5a180",
                    stroke_width=3.2,
                    stroke_linecap="round",
                ),
                svg.Line(
                    x1=11,
                    y1=-24,
                    x2=20,
                    y2=-13,
                    stroke="#d5a180",
                    stroke_width=3.2,
                    stroke_linecap="round",
                ),
                svg.Line(
                    x1=-5,
                    y1=-4,
                    x2=-10,
                    y2=9,
                    stroke="#384a5d",
                    stroke_width=3.4,
                    stroke_linecap="round",
                ),
                svg.Line(
                    x1=5,
                    y1=-4,
                    x2=10,
                    y2=9,
                    stroke="#384a5d",
                    stroke_width=3.4,
                    stroke_linecap="round",
                ),
                svg.Line(
                    x1=-10,
                    y1=9,
                    x2=-16,
                    y2=9,
                    stroke="#25292d",
                    stroke_width=3.3,
                    stroke_linecap="round",
                ),
                svg.Line(
                    x1=10,
                    y1=9,
                    x2=16,
                    y2=9,
                    stroke="#25292d",
                    stroke_width=3.3,
                    stroke_linecap="round",
                ),
            ],
        )

    return draw_boat, draw_person, draw_rowboat, draw_umbrella


@app.cell
def _(
    draw_boat,
    draw_person,
    draw_rowboat,
    draw_umbrella,
    graph_2_1_data,
    graph_2_2_data,
    math,
    oceanus_geojson,
    places_edited,
    svg,
    time_location_remapped,
):
    class DataPath(svg.Path):
        def __init__(self, **kwargs):
            self.data_info = kwargs.pop("data_info", "")
            super().__init__(**kwargs)

        def as_str(self):
            s = super().as_str()
            return s.replace("/>", f' data-info="{self.data_info}"/>', 1)

    class DataPolygon(svg.Polygon):
        def __init__(self, **kwargs):
            self.data_info = kwargs.pop("data_info", "")
            super().__init__(**kwargs)

        def as_str(self):
            s = super().as_str()
            return s.replace("/>", f' data-info="{self.data_info}"/>', 1)

    class DataG(svg.G):
        def __init__(self, **kwargs):
            self.data_info = kwargs.pop("data_info", "")
            super().__init__(**kwargs)

        def as_str(self):
            s = super().as_str()
            if "<g " in s:
                return s.replace("<g ", f'<g data-info="{self.data_info}" ', 1)
            return s.replace("<g>", f'<g data-info="{self.data_info}">', 1)

    class DataCircle(svg.Circle):
        def __init__(self, **kwargs):
            self.data_info = kwargs.pop("data_info", "")
            super().__init__(**kwargs)

        def as_str(self):
            s = super().as_str()
            return s.replace("/>", f' data-info="{self.data_info}"/>', 1)

    def format_duration(hours):
        h = float(hours)
        days = int(h // 24)
        rem_h = h % 24
        mins = int((rem_h * 60) % 60)
        hh = int(rem_h)
        time_str = f"{hh:02d} hr : {mins:02d} min"
        if days == 0:
            return time_str
        if days == 1:
            return f"1 day, {time_str}"
        return f"{days} days, {time_str}"

    def create_dashboard(mode="visits", show_others=False):
        W, H = 1100, 860
        els = [
            """
            <defs>
              <linearGradient id="page-bg" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#eef5fb"/>
                <stop offset="100%" stop-color="#f9fbfe"/>
              </linearGradient>
              <linearGradient id="water-grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#7dc7f2"/>
                <stop offset="100%" stop-color="#2b7cab"/>
              </linearGradient>
              <linearGradient id="water-soft" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#d7effc"/>
                <stop offset="100%" stop-color="#f4fbff"/>
              </linearGradient>
              <linearGradient id="sand-grad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#f0ddb1"/>
                <stop offset="100%" stop-color="#d9bb84"/>
              </linearGradient>
              <linearGradient id="shore-grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#fff3cf"/>
                <stop offset="100%" stop-color="#ead29b"/>
              </linearGradient>
              <linearGradient id="card-grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#ffffff"/>
                <stop offset="100%" stop-color="#f4f8fb"/>
              </linearGradient>
              <linearGradient id="big-boat-hull" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#f8fbff"/>
                <stop offset="55%" stop-color="#f2f7fb"/>
                <stop offset="56%" stop-color="#24465f"/>
                <stop offset="100%" stop-color="#123148"/>
              </linearGradient>
              <linearGradient id="rowboat-wood" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#81552f"/>
                <stop offset="100%" stop-color="#5d381b"/>
              </linearGradient>
              <linearGradient id="umbrella-canopy" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stop-color="#ffcc8f"/>
                <stop offset="50%" stop-color="#f97352"/>
                <stop offset="100%" stop-color="#ffd58e"/>
              </linearGradient>
              <filter id="panel-shadow" x="-20%" y="-20%" width="160%" height="160%">
                <feDropShadow dx="0" dy="10" stdDeviation="10" flood-color="#57718a" flood-opacity="0.12"/>
              </filter>
              <filter id="soft-shadow" x="-25%" y="-25%" width="170%" height="170%">
                <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#274055" flood-opacity="0.18"/>
              </filter>
              <filter id="dot-shadow" x="-50%" y="-50%" width="200%" height="200%">
                <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#1b2838" flood-opacity="0.2"/>
              </filter>
            </defs>
            <style>
              .panel-title { font-family: Inter, Segoe UI, sans-serif; font-size: 22px; font-weight: 700; fill: #20313f; }
              .panel-subtitle { font-family: Inter, Segoe UI, sans-serif; font-size: 12px; fill: #627485; }
              .axis-note { font-family: Inter, Segoe UI, sans-serif; font-size: 11px; fill: #73879a; }
              .legend-text { font-family: Inter, Segoe UI, sans-serif; font-size: 12px; fill: #304454; }
              .small-label { font-family: Inter, Segoe UI, sans-serif; font-size: 11px; fill: #4f6272; }
              .member-name { font-family: Inter, Segoe UI, sans-serif; font-size: 11px; font-weight: 600; fill: #233444; }
              .member-node text { pointer-events: none; }
              .clickable-person { cursor: pointer; }
              .locked-person .member-node circle,
              .locked-person .member-node path,
              .locked-person .member-node rect,
              .locked-person .member-node line,
              .locked-person .member-node ellipse {
                filter: drop-shadow(0 0 8px rgba(40, 67, 88, 0.28));
              }
            </style>
            """,
            svg.Rect(x=0, y=0, width=W, height=H, fill="url(#page-bg)"),
        ]

        def fmt(v):
            return f"{float(v):.0f}" if mode == "visits" else format_duration(v)

        def clamp(v, lo, hi):
            return max(lo, min(hi, v))

        def mix_hex(a, b, t):
            t = clamp(t, 0.0, 1.0)
            a = a.lstrip("#")
            b = b.lstrip("#")
            ar, ag, ab = int(a[0:2], 16), int(a[2:4], 16), int(a[4:6], 16)
            br, bg, bb = int(b[0:2], 16), int(b[2:4], 16), int(b[4:6], 16)
            return f"#{round(ar + (br - ar) * t):02x}{round(ag + (bg - ag) * t):02x}{round(ab + (bb - ab) * t):02x}"

        focus_colors = {
            "fishing": "#1f8b6f",
            "tourism": "#e47a5b",
            "other": "#93a4b4",
        }
        focus_strokes = {
            "fishing": "#10604d",
            "tourism": "#ba5a3f",
            "other": "#6f8191",
        }
        name_map = {"industrial": "fishing", "tourism": "tourism", "other": "other"}

        # Header
        els.append(
            svg.Text(
                x=38,
                y=36,
                text="Cluster 2",
                class_="panel-title",
            )
        )
        els.append(
            svg.Text(
                x=38,
                y=58,
                text="Board visit map and time spent across fishing and tourism activity",
                class_="panel-subtitle",
            )
        )

        # Panels
        c5_x, c5_y, c5_w, c5_h = 32, 84, 1036, 252
        c6_x, c6_y, c6_w, c6_h = 32, 360, 506, 468
        c7_x, c7_y, c7_w, c7_h = 562, 360, 506, 468

        for x, y, w, h in [(c5_x, c5_y, c5_w, c5_h), (c6_x, c6_y, c6_w, c6_h), (c7_x, c7_y, c7_w, c7_h)]:
            els.append(
                svg.Rect(
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    rx=16,
                    fill="url(#card-grad)",
                    stroke="#dbe6ee",
                    stroke_width=1,
                    filter="url(#panel-shadow)",
                )
            )

        # ---- C5
        title_c5 = "Board bias along the shoreline"
        subtitle_c5 = "Member position is based on the tourism vs fishing delta"
        els.append(svg.Text(x=c5_x + 24, y=c5_y + 32, text=title_c5, class_="panel-title"))
        els.append(svg.Text(x=c5_x + 24, y=c5_y + 52, text=subtitle_c5, class_="panel-subtitle"))

        data_c5 = graph_2_1_data.copy()
        pos_col = "delta"
        if mode == "time_spend":
            data_c5["delta_val"] = data_c5["delta"].apply(
                lambda x: x.total_seconds() / 3600 if hasattr(x, "total_seconds") else x
            )
            pos_col = "delta_val"

        min_d = float(min(0, data_c5[pos_col].min()) - 2)
        max_d = float(max(0, data_c5[pos_col].max()) + 2)
        range_d = max(max_d - min_d, 1.0)
        border_ratio = (0 - min_d) / range_d
        border_x = c5_x + 48 + border_ratio * (c5_w - 96)
        sky_y = c5_y + 68
        horizon_y = c5_y + 174
        sand_top_y = c5_y + 122

        els.append(svg.Rect(x=c5_x + 18, y=sky_y, width=c5_w - 36, height=58, fill="url(#water-soft)", rx=12))
        beach_poly = (
            f"{c5_x + 20},{horizon_y + 18} "
            f"{c5_x + 20},{sand_top_y} "
            f"{border_x - 42},{sand_top_y + 2} "
            f"{border_x},{horizon_y + 10} "
            f"{border_x},{c5_y + c5_h - 42} "
            f"{c5_x + 20},{c5_y + c5_h - 42}"
        )
        water_poly = (
            f"{border_x},{horizon_y + 10} "
            f"{c5_x + c5_w - 20},{horizon_y - 4} "
            f"{c5_x + c5_w - 20},{c5_y + c5_h - 42} "
            f"{border_x},{c5_y + c5_h - 42}"
        )
        els.append(svg.Polygon(points=beach_poly, fill="url(#shore-grad)"))
        els.append(svg.Polygon(points=water_poly, fill="url(#water-grad)"))
        els.append(
            svg.Path(
                d=f"M {border_x - 42} {sand_top_y + 2} Q {border_x - 14} {sand_top_y + 26} {border_x} {horizon_y + 10}",
                fill="none",
                stroke="#d7c296",
                stroke_width=6,
                stroke_linecap="round",
                opacity=0.95,
            )
        )
        els.append(
            svg.Path(
                d=f"M {border_x + 1} {horizon_y + 10} C {border_x + 72} {horizon_y + 5}, {c5_x + c5_w - 120} {horizon_y + 6}, {c5_x + c5_w - 28} {horizon_y + 16}",
                fill="none",
                stroke="#d7f1ff",
                stroke_width=4,
                opacity=0.8,
                stroke_linecap="round",
            )
        )
        els.append(draw_boat(c5_x + 92, horizon_y - 4, 0.84))
        els.append(svg.Text(x=c5_x + 54, y=sky_y + 18, text="Tourism pull", class_="legend-text"))
        els.append(svg.Text(x=c5_x + c5_w - 138, y=sky_y + 18, text="Fishing pull", class_="legend-text"))
        els.append(
            svg.Line(
                x1=border_x,
                y1=sky_y + 6,
                x2=border_x,
                y2=c5_y + c5_h - 44,
                stroke="#98aab8",
                stroke_width=1.5,
                stroke_dasharray="5 5",
            )
        )
        els.append(svg.Text(x=border_x, y=sky_y - 4, text="Neutral", text_anchor="middle", class_="axis-note"))

        member_colors = {}
        neg_color = "#ef8354"
        pos_color = "#1f8b6f"

        def ground_y_at(x):
            if x <= border_x:
                slope = (horizon_y + 10 - (sand_top_y + 2)) / max(1.0, 42.0)
                return min(horizon_y + 10, sand_top_y + 2 + max(0.0, x - (border_x - 42)) * slope)
            return horizon_y + 12

        for i, (_, row) in enumerate(data_c5.iterrows()):
            val = float(row[pos_col])
            x = c5_x + 48 + ((val - min_d) / range_d) * (c5_w - 96)
            x = clamp(x, c5_x + 74, c5_x + c5_w - 74)
            pid = row["people_id"]
            pid_safe = pid.replace(" ", "_")
            color_t = (val - min_d) / range_d
            body_color = mix_hex(neg_color, pos_color, color_t)
            member_colors[pid] = body_color
            lane = i % 3
            y_jitter = [0, 14, -10][lane]

            if val < -0.4:
                gy = ground_y_at(x) - 2 + y_jitter * 0.15
                els.append(
                    svg.G(
                        class_=f"clickable-person pid-{pid_safe}",
                        style="cursor:pointer",
                        elements=[
                            draw_umbrella(x, gy + 4, 0.88, color=body_color, name=pid),
                            draw_person(x, gy + 45, 0.72, color=body_color, name=pid),
                            svg.Text(
                                x=x,
                                y=gy + 76,
                                text=pid,
                                text_anchor="middle",
                                class_="member-name",
                            ),
                        ],
                    )
                )
            elif val > 0.4:
                gy = horizon_y + 18 + [0, 10, -8][lane]
                els.append(
                    svg.G(
                        class_=f"clickable-person pid-{pid_safe}",
                        style="cursor:pointer",
                        elements=[
                            draw_rowboat(x, gy + 18, 0.98, color=body_color, name=pid),
                            svg.Text(
                                x=x,
                                y=gy + 48,
                                text=pid,
                                text_anchor="middle",
                                class_="member-name",
                            ),
                        ],
                    )
                )
            else:
                gy = ground_y_at(x) + 2
                els.append(
                    svg.G(
                        class_=f"clickable-person pid-{pid_safe}",
                        style="cursor:pointer",
                        elements=[
                            draw_person(x, gy + 28, 0.72, color=body_color, name=pid),
                            svg.Text(
                                x=x,
                                y=gy + 60,
                                text=pid,
                                text_anchor="middle",
                                class_="member-name",
                            ),
                        ],
                    )
                )

        ax_y = c5_y + c5_h - 24
        ax_x1 = c5_x + 40
        ax_x2 = c5_x + c5_w - 40
        els.append(svg.Line(x1=ax_x1, y1=ax_y, x2=ax_x2, y2=ax_y, stroke="#90a2b2", stroke_width=1.5))
        for v in [min_d + 2, 0, max_d - 2]:
            tx = c5_x + 48 + ((v - min_d) / range_d) * (c5_w - 96)
            els.append(svg.Line(x1=tx, y1=ax_y - 5, x2=tx, y2=ax_y + 5, stroke="#90a2b2", stroke_width=1.2))
            els.append(
                svg.Text(
                    x=tx,
                    y=ax_y + 18,
                    text=f"{v:.1f}",
                    text_anchor="middle",
                    class_="axis-note",
                )
            )
        els.append(svg.Text(x=ax_x1, y=ax_y - 10, text="More tourism attention", class_="small-label"))
        els.append(
            svg.Text(
                x=ax_x2,
                y=ax_y - 10,
                text="More fishing attention",
                text_anchor="end",
                class_="small-label",
            )
        )

        # ---- C6
        title_c6 = "Place-based activity map" if mode == "visits" else "Place-based time map"
        subtitle_c6 = "Bubble size shows repeated visits or accumulated time"
        els.append(svg.Text(x=c6_x + 24, y=c6_y + 32, text=title_c6, class_="panel-title"))
        els.append(svg.Text(x=c6_x + 24, y=c6_y + 52, text=subtitle_c6, class_="panel-subtitle"))
        els.append(
            svg.Rect(
                x=c6_x + 20,
                y=c6_y + 70,
                width=c6_w - 40,
                height=c6_h - 106,
                rx=14,
                fill="url(#water-soft)",
                stroke="#d3e5f0",
                stroke_width=1,
            )
        )

        def project(lon_val, lat_val):
            x_min, x_max = -166.3, -164.2
            y_min, y_max = 38.7, 39.9
            x_pct = (lon_val - x_min) / (x_max - x_min)
            y_pct = (lat_val - y_min) / (y_max - y_min)
            px = c6_x + 44 + x_pct * (c6_w - 88)
            py = c6_y + c6_h - 52 - y_pct * (c6_h - 128)
            return px, py

        if oceanus_geojson:
            for feat in oceanus_geojson["features"]:
                geom = feat.get("geometry", {})
                if geom.get("type") == "Polygon":
                    for poly in geom.get("coordinates", []):
                        pts = " ".join(
                            [f"{project(c[0], c[1])[0]},{project(c[0], c[1])[1]}" for c in poly]
                        )
                        els.append(
                            svg.Polygon(
                                points=pts,
                                fill="#eef6dd" if feat["properties"].get("Name") == "Suna Island" else "#f7f1d7",
                                stroke="#9eb88d" if feat["properties"].get("Name") == "Suna Island" else "#c1b383",
                                stroke_width=1.1,
                                filter="url(#soft-shadow)",
                            )
                        )

        place_names = {}
        if "name" in places_edited.columns:
            place_names = places_edited.set_index("place_id")["name"].to_dict()

        visit_summary = (
            graph_2_2_data.groupby(["people_id", "place_id", "zone_remapped"])
            .agg({"time_spend": "sum", "num_visits": "sum"})
            .reset_index()
        )
        visit_summary = visit_summary.merge(places_edited[["place_id", "lat", "lon"]], on="place_id", how="left")

        metric_col = "num_visits" if mode == "visits" else "time_spend"
        visit_summary["val"] = visit_summary[metric_col]
        max_v = float(visit_summary["val"].max() or 1)

        for _, row in visit_summary.dropna(subset=["lat", "lon"]).iterrows():
            mapped_zone = name_map.get(row["zone_remapped"], "other")
            if not show_others and mapped_zone == "other":
                continue
            px, py = project(row["lat"], row["lon"])
            r = (float(row["val"]) / max_v) ** 0.5 * 16 + 2.5
            pid_safe = row["people_id"].replace(" ", "_")
            loc_name = place_names.get(row["place_id"], str(row["place_id"]))
            info = (
                f"Member Activity | Member: {row['people_id']} | Location: {loc_name} | "
                f"Focus: {mapped_zone.capitalize()} | Value: {fmt(row['val'])}"
            )
            els.append(
                DataCircle(
                    cx=px,
                    cy=py,
                    r=r,
                    fill=focus_colors.get(mapped_zone, "#93a4b4"),
                    stroke="#ffffff",
                    stroke_width=1.3,
                    opacity=0.78,
                    filter="url(#dot-shadow)",
                    class_=f"visit_{pid_safe} map-dot c6-segment",
                    style="display:none",
                    data_info=info,
                )
            )

        visit_data_agg = (
            time_location_remapped.groupby(["place_id", "zone_remapped"])
            .agg({"place_id": "count", "time_spend": "sum"})
            .rename(columns={"place_id": "count"})
            .reset_index()
        )
        visit_data_agg["hours"] = visit_data_agg["time_spend"].dt.total_seconds() / 3600
        visit_data_agg = visit_data_agg.merge(places_edited[["place_id", "lat", "lon"]], on="place_id", how="left")

        total_metric = "count" if mode == "visits" else "hours"
        max_total = float(visit_data_agg[total_metric].max() or 1)
        total_group = svg.G(id="map_total", class_="map-total", elements=[])
        for _, row in visit_data_agg.dropna(subset=["lat", "lon"]).iterrows():
            px, py = project(row["lat"], row["lon"])
            r = (float(row[total_metric]) / max_total) ** 0.5 * 14 + 2.5
            mapped_zone = name_map.get(row["zone_remapped"], "other")
            if not show_others and mapped_zone == "other":
                continue
            loc_name = place_names.get(row["place_id"], str(row["place_id"]))
            info = (
                f"Global Stats | Location: {loc_name} | Total {mode.title()}: {fmt(row[total_metric])} | "
                f"Category: {mapped_zone.capitalize()}"
            )
            total_group.elements.append(
                DataCircle(
                    cx=px,
                    cy=py,
                    r=r,
                    fill=focus_colors.get(mapped_zone, "#93a4b4"),
                    stroke=focus_strokes.get(mapped_zone, "#6f8191"),
                    stroke_width=1.1,
                    opacity=0.42,
                    filter="url(#dot-shadow)",
                    class_="c6-segment",
                    style="cursor:pointer",
                    data_info=info,
                )
            )
        els.append(total_group)

        legend_x = c6_x + 26
        legend_y = c6_y + c6_h - 24
        for label, color in [("Fishing", focus_colors["fishing"]), ("Tourism", focus_colors["tourism"])] + (
            [("Other", focus_colors["other"])] if show_others else []
        ):
            els.append(svg.Circle(cx=legend_x, cy=legend_y - 4, r=6, fill=color))
            els.append(svg.Text(x=legend_x + 12, y=legend_y, text=label, class_="legend-text"))
            legend_x += 80

        size_guide_x = c6_x + c6_w - 84
        size_guide_y = c6_y + c6_h - 30
        els.append(svg.Circle(cx=size_guide_x, cy=size_guide_y - 4, r=12, fill="#d8e7f0", stroke="#9cb0c1"))
        els.append(svg.Circle(cx=size_guide_x + 30, cy=size_guide_y - 4, r=7, fill="#d8e7f0", stroke="#9cb0c1"))
        els.append(svg.Text(x=size_guide_x - 18, y=size_guide_y + 18, text="larger = more", class_="axis-note"))

        # ---- C7
        title_c7 = "Trip split overview" if mode == "visits" else "Trip time split overview"
        subtitle_c7 = "Center donut shows overall balance; outer ring stacks each trip"
        els.append(svg.Text(x=c7_x + 24, y=c7_y + 32, text=title_c7, class_="panel-title"))
        els.append(svg.Text(x=c7_x + 24, y=c7_y + 52, text=subtitle_c7, class_="panel-subtitle"))

        cx, cy = c7_x + c7_w * 0.48, c7_y + c7_h * 0.55
        inner_r, mid_r, outer_r = 56, 92, 172
        els.append(svg.Circle(cx=cx, cy=cy, r=outer_r + 8, fill="#fbfdff", stroke="#e0e9ef", stroke_width=1))

        def draw_split(df, pid_safe, is_total=False):
            g = svg.G(
                id=f"split_{pid_safe}",
                style="display:block" if is_total else "display:none",
                class_="split-info",
                elements=[],
            )
            if df.empty:
                g.elements.append(
                    svg.Text(
                        x=cx,
                        y=cy,
                        text="No matching activity",
                        text_anchor="middle",
                        font_size=14,
                        fill="#95a5a6",
                    )
                )
                return g

            m_data = df.copy()
            m_data["zone_mapped"] = m_data["zone_remapped"].map(name_map).fillna("other")
            if not show_others:
                m_data = m_data[m_data["zone_mapped"] != "other"]
            if m_data.empty:
                g.elements.append(
                    svg.Text(
                        x=cx,
                        y=cy,
                        text="No matching activity",
                        text_anchor="middle",
                        font_size=14,
                        fill="#95a5a6",
                    )
                )
                return g

            val_col = "num_visits" if mode == "visits" else "time_spend"
            m_data["val"] = m_data[val_col]
            z_sum = m_data.groupby("zone_mapped")["val"].sum()
            total = float(z_sum.sum() or 0)

            for rr in [mid_r + 24, mid_r + 60, outer_r]:
                g.elements.append(
                    svg.Circle(
                        cx=cx,
                        cy=cy,
                        r=rr,
                        fill="none",
                        stroke="#e6edf2",
                        stroke_width=1,
                        stroke_dasharray="2 4",
                    )
                )

            if mode == "time_spend":
                center_main = f"{total / 24:.2f}"
                center_sub = "days"
            else:
                center_main = f"{total:.0f}"
                center_sub = "visits"

            donut_info_base = (
                f"{'Total Overview' if is_total else 'Member Overview'} | Mode: {mode.title()} | Total: {fmt(total)} | "
                f"Primary: {z_sum.idxmax().capitalize() if not z_sum.empty else 'N/A'}"
            )

            cur_a = -90.0
            if len(z_sum) == 1:
                zone, val = list(z_sum.items())[0]
                pct = (float(val) / total) * 100 if total > 0 else 0
                seg_info = f"{donut_info_base} | {zone.capitalize()}: {pct:.1f}%"
                donut_g = DataG(class_="c7-segment", style="cursor:pointer", data_info=seg_info, elements=[])
                donut_g.elements.append(
                    svg.Circle(
                        cx=cx,
                        cy=cy,
                        r=(inner_r + mid_r) / 2,
                        fill="none",
                        stroke=focus_colors.get(zone, "#ccd5dd"),
                        stroke_width=(mid_r - inner_r),
                    )
                )
                g.elements.append(donut_g)
            else:
                for zone, val in z_sum.items():
                    sweep = (float(val) / max(total, 0.001)) * 360
                    if sweep <= 0:
                        continue
                    seg_info = f"{donut_info_base} | {zone.capitalize()}: {(float(val) / total) * 100:.1f}%"
                    d = _arc_wedge_path(cx, cy, mid_r, inner_r, cur_a, cur_a + sweep)
                    g.elements.append(
                        DataPath(
                            d=d,
                            fill=focus_colors.get(zone, "#ccd5dd"),
                            stroke="#ffffff",
                            stroke_width=2,
                            class_="c7-segment",
                            style="cursor:pointer",
                            data_info=seg_info,
                        )
                    )
                    cur_a += sweep

            trip_data = (
                m_data.groupby(["date", "trip_id", "zone_mapped"])["val"].sum().unstack(fill_value=0)
            )
            categories = ["fishing", "tourism", "other"]
            trip_data = trip_data.reindex(columns=categories, fill_value=0).reset_index()
            trip_data = trip_data.sort_values(["date", "trip_id"])
            n_t = len(trip_data)
            if n_t > 0:
                angle_step = 360 / n_t
                max_trip_val = float(trip_data[categories].sum(axis=1).max() or 1)
                base_r = mid_r + 12
                max_h = outer_r - base_r

                label_x = c7_x + c7_w - 74
                label_y = c7_y + 102
                for step in [0.33, 0.66, 1.0]:
                    ring_r = base_r + step * max_h
                    trip_scale_val = step * max_trip_val
                    g.elements.append(
                        svg.Text(
                            x=label_x,
                            y=label_y + (1.0 - step) * 28,
                            text=f"{trip_scale_val:.0f}" if mode == "visits" else f"{trip_scale_val:.1f}h",
                            class_="axis-note",
                            text_anchor="end",
                        )
                    )
                    g.elements.append(
                        svg.Line(
                            x1=label_x + 8,
                            y1=label_y - 4 + (1.0 - step) * 28,
                            x2=label_x + 36,
                            y2=label_y - 4 + (1.0 - step) * 28,
                            stroke="#cad6df",
                            stroke_width=1,
                        )
                    )

                for i, (_, row) in enumerate(trip_data.iterrows()):
                    ang_start = -90 + i * angle_step
                    current_r = base_r
                    trip_total = float(row[categories].sum())
                    date_string = (
                        row["date"].strftime("%Y-%m-%d")
                        if hasattr(row["date"], "strftime")
                        else str(row["date"])
                    )
                    trip_group = svg.G(elements=[])
                    for zone in categories:
                        val = float(row.get(zone, 0))
                        bar_h = (val / max_trip_val) * max_h
                        if bar_h <= 0:
                            continue
                        d = _arc_wedge_path(
                            cx,
                            cy,
                            current_r + bar_h,
                            current_r,
                            ang_start,
                            ang_start + angle_step * 0.86,
                        )
                        z_info = (
                            f"Trip Details | ID: {row['trip_id']} | Date: {date_string} | "
                            f"Total: {fmt(trip_total)} | Focus: {zone.capitalize()} | Value: {fmt(val)}"
                        )
                        trip_group.elements.append(
                            DataPath(
                                d=d,
                                fill=focus_colors.get(zone, "#ccd5dd"),
                                stroke="#ffffff",
                                stroke_width=1.1,
                                class_="c7-segment",
                                style="cursor:pointer",
                                data_info=z_info,
                            )
                        )
                        current_r += bar_h
                    g.elements.append(trip_group)

            g.elements.extend(
                [
                    svg.Circle(cx=cx, cy=cy, r=inner_r - 10, fill="#ffffff", stroke="#e4ebf0", stroke_width=1.2),
                    svg.Text(
                        x=cx,
                        y=cy - 6,
                        text=center_main,
                        id=f"t_val_{pid_safe}",
                        text_anchor="middle",
                        font_size=24,
                        font_weight="700",
                        fill="#213240",
                    ),
                    svg.Text(
                        x=cx,
                        y=cy + 16,
                        text=center_sub,
                        text_anchor="middle",
                        font_size=12,
                        fill="#73879a",
                    ),
                    svg.Text(
                        x=cx,
                        y=cy + 34,
                        text="overall balance",
                        text_anchor="middle",
                        font_size=11,
                        fill="#91a0ad",
                    ),
                ]
            )
            return g

        def _arc_wedge_path(cx_val, cy_val, r_outer, r_inner, start_angle, end_angle):
            def polar(radius, angle):
                rad = math.radians(angle - 90)
                return cx_val + radius * math.cos(rad), cy_val + radius * math.sin(rad)

            x1, y1 = polar(r_outer, start_angle)
            x2, y2 = polar(r_outer, end_angle)
            x3, y3 = polar(r_inner, end_angle)
            x4, y4 = polar(r_inner, start_angle)
            large_arc = 1 if (end_angle - start_angle) > 180 else 0
            return (
                f"M {x1:.2f} {y1:.2f} "
                f"A {r_outer:.2f} {r_outer:.2f} 0 {large_arc} 1 {x2:.2f} {y2:.2f} "
                f"L {x3:.2f} {y3:.2f} "
                f"A {r_inner:.2f} {r_inner:.2f} 0 {large_arc} 0 {x4:.2f} {y4:.2f} Z"
            )

        els.append(draw_split(graph_2_2_data, "total", is_total=True))
        for member in data_c5["people_id"].unique():
            pid_safe = member.replace(" ", "_")
            els.append(draw_split(graph_2_2_data[graph_2_2_data["people_id"] == member], pid_safe))

        leg_x = c7_x + 26
        leg_y = c7_y + 88
        for label, key in [("Fishing", "fishing"), ("Tourism", "tourism")] + ([("Other", "other")] if show_others else []):
            els.append(svg.Circle(cx=leg_x, cy=leg_y - 4, r=7, fill=focus_colors[key], stroke=focus_strokes[key], stroke_width=1))
            els.append(svg.Text(x=leg_x + 14, y=leg_y, text=label, class_="legend-text"))
            leg_x += 94

        return svg.SVG(width=W, height=H, viewBox=f"0 0 {W} {H}", elements=els).as_str()

    return (create_dashboard,)


@app.cell
def _(
    create_dashboard,
    date_slider,
    knn_dist_slider,
    knn_num_slider,
    mo,
    mode_dropdown,
    pd,
    sel_end,
    sel_start,
    show_others,
):
    svg_str = create_dashboard(mode_dropdown.value, show_others.value)

    _JS = """
    <style>
    body {
        font-family: Inter, "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
        margin: 0;
        background: #f4f8fb;
        position: relative;
    }
    #tooltip {
        position: absolute;
        background: rgba(255,255,255,0.98);
        border: 1px solid #d7e3ec;
        padding: 0;
        border-radius: 10px;
        pointer-events: none;
        display: none;
        font-size: 13px;
        box-shadow: 0 18px 40px rgba(44, 62, 80, 0.18);
        z-index: 10000;
        color: #2f3640;
        min-width: 210px;
        overflow: hidden;
        backdrop-filter: blur(6px);
    }
    .tt-header {
        background: linear-gradient(180deg, #f6fbff 0%, #eef5fb 100%);
        padding: 9px 12px;
        font-weight: 700;
        border-bottom: 1px solid #dde7ef;
        color: #314555;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    .tt-body { padding: 10px 12px; line-height: 1.55; }
    .tt-row {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 16px;
        align-items: start;
        margin-bottom: 4px;
    }
    .tt-label { color: #6a7d8f; }
    .tt-val { font-weight: 600; color: #253746; text-align: right; }
    .locked-person .member-node circle,
    .locked-person .member-node path,
    .locked-person .member-node rect,
    .locked-person .member-node line,
    .locked-person .member-node ellipse {
        filter: drop-shadow(0 0 10px rgba(45, 74, 96, 0.32));
    }
    </style>
    <div id="tooltip"></div>
    <script>
    (function() {
        let lockedPid = null;
        const tooltip = document.getElementById('tooltip');

        function formatInfo(info) {
            const parts = info.split(' | ');
            if (parts.length < 2) return info;
            let html = `<div class="tt-header">${parts[0]}</div><div class="tt-body">`;
            for (let i = 1; i < parts.length; i++) {
                const sub = parts[i].split(': ');
                if (sub.length === 2) {
                    html += `<div class="tt-row"><span class="tt-label">${sub[0]}</span><span class="tt-val">${sub[1]}</span></div>`;
                } else {
                    html += `<div style="margin-top:4px; font-weight:500;">${parts[i]}</div>`;
                }
            }
            html += '</div>';
            return html;
        }

        function showMember(pid) {
            document.querySelectorAll('.map-dot').forEach(d => d.style.display = 'none');
            document.querySelectorAll('.split-info').forEach(s => s.style.display = 'none');
            const mapTotal = document.getElementById('map_total');
            if (mapTotal) mapTotal.style.display = 'none';

            document.querySelectorAll('.visit_' + pid).forEach(d => d.style.display = '');
            const split = document.getElementById('split_' + pid);
            if (split) split.style.display = 'block';

            document.querySelectorAll('.clickable-person').forEach(p => p.classList.remove('locked-person'));
            const pEl = document.querySelector('.pid-' + pid);
            if (pEl) pEl.classList.add('locked-person');
        }

        function resetView() {
            if (lockedPid) return;
            document.querySelectorAll('.map-dot').forEach(d => d.style.display = 'none');
            document.querySelectorAll('.split-info').forEach(s => s.style.display = 'none');
            const mapTotal = document.getElementById('map_total');
            if (mapTotal) mapTotal.style.display = 'block';
            const splitTotal = document.getElementById('split_total');
            if (splitTotal) splitTotal.style.display = 'block';
            document.querySelectorAll('.clickable-person').forEach(p => p.classList.remove('locked-person'));
        }

        function init() {
            const persons = document.querySelectorAll('.clickable-person');
            const segments = document.querySelectorAll('.c7-segment, .c6-segment');

            persons.forEach(p => {
                const pidClass = [...p.classList].find(c => c.startsWith('pid-'));
                if (!pidClass) return;
                const pid = pidClass.replace('pid-', '');

                p.addEventListener('mouseenter', () => { if (!lockedPid) showMember(pid); });
                p.addEventListener('mouseleave', () => resetView());
                p.addEventListener('click', (e) => {
                    e.stopPropagation();
                    if (lockedPid === pid) {
                        lockedPid = null;
                        resetView();
                    } else {
                        lockedPid = pid;
                        showMember(pid);
                    }
                });
            });

            segments.forEach(seg => {
                seg.addEventListener('mouseenter', () => {
                    const info = seg.getAttribute('data-info');
                    if (info) {
                        tooltip.style.display = 'block';
                        tooltip.innerHTML = formatInfo(info);
                    }
                });
                seg.addEventListener('mousemove', (e) => {
                    const x = e.pageX + 16;
                    const y = e.pageY + 16;
                    tooltip.style.left = x + 'px';
                    tooltip.style.top = y + 'px';
                    const box = tooltip.getBoundingClientRect();
                    if (x + box.width > window.innerWidth) tooltip.style.left = (e.pageX - box.width - 16) + 'px';
                    if (y + box.height > window.innerHeight) tooltip.style.top = (e.pageY - box.height - 16) + 'px';
                });
                seg.addEventListener('mouseleave', () => {
                    tooltip.style.display = 'none';
                });
            });

            document.addEventListener('click', () => {
                lockedPid = null;
                resetView();
            });
        }

        let timer = setInterval(() => {
            if (document.querySelector('.clickable-person')) {
                clearInterval(timer);
                init();
            }
        }, 100);
    })();
    </script>
    """

    mo.vstack(
        [
            mo.hstack(
                [
                    mo.vstack(
                        [
                            mo.hstack([mo.md("Remapper: max distance limit (km)"), knn_dist_slider], align="center"),
                            mo.hstack([mo.md("Remapper: nearest locations"), knn_num_slider], align="center"),
                        ],
                        gap=1,
                    ),
                    mo.vstack(
                        [
                            mo.hstack([mo.md("Comparison mode"), mode_dropdown], align="center"),
                            mo.hstack([mo.md("Show 'Others'"), show_others], align="center"),
                            mo.hstack(
                                [
                                    mo.md(
                                        f"Filter Date: **{pd.to_datetime(sel_start).strftime('%Y-%m-%d')}** to **{pd.to_datetime(sel_end).strftime('%Y-%m-%d')}**"
                                    ),
                                    date_slider,
                                ],
                                align="center",
                            ),
                        ],
                        gap=1,
                    ),
                ],
                justify="start",
                gap=4,
            ),
            mo.iframe(svg_str + _JS, width="100%", height="880px"),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
