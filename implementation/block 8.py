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
