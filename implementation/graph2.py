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


if __name__ == "__main__":
    app.run()
