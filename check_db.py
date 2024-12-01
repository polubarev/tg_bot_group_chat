import sqlite3

# Connect to the database
conn = sqlite3.connect("messages.db")
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", tables)

# View data from a specific table
table_name = "messages"
cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 10;")
rows = cursor.fetchall()
for row in rows:
    print(row)

# Close the connection
conn.close()