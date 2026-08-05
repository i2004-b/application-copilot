"""Run once to create data/copilot.db with the right schema.

    python -m scripts.init_db
"""
from src.db.models import init_db

if __name__ == "__main__":
    init_db()
    print("DB initialized.")
