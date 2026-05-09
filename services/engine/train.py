import os

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

DATA_PATH = os.getenv("DATASET_PATH", "/data/framingham.csv")
MODEL_PATH = os.getenv("MODEL_PATH", "/app/model.pkl")


def train():
    if not os.path.exists(DATA_PATH):
        print(f"[train] dataset not found at {DATA_PATH}, skipping training")
        return

    df = pd.read_csv(DATA_PATH).dropna()
    X = df.drop("TenYearCHD", axis=1)
    y = df["TenYearCHD"]

    X_train, _, y_train, _ = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    joblib.dump(model, MODEL_PATH)
    print(f"[train] model saved to {MODEL_PATH}")


if __name__ == "__main__":
    train()
