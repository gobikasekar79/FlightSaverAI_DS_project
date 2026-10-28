"""
generate_sample_data.py
Generates synthetic but realistic sample datasets so FlightSaver AI works
out of the box:
  - data/Clean_Dataset.csv     (for the price prediction pipeline)
  - data/flight_data_2024.csv  (for the delay prediction pipeline)

Replace these with real datasets (e.g. the Kaggle "Flight Price Prediction"
dataset) any time - just keep the same column names.
"""

import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

AIRLINES = ["IndiGo", "Air India", "SpiceJet", "Vistara", "GoAir", "AirAsia"]
CITIES = ["Delhi", "Mumbai", "Bangalore", "Kolkata", "Hyderabad", "Chennai"]
DEPARTURE_TIMES = ["Early_Morning", "Morning", "Afternoon", "Evening", "Night", "Late_Night"]
CLASSES = ["Economy", "Business"]
STOPS = ["zero", "one", "two_or_more"]

AIRLINE_BASE_FARE = {
    "IndiGo": 4500, "Air India": 5800, "SpiceJet": 4200,
    "Vistara": 6200, "GoAir": 4300, "AirAsia": 4100,
}
AIRLINE_DELAY_BIAS = {
    "IndiGo": 0.12, "Air India": 0.28, "SpiceJet": 0.22,
    "Vistara": 0.10, "GoAir": 0.20, "AirAsia": 0.18,
}
TIME_PRICE_MULT = {
    "Early_Morning": 0.95, "Morning": 1.05, "Afternoon": 1.0,
    "Evening": 1.1, "Night": 0.98, "Late_Night": 0.9,
}
TIME_DELAY_MULT = {
    "Early_Morning": 0.8, "Morning": 0.9, "Afternoon": 1.05,
    "Evening": 1.3, "Night": 1.1, "Late_Night": 0.95,
}
STOPS_DELAY_MULT = {"zero": 0.8, "one": 1.15, "two_or_more": 1.4}


def build_price_dataset(n_rows: int = 6000) -> pd.DataFrame:
    rows = []
    for _ in range(n_rows):
        airline = np.random.choice(AIRLINES)
        source_city = np.random.choice(CITIES)
        destination_city = np.random.choice([c for c in CITIES if c != source_city])
        departure_time = np.random.choice(DEPARTURE_TIMES)
        flight_class = np.random.choice(CLASSES, p=[0.82, 0.18])
        days_left = int(np.random.randint(0, 51))
        duration = round(float(np.random.uniform(0.75, 12.0)), 2)

        base = AIRLINE_BASE_FARE[airline]
        class_mult = 3.2 if flight_class == "Business" else 1.0
        duration_add = duration * 350
        if days_left <= 2:
            urgency_mult = 1.55
        elif days_left <= 7:
            urgency_mult = 1.25
        elif days_left <= 20:
            urgency_mult = 1.05
        else:
            urgency_mult = 0.92
        time_mult = TIME_PRICE_MULT[departure_time]

        price = (base + duration_add) * class_mult * urgency_mult * time_mult
        price += np.random.normal(0, 250)  # market noise
        price = max(1200, price)

        rows.append({
            "airline": airline,
            "source_city": source_city,
            "destination_city": destination_city,
            "departure_time": departure_time,
            "class": flight_class,
            "days_left": days_left,
            "duration": duration,
            "price": round(price, 2),
        })
    return pd.DataFrame(rows)


def build_delay_dataset(n_rows: int = 6000) -> pd.DataFrame:
    rows = []
    for _ in range(n_rows):
        airline = np.random.choice(AIRLINES)
        source_city = np.random.choice(CITIES)
        destination_city = np.random.choice([c for c in CITIES if c != source_city])
        departure_time = np.random.choice(DEPARTURE_TIMES)
        stops = np.random.choice(STOPS, p=[0.55, 0.35, 0.10])

        bias = AIRLINE_DELAY_BIAS[airline]
        risk = bias * STOPS_DELAY_MULT[stops] * TIME_DELAY_MULT[departure_time]
        risk = min(0.95, max(0.02, risk))
        is_delayed = int(np.random.random() < risk)

        rows.append({
            "airline": airline,
            "source_city": source_city,
            "destination_city": destination_city,
            "departure_time": departure_time,
            "stops": stops,
            "is_delayed": is_delayed,
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    price_df = build_price_dataset()
    delay_df = build_delay_dataset()

    price_path = DATA_DIR / "Clean_Dataset.csv"
    delay_path = DATA_DIR / "flight_data_2024.csv"

    price_df.to_csv(price_path, index=False)
    delay_df.to_csv(delay_path, index=False)

    print(f"Wrote {len(price_df)} rows -> {price_path}")
    print(f"Wrote {len(delay_df)} rows -> {delay_path}")
