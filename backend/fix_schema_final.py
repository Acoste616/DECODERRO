import psycopg2

conn = psycopg2.connect(
    user='postgres',
    password='postgres',
    host='localhost',
    database='ultra_db'
)
cur = conn.cursor()

# Make category nullable
cur.execute('ALTER TABLE golden_standards ALTER COLUMN category DROP NOT NULL')
conn.commit()

print('Fixed golden_standards.category - now nullable')

cur.close()
conn.close()
