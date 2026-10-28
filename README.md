# FlightSaver AI

Streamlit app for flight fare prediction and delay-risk scoring.

## Run in VS Code

1. Open the `FlightSaverAI` folder in VS Code (File > Open Folder).
2. Open a terminal (Ctrl+`) and create a virtual environment:
   - Windows: `python -m venv venv` then `venv\Scripts\activate`
   - macOS/Linux: `python3 -m venv venv` then `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. (Optional but recommended) Train the ML models:
   `python train_models.py`
   (sample data is already in `data/`; regenerate with `python generate_sample_data.py`)
5. Start the app from the project root: `streamlit run app/app.py`
6. Open http://localhost:8501, sign up, log in.

If `models/*.pkl` are missing, the app automatically uses built-in heuristics and never crashes.
To use real data, replace the CSVs in `data/` (keep the same column names) and re-run `train_models.py`.
