# models/predict.py
import joblib, os
vect = joblib.load("models/vectorizer.joblib")
# charger best model automatiquement
for f in os.listdir("models"):
    if f.startswith("best_model_"):
        model = joblib.load(os.path.join("models", f))
        break

def predict(text):
    X = vect.transform([text])
    return model.predict(X)[0]

if __name__ == "__main__":
    sample = "J'adore ce produit, très pratique et bon service !"
    print("Pred:", predict(sample))
