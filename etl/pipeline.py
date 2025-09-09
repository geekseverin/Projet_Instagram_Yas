# etl/pipeline.py
from etl import extract, transform, load

def run_all():
    print("=== ETL pipeline start ===")
    extract.extract_all(limit_posts=20)
    transform.transform()
    load.load()
    print("=== ETL pipeline finished ===")

if __name__ == "__main__":
    run_all()
