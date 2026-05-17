import csv
import json
from datetime import datetime, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset" / "ToTrain.csv"
MODEL_PATH = BASE_DIR / "linear_regression_model.json"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"
MAX_GENERATION_KW = 5.0


class SolarGenerationPredictor:
    def __init__(self, dataset_path=DATASET_PATH, model_path=MODEL_PATH):
        self.dataset_path = Path(dataset_path)
        self.model_path = Path(model_path)

        model = self._read_model()
        self.feature_columns = model["feature_columns"]
        self.feature_mean = model["feature_mean"]
        self.feature_std = model["feature_std"]
        self.weights = model["weights"]
        self.bias = model["bias"]

        self.features_by_timestamp, self.hourly_features = self._read_hourly_features()
        self.start_timestamp = min(self.features_by_timestamp)

    def _read_model(self):
        with self.model_path.open() as source:
            return json.load(source)

    def _read_hourly_features(self):
        features_by_timestamp = {}
        hourly_features = []

        with self.dataset_path.open(newline="") as source:
            for row in csv.DictReader(source):
                timestamp = datetime.strptime(row["timestamp"], TIMESTAMP_FORMAT)
                features = [float(row[column]) for column in self.feature_columns]

                features_by_timestamp[timestamp] = features
                hourly_features.append(features)

        if not hourly_features:
            raise ValueError(f"No hourly records found in {self.dataset_path}")

        return features_by_timestamp, hourly_features

    def features_at(self, timestamp):
        if timestamp in self.features_by_timestamp:
            return self.features_by_timestamp[timestamp]

        elapsed_hours = int((timestamp - self.start_timestamp).total_seconds() // 3600)
        return self.hourly_features[elapsed_hours % len(self.hourly_features)]

    def features_for_simulation_time(self, sim_day, hour):
        timestamp = self.start_timestamp + timedelta(days=int(sim_day), hours=int(hour))
        return self.features_at(timestamp)

    def predict_capacity_factor(self, features):
        normalized_features = [
            (value - mean) / std
            for value, mean, std in zip(features, self.feature_mean, self.feature_std)
        ]
        return sum(
            value * weight
            for value, weight in zip(normalized_features, self.weights)
        ) + self.bias

    def predict_kw(self, sim_day, hour, peak_solar_generation_kw):
        features = self.features_for_simulation_time(sim_day, hour)
        capacity_factor = self.predict_capacity_factor(features)
        generation_kw = capacity_factor * peak_solar_generation_kw
        return max(0.0, min(MAX_GENERATION_KW, generation_kw))


_predictor = None


def get_predictor():
    global _predictor
    if _predictor is None:
        _predictor = SolarGenerationPredictor()
    return _predictor
