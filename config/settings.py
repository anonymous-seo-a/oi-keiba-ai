"""
プロジェクト設定ファイル
"""
import os
from pathlib import Path

# プロジェクトルートディレクトリ
PROJECT_ROOT = Path(__file__).parent.parent

# データディレクトリ
DATA_DIR = PROJECT_ROOT / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'
EXTERNAL_DATA_DIR = DATA_DIR / 'external'

# ログ設定
LOG_DIR = PROJECT_ROOT / 'logs'
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# データベース設定
DATABASE_PATH = PROJECT_ROOT / 'data' / 'oi_keiba.db'

# スクレイピング設定
SCRAPING_DELAY = 1.0  # 秒
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# netkeiba.com設定
NETKEIBA_BASE_URL = 'https://db.netkeiba.com'
OI_COURSE_CODE = '30'  # 大井競馬場のコード

# モデル設定
MODEL_DIR = PROJECT_ROOT / 'models'
LIGHTGBM_PARAMS = {
    'objective': 'multiclass',
    'num_class': 16,  # 最大出走頭数を想定
    'metric': 'multi_logloss',
    'boosting_type': 'gbdt',
    'num_leaves': 31,
    'learning_rate': 0.05,
    'feature_fraction': 0.9,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'verbose': 0
}

# 予想設定
MIN_CONFIDENCE = 0.6  # 最小予想信頼度
MAX_BET_RATIO = 0.1   # 最大投票率（資金の10%まで）

# 環境変数から設定を読み込む
def load_env_settings():
    """環境変数から設定を読み込み"""
    return {
        'jravan_api_key': os.getenv('JRAVAN_API_KEY'),
        'database_url': os.getenv('DATABASE_URL', str(DATABASE_PATH)),
        'log_level': os.getenv('LOG_LEVEL', LOG_LEVEL),
        'scraping_delay': float(os.getenv('SCRAPING_DELAY', SCRAPING_DELAY))
    }
