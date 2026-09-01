from engine_init import get_engine
from sqlalchemy import text
engine = get_engine()
with engine.connect() as conn:
    print(conn.execute(text("SELECT 1")).scalar())