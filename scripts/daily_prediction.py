#!/usr/bin/env python3
"""
日次予想実行スクリプト
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.prediction.predictor import OiKeibaPredictor
from src.prediction.betting_strategy import BettingStrategy
from src.utils.logger import setup_logger
from config.settings import MIN_CONFIDENCE

def get_today_races():
    """今日のレース情報を取得（モック実装）"""
    # 実際の実装では、TCK公式サイトやAPIから取得
    # ここではサンプルデータを返す
    
    sample_races = [
        {
            'race_id': f'OI{datetime.now().strftime("%Y%m%d")}01',
            'race_name': '第1レース',
            'race_time': '19:10',
            'horses': pd.DataFrame({
                'horse_name': ['サンプルホースA', 'サンプルホースB', 'サンプルホースC'],
                'jockey_name': ['サンプル騎手A', 'サンプル騎手B', 'サンプル騎手C'],
                'trainer_name': ['サンプル調教師A', 'サンプル調教師B', 'サンプル調教師C'],
                'horse_weight': [480, 470, 490],
                'odds': [2.5, 4.0, 6.0],
                'popularity': [1, 2, 3],
                'course_length': [1200, 1200, 1200],
                'weather': ['晴', '晴', '晴'],
                'track_condition': ['良', '良', '良']
            })
        },
        {
            'race_id': f'OI{datetime.now().strftime("%Y%m%d")}02',
            'race_name': '第2レース',
            'race_time': '19:40',
            'horses': pd.DataFrame({
                'horse_name': ['サンプルホースD', 'サンプルホースE', 'サンプルホースF'],
                'jockey_name': ['サンプル騎手D', 'サンプル騎手E', 'サンプル騎手F'],
                'trainer_name': ['サンプル調教師D', 'サンプル調教師E', 'サンプル調教師F'],
                'horse_weight': [485, 475, 495],
                'odds': [3.0, 5.0, 8.0],
                'popularity': [1, 2, 3],
                'course_length': [1400, 1400, 1400],
                'weather': ['晴', '晴', '晴'],
                'track_condition': ['良', '良', '良']
            })
        }
    ]
    
    return sample_races

def predict_daily_races(predictor, races, betting_budget=10000, dry_run=True):
    """日次レースの予想を実行"""
    logger = setup_logger(__name__, 'daily_prediction.log')
    
    all_predictions = []
    all_recommendations = []
    
    strategy = BettingStrategy(initial_budget=betting_budget)
    
    for race in races:
        race_id = race['race_id']
        race_name = race['race_name']
        race_time = race['race_time']
        horses_data = race['horses']
        
        logger.info(f"予想開始: {race_name} ({race_time})")
        
        try:
            # 予想を実行
            predictions = predictor.predict_race(horses_data)
            
            if not predictions:
                logger.warning(f"予想結果がありません: {race_name}")
                continue
            
            # 投票推奨を取得
            race_budget = betting_budget // len(races)  # レース数で分割
            recommendations = strategy.calculate_bet_amount(predictions, budget_ratio=0.1)
            
            # 結果を保存
            race_result = {
                'race_id': race_id,
                'race_name': race_name,
                'race_time': race_time,
                'predictions': predictions,
                'recommendations': recommendations
            }
            
            all_predictions.append(race_result)
            
            # 結果を表示
            logger.info(f"予想結果: {race_name}")
            for pred in predictions:
                logger.info(f"  {pred['horse_name']}: {pred['predicted_position']}着予想 (信頼度: {pred['confidence']:.2%})")
            
            if recommendations:
                logger.info(f"投票推奨: {race_name}")
                for rec in recommendations:
                    logger.info(f"  {rec.horse_name}: {rec.bet_type} {rec.bet_amount:,}円 (リスク: {rec.risk_level})")
            else:
                logger.info(f"投票推奨なし: {race_name} (信頼度が低い)")
            
        except Exception as e:
            logger.error(f"予想エラー: {race_name} - {e}")
            continue
    
    return all_predictions

def save_predictions_to_file(predictions, filename=None):
    """予想結果をファイルに保存"""
    if not filename:
        filename = f"predictions_{datetime.now().strftime('%Y%m%d')}.json"
    
    predictions_dir = Path('predictions')
    predictions_dir.mkdir(exist_ok=True)
    
    filepath = predictions_dir / filename
    
    # JSONシリアライズ可能な形式に変換
    serializable_predictions = []
    
    for race_pred in predictions:
        serializable_race = {
            'race_id': race_pred['race_id'],
            'race_name': race_pred['race_name'],
            'race_time': race_pred['race_time'],
            'predictions': race_pred['predictions'],
            'recommendations': [
                {
                    'horse_name': rec.horse_name,
                    'bet_type': rec.bet_type,
                    'bet_amount': rec.bet_amount,
                    'confidence': rec.confidence,
                    'expected_return': rec.expected_return,
                    'risk_level': rec.risk_level
                } for rec in race_pred['recommendations']
            ]
        }
        serializable_predictions.append(serializable_race)
    
    import json
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(serializable_predictions, f, ensure_ascii=False, indent=2)
    
    return filepath

def generate_summary_report(predictions):
    """予想結果のサマリーレポートを作成"""
    total_races = len(predictions)
    total_predictions = sum(len(p['predictions']) for p in predictions)
    total_recommendations = sum(len(p['recommendations']) for p in predictions)
    
    high_confidence_count = 0
    total_recommended_amount = 0
    
    for race_pred in predictions:
        for pred in race_pred['predictions']:
            if pred['confidence'] >= MIN_CONFIDENCE:
                high_confidence_count += 1
        
        for rec in race_pred['recommendations']:
            total_recommended_amount += rec.bet_amount
    
    report = f"""
