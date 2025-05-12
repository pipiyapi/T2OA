import sqlite3
db_path = "state_db/state.db"
conn = sqlite3.connect(db_path, check_same_thread=False)