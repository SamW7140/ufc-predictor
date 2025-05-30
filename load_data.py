import pandas as pd
import numpy as np
import os
# from datetime import datetime # Not strictly needed if date column is just for sorting

def load_ufc_data():
    """
    Load and preprocess the UFC dataset.
    Calculates pre-fight career statistics to avoid data leakage.
    Returns a cleaned and processed DataFrame.
    """
    project_root = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(project_root, 'UFC dataset', 'Medium set', 'medium_dataset.csv'))

    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True) # Reset index after sorting

    # Initialize columns for pre-fight career stats
    pre_fight_stats_cols = [
        'r_career_fights', 'r_career_wins', 'r_career_losses', 'r_career_draws',
        'r_career_str', 'r_career_td', 'r_career_kd',
        'b_career_fights', 'b_career_wins', 'b_career_losses', 'b_career_draws',
        'b_career_str', 'b_career_td', 'b_career_kd'
    ]
    for col in pre_fight_stats_cols:
        df[col] = 0 # Initialize with 0

    career_stats_tracker = {} # To store the most up-to-date stats for each fighter

    # Iterate through each fight to calculate pre-fight stats
    for index, row in df.iterrows():
        r_fighter = row['r_fighter']
        b_fighter = row['b_fighter']

        # Get current stats for red fighter (stats *before* this fight)
        if r_fighter not in career_stats_tracker:
            career_stats_tracker[r_fighter] = {'fights': 0, 'wins': 0, 'losses': 0, 'draws': 0, 'total_str': 0, 'total_td': 0, 'total_kd': 0}
        
        df.loc[index, 'r_career_fights'] = career_stats_tracker[r_fighter]['fights']
        df.loc[index, 'r_career_wins'] = career_stats_tracker[r_fighter]['wins']
        df.loc[index, 'r_career_losses'] = career_stats_tracker[r_fighter]['losses']
        df.loc[index, 'r_career_draws'] = career_stats_tracker[r_fighter]['draws']
        df.loc[index, 'r_career_str'] = career_stats_tracker[r_fighter]['total_str']
        df.loc[index, 'r_career_td'] = career_stats_tracker[r_fighter]['total_td']
        df.loc[index, 'r_career_kd'] = career_stats_tracker[r_fighter]['total_kd']

        # Get current stats for blue fighter (stats *before* this fight)
        if b_fighter not in career_stats_tracker:
            career_stats_tracker[b_fighter] = {'fights': 0, 'wins': 0, 'losses': 0, 'draws': 0, 'total_str': 0, 'total_td': 0, 'total_kd': 0}

        df.loc[index, 'b_career_fights'] = career_stats_tracker[b_fighter]['fights']
        df.loc[index, 'b_career_wins'] = career_stats_tracker[b_fighter]['wins']
        df.loc[index, 'b_career_losses'] = career_stats_tracker[b_fighter]['losses']
        df.loc[index, 'b_career_draws'] = career_stats_tracker[b_fighter]['draws']
        df.loc[index, 'b_career_str'] = career_stats_tracker[b_fighter]['total_str']
        df.loc[index, 'b_career_td'] = career_stats_tracker[b_fighter]['total_td']
        df.loc[index, 'b_career_kd'] = career_stats_tracker[b_fighter]['total_kd']

        # Now, update the career_stats_tracker with the outcome of *this* fight
        # This updated stat will be used for the *next* fight for these fighters
        
        # Update stats for red fighter
        career_stats_tracker[r_fighter]['fights'] += 1
        if row['status'] == 'win': # Red fighter won
            career_stats_tracker[r_fighter]['wins'] += 1
        elif row['status'] == 'loss': # Red fighter lost
            career_stats_tracker[r_fighter]['losses'] += 1
        elif row['status'] == 'draw':
            career_stats_tracker[r_fighter]['draws'] += 1
        
        if not pd.isna(row['r_str']): career_stats_tracker[r_fighter]['total_str'] += row['r_str']
        if not pd.isna(row['r_td']): career_stats_tracker[r_fighter]['total_td'] += row['r_td']
        if not pd.isna(row['r_kd']): career_stats_tracker[r_fighter]['total_kd'] += row['r_kd']

        # Update stats for blue fighter
        career_stats_tracker[b_fighter]['fights'] += 1
        
        # Correct logic for blue fighter win/loss based on red fighter's status
        if row['status'] == 'win': # Red won -> Blue lost
            career_stats_tracker[b_fighter]['losses'] += 1
        elif row['status'] == 'loss': # Red lost -> Blue won 
            career_stats_tracker[b_fighter]['wins'] += 1
        elif row['status'] == 'draw': # Draw for both
            career_stats_tracker[b_fighter]['draws'] += 1

        if not pd.isna(row['b_str']): career_stats_tracker[b_fighter]['total_str'] += row['b_str']
        if not pd.isna(row['b_td']): career_stats_tracker[b_fighter]['total_td'] += row['b_td']
        if not pd.isna(row['b_kd']): career_stats_tracker[b_fighter]['total_kd'] += row['b_kd']

    # Calculate pre-fight career win rates (handle division by zero)
    df['r_career_win_rate'] = (df['r_career_wins'] / df['r_career_fights']).fillna(0)
    df['b_career_win_rate'] = (df['b_career_wins'] / df['b_career_fights']).fillna(0)
    
    # Handle missing values for other numeric columns (e.g. r_str, r_td per fight if they are used directly)
    # It's better to handle these before calculating differences or impute them carefully.
    # For now, assuming 'r_str', 'b_str' etc. are stats *for that specific fight* and might be NaN.
    # If they are NaN, their direct use in features like 'str_diff' in app.py will lead to NaN features.
    # Let's fill these per-fight stats with 0 for simplicity if they are NaN, as they represent "landed in this fight".
    fight_specific_stats = ['r_str', 'r_td', 'r_kd', 'b_str', 'b_td', 'b_kd'] # Add others if needed
    for col in fight_specific_stats:
        df[col] = df[col].fillna(0)
    
    # Clean and standardize weight class names
    if 'weight_class' in df.columns:
        df['weight_class'] = df['weight_class'].astype(str).str.strip()
        df['weight_class'] = df['weight_class'].replace('nan', 'Unknown')
        df['weight_class'] = df['weight_class'].fillna('Unknown')
    else:
        print("Warning: 'weight_class' column not found in dataset!")

    processed_data_path = os.path.join(project_root, 'backend', 'processed_data.csv')
    df.to_csv(processed_data_path, index=False)
    
    print(f"Data loaded and processed successfully (with pre-fight stats). Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}") # Print columns to verify
    print(df[['r_fighter', 'b_fighter', 'date', 'r_career_wins', 'b_career_wins', 'status', 'weight_class']].head())
    print(f"Processed data saved to: {processed_data_path}")
    
    return df

if __name__ == "__main__":
    load_ufc_data()
