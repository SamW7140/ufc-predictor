# UFC Fighter Matchup Predictor

A web application that predicts the outcome of UFC fights using an Elo rating system based on historical fight data.

## Features

- Simple web interface for entering fighter names
- Autocomplete suggestions for fighter names based on historical data
- Elo rating system for fighter performance evaluation
- Real-time predictions based on historical data
- Displays fighter Elo ratings alongside predictions

## Setup Instructions

1. Clone this repository
2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Make sure the `medium_dataset.csv` file is in the `UFC dataset/Medium set/` directory (relative to the project root)

## Running the Application

1. Start the Python backend server from the project root:
   - For development (Flask):
     ```bash
     python backend/app.py
     ```
   - For production (Waitress):
     ```bash
     python -m waitress --listen=0.0.0.0:8080 backend.app:app
     ```

2. Open your web browser and go to:
   - `http://localhost:5000` (if using Flask's built-in server)
   - `http://localhost:8080` (if using Waitress)

   The frontend will be served automatically by the backend. You do NOT need to open `index.html` manually.

## How It Works

1. The backend loads and processes the historical fight data when started (regardless of how it is started)
2. It calculates Elo ratings for all fighters based on their fight history
3. When you enter two fighter names in the web interface:
   - The frontend provides autocomplete suggestions as you type
   - The frontend sends the names to the backend API
   - The backend retrieves the fighters' Elo ratings
   - It predicts the winner based on the Elo rating comparison
   - The prediction and fighter ratings are returned to the frontend
   - The results are displayed in the web interface

## API Endpoints

- `POST /predict` — Predicts the winner between two fighters. Requires JSON body with `fighter1` and `fighter2`.
- `GET /fighters` — Returns a list of all fighter names (used for autocomplete).

## Technical Details

- Frontend: HTML, CSS, and JavaScript (served by Flask backend)
- Backend: Python with Flask
- Data Processing: pandas
- Rating System: Elo algorithm with K-factor of 32 and initial rating of 1500 