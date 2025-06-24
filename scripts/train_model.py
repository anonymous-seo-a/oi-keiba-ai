#!/usr/bin/env python3
"""
モデル訓練実行スクリプト
"""
import sys
from pathlib import Path

# プロジェクトルートを追加
sys.path.append(str(Path(__file__).parent.parent))

from src.models.lightgbm_model import LightGBMModel
from src.utils.logger import setup_logger

def main():
    logger = setup_logger(__name__, 'model_training.log')
    logger.info("モデル訓練を開始します")
    
    try:
        model = LightGBMModel()
        accuracy = model.train()
        
        if accuracy:
            logger.info(f"モデル訓練が完了しました - 精度: {accuracy:.4f}")
            
            # 特徴量重要度を表示
            importance = model.get_feature_importance()
            if importance is not None:
                logger.info("特徴量重要度:")
                for _, row in importance.head(10).iterrows():
                    logger.info(f"  {row['feature']}: {row['importance']:.4f}")
        else:
            logger.error("モデル訓練が失敗しました")
            return 1
            
    except Exception as e:
        logger.error(f"モデル訓練エラー: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
