c2_scene_width = 980
c2_scene_height = 620

c2_member_rows = []
for row in c2_filtered_visits:
    c2_member_rows.append(
        {
            "member": row["member"],
            "category": row["category"],
            "duration_hours": float(row["duration_hours"]),
        }
    )

c2_member_summary = {}
for row in c2_member_rows:
    member = row["member"]
    if member not in c2_member_summary:
        c2_member_summary[member] = {
            "member": member,
            "Fishing": 0.0,
            "Tourism": 0.0,
            "Hybrid": 0.0,
            "Neutral": 0.0,
            "total_hours": 0.0,
        }

    c2_member_summary[member][row["category"]] += row["duration_hours"]
    c2_member_summary[member]["total_hours"] += row["duration_hours"]

c2_people = []
for item in c2_member_summary.values():
    fishing_value = item["Fishing"] + 0.5 * item["Hybrid"]
    tourism_value = item["Tourism"] + 0.5 * item["Hybrid"]
    bias_gap = tourism_value - fishing_value

    c2_people.append(
        {
            "member": item["member"],
            "Fishing": fishing_value,
            "Tourism": tourism_value,
            "Hybrid": item["Hybrid"],
            "Neutral": item["Neutral"],
            "total_hours": item["total_hours"],
            "bias_gap": bias_gap,
        }
    )

if c2_people:
    c2_bias_min = min(item["bias_gap"] for item in c2_people)
    c2_bias_max = max(item["bias_gap"] for item in c2_people)
else:
    c2_bias_min = -1.0
    c2_bias_max = 1.0


def c2_bias_to_x(value):
    left_x = 0.26
    right_x = 0.82
    if abs(c2_bias_max - c2_bias_min) < 1e-9:
        return (left_x + right_x) / 2
    scaled = (value - c2_bias_min) / (c2_bias_max - c2_bias_min)
    return left_x + scaled * (right_x - left_x)


def c2_blend_hex(color_a, color_b, t):
    t = max(0.0, min(1.0, t))
    a = color_a.lstrip("#")
    b = color_b.lstrip("#")
    ar, ag, ab = int(a[0:2], 16), int(a[2:4], 16), int(a[4:6], 16)
    br, bg, bb = int(b[0:2], 16), int(b[2:4], 16), int(b[4:6], 16)
    rr = round(ar + (br - ar) * t)
    rg = round(ag + (bg - ag) * t)
    rb = round(ab + (bb - ab) * t)
    return f"#{rr:02x}{rg:02x}{rb:02x}"


def c2_bias_color(bias_gap, max_abs_bias):
    neutral = "#6f6f6f"
    fishing = CATEGORY_COLORS["Fishing"]
    tourism = CATEGORY_COLORS["Tourism"]

    if max_abs_bias <= 1e-9:
        return neutral

    if bias_gap < 0:
        return c2_blend_hex(neutral, fishing, abs(bias_gap) / max_abs_bias)
    return c2_blend_hex(neutral, tourism, abs(bias_gap) / max_abs_bias)


c2_people.sort(key=lambda item: item["bias_gap"])
c2_max_abs_bias = max([abs(item["bias_gap"]) for item in c2_people] + [0.25])

for item in c2_people:
    item["scene_x_ratio"] = c2_bias_to_x(item["bias_gap"])

    if item["scene_x_ratio"] <= 0.31:
        item["anchor"] = "boat"
        item["foot_y_ratio"] = 0.37
        item["label_x_ratio"] = item["scene_x_ratio"] - 0.02
        item["label_y_ratio"] = 0.60
        item["label_anchor"] = "end"
    elif item["scene_x_ratio"] >= 0.74:
        item["anchor"] = "shore"
        item["foot_y_ratio"] = 0.32
        item["label_x_ratio"] = item["scene_x_ratio"] + 0.02
        item["label_y_ratio"] = 0.56
        item["label_anchor"] = "start"
    else:
        item["anchor"] = "float"
        item["foot_y_ratio"] = 0.27
        item["label_x_ratio"] = item["scene_x_ratio"]
        item["label_y_ratio"] = 0.54
        item["label_anchor"] = "middle"

    item["head_y_ratio"] = item["foot_y_ratio"] + 0.10
    item["color"] = c2_bias_color(item["bias_gap"], c2_max_abs_bias)


def c2_sx(x_ratio):
    return round(x_ratio * c2_scene_width, 1)


def c2_sy(y_ratio):
    return round((1 - y_ratio) * c2_scene_height, 1)


