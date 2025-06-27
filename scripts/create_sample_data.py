#!/usr/bin/env python3
"""
サンプルデータ作成スクリプト
テスト用のダミーデータをデータベースに投入する
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.data_collection.database import OiKeibaDatabase
from src.utils.logger import setup_logger

def create_sample_data(num_races=10, horses_per_race=10):
    """サンプルデータを作成してデータベースに保存"""
    logger = setup_logger(__name__)
    db = OiKeibaDatabase()
    
    logger.info(f"サンプルデータ作成開始: {num_races}レース x {horses_per_race}頭")
    
    # サンプル馬名
    horse_names = [
        "サンプルホースA", "サンプルホースB", "サンプルホースC", "サンプルホースD",
        "サンプルホースE", "サンプルホースF", "サンプルホースG", "サンプルホースH",
        "サンプルホースI", "サンプルホースJ", "サンプルホースK", "サンプルホースL",
        "ダミーランナー1", "ダミーランナー2", "ダミーランナー3", "ダミーランナー4",
        "テストホース1", "テストホース2", "テストホース3", "テストホース4"
    ]
    
    # サンプル騎手名
    jockey_names = [
        "サンプル騎手A", "サンプル騎手B", "サンプル騎手C", "サンプル騎手D",
        "テスト騎手1", "テスト騎手2", "テスト騎手3", "テスト騎手4"
    ]
    
    # サンプル調教師名
    trainer_names = [
        "サンプル調教師A", "サンプル調教師B", "サンプル調教師C", "サンプル調教師D",
        "テスト調教師1", "テスト調教師2", "テスト調教師3", "テスト調教師4"
    ]
    
    # レース条件
    course_lengths = [1200, 1400, 1600, 1800, 2000]
    weather_conditions = ["晴", "曇", "雨", "小雨"]
    track_conditions = ["良", "稍重", "重", "不良"]
    
    created_count = 0
    base_date = datetime.now() - timedelta(days=365)  # 1年前から
    
    for race_idx in range(num_races):
        race_date = base_date + timedelta(days=race_idx * 7)  # 週1レース
        race_id = f"SAMPLE{race_date.strftime('%Y%m%d')}{race_idx+1:02d}"
        
        # レース情報
        race_info = {
            'race_id': race_id,
            'race_date': race_date.strftime('%Y-%m-%d'),
            'race_number': race_idx % 12 + 1,
            'race_name': f"サンプルレース{race_idx+1}",
            'course_length': random.choice(course_lengths),
            'weather': random.choice(weather_conditions),
            'track_condition': random.choice(track_conditions),
            'race_time': f"{random.randint(13, 20)}:{random.randint(0, 59):02d}"
        }
        
        # 出走馬をランダムに選択
        selected_horses = random.sample(horse_names, min(horses_per_race, len(horse_names)))
        
        # 着順をランダムに決定
        positions = list(range(1, len(selected_horses) + 1))
        random.shuffle(positions)
        
        for i, horse_name in enumerate(selected_horses):
            race_data = {
                'race_id': race_id,
                'race_date': race_date.strftime('%Y-%m-%d'),
                'race_number': race_info['race_number'],
                'race_name': race_info['race_name'],
                'horse_name': horse_name,
                'horse_number': i + 1,
                'jockey_name': random.choice(jockey_names),
                'trainer_name': random.choice(trainer_names),
                'horse_weight': random.randint(440, 520),
                'odds': round(random.uniform(1.5, 99.9), 1),
                'popularity': i + 1,
                'finish_position': positions[i],
                'course_length': race_info['course_length'],
                'weather': race_info['weather'],
                'track_condition': race_info['track_condition'],
                'race_time': race_info['race_time']
            }
            
            # 時間を文字列に変換（タイムを生成）
            base_time = 60 + (race_info['course_length'] / 1000) * 35  # 基準タイム
            race_data['time'] = round(base_time + random.uniform(-5, 10), 1)
            
            # データベースに保存
            db.save_race_result(race_data)
            created_count += 1
    
    logger.info(f"サンプルデータ作成完了: {created_count}件")
    
    # 統計情報を表示
    stats = db.get_data_stats()
    logger.info(f"データベース統計: {stats}")
    
    return created_count

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='サンプルデータ作成')
    parser.add_argument(
        '--races', '-r',
        type=int,
        default=10,
        help='作成するレース数（デフォルト: 10）'
    )
    parser.add_argument(
        '--horses', '-h',
        type=int,
        default=10,
        help='1レースあたりの出走頭数（デフォルト: 10）'
    )
    parser.add_argument(
        '--clear', '-c',
        action='store_true',
        help='既存データをクリアしてから作成'
    )
    
    args = parser.parse_args()
    
    logger = setup_logger(__name__)
    
    try:
        if args.clear:
            logger.warning("既存データをクリアします")
            db = OiKeibaDatabase()
            # データベースを再初期化
            db.init_database()
            logger.info("データベースをクリアしました")
        
        # サンプルデータ作成
        count = create_sample_data(args.races, args.horses)
        
        print(f"\n✅ サンプルデータを{count}件作成しました")
        
        # 作成したデータの確認
        db = OiKeibaDatabase()
        recent_races = db.get_recent_races(limit=5)
        
        if not recent_races.empty:
            print("\n📊 最近のレース:")
            print(recent_races[['race_date', 'race_name', 'horse_name', 'finish_position']].head(10))
        
        return 0
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        print(f"❌ エラー: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())