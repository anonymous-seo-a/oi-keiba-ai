"""
データベース操作ユーティリティ
"""
import sqlite3
import pandas as pd
from pathlib import Path
from config.settings import DATABASE_PATH
from src.utils.logger import setup_logger

class OiKeibaDatabase:
    def __init__(self, db_path=None):
        self.db_path = db_path or DATABASE_PATH
        self.logger = setup_logger(__name__)
        self.init_database()
    
    def init_database(self):
        """データベースの初期化"""
        # データベースディレクトリを作成
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # レース結果テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS race_results (
                race_id TEXT,
                race_date TEXT,
                race_name TEXT,
                course_length INTEGER,
                course_type TEXT,
                weather TEXT,
                track_condition TEXT,
                horse_name TEXT,
                finish_position INTEGER,
                jockey_name TEXT,
                trainer_name TEXT,
                horse_weight INTEGER,
                odds REAL,
                popularity INTEGER,
                time_result TEXT,
                margin TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (race_id, horse_name)
            )
        ''')
        
        # 馬の基本情報テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS horses (
                horse_id TEXT PRIMARY KEY,
                horse_name TEXT UNIQUE,
                birth_date TEXT,
                gender TEXT,
                coat_color TEXT,
                father_name TEXT,
                mother_name TEXT,
                owner_name TEXT,
                trainer_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # JRA成績テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jra_horse_records (
                horse_name TEXT,
                jra_race_date TEXT,
                course_name TEXT,
                race_name TEXT,
                finish_position INTEGER,
                total_horses INTEGER,
                jockey_name TEXT,
                horse_weight INTEGER,
                odds REAL,
                time_result TEXT,
                prize_money INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (horse_name, jra_race_date, race_name)
            )
        ''')
        
        # 騎手・調教師統計テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jockey_trainer_stats (
                name TEXT,
                role TEXT,  -- 'jockey' or 'trainer'
                year INTEGER,
                races INTEGER,
                wins INTEGER,
                win_rate REAL,
                places INTEGER,
                place_rate REAL,
                prize_money INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (name, role, year)
            )
        ''')
        
        conn.commit()
        conn.close()
        self.logger.info("データベースを初期化しました")
    
    def save_race_results(self, results):
        """レース結果を保存"""
        if not results:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for result in results:
            cursor.execute('''
                INSERT OR REPLACE INTO race_results 
                (race_id, race_date, race_name, course_length, course_type, weather, 
                 track_condition, horse_name, finish_position, jockey_name, trainer_name, 
                 horse_weight, odds, popularity, time_result, margin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.get('race_id'), result.get('race_date'), result.get('race_name'),
                result.get('course_length'), result.get('course_type'), result.get('weather'),
                result.get('track_condition'), result.get('horse_name'), result.get('finish_position'),
                result.get('jockey_name'), result.get('trainer_name'), result.get('horse_weight'),
                result.get('odds'), result.get('popularity'), result.get('time_result'), result.get('margin')
            ))
        
        conn.commit()
        conn.close()
        self.logger.info(f"レース結果を保存しました: {len(results)}件")
    
    def get_race_data(self, limit=None):
        """レースデータを取得"""
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM race_results ORDER BY race_date DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def get_horse_stats(self, horse_name):
        """指定した馬の統計を取得"""
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT 
            COUNT(*) as total_races,
            AVG(finish_position) as avg_position,
            MIN(finish_position) as best_position,
            COUNT(CASE WHEN finish_position = 1 THEN 1 END) as wins,
            COUNT(CASE WHEN finish_position <= 3 THEN 1 END) as places
        FROM race_results 
        WHERE horse_name = ?
        """
        
        result = pd.read_sql_query(query, conn, params=[horse_name])
        conn.close()
        
        return result.iloc[0] if not result.empty else None
