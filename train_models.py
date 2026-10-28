"""
train_models.py
Trains both ML pipelines and saves artifacts into models/:
  - rf_price_model.pkl    (RandomForestRegressor)
  - encoders.pkl          (dict of LabelEncoders for price features)
  - xgb_delay_model.pkl   (XGBClassifier)
  - delay_encoders.pkl    (dict of LabelEncoders for delay features)

Usage (from project root):
    python train_models.py
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
MODEL_DIR = PROJECT_ROOT / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Must match app/utils/ml_utils.py
PRICE_FEATURES = ["airline", "source_city", "destination_city",
                  "departure_time", "class", "days_left", "duration"]
PRICE_CATEGORICAL = ["airline", "source_city", "destination_city", "departure_time", "class"]

DELAY_FEATURES = ["airline", "source_city", "destination_city", "departure_time", "stops"]
DELAY_CATEGORICAL = DELAY_FEATURES  # all categorical


def encode(df, categorical_cols):
    encoders = {}
    df = df.copy()
    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le
    return df, encoders


def train_price_model():
    path = DATA_DIR / "Clean_Dataset.csv"
    if not path.exists():
        print("Clean_Dataset.csv missing - run generate_sample_data.py first.")
        return
    df = pd.read_csv(path)
    df = df[PRICE_FEATURES + ["price"]].dropna()
    df, encoders = encode(df, PRICE_CATEGORICAL)

    X, y = df[PRICE_FEATURES], df["price"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=150, max_depth=18, n_jobs=-1, random_state=42)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    print(f"[Price] R2={r2_score(y_test, pred):.3f}  MAE=Rs.{mean_absolute_error(y_test, pred):,.0f}")

    joblib.dump(model, MODEL_DIR / "rf_price_model.pkl")
    joblib.dump(encoders, MODEL_DIR / "encoders.pkl")
    print("Saved rf_price_model.pkl + encoders.pkl")


def train_delay_model():
    path = DATA_DIR / "flight_data_2024.csv"
    if not path.exists():
        print("flight_data_2024.csv missing - run generate_sample_data.py first.")
        return
    df = pd.read_csv(path)
    df = df[DELAY_FEATURES + ["is_delayed"]].dropna()
    df, encoders = encode(df, DELAY_CATEGORICAL)

    X, y = df[DELAY_FEATURES], df["is_delayed"].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    try:
        from xgboost import XGBClassifier
        model = XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.08,
                              eval_metric="logloss", random_state=42)
    except ImportError:
        print("xgboost not installed - using sklearn GradientBoostingClassifier instead.")
        from sklearn.ensemble import GradientBoostingClassifier
        model = GradientBoostingClassifier(random_state=42)

    model.fit(X_train, y_train)
    acc = accuracy_score(y_test, model.predict(X_test))
    print(f"[Delay] Accuracy={acc:.3f}")

    joblib.dump(model, MODEL_DIR / "xgb_delay_model.pkl")
    joblib.dump(encoders, MODEL_DIR / "delay_encoders.pkl")
    print("Saved xgb_delay_model.pkl + delay_encoders.pkl")


if __name__ == "__main__":
    train_price_model()
    train_delay_model()
    print("Done.")
