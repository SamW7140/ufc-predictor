from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import joblib
import pandas as pd
import os
import numpy as np
from sklearn.compose import ColumnTransformer
import random

app = Flask(__name__)
CORS(app)

# Load the trained models and scaler
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
red_model = joblib.load(os.path.join(project_root, 'backend', 'red_model.joblib'))
blue_model = joblib.load(os.path.join(project_root, 'backend', 'blue_model.joblib'))
scaler = joblib.load(os.path.join(project_root, 'backend', 'scaler.joblib'))
weight_class_encoder = joblib.load(os.path.join(project_root, 'backend', 'weight_class_encoder.joblib'))
fighters_df = pd.read_csv(os.path.join(project_root, 'backend', 'fighters.csv'))

def get_fighter_stats(fighter_name, color_prefix):
    """Get the latest stats for a fighter from processed data."""
    # Load the processed data
    df = pd.read_csv(os.path.join(project_root, 'backend', 'processed_data.csv'))
    # Find the latest fight for the fighter as either red or blue
    fighter_stats = df[df[f'{color_prefix}_fighter'] == fighter_name]
    if not fighter_stats.empty:
        # Get the most recent fight
        return fighter_stats.iloc[-1]
    return None

def get_fighter_weight_classes(fighter_name):
    """Get all weight classes a fighter has competed in."""
    df = pd.read_csv(os.path.join(project_root, 'backend', 'processed_data.csv'))
    red_fights = df[df['r_fighter'] == fighter_name]
    blue_fights = df[df['b_fighter'] == fighter_name]
    
    weight_classes = set()
    if not red_fights.empty:
        weight_classes.update(red_fights['weight_class'].dropna().unique())
    if not blue_fights.empty:
        weight_classes.update(blue_fights['weight_class'].dropna().unique())
    
    # Filter out invalid weight classes
    return [wc for wc in weight_classes if wc and str(wc).lower() != 'nan']

def calculate_features_for_perspective(red_fighter_stats, blue_fighter_stats, weight_class):
    """Calculate feature differences where red_fighter is red and blue_fighter is blue."""
    features = {
        'str_diff': red_fighter_stats['r_str'] - blue_fighter_stats['b_str'],
        'td_diff': red_fighter_stats['r_td'] - blue_fighter_stats['b_td'],
        'kd_diff': red_fighter_stats['r_kd'] - blue_fighter_stats['b_kd'],
        'fights_diff': red_fighter_stats['r_career_fights'] - blue_fighter_stats['b_career_fights'],
        'wins_diff': red_fighter_stats['r_career_wins'] - blue_fighter_stats['b_career_wins'],
        'losses_diff': red_fighter_stats['r_career_losses'] - blue_fighter_stats['b_career_losses'],
        'win_rate_diff': red_fighter_stats['r_career_win_rate'] - blue_fighter_stats['b_career_win_rate'],
        'str_ratio': (red_fighter_stats['r_str'] + 1) / (blue_fighter_stats['b_str'] + 1),
        'td_ratio': (red_fighter_stats['r_td'] + 1) / (blue_fighter_stats['b_td'] + 1),
        'win_rate_ratio': (red_fighter_stats['r_career_win_rate'] + 0.01) / (blue_fighter_stats['b_career_win_rate'] + 0.01),
        'weight_class': weight_class
    }
    return features

def calculate_features(fighter1_stats, fighter2_stats, weight_class):
    """Calculate feature differences between two fighters. (DEPRECATED - use calculate_features_for_perspective)"""
    features = {
        'str_diff': fighter1_stats['r_str'] - fighter2_stats['b_str'],
        'td_diff': fighter1_stats['r_td'] - fighter2_stats['b_td'],
        'kd_diff': fighter1_stats['r_kd'] - fighter2_stats['b_kd'],
        'fights_diff': fighter1_stats['r_career_fights'] - fighter2_stats['b_career_fights'],
        'wins_diff': fighter1_stats['r_career_wins'] - fighter2_stats['b_career_wins'],
        'losses_diff': fighter1_stats['r_career_losses'] - fighter2_stats['b_career_losses'],
        'win_rate_diff': fighter1_stats['r_career_win_rate'] - fighter2_stats['b_career_win_rate'],
        'str_ratio': (fighter1_stats['r_str'] + 1) / (fighter2_stats['b_str'] + 1),
        'td_ratio': (fighter1_stats['r_td'] + 1) / (fighter2_stats['b_td'] + 1),
        'win_rate_ratio': (fighter1_stats['r_career_win_rate'] + 0.01) / (fighter2_stats['b_career_win_rate'] + 0.01),
        'weight_class': weight_class
    }
    return features

