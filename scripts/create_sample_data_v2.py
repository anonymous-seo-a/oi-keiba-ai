#!/usr/bin/env python3
"""
大井競馬AIシステムのテスト用サンプルデータを作成するスクリプト
実際のデータ形式に近い形でサンプルを生成し、システム全体の動作確認を可能にする
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import datetime, timedelta
import pandas as pd
import sqlite3
from pathlib import Path

from config.settings import DATABASE_PATH
from src.data_collection.database import OiKeibaDatabase
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class SampleDataGenerator:
    def __init__(self):
        self.db = OiKeibaDatabase()
        
        # サンプル用の馬名
        self.horse_names = [
            "シンボリクリスエス", "ディープインパクト", "オルフェーヴル", "ジェンティルドンナ",
            "ゴールドシップ", "キタサンブラック", "アーモンドアイ", "コントレイル",
            "デアリングタクト", "エフフォーリア", "イクイノックス", "ドウデュース",
            "リバティアイランド", "ウシュバテソーロ", "タイトルホルダー", "パンサラッサ"
        ]
        
        # サンプル用の騎手名
        self.jockey_names = [
            "武豊", "福永祐一", "川田将雅", "ルメール", "デムーロ", "戸崎圭太",
            "田辺裕信", "横山典弘", "池添謙一", "松山弘平", "藤岡佑介", "岩田望来"
        ]
        
        # サンプル用の調教師名
        self.trainer_names = [
            "藤沢和雄", "堀宣行", "友道康夫", "国枝栄", "矢作芳人", "木村哲也",
            "中内田充正", "高野友和", "斉藤崇史", "杉山晴紀"
        ]
        
        # レース名のテンプレート
        self.race_name_templates = [
            "東京大賞典", "帝王賞", "マイルチャンピオンシップ南部杯", "かしわ記念",
            "大井記念", "東京シティカップ", "優駿スプリント", "サンタアニタトロフィー",
            "3歳特別", "C1特別", "B2特別", "未勝利戦"
        ]
    
    def generate_race_data(self, num_days=30, races_per_day=8):
        """レースデータを生成"""
        logger.info(f"{num_days}日分のレースデータを生成開始...")
        
        race_results = []
        end_date = datetime.now()
        
        for day_offset in range(num_days):
            race_date = end_date - timedelta(days=day_offset)
            
            # 土日水曜日のみ開催
            if race_date.weekday() not in [2, 5, 6]:  # 水、土、日
                continue
            
            for race_num in range(1, races_per_day + 1):
                race_id = f"S{race_date.strftime('%Y%m%d')}{race_num:02d}"
                race_name = f"{random.choice(self.race_name_templates)} (R{race_num})"
                
                # レース条件
                course_length = random.choice([1200, 1400, 1600, 1800, 2000])
                course_type = "ダート"  # 大井は基本ダート
                weather = random.choice(["晴", "曇", "雨", "小雨"])
                track_condition = random.choice(["良", "稍重", "重", "不良"])
                
                # 出走頭数
                num_horses = random.randint(8, 16)
                
                # 各馬の結果を生成
                horses = random.sample(self.horse_names, min(num_horses, len(self.horse_names)))
                jockeys = [random.choice(self.jockey_names) for _ in range(num_horses)]
                trainers = [random.choice(self.trainer_names) for _ in range(num_horses)]
                
                # オッズと人気順を生成
                odds_list = sorted([random.uniform(1.5, 100.0) for _ in range(num_horses)])
                
                for position in range(1, num_horses + 1):
                    # ランダムに馬を選んで着順を決定
                    horse_idx = position - 1
                    
                    result = {
                        'race_id': race_id,
                        'race_date': race_date.strftime('%Y-%m-%d'),
                        'race_name': race_name,
                        'course_length': course_length,
                        'course_type': course_type,
                        'weather': weather,
                        'track_condition': track_condition,
                        'finish_position': position,
                        'horse_name': horses[horse_idx],
                        'jockey_name': jockeys[horse_idx],
                        'trainer_name': trainers[horse_idx],
                        'horse_weight': random.randint(440, 520),
                        'odds': odds_list[horse_idx],
                        'popularity': horse_idx + 1,
                        'time_result': f"{course_length//1000}:{random.randint(10,59)}.{random.randint(0,9)}",
                        'margin': "アタマ" if position == 1 else random.choice(["アタマ", "クビ", "1/2馬身", "1馬身", "2馬身"])
                    }
                    race_results.append(result)
        
        logger.info(f"生成されたレース結果: {len(race_results)}件")
        return race_results
    
    def generate_horse_data(self, race_results):
        """馬の基本情報を生成"""
        logger.info("馬の基本情報を生成中...")
        
        horses_df = pd.DataFrame(race_results)
        unique_horses = horses_df['horse_name'].unique()
        
        horses_data = []
        for horse_name in unique_horses:
            horse_data = {
                'horse_name': horse_name,
                'birth_year': random.randint(2018, 2022),
                'sex': random.choice(['牡', '牝', 'セ']),
                'father': random.choice(["ディープインパクト", "ロードカナロア", "キングカメハメハ", "ハーツクライ"]),
                'mother': f"母馬{random.randint(1, 100)}",
                'trainer_name': random.choice(self.trainer_names),
                'owner_name': f"オーナー{random.randint(1, 50)}",
                'breeder_name': f"生産者{random.randint(1, 30)}"
            }
            horses_data.append(horse_data)
        
        return horses_data
    
    def generate_jra_horse_records(self, horses_data):
        """JRA転入馬の記録を生成"""
        logger.info("JRA転入馬データを生成中...")
        
        jra_records = []
        # 一部の馬をJRA転入馬として設定
        jra_horses = random.sample(horses_data, k=len(horses_data)//3)
        
        for horse in jra_horses:
            # JRAでの戦績を生成
            num_races = random.randint(5, 20)
            wins = random.randint(0, min(3, num_races//3))
            seconds = random.randint(0, min(3, (num_races-wins)//2))
            thirds = random.randint(0, min(3, num_races-wins-seconds))
            
            record = {
                'horse_name': horse['horse_name'],
                'jra_races': num_races,
                'jra_wins': wins,
                'jra_seconds': seconds,
                'jra_thirds': thirds,
                'jra_earnings': random.randint(1000000, 50000000),
                'jra_last_race_date': (datetime.now() - timedelta(days=random.randint(30, 180))).strftime('%Y-%m-%d'),
                'jra_last_race_name': random.choice(["東京記念", "中山大障害", "阪神カップ", "新馬戦"]),
                'jra_last_position': random.randint(1, 10)
            }
            jra_records.append(record)
        
        return jra_records
    
    def generate_jockey_trainer_stats(self, race_results):
        """騎手・調教師の統計を生成"""
        logger.info("騎手・調教師統計を生成中...")
        
        stats = []
        
        # 騎手統計
        results_df = pd.DataFrame(race_results)
        for jockey in self.jockey_names:
            jockey_races = results_df[results_df['jockey_name'] == jockey]
            if len(jockey_races) > 0:
                wins = len(jockey_races[jockey_races['finish_position'] == 1])
                stat = {
                    'person_type': 'jockey',
                    'person_name': jockey,
                    'year': 2025,
                    'total_races': len(jockey_races),
                    'wins': wins,
                    'win_rate': wins / len(jockey_races) if len(jockey_races) > 0 else 0,
                    'top3_rate': len(jockey_races[jockey_races['finish_position'] <= 3]) / len(jockey_races) if len(jockey_races) > 0 else 0
                }
                stats.append(stat)
        
        # 調教師統計
        for trainer in self.trainer_names:
            trainer_races = results_df[results_df['trainer_name'] == trainer]
            if len(trainer_races) > 0:
                wins = len(trainer_races[trainer_races['finish_position'] == 1])
                stat = {
                    'person_type': 'trainer',
                    'person_name': trainer,
                    'year': 2025,
                    'total_races': len(trainer_races),
                    'wins': wins,
                    'win_rate': wins / len(trainer_races) if len(trainer_races) > 0 else 0,
                    'top3_rate': len(trainer_races[trainer_races['finish_position'] <= 3]) / len(trainer_races) if len(trainer_races) > 0 else 0
                }
                stats.append(stat)
        
        return stats
    
    def save_to_database(self, race_results, horses_data, jra_records, stats):
        """データベースに保存"""
        logger.info("データベースに保存中...")
        
        # レース結果を保存
        self.db.save_race_results(race_results)
        
        # 馬データを保存
        conn = sqlite3.connect(DATABASE_PATH)
        
        # horsesテーブル
        horses_df = pd.DataFrame(horses_data)
        horses_df.to_sql('horses', conn, if_exists='replace', index=False)
        
        # jra_horse_recordsテーブル
        jra_df = pd.DataFrame(jra_records)
        jra_df.to_sql('jra_horse_records', conn, if_exists='replace', index=False)
        
        # jockey_trainer_statsテーブル
        stats_df = pd.DataFrame(stats)
        stats_df.to_sql('jockey_trainer_stats', conn, if_exists='replace', index=False)
        
        conn.close()
        
        logger.info("データベースへの保存完了！")
    
    def verify_data(self):
        """保存されたデータを確認"""
        logger.info("\nデータベースの内容を確認中...")
        
        conn = sqlite3.connect(DATABASE_PATH)
        
        # 各テーブルのレコード数を確認
        tables = ['race_results', 'horses', 'jra_horse_records', 'jockey_trainer_stats']
        
        for table in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            logger.info(f"{table}: {count}件")
            
            # サンプルデータを表示
            df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT 3", conn)
            print(f"\n{table}のサンプル:")
            print(df)
        
        conn.close()

def main():
    """メイン処理"""
    logger.info("サンプルデータ生成を開始します...")
    
    generator = SampleDataGenerator()
    
    # データ生成
    race_results = generator.generate_race_data(num_days=60, races_per_day=10)
    horses_data = generator.generate_horse_data(race_results)
    jra_records = generator.generate_jra_horse_records(horses_data)
    stats = generator.generate_jockey_trainer_stats(race_results)
    
    # データベースに保存
    generator.save_to_database(race_results, horses_data, jra_records, stats)
    
    # データ確認
    generator.verify_data()
    
    logger.info("\nサンプルデータの生成が完了しました！")
    logger.info("以下のコマンドでシステムをテストできます:")
    logger.info("1. モデル訓練: python scripts/train_model.py")
    logger.info("2. 予想実行: python scripts/daily_prediction.py --dry-run")
    logger.info("3. Webアプリ: streamlit run web_app/app.py")

if __name__ == "__main__":
    main()