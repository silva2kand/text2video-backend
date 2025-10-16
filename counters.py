import sqlite3
import datetime
import threading
from typing import Dict, Any

class ApiCounters:
    def __init__(self, db_path: str = 'usage.db'):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint TEXT NOT NULL,
                    count INTEGER DEFAULT 0,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT PRIMARY KEY,
                    total_requests INTEGER DEFAULT 0,
                    image_generations INTEGER DEFAULT 0,
                    video_generations INTEGER DEFAULT 0,
                    prompt_enhancements INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def increment(self, endpoint: str) -> None:
        """Increment counter for specific endpoint"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                # Update endpoint counter
                conn.execute('''
                    INSERT OR REPLACE INTO api_usage (endpoint, count, last_used)
                    VALUES (?, COALESCE((SELECT count FROM api_usage WHERE endpoint = ?), 0) + 1, ?)
                ''', (endpoint, endpoint, datetime.datetime.now()))
                
                # Update daily stats
                today = datetime.date.today().isoformat()
                
                # Get current daily stats
                cursor = conn.execute('SELECT * FROM daily_stats WHERE date = ?', (today,))
                daily_row = cursor.fetchone()
                
                if daily_row:
                    # Update existing record
                    updates = {
                        'total_requests': daily_row[1] + 1,
                        'image_generations': daily_row[2] + (1 if endpoint == 'image_generations' else 0),
                        'video_generations': daily_row[3] + (1 if endpoint == 'video_generations' else 0),
                        'prompt_enhancements': daily_row[4] + (1 if endpoint == 'prompt_enhancements' else 0)
                    }
                    
                    conn.execute('''
                        UPDATE daily_stats 
                        SET total_requests = ?, image_generations = ?, video_generations = ?, prompt_enhancements = ?
                        WHERE date = ?
                    ''', (updates['total_requests'], updates['image_generations'], 
                         updates['video_generations'], updates['prompt_enhancements'], today))
                else:
                    # Create new record
                    conn.execute('''
                        INSERT INTO daily_stats (date, total_requests, image_generations, video_generations, prompt_enhancements)
                        VALUES (?, 1, ?, ?, ?)
                    ''', (today, 
                         1 if endpoint == 'image_generations' else 0,
                         1 if endpoint == 'video_generations' else 0, 
                         1 if endpoint == 'prompt_enhancements' else 0))
                
                conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive usage statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Get endpoint stats
            cursor = conn.execute('SELECT endpoint, count, last_used FROM api_usage ORDER BY count DESC')
            endpoint_stats = {}
            for row in cursor.fetchall():
                endpoint_stats[row[0]] = {
                    'count': row[1],
                    'last_used': row[2]
                }
            
            # Get today's stats
            today = datetime.date.today().isoformat()
            cursor = conn.execute('SELECT * FROM daily_stats WHERE date = ?', (today,))
            today_row = cursor.fetchone()
            
            today_stats = {
                'total_requests': today_row[1] if today_row else 0,
                'image_generations': today_row[2] if today_row else 0,
                'video_generations': today_row[3] if today_row else 0,
                'prompt_enhancements': today_row[4] if today_row else 0
            }
            
            # Get last 7 days stats
            cursor = conn.execute('''
                SELECT date, total_requests, image_generations, video_generations, prompt_enhancements 
                FROM daily_stats 
                WHERE date >= date('now', '-7 days') 
                ORDER BY date DESC
            ''')
            
            weekly_stats = []
            for row in cursor.fetchall():
                weekly_stats.append({
                    'date': row[0],
                    'total_requests': row[1],
                    'image_generations': row[2],
                    'video_generations': row[3],
                    'prompt_enhancements': row[4]
                })
            
            # Calculate totals
            cursor = conn.execute('SELECT SUM(count) FROM api_usage')
            total_all_time = cursor.fetchone()[0] or 0
            
            return {
                'endpoint_stats': endpoint_stats,
                'today': today_stats,
                'last_7_days': weekly_stats,
                'total_all_time': total_all_time,
                'timestamp': datetime.datetime.now().isoformat()
            }
    
    def reset_stats(self) -> None:
        """Reset all statistics (use with caution)"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('DELETE FROM api_usage')
                conn.execute('DELETE FROM daily_stats')
                conn.commit()
    
    def get_endpoint_count(self, endpoint: str) -> int:
        """Get count for specific endpoint"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT count FROM api_usage WHERE endpoint = ?', (endpoint,))
            row = cursor.fetchone()
            return row[0] if row else 0