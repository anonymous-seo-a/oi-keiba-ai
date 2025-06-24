"""
投票戦略システム
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from src.utils.logger import setup_logger
from config.settings import MAX_BET_RATIO, MIN_CONFIDENCE

@dataclass
class BetRecommendation:
    horse_name: str
    bet_type: str  # 'win', 'place', 'quinella', etc.
    bet_amount: int
    confidence: float
    expected_return: float
    risk_level: str  # 'low', 'medium', 'high'

class BettingStrategy:
    def __init__(self, initial_budget: float = 100000):
        self.initial_budget = initial_budget
        self.current_budget = initial_budget
        self.betting_history = []
        self.logger = setup_logger(__name__)
    
    def kelly_criterion(self, win_probability: float, odds: float) -> float:
        """ケリー基準による最適投票額を計算"""
        if win_probability <= 0 or odds <= 1:
            return 0
        
        # ケリー基準: f = (bp - q) / b
        # b = オッズ-1, p = 勝率, q = 負率
        b = odds - 1
        p = win_probability
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b
        
        # 負の値の場合は投票しない
        if kelly_fraction <= 0:
            return 0
        
        # 最大投票率で制限
        kelly_fraction = min(kelly_fraction, MAX_BET_RATIO)
        
        return self.current_budget * kelly_fraction
    
    def calculate_bet_amount(self, predictions: List[Dict], 
                           budget_ratio: float = 0.1) -> List[BetRecommendation]:
        """投票額を計算"""
        recommendations = []
        available_budget = self.current_budget * budget_ratio
        
        # 信頼度の高い予想のみを対象
        high_confidence_predictions = [
            pred for pred in predictions 
            if pred['confidence'] >= MIN_CONFIDENCE
        ]
        
        if not high_confidence_predictions:
            self.logger.info("信頼度の高い予想がありません")
            return recommendations
        
        # 各予想に対して投票額を計算
        for pred in high_confidence_predictions:
            horse_name = pred['horse_name']
            confidence = pred['confidence']
            predicted_position = pred['predicted_position']
            
            # オッズ情報がある場合（実際の運用では外部から取得）
            estimated_odds = self.estimate_odds(predicted_position, confidence)
            
            # ケリー基準による投票額
            kelly_amount = self.kelly_criterion(confidence, estimated_odds)
            
            # 投票タイプを決定
            if predicted_position == 1 and confidence >= 0.7:
                bet_type = 'win'
                risk_level = 'high'
            elif predicted_position <= 3:
                bet_type = 'place'
                risk_level = 'medium' if predicted_position <= 2 else 'low'
            else:
                continue  # 4着以下は投票しない
            
            # 最終投票額を決定（最小100円、最大available_budgetの30%）
            final_amount = max(100, min(kelly_amount, available_budget * 0.3))
            
            if final_amount >= 100:
                expected_return = final_amount * estimated_odds * confidence
                
                recommendations.append(BetRecommendation(
                    horse_name=horse_name,
                    bet_type=bet_type,
                    bet_amount=int(final_amount),
                    confidence=confidence,
                    expected_return=expected_return,
                    risk_level=risk_level
                ))
        
        # 投票額の合計が予算を超えないよう調整
        total_bet = sum(rec.bet_amount for rec in recommendations)
        if total_bet > available_budget:
            adjustment_ratio = available_budget / total_bet
            for rec in recommendations:
                rec.bet_amount = int(rec.bet_amount * adjustment_ratio)
        
        return recommendations
    
    def estimate_odds(self, predicted_position: int, confidence: float) -> float:
        """予想順位と信頼度からオッズを推定"""
        # 簡易的なオッズ推定（実際の運用では外部APIから取得）
        base_odds = {
            1: 3.0,  # 1番人気
            2: 5.0,  # 2番人気
            3: 8.0,  # 3番人気
        }
        
        estimated_odds = base_odds.get(predicted_position, 10.0)
        
        # 信頼度に基づいて調整
        confidence_factor = 1 + (1 - confidence)
        estimated_odds *= confidence_factor
        
        return max(1.1, estimated_odds)  # 最小オッズ1.1倍
    
    def record_bet_result(self, horse_name: str, bet_type: str, 
                         bet_amount: int, actual_result: int, 
                         actual_odds: float) -> Dict:
        """投票結果を記録"""
        # 的中判定
        is_hit = False
        payout = 0
        
        if bet_type == 'win' and actual_result == 1:
            is_hit = True
            payout = bet_amount * actual_odds
        elif bet_type == 'place' and actual_result <= 3:
            is_hit = True
            # 複勝オッズは単勝オッズの約1/3と仮定
            place_odds = max(1.1, actual_odds / 3)
            payout = bet_amount * place_odds
        
        # 収支計算
        profit_loss = payout - bet_amount if is_hit else -bet_amount
        
        # 履歴に記録
        bet_record = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'horse_name': horse_name,
            'bet_type': bet_type,
            'bet_amount': bet_amount,
            'actual_result': actual_result,
            'actual_odds': actual_odds,
            'is_hit': is_hit,
            'payout': payout,
            'profit_loss': profit_loss
        }
        
        self.betting_history.append(bet_record)
        
        # 予算更新
        self.current_budget += profit_loss
        
        self.logger.info(f"投票結果記録: {horse_name} - {'的中' if is_hit else '不的中'} - 収支: {profit_loss:+d}円")
        
        return bet_record
    
    def get_performance_summary(self) -> Dict:
        """投票成績のサマリーを取得"""
        if not self.betting_history:
            return {'error': '投票履歴がありません'}
        
        df = pd.DataFrame(self.betting_history)
        
        total_bets = len(df)
        total_invested = df['bet_amount'].sum()
        total_payout = df['payout'].sum()
        total_profit_loss = df['profit_loss'].sum()
        
        hit_rate = df['is_hit'].mean()
        recovery_rate = total_payout / total_invested if total_invested > 0 else 0
        
        # タイプ別成績
        win_bets = df[df['bet_type'] == 'win']
        place_bets = df[df['bet_type'] == 'place']
        
        summary = {
            'total_bets': total_bets,
            'total_invested': total_invested,
            'total_payout': total_payout,
            'total_profit_loss': total_profit_loss,
            'hit_rate': hit_rate,
            'recovery_rate': recovery_rate,
            'current_budget': self.current_budget,
            'budget_change': self.current_budget - self.initial_budget,
            'win_bet_stats': {
                'count': len(win_bets),
                'hit_rate': win_bets['is_hit'].mean() if len(win_bets) > 0 else 0,
                'recovery_rate': win_bets['payout'].sum() / win_bets['bet_amount'].sum() if len(win_bets) > 0 else 0
            },
            'place_bet_stats': {
                'count': len(place_bets),
                'hit_rate': place_bets['is_hit'].mean() if len(place_bets) > 0 else 0,
                'recovery_rate': place_bets['payout'].sum() / place_bets['bet_amount'].sum() if len(place_bets) > 0 else 0
            }
        }
        
        return summary
    
    def optimize_strategy(self) -> Dict:
        """戦略の最適化提案"""
        if len(self.betting_history) < 10:
            return {'message': '十分な履歴データがないため、最適化できません'}
        
        df = pd.DataFrame(self.betting_history)
        
        # 信頼度別の成績分析
        # （実装では予想時の信頼度も記録する必要があります）
        
        recommendations = []
        
        # 的中率が低い場合
        hit_rate = df['is_hit'].mean()
        if hit_rate < 0.3:
            recommendations.append("信頼度閾値を上げることを検討してください")
        
        # 回収率が低い場合
        recovery_rate = df['payout'].sum() / df['bet_amount'].sum()
        if recovery_rate < 0.8:
            recommendations.append("投票額を保守的にすることを検討してください")
        
        # 単勝・複勝の成績比較
        win_recovery = df[df['bet_type'] == 'win']['payout'].sum() / max(1, df[df['bet_type'] == 'win']['bet_amount'].sum())
        place_recovery = df[df['bet_type'] == 'place']['payout'].sum() / max(1, df[df['bet_type'] == 'place']['bet_amount'].sum())
        
        if place_recovery > win_recovery * 1.2:
            recommendations.append("複勝中心の戦略が効果的かもしれません")
        elif win_recovery > place_recovery * 1.2:
            recommendations.append("単勝中心の戦略が効果的かもしれません")
        
        return {
            'current_performance': {
                'hit_rate': hit_rate,
                'recovery_rate': recovery_rate,
                'total_profit_loss': df['profit_loss'].sum()
            },
            'recommendations': recommendations
        }
