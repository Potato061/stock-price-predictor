from sqlalchemy import text
from fetch_data_engine import get_engine
engine = get_engine()
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM items"))
    rows = result.fetchall()
    for row in rows:
        print(row)




import os
from dotenv import load_dotenv
load_dotenv()
print(repr(os.getenv("TWELVEDATA_API")))

from fetch_data_engine import get_symbols_df
symbols = get_symbols_df()
print(len(symbols), symbols[:10])


from fetch_data_engine import get_engine
engine = get_engine()
print(engine)


