with open('database.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_func = '''
def get_all_events_for_export():
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT timestamp, event_type, severity, confidence, description FROM events ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"DB Export Error: {e}")
        return []
'''

if 'get_all_events_for_export' not in text:
    text += new_func
    with open('database.py', 'w', encoding='utf-8') as f:
        f.write(text)
print('Patched database.py')
