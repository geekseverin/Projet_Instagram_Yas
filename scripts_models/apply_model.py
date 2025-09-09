# scripts_models/apply_model.py
import os, joblib
import pandas as pd
import psycopg2
from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

MODEL_DIR = "models"

def get_model_and_vectorizer():
    vect_path = os.path.join(MODEL_DIR, "vectorizer.joblib")
    model_path = None
    for f in os.listdir(MODEL_DIR):
        if f.startswith("best_model_"):
            model_path = os.path.join(MODEL_DIR, f)
            break
    if not model_path or not os.path.exists(vect_path):
        raise FileNotFoundError("Modèle ou vectorizer introuvable. Entraîne d'abord.")
    vect = joblib.load(vect_path)
    model = joblib.load(model_path)
    return model, vect

def fetch_unpredicted():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    df = pd.read_sql_query("SELECT id, text FROM flat_texts WHERE text IS NOT NULL AND (predicted_sentiment IS NULL OR predicted_sentiment = '')", conn)
    conn.close()
    return df

def update_predictions(df_ids_preds):
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    for idx, pred in df_ids_preds.items():
        cur.execute("UPDATE flat_texts SET predicted_sentiment = %s WHERE id = %s", (pred[0], pred[1]))
    conn.commit()
    cur.close()
    conn.close()

def apply_model(batch_size=500):
    model, vect = get_model_and_vectorizer()
    df = fetch_unpredicted()
    if df.empty:
        print("Rien à prédire.")
        return
    X = vect.transform(df['text'].fillna(''))
    preds = model.predict(X)
    # Build dict to update
    updates = {i: (preds[idx], df.loc[idx, 'id']) for idx, i in enumerate(df.index)}
    # Update DB
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    for idx in updates:
        pred_label, uid = updates[idx]
        cur.execute("UPDATE flat_texts SET predicted_sentiment = %s WHERE id = %s", (pred_label, uid))
    conn.commit()
    cur.close()
    conn.close()
    print(f"[apply_model] {len(preds)} rows updated.")

if __name__ == "__main__":
    apply_model()
