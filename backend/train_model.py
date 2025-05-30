import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import brier_score_loss, roc_auc_score, precision_recall_curve, average_precision_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import matplotlib.pyplot as plt
import joblib
import os
import sys
from imblearn.over_sampling import SMOTE

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from load_data import load_ufc_data

def preprocess_data(create_balanced=True):
    """
    Preprocess the data for model training.
    
    Args:
        create_balanced: If True, creates a balanced dataset by including each fight twice
                        (once with red/blue as original, once with red/blue swapped)
    """
    # Load the processed data
    df = load_ufc_data()
    
    # Create target variable (1 if red fighter wins, 0 if blue fighter wins)
    df['target'] = (df['status'] == 'win').astype(int)
    
    if create_balanced:
        print("Creating balanced dataset by swapping red/blue fighters...")
        # Create a copy of the dataframe with red and blue fighters swapped
        df_swapped = df.copy()
        
        # Swap red and blue stats
        red_cols = [col for col in df.columns if col.startswith('r_')]
        blue_cols = [col for col in df.columns if col.startswith('b_')]
        
        # Create mapping of column names to swap
        swap_dict = {}
        for r_col, b_col in zip(red_cols, blue_cols):
            swap_dict[r_col] = b_col
            swap_dict[b_col] = r_col
        
        # Rename columns to swap red/blue
        df_swapped = df_swapped.rename(columns=swap_dict)
        
        # Invert the target - if red won (1), now they're blue, so target should be 0
        df_swapped['target'] = 1 - df_swapped['target']
        
        # For status, swap win/loss
        status_map = {'win': 'loss', 'loss': 'win', 'draw': 'draw'}
        df_swapped['status'] = df_swapped['status'].map(status_map)
        
        # Combine original and swapped dataframes
        df_balanced = pd.concat([df, df_swapped], ignore_index=True)
        print(f"Original dataset size: {len(df)}, Balanced dataset size: {len(df_balanced)}")
        df = df_balanced
    
    # Create feature differences
    df['str_diff'] = df['r_str'] - df['b_str']
    df['td_diff'] = df['r_td'] - df['b_td']
    df['kd_diff'] = df['r_kd'] - df['b_kd']
    df['fights_diff'] = df['r_career_fights'] - df['b_career_fights']
    df['wins_diff'] = df['r_career_wins'] - df['b_career_wins']
    df['losses_diff'] = df['r_career_losses'] - df['b_career_losses']
    df['win_rate_diff'] = df['r_career_win_rate'] - df['b_career_win_rate']
    
    # Add ratio features that might be more informative
    df['str_ratio'] = (df['r_str'] + 1) / (df['b_str'] + 1)  # +1 to avoid division by zero
    df['td_ratio'] = (df['r_td'] + 1) / (df['b_td'] + 1)
    df['win_rate_ratio'] = (df['r_career_win_rate'] + 0.01) / (df['b_career_win_rate'] + 0.01)
    
    # Select numerical features
    numerical_features = [
        'str_diff', 'td_diff', 'kd_diff', 'fights_diff',
        'wins_diff', 'losses_diff', 'win_rate_diff',
        'str_ratio', 'td_ratio', 'win_rate_ratio'
    ]
    
    # One-hot encode weight classes
    print("Weight class distribution:")
    print(df['weight_class'].value_counts())
    
    # Create column transformer for weight classes
    categorical_features = ['weight_class']
    
    # Create a preprocessor for one-hot encoding
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
        ],
        remainder='passthrough'
    )
    
    # Setup data for training
    X_with_weight_classes = df[numerical_features + categorical_features]
    y = df['target']
    
    # Apply the categorical transformation on the entire dataset
    # This creates the weight class one-hot encoded columns
    preprocessor.fit(X_with_weight_classes)
    
    # Save the preprocessor for later use
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    joblib.dump(preprocessor, os.path.join(project_root, 'backend', 'weight_class_encoder.joblib'))
    print("Weight class encoder saved.")
    
    # Transform the data 
    X_transformed = preprocessor.transform(X_with_weight_classes)
    
    # Convert back to DataFrame for better handling
    transformed_feature_names = (
        [f"weight_class_{class_name}" for class_name in preprocessor.named_transformers_['cat'].categories_[0]]
        + numerical_features
    )
    X = pd.DataFrame(X_transformed, columns=transformed_feature_names)
    
    print("Features after one-hot encoding:")
    print(X.columns.tolist())
    
    print("Target variable distribution (y):")
    print(y.value_counts(normalize=True))
    print(y.value_counts())
    
    return X, y, df[['r_fighter', 'b_fighter']]

