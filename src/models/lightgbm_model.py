"""
LightGBMを使用した競馬予想モデル（修正版v2）
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
    
    def prepare_features(self, df, is_training=True):
        """特徴量を作成"""
        features_df = df.copy()
        
        # 基本特徴量
        feature_columns = [
            'course_length', 'horse_weight', 'odds', 'popularity'
        ]
        
        # 馬の過去成績特徴量を先に作成（エンコード前）
        if is_training:
            horse_stats = self.create_horse_features_training(features_df)
        else:
            horse_stats = self.create_horse_features_prediction(features_df)
            
        if horse_stats is not None:
            features_df = features_df.merge(horse_stats, on='horse_name', how='left')
            feature_columns.extend(['avg_position', 'win_rate', 'place_rate'])
        
        # 騎手・調教師特徴量を先に作成（エンコード前）
        if is_training:
            jockey_stats = self.create_jockey_trainer_features_training(features_df)
        else:
            jockey_stats = self.create_jockey_trainer_features_prediction(features_df)
            
        if jockey_stats is not None:
            features_df = features_df.merge(jockey_stats, on=['jockey_name', 'trainer_name'], how='left')
            feature_columns.extend(['jockey_win_rate', 'trainer_win_rate'])
        
        # カテゴリカル変数のエンコード（特徴量作成後）
        categorical_columns = ['weather', 'track_condition', 'jockey_name', 'trainer_name']
        
        for col in categorical_columns:
            if col in features_df.columns:
                if is_training:
                    # 訓練時：新しいエンコーダーを作成
                    if col not in self.label_encoders:
                        self.label_encoders[col] = LabelEncoder()
                    features_df[col] = self.label_encoders[col].fit_transform(features_df[col].fillna('unknown'))
                else:
                    # 予測時：既存のエンコーダーを使用
                    if col in self.label_encoders:
                        try:
                            # fillnaで欠損値を埋めてからtransform
                            features_df[col] = features_df[col].fillna('unknown')
                            features_df[col] = self.label_encoders[col].transform(features_df[col])
                        except ValueError as e:
                            # 未知のラベルがある場合
                            self.logger.warning(f"未知のラベルを検出: {col}")
                            # 各値を個別に処理
                            encoded_values = []
                            for value in features_df[col]:
                                if value in self.label_encoders[col].classes_:
                                    encoded_values.append(self.label_encoders[col].transform([value])[0])
                                else:
                                    encoded_values.append(0)  # 未知の値は0
                            features_df[col] = encoded_values
                    else:
                        # エンコーダーがない場合は0で初期化
                        features_df[col] = 0
                
                feature_columns.append(col)
        
        # 欠損値を埋める
        features_df[feature_columns] = features_df[feature_columns].fillna(0)
        
        self.feature_names = feature_columns
        return features_df[feature_columns]
    
    def create_horse_features_training(self, df):
        """訓練時の馬の過去成績特徴量を作成"""
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
    
    def create_horse_features_prediction(self, df):
        """予測時の馬の過去成績特徴量を作成"""
        try:
            # データベースから過去のレース結果を取得
            past_races = self.db.get_race_data()
            
            # デフォルト値のDataFrameを作成
            unique_horses = df['horse_name'].unique()
            default_stats = pd.DataFrame({
                'horse_name': unique_horses,
                'avg_position': 0.0,
                'win_rate': 0.0,
                'place_rate': 0.0
            })
            
            if past_races.empty:
                return default_stats
            
            # 馬ごとの統計を計算
            horse_stats = past_races.groupby('horse_name').agg({
                'finish_position': ['mean', 'count'],
            }).round(2)
            
            horse_stats.columns = ['avg_position', 'total_races']
            horse_stats = horse_stats.reset_index()
            
            # 勝率、連対率を計算
            wins = past_races[past_races['finish_position'] == 1].groupby('horse_name').size()
            places = past_races[past_races['finish_position'] <= 3].groupby('horse_name').size()
            
            horse_stats = horse_stats.merge(wins.to_frame('wins'), left_on='horse_name', right_index=True, how='left')
            horse_stats = horse_stats.merge(places.to_frame('places'), left_on='horse_name', right_index=True, how='left')
            
            horse_stats['wins'] = horse_stats['wins'].fillna(0)
            horse_stats['places'] = horse_stats['places'].fillna(0)
            
            horse_stats['win_rate'] = (horse_stats['wins'] / horse_stats['total_races']).fillna(0)
            horse_stats['place_rate'] = (horse_stats['places'] / horse_stats['total_races']).fillna(0)
            
            # 現在のレースの馬の情報とマージ（過去データがない馬も含む）
            result = default_stats.merge(
                horse_stats[['horse_name', 'avg_position', 'win_rate', 'place_rate']], 
                on='horse_name', 
                how='left',
                suffixes=('', '_past')
            )
            
            # 過去データがある場合は使用、ない場合はデフォルト値
            for col in ['avg_position', 'win_rate', 'place_rate']:
                past_col = f'{col}_past'
                if past_col in result.columns:
                    result[col] = result[past_col].fillna(result[col])
                    result = result.drop(columns=[past_col])
            
            return result
        
        except Exception as e:
            self.logger.error(f"予測時の馬特徴量作成エラー: {e}")
            # エラー時はデフォルト値を返す
            return pd.DataFrame({
                'horse_name': df['horse_name'].unique(),
                'avg_position': 0.0,
                'win_rate': 0.0,
                'place_rate': 0.0
            })
    
    def create_jockey_trainer_features_training(self, df):
        """訓練時の騎手・調教師の特徴量を作成"""
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
    
    def create_jockey_trainer_features_prediction(self, df):
        """予測時の騎手・調教師の特徴量を作成"""
        try:
            # データベースから過去のレース結果を取得
            past_races = self.db.get_race_data()
            
            # デフォルト値のDataFrameを作成
            result = df[['jockey_name', 'trainer_name']].drop_duplicates()
            result['jockey_win_rate'] = 0.0
            result['trainer_win_rate'] = 0.0
            
            if past_races.empty:
                return result
            
            # 騎手統計
            jockey_stats = past_races.groupby('jockey_name').agg({
                'finish_position': 'count'
            })
            jockey_wins = past_races[past_races['finish_position'] == 1].groupby('jockey_name').size()
            jockey_stats = jockey_stats.merge(jockey_wins.to_frame('wins'), left_index=True, right_index=True, how='left')
            jockey_stats['wins'] = jockey_stats['wins'].fillna(0)
            jockey_stats['jockey_win_rate'] = (jockey_stats['wins'] / jockey_stats['finish_position']).fillna(0)
            jockey_stats = jockey_stats.reset_index()
            
            # 調教師統計
            trainer_stats = past_races.groupby('trainer_name').agg({
                'finish_position': 'count'
            })
            trainer_wins = past_races[past_races['finish_position'] == 1].groupby('trainer_name').size()
            trainer_stats = trainer_stats.merge(trainer_wins.to_frame('wins'), left_index=True, right_index=True, how='left')
            trainer_stats['wins'] = trainer_stats['wins'].fillna(0)
            trainer_stats['trainer_win_rate'] = (trainer_stats['wins'] / trainer_stats['finish_position']).fillna(0)
            trainer_stats = trainer_stats.reset_index()
            
            # 結合（過去データがない騎手・調教師も含む）
            result = result.merge(
                jockey_stats[['jockey_name', 'jockey_win_rate']], 
                on='jockey_name', 
                how='left',
                suffixes=('', '_past')
            )
            result = result.merge(
                trainer_stats[['trainer_name', 'trainer_win_rate']], 
                on='trainer_name', 
                how='left',
                suffixes=('', '_past')
            )
            
            # 過去データがある場合は使用、ない場合はデフォルト値
            if 'jockey_win_rate_past' in result.columns:
                result['jockey_win_rate'] = result['jockey_win_rate_past'].fillna(result['jockey_win_rate'])
                result = result.drop(columns=['jockey_win_rate_past'])
                
            if 'trainer_win_rate_past' in result.columns:
                result['trainer_win_rate'] = result['trainer_win_rate_past'].fillna(result['trainer_win_rate'])
                result = result.drop(columns=['trainer_win_rate_past'])
            
            return result
        
        except Exception as e:
            self.logger.error(f"予測時の騎手・調教師特徴量作成エラー: {e}")
            # エラー時はデフォルト値を返す
            result = df[['jockey_name', 'trainer_name']].drop_duplicates()
            result['jockey_win_rate'] = 0.0
            result['trainer_win_rate'] = 0.0
            return result
    
    def train(self, test_size=0.2, random_state=42):
        """モデルを訓練"""
        self.logger.info("モデル訓練を開始します")
        
        # データを取得
        df = self.db.get_race_data()
        if df.empty:
            self.logger.error("訓練データがありません")
            return
        
        self.logger.info(f"訓練データ数: {len(df)}")
        
        # 特徴量を作成（訓練モード）
        X = self.prepare_features(df, is_training=True)
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
        
        # 特徴量を作成（予測モード）
        X = self.prepare_features(race_data, is_training=False)
        
        # 特徴量の数を確認
        if len(X.columns) != len(self.feature_names):
            self.logger.error(f"特徴量の数が一致しません: 期待={len(self.feature_names)}, 実際={len(X.columns)}")
            self.logger.error(f"期待される特徴量: {self.feature_names}")
            self.logger.error(f"実際の特徴量: {list(X.columns)}")
            return None
        
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