def c2_draw_person(svg_parts, x_ratio, foot_y_ratio, stroke_color):
    x = c2_sx(x_ratio)
    foot_y = c2_sy(foot_y_ratio)
    knee_y = c2_sy(foot_y_ratio + 0.07)
    arm_y = c2_sy(foot_y_ratio + 0.045)
    left_hand_x = c2_sx(x_ratio - 0.045)
    right_hand_x = c2_sx(x_ratio + 0.045)
    left_foot_x = c2_sx(x_ratio - 0.035)
    right_foot_x = c2_sx(x_ratio + 0.035)
    head_y = c2_sy(foot_y_ratio + 0.10)

    svg_parts.append(
        f'<line x1="{x}" y1="{foot_y}" x2="{x}" y2="{knee_y}" stroke="{stroke_color}" stroke-width="2.2" stroke-linecap="round"/>'
    )
    svg_parts.append(
        f'<line x1="{left_hand_x}" y1="{arm_y}" x2="{right_hand_x}" y2="{arm_y}" stroke="{stroke_color}" stroke-width="2.2" stroke-linecap="round"/>'
    )
    svg_parts.append(
        f'<line x1="{x}" y1="{foot_y}" x2="{left_foot_x}" y2="{c2_sy(foot_y_ratio - 0.035)}" stroke="{stroke_color}" stroke-width="2.2" stroke-linecap="round"/>'
    )
    svg_parts.append(
        f'<line x1="{x}" y1="{foot_y}" x2="{right_foot_x}" y2="{c2_sy(foot_y_ratio - 0.035)}" stroke="{stroke_color}" stroke-width="2.2" stroke-linecap="round"/>'
    )
    svg_parts.append(
        f'<circle cx="{x}" cy="{head_y}" r="7.5" fill="none" stroke="{stroke_color}" stroke-width="2.2"/>'
    )


c2_svg = []
c2_svg.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{c2_scene_width}" height="{c2_scene_height}" viewBox="0 0 {c2_scene_width} {c2_scene_height}">'
)
c2_svg.append(
    f'<rect x="0" y="0" width="{c2_scene_width}" height="{c2_scene_height}" fill="#fbfaf7" rx="20" ry="20"/>'
)

c2_svg.append(
    f'<rect x="{c2_sx(0.05)}" y="{c2_sy(0.95)}" width="{c2_sx(0.95) - c2_sx(0.05)}" height="{c2_sy(0.52) - c2_sy(0.95)}" fill="#fbf4e8"/>'
)
c2_svg.append(
    f'<rect x="{c2_sx(0.05)}" y="{c2_sy(0.28)}" width="{c2_sx(0.67) - c2_sx(0.05)}" height="{c2_sy(0.05) - c2_sy(0.28)}" fill="#cfe2ec"/>'
)
c2_svg.append(
    f'<polygon points="{c2_sx(0.67)},{c2_sy(0.05)} {c2_sx(0.95)},{c2_sy(0.05)} {c2_sx(0.95)},{c2_sy(0.34)} {c2_sx(0.81)},{c2_sy(0.34)} {c2_sx(0.76)},{c2_sy(0.32)} {c2_sx(0.73)},{c2_sy(0.30)} {c2_sx(0.67)},{c2_sy(0.28)}" fill="#ead8ab"/>'
)
c2_svg.append(
    f'<line x1="{c2_sx(0.05)}" y1="{c2_sy(0.28)}" x2="{c2_sx(0.95)}" y2="{c2_sy(0.28)}" stroke="#403d39" stroke-width="1.4"/>'
)

c2_svg.append(
    f'<polygon points="{c2_sx(0.11)},{c2_sy(0.39)} {c2_sx(0.28)},{c2_sy(0.39)} {c2_sx(0.245)},{c2_sy(0.28)} {c2_sx(0.165)},{c2_sy(0.28)}" fill="#97633e" stroke="#4b3a30" stroke-width="2"/>'
)
c2_svg.append(
    f'<line x1="{c2_sx(0.16)}" y1="{c2_sy(0.39)}" x2="{c2_sx(0.16)}" y2="{c2_sy(0.59)}" stroke="#4b3a30" stroke-width="2.2"/>'
)
c2_svg.append(
    f'<line x1="{c2_sx(0.16)}" y1="{c2_sy(0.59)}" x2="{c2_sx(0.20)}" y2="{c2_sy(0.58)}" stroke="#4b3a30" stroke-width="1.8"/>'
)
c2_svg.append(
    f'<path d="M {c2_sx(0.16)} {c2_sy(0.59)} Q {c2_sx(0.10)} {c2_sy(0.45)} {c2_sx(0.09)} {c2_sy(0.26)}" fill="none" stroke="#4b3a30" stroke-width="1.8"/>'
)
c2_svg.append(
    f'<line x1="{c2_sx(0.11)}" y1="{c2_sy(0.39)}" x2="{c2_sx(0.30)}" y2="{c2_sy(0.39)}" stroke="#4b3a30" stroke-width="1.8"/>'
)

