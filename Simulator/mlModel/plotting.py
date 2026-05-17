import numpy as np


def scale(value, source_min, source_max, target_min, target_max):
    if source_max == source_min:
        return (target_min + target_max) / 2
    ratio = (value - source_min) / (source_max - source_min)
    return target_min + ratio * (target_max - target_min)


def svg_text(x, y, text, size=14, anchor="start", fill="#1f2937"):
    return (
        f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" '
        f'font-size="{size}" text-anchor="{anchor}" fill="{fill}">{text}</text>'
    )


def create_regression_plot(output_path, train_x_values, train_y_values, test_x_values, test_y_values, weights, bias, feature_mean, feature_std):
    all_x_values = np.vstack((train_x_values, test_x_values))
    all_y_values = np.vstack((train_y_values, test_y_values))

    ghi_values = all_x_values[:, 0]
    capacity_values = all_y_values[:, 0]
    ghi_min = float(np.min(ghi_values))
    ghi_max = float(np.max(ghi_values))
    y_min = min(0.0, float(np.min(capacity_values)))
    y_max = max(1.0, float(np.max(capacity_values)))

    line_x_values = np.linspace(ghi_min, ghi_max, 120)
    line_features = np.column_stack((
        (line_x_values - feature_mean[0]) / feature_std[0],
        np.zeros(line_x_values.shape),
    ))
    line_y_values = (line_features @ weights + bias)[:, 0]
    y_min = min(y_min, float(np.min(line_y_values)))
    y_max = max(y_max, float(np.max(line_y_values)))

    width = 1200
    height = 760
    margin_left = 92
    margin_right = 36
    margin_top = 72
    margin_bottom = 82
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    def x_to_svg(value):
        return scale(value, ghi_min, ghi_max, margin_left, margin_left + plot_width)

    def y_to_svg(value):
        return scale(value, y_min, y_max, margin_top + plot_height, margin_top)

    elements = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760">',
        '<rect width="1200" height="760" fill="#ffffff"/>',
        svg_text(600, 34, "Linear Regression: Capacity Factor vs GHI", size=22, anchor="middle"),
        svg_text(600, 58, "Regression line uses Solar Zenith Angle fixed at the training mean", size=13, anchor="middle", fill="#4b5563"),
        f'<rect x="{margin_left}" y="{margin_top}" width="{plot_width}" height="{plot_height}" fill="#f9fafb" stroke="#d1d5db"/>',
    ]

    for tick_index in range(6):
        x_value = ghi_min + (ghi_max - ghi_min) * tick_index / 5
        x = x_to_svg(x_value)
        elements.append(f'<line x1="{x:.2f}" y1="{margin_top}" x2="{x:.2f}" y2="{margin_top + plot_height}" stroke="#e5e7eb"/>')
        elements.append(f'<line x1="{x:.2f}" y1="{margin_top + plot_height}" x2="{x:.2f}" y2="{margin_top + plot_height + 6}" stroke="#6b7280"/>')
        elements.append(svg_text(f"{x:.2f}", margin_top + plot_height + 24, f"{x_value:.0f}", size=12, anchor="middle", fill="#4b5563"))

        y_value = y_min + (y_max - y_min) * tick_index / 5
        y = y_to_svg(y_value)
        elements.append(f'<line x1="{margin_left}" y1="{y:.2f}" x2="{margin_left + plot_width}" y2="{y:.2f}" stroke="#e5e7eb"/>')
        elements.append(f'<line x1="{margin_left - 6}" y1="{y:.2f}" x2="{margin_left}" y2="{y:.2f}" stroke="#6b7280"/>')
        elements.append(svg_text(margin_left - 12, f"{y + 4:.2f}", f"{y_value:.2f}", size=12, anchor="end", fill="#4b5563"))

    elements.append('<g fill="#2563eb" fill-opacity="0.20">')
    for x_row, y_row in zip(train_x_values, train_y_values):
        elements.append(
            f'<circle cx="{x_to_svg(float(x_row[0])):.2f}" cy="{y_to_svg(float(y_row[0])):.2f}" r="1.4"/>'
        )
    elements.append("</g>")

    elements.append('<g fill="#f97316" fill-opacity="0.50">')
    for x_row, y_row in zip(test_x_values, test_y_values):
        elements.append(
            f'<circle cx="{x_to_svg(float(x_row[0])):.2f}" cy="{y_to_svg(float(y_row[0])):.2f}" r="2.2"/>'
        )
    elements.append("</g>")

    line_points = " ".join(
        f"{x_to_svg(float(x_value)):.2f},{y_to_svg(float(y_value)):.2f}"
        for x_value, y_value in zip(line_x_values, line_y_values)
    )
    elements.append(f'<polyline points="{line_points}" fill="none" stroke="#dc2626" stroke-width="3"/>')
    elements.append(f'<line x1="{margin_left}" y1="{margin_top + plot_height}" x2="{margin_left + plot_width}" y2="{margin_top + plot_height}" stroke="#374151"/>')
    elements.append(f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_height}" stroke="#374151"/>')
    elements.append(svg_text(600, height - 28, "GHI", size=15, anchor="middle"))
    elements.append(
        '<text x="26" y="380" font-family="Arial, sans-serif" font-size="15" '
        'text-anchor="middle" fill="#1f2937" transform="rotate(-90 26 380)">capacity_factor</text>'
    )
    elements.append('<circle cx="932" cy="34" r="5" fill="#2563eb" fill-opacity="0.45"/>')
    elements.append(svg_text(944, 39, "Training rows", size=12, fill="#4b5563"))
    elements.append('<circle cx="1038" cy="34" r="5" fill="#f97316" fill-opacity="0.65"/>')
    elements.append(svg_text(1050, 39, "Testing rows", size=12, fill="#4b5563"))
    elements.append('<line x1="932" y1="54" x2="960" y2="54" stroke="#dc2626" stroke-width="3"/>')
    elements.append(svg_text(970, 59, "Regression line", size=12, fill="#4b5563"))
    elements.append("</svg>")

    output_path.write_text("\n".join(elements))


