"""
競馬予想システム
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional

from src.models.lightgbm_model import LightGBMModel
from src.data_collection.database import OiKeibaDatabase
from src.utils.logger import setup_logger
from config.settings import MIN_CONFIDENCE

class OiKeibaPredictor:
    def __init__(self, model_name='oi_keiba_lightgbm'):
        self.model = LightGBMModel(model_name)
        self.db = OiKeibaDatabase()
        self.logger = setup_logger(__name__)
        
        # モデルを読み込み
        if not self.model.load_model():
            self.logger.warning("モデルが読み込めません。訓練が必要です。")
    
    def predict_race(self, race_data: pd.DataFrame) -> List[Dict]:
        """レースの予想を実行"""
        if self.model.model is None:
            self.logger.error("モデルが読み込まれていません")
            return []
        
        try:
            # 予想実行
            predictions = self.model.predict(race_data)
            
            # 信頼度でフィルタリング
            filtered_predictions = [
                pred for pred in predictions 
                if pred['confidence'] >= MIN_CONFIDENCE
            ]
            
            # 予想着順でソート
            filtered_predictions.sort(key=lambda x: x['predicted_position'])
            
            self.logger.info(f"予想完了: {len(filtered_predictions)}頭の予想")
            return filtered_predictions
            
        except Exception as e:
            self.logger.error(f"予想エラー: {e}")
            return []
    
    def get_betting_recommendations(self, predictions: List[Dict], 
                                 betting_budget: float = 10000) -> List[Dict]:
        """投票推奨案を作成"""
        recommendations = []
        
        if not predictions:
            return recommendations
        
        # 信頼度の高い順にソート
        sorted_predictions = sorted(predictions, key=lambda x: x['confidence'], reverse=True)
        
        # 予算配分
        total_confidence = sum(pred['confidence'] for pred in sorted_predictions)
        
        for pred in sorted_predictions:
            confidence_ratio = pred['confidence'] / total_confidence
            bet_amount = int(betting_budget * confidence_ratio)
            
            if bet_amount >= 100:  # 最小投票額
                recommendations.append({
                    'horse_name': pred['horse_name'],
                    'predicted_position': pred['predicted_position'],
                    'confidence': pred['confidence'],
                    'recommended_bet': bet_amount,
                    'bet_type': 'win' if pred['predicted_position'] == 1 else 'place'
                })
        
        return recommendations
    
    def analyze_prediction_accuracy(self, start_date: str, end_date: str) -> Dict:
        """予想精度を分析"""
        try:
            # 期間内のレース結果を取得
            query = f"""
            SELECT * FROM race_results 
            WHERE race_date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY race_date, race_id
            """
            
            df = pd.read_sql_query(query, self.db.db_path)
            
            if df.empty:
                return {'error': '対象期間のデータがありません'}
            
            # レース単位でグループ化
            race_groups = df.groupby(['race_date', 'race_id'])
            
            total_races = 0
            correct_predictions = 0
            place_predictions = 0
            
            for (race_date, race_id), race_df in race_groups:
                # 各レースの予想を実行
                predictions = self.predict_race(race_df)
                
                if not predictions:
                    continue
                
                total_races += 1
                
                # 実際の1着馬
                winner = race_df[race_df['finish_position'] == 1]['horse_name'].iloc[0]
                
                # 予想1着馬
                predicted_winner = predictions[0]['horse_name'] if predictions else None
                
                if predicted_winner == winner:
                    correct_predictions += 1
                
                # 3着以内予想の確認
                top3_actual = race_df[race_df['finish_position'] <= 3]['horse_name'].tolist()
                predicted_top3 = [pred['horse_name'] for pred in predictions if pred['predicted_position'] <= 3]
                
                if any(horse in top3_actual for horse in predicted_top3):
                    place_predictions += 1
            
            win_accuracy = correct_predictions / total_races if total_races > 0 else 0
            place_accuracy = place_predictions / total_races if total_races > 0 else 0
            
            return {
                'total_races': total_races,
                'win_predictions': correct_predictions,
                'win_accuracy': win_accuracy,
                'place_predictions': place_predictions,
                'place_accuracy': place_accuracy,
                'analysis_period': f'{start_date} - {end_date}'
            }
            
        except Exception as e:
            self.logger.error(f"精度分析エラー: {e}")
            return {'error': str(e)}