for item in c2_people:
    if item["anchor"] == "float":
        c2_svg.append(
            f'<rect x="{c2_sx(item["scene_x_ratio"] - 0.035)}" y="{c2_sy(item["foot_y_ratio"] - 0.002)}" width="{c2_sx(0.07) - c2_sx(0)}" height="7" fill="#9a7a54" stroke="#4b3a30" stroke-width="1"/>'
        )

    c2_draw_person(c2_svg, item["scene_x_ratio"], item["foot_y_ratio"], item["color"])
    c2_svg.append(
        f'<line x1="{c2_sx(item["scene_x_ratio"])}" y1="{c2_sy(item["head_y_ratio"] + 0.02)}" x2="{c2_sx(item["label_x_ratio"])}" y2="{c2_sy(item["label_y_ratio"] - 0.02)}" stroke="#8d877d" stroke-width="1" stroke-dasharray="4,4"/>'
    )

    if item["label_anchor"] == "start":
        c2_text_anchor = "start"
    elif item["label_anchor"] == "end":
        c2_text_anchor = "end"
    else:
        c2_text_anchor = "middle"

    c2_svg.append(
        f'<text x="{c2_sx(item["label_x_ratio"])}" y="{c2_sy(item["label_y_ratio"])}" font-size="14" font-weight="700" text-anchor="{c2_text_anchor}" fill="{item["color"]}">{escape(item["member"])}</text>'
    )
    c2_svg.append(
        f'<text x="{c2_sx(item["label_x_ratio"])}" y="{c2_sy(item["label_y_ratio"]) + 18}" font-size="12" text-anchor="{c2_text_anchor}" fill="{item["color"]}">{item["bias_gap"]:+.2f}</text>'
    )

c2_svg.append(
    f'<line x1="{c2_sx(0.29)}" y1="{c2_sy(0.64)}" x2="{c2_sx(0.82)}" y2="{c2_sy(0.64)}" stroke="#403d39" stroke-width="2"/>'
)
c2_svg.append(
    f'<polygon points="{c2_sx(0.29)},{c2_sy(0.64)} {c2_sx(0.305)},{c2_sy(0.648)} {c2_sx(0.305)},{c2_sy(0.632)}" fill="#403d39"/>'
)
c2_svg.append(
    f'<polygon points="{c2_sx(0.82)},{c2_sy(0.64)} {c2_sx(0.805)},{c2_sy(0.648)} {c2_sx(0.805)},{c2_sy(0.632)}" fill="#403d39"/>'
)

c2_svg.append(
    f'<text x="{c2_sx(0.555)}" y="{c2_sy(0.68)}" font-size="15" font-weight="700" text-anchor="middle" fill="#403d39">Bias gap = Tourism sentiment minus Fishing sentiment</text>'
)
c2_svg.append(
    f'<text x="{c2_sx(0.17)}" y="{c2_sy(0.58)}" font-size="13" fill="{CATEGORY_COLORS["Fishing"]}">warmer to fishing</text>'
)
c2_svg.append(
    f'<text x="{c2_sx(0.79)}" y="{c2_sy(0.58)}" font-size="13" fill="{CATEGORY_COLORS["Tourism"]}">warmer to tourism</text>'
)

c2_svg.append(
    f'<text x="{c2_sx(0.055)}" y="{c2_sy(0.94)}" font-size="30" font-weight="700" fill="#202020">From Boat to Beach: Where Members Lean</text>'
)
c2_svg.append(
    f'<text x="{c2_sx(0.055)}" y="{c2_sy(0.89)}" font-size="17" fill="#202020">Members move toward the fishing boat or the tourist shore based on their travel-linked focus.</text>'
)

c2_svg.append(
    f'<rect x="{c2_sx(0.11)}" y="{c2_sy(0.145)}" width="110" height="30" rx="8" ry="8" fill="{CATEGORY_COLORS["Fishing"]}"/>'
)
c2_svg.append(
    f'<text x="{c2_sx(0.165)}" y="{c2_sy(0.125)}" font-size="13" font-weight="700" text-anchor="middle" fill="white">Fishing boat</text>'
)

c2_svg.append(
    f'<rect x="{c2_sx(0.82)}" y="{c2_sy(0.145)}" width="120" height="30" rx="8" ry="8" fill="{CATEGORY_COLORS["Tourism"]}"/>'
)
c2_svg.append(
    f'<text x="{c2_sx(0.88)}" y="{c2_sy(0.125)}" font-size="13" font-weight="700" text-anchor="middle" fill="white">Tourist shore</text>'
)

c2_note = (
    "Placement uses tourism minus fishing allocated hours from the filtered trip data. "
    "Hybrid time contributes half to each side."
)
c2_svg.append(
    f'<text x="{c2_sx(0.055)}" y="{c2_sy(0.02)}" font-size="11" fill="#2c2c2c">{escape(c2_note)}</text>'
)

if not c2_people:
    c2_svg.append(
        f'<text x="{c2_scene_width / 2:.1f}" y="{c2_scene_height / 2:.1f}" text-anchor="middle" font-size="22" fill="#6b7280">No member data after current filters</text>'
    )

c2_svg.append("</svg>")

c2_fishing_full_svg = "".join(c2_svg)

mo.Html(c2_fishing_full_svg)
