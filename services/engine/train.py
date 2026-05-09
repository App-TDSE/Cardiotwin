import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import joblib
import os

DATA_PATH = "../../data/framingham.csv"
MODEL_PATH = "model.pkl"

def train():
    if not os.path.exists(DATA_PATH):
        print("Data not found, skipping training...")
        return

    df = pd.read_csv(DATA_PATH).dropna()
    X = df.drop('TenYearCHD', axis=1)
    y = df['TenYearCHD']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    joblib.dump(model, MODEL_PATH)
    print(f"Model trained and saved to {MODEL_PATH}")

if __name__ == "__main__":
    train()
