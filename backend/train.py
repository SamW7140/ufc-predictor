import joblib
from preprocess import load_and_preprocess
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss, classification_report
 
def train_and_save_model():
    # Load preprocessed train/test split
    X_train, X_test, y_train, y_test = load_and_preprocess()

    # Apply preprocessing pipeline
    preprocessor = joblib.load('models/preprocessor.joblib')
    X_train = preprocessor.transform(X_train)
    X_test = preprocessor.transform(X_test)

    # Initialize and train classifier
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    # Evaluate on test set
    y_pred = clf.predict(X_test)
    y_pred_proba = clf.predict_proba(X_test)[:, 1]
    acc = accuracy_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    ll = log_loss(y_test, y_pred_proba)
    print(f"Accuracy: {acc:.2f}")
    print(f"ROC AUC: {roc_auc:.2f}")
    print(f"Log Loss: {ll:.2f}")
    print(classification_report(y_test, y_pred, target_names=['Blue Win (0)', 'Red Win (1)']))

    # Save the trained model
    model_path = 'models/model.joblib'
    joblib.dump(clf, model_path)
    print(f"Trained model saved to {model_path}")

if __name__ == '__main__':
    train_and_save_model()