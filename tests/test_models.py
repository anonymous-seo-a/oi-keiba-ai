#!/usr/bin/env python3
"""
機械学習モデルのテスト
"""
import unittest
import tempfile
import os
from pathlib import Path
import sys
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.models.lightgbm_model import LightGBMModel

class TestLightGBMModel(unittest.TestCase):
    def setUp(self):
        """テストセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.model = LightGBMModel(model_name='test_model')
        
        # テスト用のサンプルデータを作成
        self.sample_data = pd.DataFrame({
            'race_id': ['R001', 'R001', 'R001', 'R002', 'R002', 'R002'] * 10,
            'race_date': ['2024-01-01'] * 60,
            'horse_name': ['馬A', '馬B', '馬C'] * 20,
            'jockey_name': ['騎手1', '騎手2', '騎手3'] * 20,
            'trainer_name': ['調教師1', '調教師2', '調教師3'] * 20,
            'course_length': [1200] * 60,
            'horse_weight': np.random.randint(450, 520, 60),
            'odds': np.random.uniform(1.5, 10.0, 60),
            'popularity': np.random.randint(1, 16, 60),
            'weather': ['晴'] * 60,
            'track_condition': ['良'] * 60,
            'finish_position': np.random.randint(1, 17, 60)
        })
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        # 一時ファイルを削除
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_prepare_features(self):
        """特徴量作成のテスト"""
        features = self.model.prepare_features(self.sample_data)
        
        # 特徴量が正しく作成されているか確認
        self.assertIsInstance(features, pd.DataFrame)
        self.assertGreater(len(features.columns), 0)
        
        # 基本的な特徴量が含まれているか確認
        expected_features = ['course_length', 'horse_weight', 'odds', 'popularity']
        for feature in expected_features:
            self.assertIn(feature, features.columns)
        
        # 欠損値がないか確認
        self.assertEqual(features.isnull().sum().sum(), 0)
    
    def test_create_horse_features(self):
        """馬の特徴量作成のテスト"""
        horse_features = self.model.create_horse_features(self.sample_data)
        
        if horse_features is not None:
            # 必要な列が含まれているか確認
            required_columns = ['horse_name', 'avg_position', 'win_rate', 'place_rate']
            for col in required_columns:
                self.assertIn(col, horse_features.columns)
            
            # 勝率と連対率が0-1の範囲内か確認
            self.assertTrue((horse_features['win_rate'] >= 0).all())
            self.assertTrue((horse_features['win_rate'] <= 1).all())
            self.assertTrue((horse_features['place_rate'] >= 0).all())
            self.assertTrue((horse_features['place_rate'] <= 1).all())
    
    def test_create_jockey_trainer_features(self):
        """騎手・調教師特徴量作成のテスト"""
        jt_features = self.model.create_jockey_trainer_features(self.sample_data)
        
        if jt_features is not None:
            # 必要な列が含まれているか確認
            required_columns = ['jockey_name', 'trainer_name', 'jockey_win_rate', 'trainer_win_rate']
            for col in required_columns:
                self.assertIn(col, jt_features.columns)
            
            # 勝率が0-1の範囲内か確認
            self.assertTrue((jt_features['jockey_win_rate'] >= 0).all())
            self.assertTrue((jt_features['jockey_win_rate'] <= 1).all())
            self.assertTrue((jt_features['trainer_win_rate'] >= 0).all())
            self.assertTrue((jt_features['trainer_win_rate'] <= 1).all())
    
    @patch('src.models.lightgbm_model.LightGBMModel.save_model')
    def test_train_with_mock_data(self, mock_save):
        """モックデータでの訓練テスト"""
        # モックデータベースを作成
        mock_db = Mock()
        mock_db.get_race_data.return_value = self.sample_data
        
        # モデルのデータベースをモックに置き換え
        self.model.db = mock_db
        
        # 訓練を実行
        try:
            accuracy = self.model.train(test_size=0.3, random_state=42)
            
            # 精度が数値で返されるか確認
            self.assertIsInstance(accuracy, float)
            self.assertGreaterEqual(accuracy, 0.0)
            self.assertLessEqual(accuracy, 1.0)
            
            # save_modelが呼ばれたか確認
            mock_save.assert_called_once()
            
        except Exception as e:
            # データが小さい場合のエラーは許容
            if "stratify" in str(e):
                self.skipTest("データサイズが小さいためスキップ")
            else:
                raise
    
    def test_predict_with_mock_model(self):
        """モックモデルでの予想テスト"""
        # モックLightGBMモデルを作成
        mock_lgb_model = Mock()
        mock_lgb_model.predict.return_value = np.array([
            [0.1, 0.8, 0.05, 0.05],  # 馬A: 2着予想
            [0.6, 0.2, 0.1, 0.1],    # 馬B: 1着予想 
            [0.05, 0.1, 0.7, 0.15]   # 馬C: 3着予想
        ])
        
        self.model.model = mock_lgb_model
        self.model.feature_names = ['course_length', 'horse_weight', 'odds', 'popularity']
        
        # テストデータ
        test_data = pd.DataFrame({
            'horse_name': ['馬A', '馬B', '馬C'],
            'course_length': [1200, 1200, 1200],
            'horse_weight': [480, 470, 490],
            'odds': [3.0, 2.5, 5.0],
            'popularity': [2, 1, 3],
            'jockey_name': ['騎手1', '騎手2', '騎手3'],
            'trainer_name': ['調教師1', '調教師2', '調教師3'],
            'weather': ['晴', '晴', '晴'],
            'track_condition': ['良', '良', '良']
        })
        
        # 予想を実行
        predictions = self.model.predict(test_data)
        
        # 検証
        self.assertEqual(len(predictions), 3)
        
        for pred in predictions:
            self.assertIn('horse_name', pred)
            self.assertIn('predicted_position', pred)
            self.assertIn('confidence', pred)
            self.assertIn('probabilities', pred)
            
            # 予想着順が1-16の範囲内か確認
            self.assertGreaterEqual(pred['predicted_position'], 1)
            self.assertLessEqual(pred['predicted_position'], 16)
            
            # 信頼度が0-1の範囲内か確認
            self.assertGreaterEqual(pred['confidence'], 0.0)
            self.assertLessEqual(pred['confidence'], 1.0)
    
    def test_label_encoder_consistency(self):
        """ラベルエンコーダーの一貫性テスト"""
        # 初回の特徴量作成
        features1 = self.model.prepare_features(self.sample_data)
        
        # 新しいデータで特徴量作成
        new_data = self.sample_data.copy()
        new_data.loc[0, 'jockey_name'] = '新しい騎手'  # 未知のラベルを追加
        
        features2 = self.model.prepare_features(new_data)
        
        # 特徴量の列数が同じか確認
        self.assertEqual(len(features1.columns), len(features2.columns))
        
        # 列名が同じか確認
        self.assertListEqual(list(features1.columns), list(features2.columns))

if __name__ == '__main__':
    unittest.main()
