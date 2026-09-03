from engine_init import get_engine
from sqlalchemy import text

engine = get_engine()
print(f"Engine URL: {engine.url}")

with engine.connect() as conn:
    result = conn.execute(text("SELECT DB_NAME()"))
    print(f"✅ Connected to: {result.fetchall()[0][0]}")

    result = conn.execute(text("SELECT TOP 5 * FROM curated_features"))
    columns = result.keys()
    print(f"Columns: {list(columns)}")