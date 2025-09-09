# scripts_models/train_and_select.py
import os, joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, classification_report
import psycopg2
from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

def fetch_labeled_texts(limit=None):
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    q = "SELECT id, text, sentiment_label FROM flat_texts WHERE text IS NOT NULL AND sentiment_label IS NOT NULL"
    if limit:
        q += f" LIMIT {limit}"
    df = pd.read_sql_query(q, conn)
    conn.close()
    return df

def train_and_select():
    df = fetch_labeled_texts()
    if df.empty or df['sentiment_label'].nunique() < 2:
        print("Pas assez de labels pour entraîner (besoin d'au moins 2 classes).")
        return

    X = df['text'].fillna('')
    y = df['sentiment_label']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    vect = TfidfVectorizer(ngram_range=(1,2), max_features=15000)
    X_train_t = vect.fit_transform(X_train)
    X_test_t = vect.transform(X_test)

    candidates = {
        'logreg': LogisticRegression(max_iter=2000),
        'rf': RandomForestClassifier(n_estimators=200, random_state=42)
    }

    best_name, best_score, best_model = None, -1, None
    for name, model in candidates.items():
        model.fit(X_train_t, y_train)
        preds = model.predict(X_test_t)
        score = f1_score(y_test, preds, average='macro')
        print(f"{name} f1_macro={score:.4f}")
        print(classification_report(y_test, preds))
        if score > best_score:
            best_score = score
            best_model = model
            best_name = name

    print(f"Best model: {best_name} (f1_macro={best_score:.4f})")
    joblib.dump(best_model, os.path.join(MODEL_DIR, f"best_model_{best_name}.joblib"))
    joblib.dump(vect, os.path.join(MODEL_DIR, "vectorizer.joblib"))
    print("Model and vectorizer saved.")

if __name__ == "__main__":
    train_and_select()

