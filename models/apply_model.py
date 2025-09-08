# models/apply_model.py
import psycopg2
import pandas as pd
import joblib, os
from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

# Charger modèle et vectorizer
vect = joblib.load("models/vectorizer.joblib")
model = None
for f in os.listdir("models"):
    if f.startswith("best_model_"):
        model = joblib.load(os.path.join("models", f))
        print(f"[apply_model] modèle chargé: {f}")
        break

def connect():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )

def apply_model(batch_size=500):
    conn = connect()
    cur = conn.cursor()

    # récupérer textes sans prédiction
    df = pd.read_sql_query("""
        SELECT id, text FROM flat_texts
        WHERE text IS NOT NULL AND (predicted_sentiment IS NULL OR predicted_sentiment = '')
    """, conn)

    if df.empty:
        print("[apply_model] Rien à prédire (tout est déjà labellisé).")
        return

    print(f"[apply_model] {len(df)} lignes à prédire…")

    X = vect.transform(df["text"].fillna(""))
    preds = model.predict(X)

    for idx, row in df.iterrows():
        pred = preds[idx]
        cur.execute("""
            UPDATE flat_texts
            SET predicted_sentiment = %s
            WHERE id = %s
        """, (pred, row["id"]))

    conn.commit()
    cur.close()
    conn.close()
    print("[apply_model] Prédictions enregistrées en base.")

if __name__ == "__main__":
    apply_model()
