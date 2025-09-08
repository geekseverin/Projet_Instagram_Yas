# etl/pipeline.py
from etl.extract import extract_all
from etl.transform import transform
from etl.load import load_data

if __name__ == "__main__":
    print("📌 Lancement pipeline ETL Instagram")
    extract_all(limit_posts=20)   # 20 posts (ajuste)
    transform()
    load_data()
    print("✅ ETL terminé")
