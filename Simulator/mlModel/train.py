import csv
import json
from pathlib import Path

import numpy as np

from plotting import create_effectiveness_plot, create_regression_plot


BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset" / "ToTrain.csv"
MODEL_OUTPUT_PATH = BASE_DIR / "linear_regression_model.json"
PLOT_OUTPUT_PATH = BASE_DIR / "linear_regression_plot.svg"
EFFECTIVENESS_PLOT_OUTPUT_PATH = BASE_DIR / "model_effectiveness_plot.svg"

FEATURE_COLUMNS = ["GHI", "Solar Zenith Angle"]
TARGET_COLUMN = "capacity_factor"


def load_training_data(path):
    train_x_values = []
    train_y_values = []
    test_x_values = []
    test_y_values = []
    test_metadata = []

    with path.open(newline="") as source:
        reader = csv.DictReader(source)
        missing_columns = [
            column
            for column in [*FEATURE_COLUMNS, TARGET_COLUMN]
            if column not in reader.fieldnames
        ]
        if missing_columns:
            raise ValueError(f"Missing required columns in {path}: {missing_columns}")

        for row_index, row in enumerate(reader, start=1):
            x_row = [float(row[column]) for column in FEATURE_COLUMNS]
            y_row = [float(row[TARGET_COLUMN])]

            if row_index % 10 == 0:
                test_x_values.append(x_row)
                test_y_values.append(y_row)
                test_metadata.append({
                    "row_index": row_index,
                    "timestamp": row["timestamp"],
                })
            else:
                train_x_values.append(x_row)
                train_y_values.append(y_row)

    if not train_x_values:
        raise ValueError(f"No training rows found in {path}")
    if not test_x_values:
        raise ValueError(f"No testing rows found in {path}")

    return (
        np.array(train_x_values, dtype=float),
        np.array(train_y_values, dtype=float),
        np.array(test_x_values, dtype=float),
        np.array(test_y_values, dtype=float),
        test_metadata,
    )


def normalize_features(x_values):
    mean = np.mean(x_values, axis=0)
    std = np.std(x_values, axis=0)
    std[std == 0] = 1.0

    return (x_values - mean) / std, mean, std


def compute_cost(x_values, y_values, weights, bias):
    row_count = x_values.shape[0]
    predictions = x_values @ weights + bias
    errors = predictions - y_values
    return float((1 / (2 * row_count)) * np.sum(errors ** 2))


def compute_gradients(x_values, y_values, weights, bias):
    row_count = x_values.shape[0]
    predictions = x_values @ weights + bias
    errors = predictions - y_values

    weight_gradient = (1 / row_count) * (x_values.T @ errors)
    bias_gradient = float((1 / row_count) * np.sum(errors))

    return weight_gradient, bias_gradient


def train_linear_regression(x_values, y_values, alpha=0.1, epochs=5000, print_every=500):
    _, feature_count = x_values.shape
    weights = np.zeros((feature_count, 1))
    bias = 0.0
    cost_history = []

    for epoch in range(epochs + 1):
        cost = compute_cost(x_values, y_values, weights, bias)
        cost_history.append(cost)

        if epoch % print_every == 0:
            print(f"Epoch {epoch}: cost = {cost:.10f}", flush=True)

        if epoch == epochs:
            break

        weight_gradient, bias_gradient = compute_gradients(x_values, y_values, weights, bias)
        weights = weights - alpha * weight_gradient
        bias = bias - alpha * bias_gradient

    return weights, bias, cost_history


def predict(x_values, weights, bias):
    return x_values @ weights + bias


def evaluate_tests(test_x_values, test_y_values, test_metadata, weights, bias):
    predictions = predict(test_x_values, weights, bias)
    absolute_errors = []

    print("\n--- Test executions ---")
    for index, (prediction_row, expected_row, metadata) in enumerate(
        zip(predictions, test_y_values, test_metadata),
        start=1,
    ):
        predicted = float(prediction_row[0])
        expected = float(expected_row[0])
        absolute_error = abs(predicted - expected)
        absolute_errors.append(absolute_error)

        print(
            f"Test {index} | row {metadata['row_index']} | "
            f"timestamp {metadata['timestamp']} | "
            f"expected={expected:.8f} | predicted={predicted:.8f} | "
            f"abs_error={absolute_error:.8f}"
        )

    mean_absolute_error = float(np.mean(absolute_errors))
    print(f"Mean absolute error: {mean_absolute_error:.8f}")

    return {
        "test_rows": int(test_y_values.shape[0]),
        "mean_absolute_error": mean_absolute_error,
    }, predictions


def save_model(weights, bias, feature_mean, feature_std, cost_history, alpha, epochs, test_metrics):
    model = {
        "model_type": "linear_regression",
        "target_column": TARGET_COLUMN,
        "feature_columns": FEATURE_COLUMNS,
        "feature_mean": feature_mean.tolist(),
        "feature_std": feature_std.tolist(),
        "weights": weights.flatten().tolist(),
        "bias": bias,
        "alpha": alpha,
        "epochs": epochs,
        "initial_cost": cost_history[0],
        "final_cost": cost_history[-1],
        "test_metrics": test_metrics,
        "plot_paths": {
            "feature_slice": str(PLOT_OUTPUT_PATH.relative_to(BASE_DIR.parent)),
            "effectiveness": str(EFFECTIVENESS_PLOT_OUTPUT_PATH.relative_to(BASE_DIR.parent)),
        },
    }

    with MODEL_OUTPUT_PATH.open("w") as output:
        json.dump(model, output, indent=2)


def main():
    alpha = 0.1
    epochs = 1000
    print_every = 100

    train_x_values, train_y_values, test_x_values, test_y_values, test_metadata = load_training_data(DATASET_PATH)
    train_x_normalized, feature_mean, feature_std = normalize_features(train_x_values)
    test_x_normalized = (test_x_values - feature_mean) / feature_std

    print(f"Training rows: {train_x_values.shape[0]}")
    print(f"Testing rows: {test_x_values.shape[0]}")

    weights, bias, cost_history = train_linear_regression(
        train_x_normalized,
        train_y_values,
        alpha=alpha,
        epochs=epochs,
        print_every=print_every,
    )
    test_metrics, test_predictions = evaluate_tests(
        test_x_normalized,
        test_y_values,
        test_metadata,
        weights,
        bias,
    )
    train_predictions = predict(train_x_normalized, weights, bias)
    create_regression_plot(
        PLOT_OUTPUT_PATH,
        train_x_values,
        train_y_values,
        test_x_values,
        test_y_values,
        weights,
        bias,
        feature_mean,
        feature_std,
    )
    create_effectiveness_plot(
        EFFECTIVENESS_PLOT_OUTPUT_PATH,
        train_y_values,
        train_predictions,
        test_y_values,
        test_predictions,
    )
    save_model(weights, bias, feature_mean, feature_std, cost_history, alpha, epochs, test_metrics)

    print(f"Final cost: {cost_history[-1]:.10f}")
    print(f"Weights: {weights.flatten().tolist()}")
    print(f"Bias: {bias}")
    print(f"Model saved to: {MODEL_OUTPUT_PATH.relative_to(BASE_DIR.parent)}")
    print(f"Plot saved to: {PLOT_OUTPUT_PATH.relative_to(BASE_DIR.parent)}")
    print(f"Effectiveness plot saved to: {EFFECTIVENESS_PLOT_OUTPUT_PATH.relative_to(BASE_DIR.parent)}")


if __name__ == "__main__":
    main()
