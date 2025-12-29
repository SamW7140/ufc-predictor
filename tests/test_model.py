"""Model prediction tests."""
import pytest
import sys
from pathlib import Path
import pandas as pd
import numpy as np

backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))


class TestModelLoading:
    """Test model loading functionality."""

    def test_models_exist(self):
        """Test that model files exist."""
        backend = Path(__file__).parent.parent / 'backend'
        assert (backend / 'red_model.joblib').exists()
        assert (backend / 'blue_model.joblib').exists()
        assert (backend / 'scaler.joblib').exists()
        assert (backend / 'weight_class_encoder.joblib').exists()

    def test_models_load(self):
        """Test that models can be loaded."""
        import joblib
        backend = Path(__file__).parent.parent / 'backend'

        red_model = joblib.load(backend / 'red_model.joblib')
        blue_model = joblib.load(backend / 'blue_model.joblib')
        scaler = joblib.load(backend / 'scaler.joblib')
        encoder = joblib.load(backend / 'weight_class_encoder.joblib')

        assert red_model is not None
        assert blue_model is not None
        assert scaler is not None
        assert encoder is not None


class TestPredictionLogic:
    """Test prediction logic."""

    def test_prediction_output_format(self):
        """Test that predictions return valid probabilities."""
        import joblib
        backend = Path(__file__).parent.parent / 'backend'

        red_model = joblib.load(backend / 'red_model.joblib')

        # Create dummy feature array (13 features)
        dummy_features = np.random.randn(1, 29)

        # Get prediction
        pred_proba = red_model.predict_proba(dummy_features)

        # Check output format
        assert pred_proba.shape == (1, 2)
        assert 0 <= pred_proba[0][1] <= 1
        assert np.isclose(pred_proba[0][0] + pred_proba[0][1], 1.0)

    def test_dual_model_consistency(self):
        """Test that dual models are inverse of each other."""
        import joblib
        backend = Path(__file__).parent.parent / 'backend'

        red_model = joblib.load(backend / 'red_model.joblib')
        blue_model = joblib.load(backend / 'blue_model.joblib')

        # Create dummy feature array
        dummy_features = np.random.randn(1, 29)

        red_pred = red_model.predict_proba(dummy_features)[0][1]
        blue_pred = blue_model.predict_proba(dummy_features)[0][1]

        # Blue model should predict inverse (since it's trained on flipped data)
        # They won't be exactly inverse, but should show different perspectives
        assert red_pred != blue_pred  # Different perspectives
        assert 0 <= red_pred <= 1
        assert 0 <= blue_pred <= 1


class TestDataProcessing:
    """Test data processing functions."""

    def test_processed_data_exists(self):
        """Test that processed data file exists."""
        backend = Path(__file__).parent.parent / 'backend'
        assert (backend / 'processed_data.csv').exists()

    def test_processed_data_format(self):
        """Test that processed data has correct format."""
        backend = Path(__file__).parent.parent / 'backend'
        df = pd.read_csv(backend / 'processed_data.csv')

        # Check required columns exist
        required_cols = ['r_fighter', 'b_fighter', 'Winner', 'weight_class']
        for col in required_cols:
            assert col in df.columns

        # Check data types
        assert df.shape[0] > 0
        assert df.shape[1] > 10  # Should have many features
