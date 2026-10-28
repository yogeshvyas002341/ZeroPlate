# ZeroPlate frontend demo

ZeroPlate is a responsive HTML/CSS dashboard connected to a Flask API that trains
a scikit-learn Random Forest for each menu item. The included sales history is
synthetic demo data, not real canteen records.

## Run on Windows

From this folder, in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). The dashboard fetches
predictions from `/api/forecast`. It can also be opened as a static preview,
but live model forecasts require the Flask server.

## Use real sales data

The demo model is generated in `build_demo_history()` in `app.py`. Replace that
sample-data function with your point-of-sale history before using its
predictions for kitchen production. The sample weather and holiday values are
also illustrative; connect a trusted data source for real forecasts.
