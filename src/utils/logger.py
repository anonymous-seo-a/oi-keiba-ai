"""
ログ設定ユーティリティ
"""
import logging
import sys
from pathlib import Path
from config.settings import LOG_DIR, LOG_LEVEL, LOG_FORMAT

def setup_logger(name, log_file=None, level=None):
    """ロガーのセットアップ"""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    # ログレベル設定
    log_level = level or LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # フォーマッター
    formatter = logging.Formatter(LOG_FORMAT)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ファイルハンドラー
    if log_file:
        LOG_DIR.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(LOG_DIR / log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