@app.route('/predict', methods=['POST'])
def predict_winner():
    try:
        data = request.get_json()
        fighter1 = data.get('fighter1')
        fighter2 = data.get('fighter2')
        weight_class = data.get('weight_class')
        
        if not fighter1 or not fighter2:
            return jsonify({
                'error': 'Both fighter names are required',
                'status': 'error'
            }), 400
        
        # Randomize fighter order to eliminate positional bias
        fighter_order_randomized = random.choice([True, False])
        if fighter_order_randomized:
            actual_fighter1, actual_fighter2 = fighter2, fighter1
        else:
            actual_fighter1, actual_fighter2 = fighter1, fighter2
        
        # Get stats for both perspectives
        f1_red_stats = get_fighter_stats(actual_fighter1, 'r') 
        f2_blue_stats = get_fighter_stats(actual_fighter2, 'b')
        f2_red_stats = get_fighter_stats(actual_fighter2, 'r')
        f1_blue_stats = get_fighter_stats(actual_fighter1, 'b')
        
        print(f"Randomized order: {fighter_order_randomized}")
        print(f"Original input: {fighter1} vs {fighter2}")
        print(f"Actual assignment: {actual_fighter1} (red) vs {actual_fighter2} (blue)")
        print(f"Stats for {actual_fighter1} (as red fighter):")
        print(f1_red_stats)
        print(f"Stats for {actual_fighter2} (as blue fighter):")
        print(f2_blue_stats)
        
        if f1_red_stats is None or f2_blue_stats is None or f2_red_stats is None or f1_blue_stats is None:
            return jsonify({
                'error': 'One or both fighters not found in processed data',
                'status': 'error'
            }), 404
        
        # Validate weight class compatibility if provided
        if weight_class:
            f1_weight_classes = get_fighter_weight_classes(actual_fighter1)
            f2_weight_classes = get_fighter_weight_classes(actual_fighter2)
            
            if weight_class not in f1_weight_classes and weight_class not in f2_weight_classes:
                return jsonify({
                    'error': f'Neither fighter has competed in {weight_class}',
                    'status': 'error',
                    'fighter1_weight_classes': f1_weight_classes,
                    'fighter2_weight_classes': f2_weight_classes
                }), 400
        
        # If weight_class was not provided, try to determine it from the fighter stats
        if not weight_class:
            # Get common weight classes between fighters
            f1_weight_classes = set(get_fighter_weight_classes(actual_fighter1))
            f2_weight_classes = set(get_fighter_weight_classes(actual_fighter2))
            common_weight_classes = f1_weight_classes.intersection(f2_weight_classes)
            
            if common_weight_classes:
                # Use the most recent common weight class
                weight_class = list(common_weight_classes)[0]
            elif 'weight_class' in f1_red_stats and pd.notna(f1_red_stats['weight_class']) and f1_red_stats['weight_class'] != 'nan':
                weight_class = f1_red_stats['weight_class']
            elif 'weight_class' in f2_blue_stats and pd.notna(f2_blue_stats['weight_class']) and f2_blue_stats['weight_class'] != 'nan':
                weight_class = f2_blue_stats['weight_class']
            else:
                weight_class = 'Unknown'
        
        print(f"Using weight class: {weight_class}")
        
        # Calculate features for both perspectives
        perspective1_features = calculate_features_for_perspective(f1_red_stats, f2_blue_stats, weight_class)
        perspective2_features = calculate_features_for_perspective(f2_red_stats, f1_blue_stats, weight_class)
        
        print('Features for perspective 1 (fighter1 as red):', perspective1_features)
        print('Features for perspective 2 (fighter2 as red):', perspective2_features)
        
        # Prepare dataframes for prediction
        X_perspective1 = pd.DataFrame([perspective1_features])
        X_perspective2 = pd.DataFrame([perspective2_features])
        
        # Apply the weight class encoder to get one-hot encoded features
        X_perspective1_encoded = weight_class_encoder.transform(X_perspective1)
        X_perspective2_encoded = weight_class_encoder.transform(X_perspective2)
        
        # Scale features
        X_perspective1_scaled = scaler.transform(X_perspective1_encoded)
        X_perspective2_scaled = scaler.transform(X_perspective2_encoded)
        
        # Get predictions with probabilities
        red_model_proba = red_model.predict_proba(X_perspective1_scaled)[0]
        blue_model_proba = blue_model.predict_proba(X_perspective2_scaled)[0]
        
        # Extract win probabilities
        red_model_prob_fighter1 = red_model_proba[1]  # Probability of red fighter winning
        blue_model_prob_fighter1 = blue_model_proba[1]  # FIXED: Removed incorrect "1 -" inversion!
        
        # Calculate confidence scores (higher confidence = closer to 0 or 1)
        red_confidence = abs(red_model_prob_fighter1 - 0.5) * 2
        blue_confidence = abs(blue_model_prob_fighter1 - 0.5) * 2
        
        # Weighted average based on confidence
        total_confidence = red_confidence + blue_confidence + 0.01  # Add small epsilon to avoid division by zero
        weighted_prob_fighter1 = (red_model_prob_fighter1 * red_confidence + blue_model_prob_fighter1 * blue_confidence) / total_confidence
        
        # Simple average as fallback
        simple_avg_prob_fighter1 = (red_model_prob_fighter1 + blue_model_prob_fighter1) / 2
        
        # Use weighted average if confidence difference is significant, otherwise use simple average
        if abs(red_confidence - blue_confidence) > 0.1:
            final_prob_fighter1 = weighted_prob_fighter1
        else:
            final_prob_fighter1 = simple_avg_prob_fighter1
        
        print(f'Red model probability for {actual_fighter1}:', red_model_prob_fighter1)
        print(f'Blue model probability for {actual_fighter1}:', blue_model_prob_fighter1)
        print(f'Red confidence: {red_confidence:.3f}, Blue confidence: {blue_confidence:.3f}')
        print(f'Final probability for {actual_fighter1}:', final_prob_fighter1)
        
        # Map back to original fighter names
        if fighter_order_randomized:
            final_prob_original_fighter1 = 1 - final_prob_fighter1
        else:
            final_prob_original_fighter1 = final_prob_fighter1
        
        print(f'Final probability for original {fighter1}: {final_prob_original_fighter1:.3f}')
        print(f'Final probability for original {fighter2}: {1 - final_prob_original_fighter1:.3f}')
        
        # Determine winner based on final probability
        if final_prob_original_fighter1 > 0.5:
            winner = fighter1
            final_win_probability = final_prob_original_fighter1
        else:
            winner = fighter2
            final_win_probability = 1 - final_prob_original_fighter1
        
        print(f'WINNER: {winner} with probability: {final_win_probability:.3f}')
        
        # Calculate confidence level
        confidence_level = abs(final_win_probability - 0.5) * 2
        
        return jsonify({
            'prediction': f'{winner} is predicted to win with {final_win_probability:.1%} probability',
            'status': 'success',
            'winner': winner,
            'win_probability': float(final_win_probability),
            'confidence_level': float(confidence_level),
            'weight_class': weight_class,
            'fighter_order_randomized': fighter_order_randomized,
            'model_details': {
                'red_model_confidence': float(red_confidence),
                'blue_model_confidence': float(blue_confidence),
                'prediction_method': 'weighted' if abs(red_confidence - blue_confidence) > 0.1 else 'simple_average'
            }
        })
        
    except Exception as e:
        print(f"Error in prediction: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'An error occurred: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/fighters', methods=['GET'])
def get_fighters():
    """Return a list of all fighter names for autocomplete."""
    weight_class = request.args.get('weight_class')
    
    if weight_class and weight_class != 'All':
        # Filter fighters by weight class
        df = pd.read_csv(os.path.join(project_root, 'backend', 'processed_data.csv'))
        weight_class_df = df[df['weight_class'] == weight_class]
        
        red_fighters = weight_class_df['r_fighter'].dropna().astype(str)
        blue_fighters = weight_class_df['b_fighter'].dropna().astype(str)
    else:
        # Get all fighters
        red_fighters = fighters_df['r_fighter'].dropna().astype(str)
        blue_fighters = fighters_df['b_fighter'].dropna().astype(str)
    
    # Combine and get unique names, filtering out empty strings, 'nan', and non-alpha names
    fighters = pd.concat([red_fighters, blue_fighters]).unique()
    clean_fighters = []
    for f in fighters:
        if f and isinstance(f, str):
            f_stripped = f.strip()
            if f_stripped and f_stripped.lower() != 'nan' and f_stripped.lower() != 'none':
                clean_fighters.append(f_stripped)
    
    # Remove duplicates and sort
    clean_fighters = sorted(set(clean_fighters))
    
    print(f"Returning {len(clean_fighters)} fighters for weight class: {weight_class or 'All'}")
    return jsonify({'fighters': clean_fighters})

@app.route('/fighters-by-weight-class/<weight_class>', methods=['GET'])
def get_fighters_by_weight_class(weight_class):
    """Return a list of fighters who have competed in a specific weight class."""
    df = pd.read_csv(os.path.join(project_root, 'backend', 'processed_data.csv'))
    weight_class_df = df[df['weight_class'] == weight_class]
    
    red_fighters = weight_class_df['r_fighter'].dropna().astype(str)
    blue_fighters = weight_class_df['b_fighter'].dropna().astype(str)
    
    # Combine and get unique names
    fighters = pd.concat([red_fighters, blue_fighters]).unique()
    clean_fighters = []
    for f in fighters:
        if f and isinstance(f, str):
            f_stripped = f.strip()
            if f_stripped and f_stripped.lower() != 'nan' and f_stripped.lower() != 'none':
                clean_fighters.append(f_stripped)
    
    clean_fighters = sorted(set(clean_fighters))
    
    return jsonify({
        'weight_class': weight_class,
        'fighters': clean_fighters,
        'count': len(clean_fighters)
    })

@app.route('/fighter-weight-classes/<fighter_name>', methods=['GET'])
def get_fighter_weight_classes_endpoint(fighter_name):
    """Get all weight classes a specific fighter has competed in."""
    weight_classes = get_fighter_weight_classes(fighter_name)
    return jsonify({
        'fighter': fighter_name,
        'weight_classes': weight_classes,
        'count': len(weight_classes)
    })

@app.route('/weight-classes', methods=['GET'])
def get_weight_classes():
    """Return a list of all weight classes from the dataset"""
    # Load the processed data
    df = pd.read_csv(os.path.join(project_root, 'backend', 'processed_data.csv'))
    weight_classes = df['weight_class'].dropna().unique().tolist()
    # Clean up weight classes
    clean_weight_classes = [wc for wc in weight_classes if wc and str(wc).lower() != 'nan' and str(wc) != 'Unknown']
    # Add unknown as a fallback option
    if 'Unknown' not in clean_weight_classes:
        clean_weight_classes.append('Unknown')
    clean_weight_classes = sorted(set(clean_weight_classes))
    return jsonify({'weight_classes': clean_weight_classes})

# Serve the frontend index.html at the root URL
@app.route('/')
def serve_index():
    return send_from_directory(os.path.join(project_root, 'frontend'), 'index.html')

# Serve other static files
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(os.path.join(project_root, 'frontend'), path)

if __name__ == '__main__':
    app.run(debug=True)