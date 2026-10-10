import sqlite3
import time
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), 'health_guard.db')

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                date_str TEXT,
                event_type TEXT,
                severity TEXT,
                confidence REAL,
                description TEXT
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Database initialized.")
    except Exception as e:
        logger.error(f"DB Init Error: {e}")

def log_event(event_type, severity, confidence, description):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        ts = time.time()
        date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        
        cursor.execute('''
            INSERT INTO events (timestamp, date_str, event_type, severity, confidence, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (ts, date_str, event_type, severity, confidence, description))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB Insert Error: {e}")

def get_recent_events(limit=50):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp, event_type, severity, confidence, description 
            FROM events 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        events = []
        for r in rows:
            events.append({
                'timestamp': r[0],
                'event_type': r[1],
                'severity': r[2],
                'confidence': r[3],
                'description': r[4]
            })
        return events
    except Exception as e:
        logger.error(f"DB Select Error: {e}")
        return []

def get_weekly_stats():
    """Returns event counts grouped by date for the last 7 days."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT date_str, severity, COUNT(*) 
            FROM events 
            WHERE timestamp >= ?
            GROUP BY date_str, severity
            ORDER BY date_str ASC
        ''', (time.time() - 7*24*3600,))
        
        rows = cursor.fetchall()
        conn.close()
        
        stats = {}
        for date_str, severity, count in rows:
            if date_str not in stats:
                stats[date_str] = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'normal': 0}
            if severity in stats[date_str]:
                stats[date_str][severity] = count
                
        return stats
    except Exception as e:
        logger.error(f"DB Stats Error: {e}")
        return {}

# Khởi tạo DB ngay khi module được import
init_db()

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