📈 日次予想サマリー - {datetime.now().strftime('%Y年%m月%d日')}
{'=' * 50}

🏇 レース数: {total_races}レース
🔮 予想数: {total_predictions}件
✨ 高信頼度予想: {high_confidence_count}件
💰 投票推奨: {total_recommendations}件
💵 推奨投票総額: {total_recommended_amount:,}円

🎯 レース別詳細:
"""
    
    for i, race_pred in enumerate(predictions, 1):
        report += f"\n{i}. {race_pred['race_name']} ({race_pred['race_time']})\n"
        
        if race_pred['predictions']:
            report += "   🔮 予想:\n"
            for pred in race_pred['predictions']:
                report += f"      {pred['horse_name']}: {pred['predicted_position']}着 (信頼度: {pred['confidence']:.1%})\n"
        
        if race_pred['recommendations']:
            report += "   💰 投票推奨:\n"
            for rec in race_pred['recommendations']:
                report += f"      {rec.horse_name}: {rec.bet_type} {rec.bet_amount:,}円\n"
        else:
            report += "   ⚠️  投票推奨なし\n"
    
    report += f"\n{'=' * 50}\n"
    report += f"ℹ️  この予想は教育・研究目的です。投資は自己責任で行ってください。\n"
    
    return report

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='日次予想実行')
    parser.add_argument(
        '--budget', '-b',
        type=int,
        default=10000,
        help='投票予算 (円)'
    )
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='ドライランモード（実際の投票は行わない）'
    )
    parser.add_argument(
        '--save-file', '-s',
        help='予想結果の保存ファイル名'
    )
    
    args = parser.parse_args()
    
    logger = setup_logger(__name__, 'daily_prediction.log')
    
    try:
        print("🏇 大井競馬予想AI - 日次予想")
        print("=" * 50)
        print(f"📅 日付: {datetime.now().strftime('%Y年%m月%d日')}")
        print(f"💰 予算: {args.budget:,}円")
        print(f"🎨 モード: {'DRY RUN' if args.dry_run else 'LIVE'}")
        print()
        
        # 予想システムを初期化
        logger.info("予想システムを初期化中...")
        predictor = OiKeibaPredictor()
        
        # 今日のレース情報を取得
        logger.info("今日のレース情報を取得中...")
        races = get_today_races()
        
        if not races:
            print("⚠️  今日のレース情報がありません")
            return 1
        
        print(f"🏇 今日のレース数: {len(races)}")
        print()
        
        # 予想を実行
        logger.info("予想を開始...")
        predictions = predict_daily_races(
            predictor=predictor,
            races=races,
            betting_budget=args.budget,
            dry_run=args.dry_run
        )
        
        if not predictions:
            print("⚠️  予想結果がありません")
            return 1
        
        # 結果をファイルに保存
        if args.save_file or args.dry_run:
            filepath = save_predictions_to_file(predictions, args.save_file)
            logger.info(f"予想結果を保存: {filepath}")
            print(f"💾 予想結果を保存しました: {filepath}")
        
        # サマリーレポートを表示
        report = generate_summary_report(predictions)
        print(report)
        
        logger.info("日次予想が完了しました")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  予想が中断されました")
        return 1
        
    except Exception as e:
        logger.error(f"日次予想エラー: {e}")
        print(f"🚨 エラーが発生しました: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
