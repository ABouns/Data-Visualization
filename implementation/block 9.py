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