def train_dual_perspective_models():
    """
    Train two models from different perspectives:
    1. Red fighter perspective (predicting if red fighter wins)
    2. Blue fighter perspective (predicting if blue fighter wins)
    
    This allows us to average predictions from both perspectives.
    """
    print("\n===== TRAINING DUAL PERSPECTIVE MODELS =====")
    
    # Create balanced dataset by swapping fighters
    X, y, fighters = preprocess_data(create_balanced=True)
    
    # Use different random states for the two models to ensure diversity
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train main model (red perspective)
    print("\n----- Training Red Perspective Model -----")
    red_model = GradientBoostingClassifier(
        n_estimators=100, 
        learning_rate=0.1, 
        max_depth=5,
        random_state=42
    )
    
    # Fit the model directly - with our balanced dataset, we don't need SMOTE
    red_model.fit(X_train_scaled, y_train)
    
    # Check probability distribution 
    y_proba_red = red_model.predict_proba(X_test_scaled)[:, 1]
    print("\nRed Model Probability Distribution:")
    print("Min probability:", np.min(y_proba_red))
    print("Max probability:", np.max(y_proba_red))
    print("Mean probability:", np.mean(y_proba_red))
    
    # Calibrate probabilities
    red_model_calibrated = CalibratedClassifierCV(red_model, method='sigmoid', cv=5)
    red_model_calibrated.fit(X_train_scaled, y_train)
    
    # Train blue perspective model (predicts if blue fighter wins)
    print("\n----- Training Blue Perspective Model -----")
    blue_model = GradientBoostingClassifier(
        n_estimators=100, 
        learning_rate=0.1, 
        max_depth=5,
        random_state=43  # Different random state for diversity
    )
    
    # For blue perspective, the target is inverted
    blue_model.fit(X_train_scaled, 1 - y_train)
    
    # Calibrate blue model
    blue_model_calibrated = CalibratedClassifierCV(blue_model, method='sigmoid', cv=5)
    blue_model_calibrated.fit(X_train_scaled, 1 - y_train)
    
    # Evaluate dual perspective approach
    print("\n----- Evaluating Dual Perspective Approach -----")
    y_proba_red_calibrated = red_model_calibrated.predict_proba(X_test_scaled)[:, 1]
    y_proba_blue_calibrated = blue_model_calibrated.predict_proba(X_test_scaled)[:, 1]
    
    # Combine predictions from both perspectives (blue perspective is inverted)
    y_proba_combined = (y_proba_red_calibrated + (1 - y_proba_blue_calibrated)) / 2
    
    # Evaluate combined model
    brier_combined = brier_score_loss(y_test, y_proba_combined)
    auc_combined = roc_auc_score(y_test, y_proba_combined)
    print(f"Combined model - Brier score: {brier_combined:.4f}, AUC: {auc_combined:.4f}")
    
    # Calculate predictions for combined model
    y_pred_combined = (y_proba_combined > 0.5).astype(int)
    
    # Print combined model's probability distribution
    print("\nCombined Model Probability Distribution:")
    print("Min probability:", np.min(y_proba_combined))
    print("Max probability:", np.max(y_proba_combined))
    print("Mean probability:", np.mean(y_proba_combined))
    hist, bins = np.histogram(y_proba_combined, bins=10, range=(0, 1))
    for i in range(len(hist)):
        print(f"{bins[i]:.1f}-{bins[i+1]:.1f}: {hist[i]} samples")
    
    # Save all models and scaler
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    joblib.dump(red_model_calibrated, os.path.join(project_root, 'backend', 'red_model.joblib'))
    joblib.dump(blue_model_calibrated, os.path.join(project_root, 'backend', 'blue_model.joblib'))
    joblib.dump(scaler, os.path.join(project_root, 'backend', 'scaler.joblib'))
    fighters.to_csv(os.path.join(project_root, 'backend', 'fighters.csv'), index=False)
    
    return red_model_calibrated, blue_model_calibrated, scaler

