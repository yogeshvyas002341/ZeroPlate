from datetime import date, timedelta

import numpy as np
import pandas as pd
from flask import Flask, jsonify, send_from_directory
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

app = Flask(__name__, static_folder=".", static_url_path="")

MENU = {
    "Rajma chawal": {"base": 172, "icon": "curry"},
    "Seasonal veg thali": {"base": 130, "icon": "vegetable"},
    "Masala dosa": {"base": 96, "icon": "dosa"},
    "Gulab jamun": {"base": 55, "icon": "dessert"},
}
FEATURES = [
    "day_of_week",
    "is_holiday",
    "temperature_c",
    "rain_mm",
    "sales_lag_7",
    "sales_lag_14",
    "promotion",
]


def build_demo_history():
    """Create reproducible sample sales; replace this function with real POS data."""
    rng = np.random.default_rng(20261027)
    start = date.today() - timedelta(days=365)
    rows = []

    for offset in range(365):
        sales_date = start + timedelta(days=offset)
        temperature = 18 + 8 * np.sin((sales_date.timetuple().tm_yday - 80) * 2 * np.pi / 365)
        rain = max(0, rng.normal(2.2, 4))
        holiday = int(sales_date.month in (3, 10) and sales_date.day in (2, 12, 24))
        weekday_factor = [0.83, 0.96, 1.0, 0.99, 1.12, 1.19, 0.91][sales_date.weekday()]
        promotion = int(sales_date.day % 11 == 0)

        for item, details in MENU.items():
            base = details["base"]
            weather_factor = 1 - max(0, rain - 5) * 0.008
            holiday_factor = 0.74 if holiday else 1.0
            promotion_factor = 1.12 if promotion else 1.0
            demand = (
                base
                * weekday_factor
                * weather_factor
                * holiday_factor
                * promotion_factor
                * (1 + (temperature - 22) * 0.003)
                + rng.normal(0, base * 0.055)
            )
            rows.append(
                {
                    "date": sales_date,
                    "item": item,
                    "sales": max(0, int(round(demand))),
                    "temperature_c": round(temperature, 1),
                    "rain_mm": round(rain, 1),
                    "is_holiday": holiday,
                    "promotion": promotion,
                }
            )

    history = pd.DataFrame(rows).sort_values(["item", "date"]).reset_index(drop=True)
    history["day_of_week"] = pd.to_datetime(history["date"]).dt.day_of_week
    for lag in (7, 14):
        history[f"sales_lag_{lag}"] = history.groupby("item")["sales"].shift(lag)
    return history.dropna().reset_index(drop=True)


def train_models(history):
    models = {}
    errors = []

    for item in MENU:
        item_history = history[history["item"] == item].sort_values("date")
        split_at = int(len(item_history) * 0.8)
        train = item_history.iloc[:split_at]
        holdout = item_history.iloc[split_at:]
        model = RandomForestRegressor(
            n_estimators=100,
            min_samples_leaf=3,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(train[FEATURES], train["sales"])
        errors.append(
            mean_squared_error(
                holdout["sales"],
                model.predict(holdout[FEATURES]),
            )
            ** 0.5
        )
        model.fit(item_history[FEATURES], item_history["sales"])
        models[item] = model

    return models, float(np.mean(errors))


HISTORY = build_demo_history()
MODELS, AVERAGE_RMSE = train_models(HISTORY)


@app.get("/")
def home():
    return send_from_directory(".", "index.html")


@app.get("/api/forecast")
def forecast():
    today = date.today()
    predictions = []

    for item in MENU:
        item_history = HISTORY[HISTORY["item"] == item].sort_values("date")
        sales_by_date = item_history.set_index("date")["sales"]
        last_week = int(sales_by_date.loc[today - timedelta(days=7)])
        two_weeks = int(sales_by_date.loc[today - timedelta(days=14)])
        values = {
            "day_of_week": today.weekday(),
            "is_holiday": 0,
            "temperature_c": 24.0,
            "rain_mm": 1.0,
            "sales_lag_7": last_week,
            "sales_lag_14": two_weeks,
            "promotion": 0,
        }
        features = pd.DataFrame([values], columns=FEATURES)
        predicted = max(0, int(round(float(MODELS[item].predict(features)[0]))))
        previous_week = last_week
        predictions.append(
            {
                "item": item,
                "predicted_qty": predicted,
                "recommended_qty": predicted,
                "last_week_qty": previous_week,
                "status": (
                    "Review"
                    if previous_week and abs(predicted - previous_week) / previous_week >= 0.12
                    else "Ready"
                ),
            }
        )

    return jsonify(
        {
            "date": today.isoformat(),
            "model": "Random Forest",
            "history_days": 365,
            "average_rmse": round(AVERAGE_RMSE, 1),
            "data_source": "synthetic demo history",
            "forecasts": predictions,
        }
    )


if __name__ == "__main__":
    app.run(debug=False, port=5000)
