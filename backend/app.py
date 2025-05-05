from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import joblib
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Constants
INITIAL_ELO = 1500
K_FACTOR = 32

# Global variable to store fighter Elo ratings
fighter_elos = {}

def calculate_expected_score(rating_a, rating_b):
    """Calculate expected score for player A against player B."""
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def update_elo(winner_rating, loser_rating, k_factor):
    """Update Elo ratings after a win/loss."""
    expected_winner = calculate_expected_score(winner_rating, loser_rating)
    expected_loser = 1 - expected_winner
    
    new_winner_rating = winner_rating + k_factor * (1 - expected_winner)
    new_loser_rating = loser_rating + k_factor * (0 - expected_loser)
    
    return new_winner_rating, new_loser_rating

def update_elo_draw(rating_a, rating_b, k_factor):
    """Update Elo ratings after a draw."""
    expected_a = calculate_expected_score(rating_a, rating_b)
    expected_b = 1 - expected_a
    
    new_rating_a = rating_a + k_factor * (0.5 - expected_a)
    new_rating_b = rating_b + k_factor * (0.5 - expected_b)
    
    return new_rating_a, new_rating_b

def load_and_process_data():
    """Load and process the UFC dataset to calculate Elo ratings."""
    global fighter_elos
    
    try:
        # Get the absolute path to the project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Load the dataset
        df = pd.read_csv(os.path.join(project_root, 'UFC dataset', 'Medium set', 'medium_dataset.csv'))
        
        # Convert date to datetime and sort chronologically
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Initialize fighter Elo ratings
        fighter_elos = {}
        
        # Process each fight
        for _, row in df.iterrows():
            r_fighter = row['r_fighter']
            b_fighter = row['b_fighter']
            status = row['status']
            
            # Skip if essential data is missing
            if pd.isna(r_fighter) or pd.isna(b_fighter) or pd.isna(status):
                continue
                
            # Initialize fighter ratings if not present
            if r_fighter not in fighter_elos:
                fighter_elos[r_fighter] = INITIAL_ELO
            if b_fighter not in fighter_elos:
                fighter_elos[b_fighter] = INITIAL_ELO
                
            # Get current ratings
            r_rating = fighter_elos[r_fighter]
            b_rating = fighter_elos[b_fighter]
            
            # Update ratings based on fight outcome
            if status == 'win':  # Red fighter won
                new_r_rating, new_b_rating = update_elo(r_rating, b_rating, K_FACTOR)
            elif status == 'loss':  # Blue fighter won
                new_b_rating, new_r_rating = update_elo(b_rating, r_rating, K_FACTOR)
            elif status == 'draw':  # Draw
                new_r_rating, new_b_rating = update_elo_draw(r_rating, b_rating, K_FACTOR)
            else:  # Skip other outcomes
                continue
                
            # Update the ratings
            fighter_elos[r_fighter] = new_r_rating
            fighter_elos[b_fighter] = new_b_rating
            
    except Exception as e:
        print(f"Error processing data: {str(e)}")
        raise

@app.route('/predict', methods=['POST'])
def predict_winner():
    try:
        data = request.get_json()
        fighter1 = data.get('fighter1')
        fighter2 = data.get('fighter2')
        
        if not fighter1 or not fighter2:
            return jsonify({
                'error': 'Both fighter names are required',
                'status': 'error'
            }), 400
            
        # Check if fighters exist in our data
        if fighter1 not in fighter_elos:
            return jsonify({
                'error': f'Fighter {fighter1} not found in historical data',
                'status': 'error'
            }), 404
            
        if fighter2 not in fighter_elos:
            return jsonify({
                'error': f'Fighter {fighter2} not found in historical data',
                'status': 'error'
            }), 404
            
        # Get fighter ratings
        fighter1_elo = fighter_elos[fighter1]
        fighter2_elo = fighter_elos[fighter2]
        
        # Calculate win probability
        fighter1_win_prob = calculate_expected_score(fighter1_elo, fighter2_elo)
        
        # Predict winner based on Elo ratings
        if fighter1_elo > fighter2_elo:
            winner = fighter1
            win_probability = fighter1_win_prob
        else:
            winner = fighter2
            win_probability = 1 - fighter1_win_prob
            
        return jsonify({
            'prediction': f'{winner} is predicted to win with {win_probability:.1%} probability',
            'status': 'success',
            'fighter1_elo': fighter1_elo,
            'fighter2_elo': fighter2_elo,
            'win_probability': win_probability
        })
        
    except Exception as e:
        return jsonify({
            'error': f'An error occurred: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/fighters', methods=['GET'])
def get_fighters():
    """Return a list of all fighter names for autocomplete."""
    return jsonify({
        'fighters': list(fighter_elos.keys())
    })

# Serve the frontend index.html at the root URL
@app.route('/')
def serve_index():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return send_from_directory(os.path.join(project_root, 'frontend'), 'index.html')

# Serve other static files (JS, CSS, images, etc.)
@app.route('/<path:path>')
def serve_static(path):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return send_from_directory(os.path.join(project_root, 'frontend'), path)

load_and_process_data()
print("Data loaded and Elo ratings calculated successfully")

if __name__ == '__main__':
    # Development server - comment out for production
    # app.run(debug=True)
    # For production, use: python -m waitress --listen=0.0.0.0:8080 app:app
    pass