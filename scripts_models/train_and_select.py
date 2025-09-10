# scripts_models/train_and_select.py
import os, joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, classification_report
import psycopg2
from sqlalchemy import create_engine
from textblob import TextBlob
from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

def create_engine_connection():
    """Créer une connexion SQLAlchemy pour pandas"""
    connection_string = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(connection_string)

def generate_sentiment_labels():
    """Générer des labels de sentiment automatiquement avec TextBlob"""
    engine = create_engine_connection()
    
    # Récupérer tous les textes sans labels
    query = """
    SELECT id, text 
    FROM flat_texts 
    WHERE text IS NOT NULL 
    AND text != '' 
    AND (sentiment_label IS NULL OR sentiment_label = '')
    """
    
    df = pd.read_sql_query(query, engine)
    print(f"Génération de labels pour {len(df)} textes...")
    
    # Générer les labels avec TextBlob
    def get_sentiment_label(text):
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            if polarity > 0.1:
                return 'positif'
            elif polarity < -0.1:
                return 'negatif'
            else:
                return 'neutre'
        except:
            return 'neutre'
    
    df['sentiment_label'] = df['text'].apply(get_sentiment_label)
    
    # Mettre à jour la base de données
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, 
        user=DB_USER, password=DB_PASS
    )
    cur = conn.cursor()
    
    for _, row in df.iterrows():
        cur.execute(
            "UPDATE flat_texts SET sentiment_label = %s WHERE id = %s",
            (row['sentiment_label'], row['id'])
        )
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"Labels générés: {df['sentiment_label'].value_counts().to_dict()}")
    return df

def fetch_labeled_texts(limit=None):
    """Récupérer les textes avec labels"""
    engine = create_engine_connection()
    
    query = """
    SELECT id, text, sentiment_label 
    FROM flat_texts 
    WHERE text IS NOT NULL 
    AND text != '' 
    AND sentiment_label IS NOT NULL 
    AND sentiment_label != ''
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    df = pd.read_sql_query(query, engine)
    return df

def train_and_select():
    """Entraîner et sélectionner le meilleur modèle"""
    # D'abord, générer les labels si nécessaire
    df_check = fetch_labeled_texts()
    
    if df_check.empty or df_check['sentiment_label'].nunique() < 2:
        print("Pas assez de labels existants. Génération automatique...")
        generate_sentiment_labels()
        df = fetch_labeled_texts()
    else:
        df = df_check
    
    if df.empty or df['sentiment_label'].nunique() < 2:
        print("Impossible de créer des labels de sentiment.")
        return
    
    print(f"Entraînement avec {len(df)} textes")
    print(f"Distribution: {df['sentiment_label'].value_counts().to_dict()}")
    
    X = df['text'].fillna('')
    y = df['sentiment_label']
    
    # Vérifier qu'on a assez d'exemples par classe
    min_class_size = y.value_counts().min()
    if min_class_size < 2:
        print(f"Pas assez d'exemples par classe (min: {min_class_size})")
        return
    
    # Split stratifié
    test_size = min(0.3, max(0.1, min_class_size * 0.3 / len(df)))
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=42
    )
    
    # Vectorisation
    vect = TfidfVectorizer(
        ngram_range=(1,2), 
        max_features=5000,  # Réduit pour les petits datasets
        stop_words='english'
    )
    X_train_t = vect.fit_transform(X_train)
    X_test_t = vect.transform(X_test)
    
    # Modèles candidats
    candidates = {
        'logreg': LogisticRegression(max_iter=1000, random_state=42),
        'rf': RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    }
    
    best_name, best_score, best_model = None, -1, None
    
    for name, model in candidates.items():
        print(f"\nEntraînement {name}...")
        model.fit(X_train_t, y_train)
        preds = model.predict(X_test_t)
        
        # Calculer les métriques
        score = f1_score(y_test, preds, average='macro')
        print(f"{name} f1_macro={score:.4f}")
        print(classification_report(y_test, preds))
        
        if score > best_score:
            best_score = score
            best_model = model
            best_name = name
    
    print(f"\nMeilleur modèle: {best_name} (f1_macro={best_score:.4f})")
    
    # Sauvegarder le meilleur modèle
    model_path = os.path.join(MODEL_DIR, f"best_model_{best_name}.joblib")
    vect_path = os.path.join(MODEL_DIR, "vectorizer.joblib")
    
    joblib.dump(best_model, model_path)
    joblib.dump(vect, vect_path)
    
    print(f"Modèle sauvé: {model_path}")
    print(f"Vectorizer sauvé: {vect_path}")
    
    # Enregistrer les performances
    save_model_performance(best_name, best_score, y_test, model.predict(X_test_t))
    
    return best_model, vect

def save_model_performance(model_name, f1_score, y_true, y_pred):
    """Sauvegarder les performances du modèle"""
    from sklearn.metrics import accuracy_score, precision_score, recall_score
    
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, 
        user=DB_USER, password=DB_PASS
    )
    cur = conn.cursor()
    
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average='macro')
    recall = recall_score(y_true, y_pred, average='macro')
    
    cur.execute("""
        INSERT INTO model_performance (model_name, accuracy, f1_macro, precision, recall)
        VALUES (%s, %s, %s, %s, %s)
    """, (model_name, accuracy, f1_score, precision, recall))
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"Performances sauvées: acc={accuracy:.4f}, f1={f1_score:.4f}")

if __name__ == "__main__":
    train_and_select()