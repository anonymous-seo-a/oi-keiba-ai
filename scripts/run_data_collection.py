#!/usr/bin/env python3
"""
データ収集実行スクリプト
コマンドライン引数で期間を指定可能
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# プロジェクトルートを追加
sys.path.append(str(Path(__file__).parent.parent))

from src.data_collection.scraper import OiKeibaScraper
from src.data_collection.database import OiKeibaDatabase
from src.utils.logger import setup_logger


def parse_date(date_str):
    """日付文字列をパース"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f"日付は YYYY-MM-DD 形式で指定してください: {date_str}")


def main():
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(
        description='大井競馬のレースデータを収集します',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 過去3ヶ月のデータを収集
  python scripts/run_data_collection.py --months-back 3
  
  # 特定期間のデータを収集
  python scripts/run_data_collection.py --start-date 2025-06-01 --end-date 2025-06-25
  
  # 最近7日間のデータを収集
  python scripts/run_data_collection.py --days-back 7
        """
    )
    
    # 期間指定オプション（3つの方法から選択）
    period_group = parser.add_mutually_exclusive_group()
    period_group.add_argument(
        '--months-back',
        type=int,
        help='何ヶ月前からのデータを収集するか（デフォルト: 36）'
    )
    period_group.add_argument(
        '--days-back',
        type=int,
        help='何日前からのデータを収集するか'
    )
    period_group.add_argument(
        '--start-date',
        type=parse_date,
        help='収集開始日（YYYY-MM-DD形式）'
    )
    
    # 終了日オプション（start-dateと組み合わせて使用）
    parser.add_argument(
        '--end-date',
        type=parse_date,
        help='収集終了日（YYYY-MM-DD形式、デフォルト: 今日）'
    )
    
    # その他のオプション
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='実際にはデータを保存せず、収集対象を確認するだけ'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='詳細なログを出力'
    )
    
    args = parser.parse_args()
    
    # ロガーの設定
    log_level = 'DEBUG' if args.verbose else 'INFO'
    logger = setup_logger(__name__, 'data_collection.log', level=log_level)
    
    # 期間の決定
    end_date = args.end_date or datetime.now()
    
    if args.start_date:
        if args.end_date and args.start_date > args.end_date:
            logger.error("開始日が終了日より後になっています")
            return 1
        start_date = args.start_date
        logger.info(f"指定期間: {start_date.strftime('%Y-%m-%d')} から {end_date.strftime('%Y-%m-%d')}")
        
    elif args.days_back:
        start_date = end_date - timedelta(days=args.days_back)
        logger.info(f"過去 {args.days_back} 日間のデータを収集")
        
    elif args.months_back:
        start_date = end_date - timedelta(days=args.months_back * 30)
        logger.info(f"過去 {args.months_back} ヶ月間のデータを収集")
        
    else:
        # デフォルトは36ヶ月
        months_back = 36
        start_date = end_date - timedelta(days=months_back * 30)
        logger.info(f"デフォルト設定: 過去 {months_back} ヶ月間のデータを収集")
    
    # 収集期間の確認
    total_days = (end_date - start_date).days
    logger.info(f"収集期間: {start_date.strftime('%Y-%m-%d')} 〜 {end_date.strftime('%Y-%m-%d')} ({total_days}日間)")
    
    if args.dry_run:
        logger.info("ドライランモード: データの保存は行いません")
    
    try:
        # スクレイパーの初期化
        db = OiKeibaDatabase() if not args.dry_run else None
        scraper = OiKeibaScraper(db=db)
        
        # データ収集の実行
        logger.info("データ収集を開始します...")
        
        # get_race_listメソッドを直接呼び出し
        race_list = scraper.get_race_list(start_date, end_date)
        logger.info(f"取得対象レース数: {len(race_list)}")
        
        if args.dry_run:
            # ドライランモードでは最初の10件を表示
            logger.info("ドライランモード: 収集対象レースの確認")
            for i, race in enumerate(race_list[:10]):
                logger.info(f"  {i+1}. {race['race_date']} - {race['race_name']} (ID: {race['race_id']})")
            if len(race_list) > 10:
                logger.info(f"  ... 他 {len(race_list) - 10} レース")
        else:
            # 実際のデータ収集
            import time
            from config.settings import SCRAPING_DELAY
            
            for i, race in enumerate(race_list):
                logger.info(f"進捗: {i+1}/{len(race_list)} - {race['race_name']}")
                
                results = scraper.scrape_race_result(race['race_id'], race['race_date'])
                if results:
                    scraper.db.save_race_results(results)
                    logger.info(f"保存完了: {len(results)}件")
                else:
                    logger.warning(f"データ取得失敗: {race['race_id']}")
                
                # サーバーに負荷をかけないように待機
                if i < len(race_list) - 1:  # 最後のレースの後は待機不要
                    time.sleep(SCRAPING_DELAY)
        
        logger.info("データ収集が完了しました！")
        
        # 統計情報の表示
        if not args.dry_run and scraper.db:
            conn = scraper.db.get_connection()
            total_records = conn.execute("SELECT COUNT(*) FROM race_results").fetchone()[0]
            logger.info(f"データベース内の総レコード数: {total_records}")
            conn.close()
        
        return 0
        
    except Exception as e:
        logger.error(f"データ収集エラー: {e}")
        if args.verbose:
            import traceback
            logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