def train_model():
    """Legacy train_model function that trains a single model with SMOTE."""
    # Preprocess data - use regular unbalanced dataset
    X, y, fighters = preprocess_data(create_balanced=False)
    
    # Stratified split is important for calibration too
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("Target distribution before SMOTE (on X_train):")
    print(y_train.value_counts())
    
    # Use SMOTE for training data only
    smote = SMOTE(random_state=42)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
    
    print("Target distribution after SMOTE (on X_train_resampled):")
    print(y_train_resampled.value_counts())
    
    # Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_resampled)
    X_test_scaled = scaler.transform(X_test)
    
    # Try GradientBoostingClassifier for better probability calibration
    base_model = GradientBoostingClassifier(
        n_estimators=100, 
        learning_rate=0.1, 
        max_depth=5,
        random_state=42
    )
    
    # Fit the base model
    base_model.fit(X_train_scaled, y_train_resampled)
    
    # Check probability distribution on test set BEFORE calibration
    y_proba_base = base_model.predict_proba(X_test_scaled)[:, 1]
    print("\nPROBABILITY DISTRIBUTION BEFORE CALIBRATION:")
    print("Min probability:", np.min(y_proba_base))
    print("Max probability:", np.max(y_proba_base))
    print("Mean probability:", np.mean(y_proba_base))
    print("Probability histogram buckets:")
    hist, bins = np.histogram(y_proba_base, bins=10, range=(0, 1))
    for i in range(len(hist)):
        print(f"{bins[i]:.1f}-{bins[i+1]:.1f}: {hist[i]} samples")
    
    # Evaluate base model
    brier_base = brier_score_loss(y_test, y_proba_base)
    auc_base = roc_auc_score(y_test, y_proba_base)
    print(f"Base model - Brier score: {brier_base:.4f}, AUC: {auc_base:.4f}")
    
    # Calibrate probabilities using Platt Scaling (sigmoid method)
    # Sigmoid is generally more appropriate when you have few samples in some bins
    calibrated_model = CalibratedClassifierCV(base_model, method='sigmoid', cv=5)
    calibrated_model.fit(X_train_scaled, y_train_resampled)
    
    # Check probability distribution AFTER calibration
    y_proba_calibrated = calibrated_model.predict_proba(X_test_scaled)[:, 1]
    print("\nPROBABILITY DISTRIBUTION AFTER CALIBRATION:")
    print("Min probability:", np.min(y_proba_calibrated))
    print("Max probability:", np.max(y_proba_calibrated))
    print("Mean probability:", np.mean(y_proba_calibrated))
    print("Probability histogram buckets:")
    hist, bins = np.histogram(y_proba_calibrated, bins=10, range=(0, 1))
    for i in range(len(hist)):
        print(f"{bins[i]:.1f}-{bins[i+1]:.1f}: {hist[i]} samples")
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Save the calibrated model
    joblib.dump(calibrated_model, os.path.join(project_root, 'backend', 'model.joblib'))
    joblib.dump(scaler, os.path.join(project_root, 'backend', 'scaler.joblib'))
    
    fighters.to_csv(os.path.join(project_root, 'backend', 'fighters.csv'), index=False)
    
    # Evaluate calibrated model
    brier_calibrated = brier_score_loss(y_test, y_proba_calibrated)
    auc_calibrated = roc_auc_score(y_test, y_proba_calibrated)
    print(f"Calibrated model - Brier score: {brier_calibrated:.4f}, AUC: {auc_calibrated:.4f}")
    
    from sklearn.metrics import classification_report
    print("\nClassification Report on Test Set (Calibrated Model):")
    y_pred_test_calibrated = calibrated_model.predict(X_test_scaled)
    print(classification_report(y_test, y_pred_test_calibrated))
    
    # Check distribution of predicted classes to see imbalance
    print("Distribution of predicted classes:")
    print(pd.Series(y_pred_test_calibrated).value_counts())
    
    # Feature importance from base model
    if hasattr(base_model, 'feature_importances_'):
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': base_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nFeature Importance:")
        print(feature_importance)

if __name__ == "__main__":
    # Use the dual perspective approach instead of the single model
    train_dual_perspective_models()
    # If you want to train the single model instead, uncomment this line:
    # train_model() 