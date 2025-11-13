import psycopg2

conn = psycopg2.connect(
    user='postgres',
    password='postgres',
    host='localhost',
    database='ultra_db'
)
cur = conn.cursor()

# Add tags column
cur.execute('ALTER TABLE golden_standards ADD COLUMN IF NOT EXISTS tags TEXT[]')
conn.commit()

print('Added tags column to golden_standards table')

cur.close()
conn.close()
