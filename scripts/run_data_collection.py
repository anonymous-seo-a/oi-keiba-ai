#!/usr/bin/env python3
"""
データ収集実行スクリプト
"""
import sys
from pathlib import Path

# プロジェクトルートを追加
sys.path.append(str(Path(__file__).parent.parent))

from src.data_collection.scraper import OiKeibaScraper
from src.utils.logger import setup_logger

def main():
    logger = setup_logger(__name__, 'data_collection.log')
    logger.info("データ収集を開始します")
    
    try:
        scraper = OiKeibaScraper()
        scraper.run_scraping(months_back=36)
        logger.info("データ収集が完了しました")
    except Exception as e:
        logger.error(f"データ収集エラー: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