def create_effectiveness_plot(output_path, train_y_values, train_predictions, test_y_values, test_predictions):
    actual_values = np.vstack((train_y_values, test_y_values))[:, 0]
    predicted_values = np.vstack((train_predictions, test_predictions))[:, 0]

    axis_min = min(0.0, float(np.min(actual_values)), float(np.min(predicted_values)))
    axis_max = max(1.0, float(np.max(actual_values)), float(np.max(predicted_values)))

    width = 980
    height = 760
    margin_left = 92
    margin_right = 42
    margin_top = 76
    margin_bottom = 82
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    def x_to_svg(value):
        return scale(value, axis_min, axis_max, margin_left, margin_left + plot_width)

    def y_to_svg(value):
        return scale(value, axis_min, axis_max, margin_top + plot_height, margin_top)

    elements = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="980" height="760" viewBox="0 0 980 760">',
        '<rect width="980" height="760" fill="#ffffff"/>',
        svg_text(490, 34, "Model Effectiveness: Actual vs Predicted", size=22, anchor="middle"),
        svg_text(490, 58, "Predictions use both GHI and Solar Zenith Angle", size=13, anchor="middle", fill="#4b5563"),
        f'<rect x="{margin_left}" y="{margin_top}" width="{plot_width}" height="{plot_height}" fill="#f9fafb" stroke="#d1d5db"/>',
    ]

    for tick_index in range(6):
        tick_value = axis_min + (axis_max - axis_min) * tick_index / 5
        x = x_to_svg(tick_value)
        y = y_to_svg(tick_value)
        elements.append(f'<line x1="{x:.2f}" y1="{margin_top}" x2="{x:.2f}" y2="{margin_top + plot_height}" stroke="#e5e7eb"/>')
        elements.append(f'<line x1="{x:.2f}" y1="{margin_top + plot_height}" x2="{x:.2f}" y2="{margin_top + plot_height + 6}" stroke="#6b7280"/>')
        elements.append(svg_text(f"{x:.2f}", margin_top + plot_height + 24, f"{tick_value:.2f}", size=12, anchor="middle", fill="#4b5563"))
        elements.append(f'<line x1="{margin_left}" y1="{y:.2f}" x2="{margin_left + plot_width}" y2="{y:.2f}" stroke="#e5e7eb"/>')
        elements.append(f'<line x1="{margin_left - 6}" y1="{y:.2f}" x2="{margin_left}" y2="{y:.2f}" stroke="#6b7280"/>')
        elements.append(svg_text(margin_left - 12, f"{y + 4:.2f}", f"{tick_value:.2f}", size=12, anchor="end", fill="#4b5563"))

    ideal_line = (
        f'{x_to_svg(axis_min):.2f},{y_to_svg(axis_min):.2f} '
        f'{x_to_svg(axis_max):.2f},{y_to_svg(axis_max):.2f}'
    )
    elements.append(f'<polyline points="{ideal_line}" fill="none" stroke="#16a34a" stroke-width="3"/>')

    elements.append('<g fill="#2563eb" fill-opacity="0.18">')
    for actual_row, predicted_row in zip(train_y_values, train_predictions):
        elements.append(
            f'<circle cx="{x_to_svg(float(actual_row[0])):.2f}" cy="{y_to_svg(float(predicted_row[0])):.2f}" r="1.4"/>'
        )
    elements.append("</g>")

    elements.append('<g fill="#f97316" fill-opacity="0.55">')
    for actual_row, predicted_row in zip(test_y_values, test_predictions):
        elements.append(
            f'<circle cx="{x_to_svg(float(actual_row[0])):.2f}" cy="{y_to_svg(float(predicted_row[0])):.2f}" r="2.2"/>'
        )
    elements.append("</g>")

    elements.append(f'<line x1="{margin_left}" y1="{margin_top + plot_height}" x2="{margin_left + plot_width}" y2="{margin_top + plot_height}" stroke="#374151"/>')
    elements.append(f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_height}" stroke="#374151"/>')
    elements.append(svg_text(490, height - 28, "Actual capacity_factor", size=15, anchor="middle"))
    elements.append(
        '<text x="26" y="380" font-family="Arial, sans-serif" font-size="15" '
        'text-anchor="middle" fill="#1f2937" transform="rotate(-90 26 380)">Predicted capacity_factor</text>'
    )
    elements.append('<circle cx="672" cy="34" r="5" fill="#2563eb" fill-opacity="0.45"/>')
    elements.append(svg_text(684, 39, "Training rows", size=12, fill="#4b5563"))
    elements.append('<circle cx="778" cy="34" r="5" fill="#f97316" fill-opacity="0.65"/>')
    elements.append(svg_text(790, 39, "Testing rows", size=12, fill="#4b5563"))
    elements.append('<line x1="672" y1="54" x2="700" y2="54" stroke="#16a34a" stroke-width="3"/>')
    elements.append(svg_text(710, 59, "Ideal y=x", size=12, fill="#4b5563"))
    elements.append("</svg>")

    output_path.write_text("\n".join(elements))
