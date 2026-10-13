# Smart Bus – Bus Route & Passenger Management System (Tamil Nadu)

Hackathon problem PL048. Python 3.9+.

## Run
- Command line (no installs): `python smart_bus.py`  (automatic test: `python smart_bus.py --selftest`)
- Web interface: `pip install -r requirements.txt` then `streamlit run streamlit_app.py`

## What it covers
Bus management, route management, ticket booking/cancellation, fare calculation, passenger details,
Bus Status Report (BUS101 · R12 · Erode → Coimbatore · 50 / 42 / 8 · Running), passenger load analysis,
peak-hour analysis, 67 Tamil Nadu stands, bus-stand statistics, helplines, schemes.

## Honest notes
Fares are approximate per-km rates. Distances = map distance × 1.25 (not Google Maps). Payment is a demo.
Sample buses are not real fleet records. Bus-stand statistics (184 total) were supplied by the team and should be verified.
Data is stored in `smart_bus_data.json`.
