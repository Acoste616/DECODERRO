import psycopg2

conn = psycopg2.connect(
    user='postgres',
    password='postgres',
    host='localhost',
    database='ultra_db'
)
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM feedback_logs')
print(f'Feedback count: {cur.fetchone()[0]}')

cur.execute('SELECT feedback_type, session_id, feedback_note FROM feedback_logs ORDER BY created_at DESC LIMIT 5')
print('\nRecent feedback:')
for row in cur.fetchall():
    note = row[2][:50] if row[2] else "No comment"
    print(f'  {row[0]} | {row[1]} | {note}')

cur.close()
conn.close()
