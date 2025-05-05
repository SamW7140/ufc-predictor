import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib


def load_and_preprocess():
    # Load dataset
    try:
        df = pd.read_csv('data/large_dataset.csv')
    except FileNotFoundError:
        print("--- ERROR ---")
        print("The file was not found at data/large_dataset.csv")
        raise

    # Remove draws and map target
    df = df[df['winner'] != 'Draw'].copy()
    df['target'] = df['winner'].map({'Red': 1, 'Blue': 0})

    # Define feature sets
    numerical_features = [
        'r_age','b_age','age_diff',
        'r_height','b_height','height_diff',
        'r_weight','b_weight','weight_diff',
        'r_reach','b_reach','reach_diff',
        'r_wins_total','b_wins_total','wins_total_diff',
        'r_losses_total','b_losses_total','losses_total_diff',
        'r_SLpM_total','b_SLpM_total','SLpM_total_diff',
        'r_SApM_total','b_SApM_total','SApM_total_diff',
        'r_sig_str_acc_total','b_sig_str_acc_total','sig_str_acc_total_diff',
        'r_str_def_total','b_str_def_total','str_def_total_diff',
        'r_td_avg','b_td_avg','td_avg_diff',
        'r_td_acc_total','b_td_acc_total','td_acc_total_diff',
        'r_td_def_total','b_td_def_total','td_def_total_diff',
        'r_sub_avg','b_sub_avg','sub_avg_diff'
    ]
    categorical_features = ['r_stance','b_stance','weight_class','gender','is_title_bout']

    # Split features and target
    X = df[numerical_features + categorical_features]
    y = df['target']
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    # Pipelines
    numerical_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    categorical_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])

    # ColumnTransformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numerical_pipeline, numerical_features),
            ('cat', categorical_pipeline, categorical_features)
        ],
        remainder='passthrough'
    )

    # Fit preprocessor
    preprocessor.fit(X_train)

    # Save preprocessor
    joblib.dump(preprocessor, 'models/preprocessor.joblib')
    print("Preprocessor saved to models/preprocessor.joblib")

    return X_train, X_test, y_train, y_test


if __name__ == '__main__':
    load_and_preprocess()
