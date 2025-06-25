"""
LightGBMを使用した競馬予想モデル
"""
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import joblib
from pathlib import Path

from config.settings import MODEL_DIR, LIGHTGBM_PARAMS
from src.data_collection.database import OiKeibaDatabase
from src.utils.logger import setup_logger

class LightGBMModel:
    def __init__(self, model_name='oi_keiba_lightgbm'):
        self.model_name = model_name
        self.model = None
        self.label_encoders = {}
        self.feature_names = []
        self.db = OiKeibaDatabase()
        self.logger = setup_logger(__name__)
        
        # モデルディレクトリを作成
        MODEL_DIR.mkdir(exist_ok=True)
    
    def prepare_features(self, df):
        """特徴量を作成"""
        features_df = df.copy()
        
        # 基本特徴量
        feature_columns = [
            'course_length', 'horse_weight', 'odds', 'popularity'
        ]
        
        # カテゴリカル変数のエンコード
        categorical_columns = ['weather', 'track_condition', 'jockey_name', 'trainer_name']
        
        for col in categorical_columns:
            if col in features_df.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    features_df[col] = self.label_encoders[col].fit_transform(features_df[col].fillna('unknown'))
                else:
                    # 既存のエンコーダーを使用
                    try:
                        features_df[col] = self.label_encoders[col].transform(features_df[col].fillna('unknown'))
                    except ValueError:
                        # 未知のラベルは0で置換
                        features_df[col] = 0
                
                feature_columns.append(col)
        
        # 馬の過去成績特徴量
        horse_stats = self.create_horse_features(features_df)
        if horse_stats is not None:
            features_df = features_df.merge(horse_stats, on='horse_name', how='left')
            feature_columns.extend(['avg_position', 'win_rate', 'place_rate'])
        
        # 騎手・調教師特徴量
        jockey_stats = self.create_jockey_trainer_features(features_df)
        if jockey_stats is not None:
            features_df = features_df.merge(jockey_stats, on=['jockey_name', 'trainer_name'], how='left')
            feature_columns.extend(['jockey_win_rate', 'trainer_win_rate'])
        
        # 欠損値を埋める
        features_df[feature_columns] = features_df[feature_columns].fillna(0)
        
        self.feature_names = feature_columns
        return features_df[feature_columns]
    
    def create_horse_features(self, df):
        """馬の過去成績特徴量を作成"""
        try:
            # 馬ごとの統計を計算
            horse_stats = df.groupby('horse_name').agg({
                'finish_position': ['mean', 'count'],
            }).round(2)
            
            horse_stats.columns = ['avg_position', 'total_races']
            horse_stats = horse_stats.reset_index()
            
            # 勝率、連対率を計算
            wins = df[df['finish_position'] == 1].groupby('horse_name').size()
            places = df[df['finish_position'] <= 3].groupby('horse_name').size()
            
            horse_stats = horse_stats.merge(wins.to_frame('wins'), left_on='horse_name', right_index=True, how='left')
            horse_stats = horse_stats.merge(places.to_frame('places'), left_on='horse_name', right_index=True, how='left')
            
            horse_stats['wins'] = horse_stats['wins'].fillna(0)
            horse_stats['places'] = horse_stats['places'].fillna(0)
            
            horse_stats['win_rate'] = (horse_stats['wins'] / horse_stats['total_races']).fillna(0)
            horse_stats['place_rate'] = (horse_stats['places'] / horse_stats['total_races']).fillna(0)
            
            return horse_stats[['horse_name', 'avg_position', 'win_rate', 'place_rate']]
        
        except Exception as e:
            self.logger.error(f"馬特徴量作成エラー: {e}")
            return None
    
    def create_jockey_trainer_features(self, df):
        """騎手・調教師の特徴量を作成"""
        try:
            # 騎手統計
            jockey_stats = df.groupby('jockey_name').agg({
                'finish_position': 'count'
            })
            jockey_wins = df[df['finish_position'] == 1].groupby('jockey_name').size()
            jockey_stats = jockey_stats.merge(jockey_wins.to_frame('wins'), left_index=True, right_index=True, how='left')
            jockey_stats['wins'] = jockey_stats['wins'].fillna(0)
            jockey_stats['jockey_win_rate'] = (jockey_stats['wins'] / jockey_stats['finish_position']).fillna(0)
            
            # 調教師統計
            trainer_stats = df.groupby('trainer_name').agg({
                'finish_position': 'count'
            })
            trainer_wins = df[df['finish_position'] == 1].groupby('trainer_name').size()
            trainer_stats = trainer_stats.merge(trainer_wins.to_frame('wins'), left_index=True, right_index=True, how='left')
            trainer_stats['wins'] = trainer_stats['wins'].fillna(0)
            trainer_stats['trainer_win_rate'] = (trainer_stats['wins'] / trainer_stats['finish_position']).fillna(0)
            
            # 結合
            result = df[['jockey_name', 'trainer_name']].drop_duplicates()
            result = result.merge(jockey_stats[['jockey_win_rate']], left_on='jockey_name', right_index=True, how='left')
            result = result.merge(trainer_stats[['trainer_win_rate']], left_on='trainer_name', right_index=True, how='left')
            
            return result
        
        except Exception as e:
            self.logger.error(f"騎手・調教師特徴量作成エラー: {e}")
            return None
    
    def train(self, test_size=0.2, random_state=42):
        """モデルを訓練"""
        self.logger.info("モデル訓練を開始します")
        
        # データを取得
        df = self.db.get_race_data()
        if df.empty:
            self.logger.error("訓練データがありません")
            return
        
        self.logger.info(f"誓練データ数: {len(df)}")
        
        # 特徴量を作成
        X = self.prepare_features(df)
        y = df['finish_position'] - 1  # 0ベースに変換
        
        # 訓練・テストデータに分割
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        # LightGBMデータセットを作成
        train_data = lgb.Dataset(X_train, label=y_train)
        valid_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
        
        # モデル訓練
        self.model = lgb.train(
            LIGHTGBM_PARAMS,
            train_data,
            valid_sets=[valid_data],
            num_boost_round=1000,
            callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)]
        )
        
        # モデル評価
        y_pred = self.model.predict(X_test)
        y_pred_class = np.argmax(y_pred, axis=1)
        
        accuracy = accuracy_score(y_test, y_pred_class)
        self.logger.info(f"モデル精度: {accuracy:.4f}")
        
        # モデルを保存
        self.save_model()
        
        return accuracy
    
    def predict(self, race_data):
        """予想を実行"""
        if self.model is None:
            self.load_model()
        
        if self.model is None:
            self.logger.error("モデルが読み込まれていません")
            return None
        
        # 特徴量を作成
        X = self.prepare_features(race_data)
        
        # 予想実行
        predictions = self.model.predict(X)
        
        # 結果を整形
        results = []
        for i, pred in enumerate(predictions):
            results.append({
                'horse_name': race_data.iloc[i]['horse_name'],
                'predicted_position': np.argmax(pred) + 1,
                'confidence': np.max(pred),
                'probabilities': pred.tolist()
            })
        
        return results
    
    def save_model(self):
        """モデルを保存"""
        model_path = MODEL_DIR / f"{self.model_name}.txt"
        encoders_path = MODEL_DIR / f"{self.model_name}_encoders.pkl"
        features_path = MODEL_DIR / f"{self.model_name}_features.pkl"
        
        # LightGBMモデルを保存
        self.model.save_model(str(model_path))
        
        # エンコーダーを保存
        joblib.dump(self.label_encoders, encoders_path)
        
        # 特徴量名を保存
        joblib.dump(self.feature_names, features_path)
        
        self.logger.info(f"モデルを保存しました: {model_path}")
    
    def load_model(self):
        """モデルを読み込み"""
        model_path = MODEL_DIR / f"{self.model_name}.txt"
        encoders_path = MODEL_DIR / f"{self.model_name}_encoders.pkl"
        features_path = MODEL_DIR / f"{self.model_name}_features.pkl"
        
        try:
            # LightGBMモデルを読み込み
            self.model = lgb.Booster(model_file=str(model_path))
            
            # エンコーダーを読み込み
            self.label_encoders = joblib.load(encoders_path)
            
            # 特徴量名を読み込み
            self.feature_names = joblib.load(features_path)
            
            self.logger.info(f"モデルを読み込みました: {model_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"モデル読み込みエラー: {e}")
            return False
    
    def get_feature_importance(self):
        """特徴量重要度を取得"""
        if self.model is None:
            return None
        
        importance = self.model.feature_importance(importance_type='gain')
        
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        return feature_importance
