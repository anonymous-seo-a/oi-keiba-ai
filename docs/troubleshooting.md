# トラブルシューティングガイド

## 🔧 よくあるエラーと解決方法

### 1. スクレイピング関連

#### 問題: レースデータが0件
```
収集したレース数: 0
```
**原因**: 
- netkeibaのURL形式が変更された可能性
- コースコード（23）が正しくない可能性
- robots.txtやアクセス制限の可能性

**解決策**:
1. netkeibaの現在のURL形式を確認
2. 大井競馬場のコースコードを再確認
3. User-Agentとアクセス間隔の調整

#### 問題: コマンドライン引数が効かない
```bash
python scripts/run_data_collection.py --days 7  # 3年前から始まってしまう
```
**原因**: 引数パース部分の実装が不完全

**解決策**: argparseの実装を修正

### 2. モデル予測関連

#### 問題: 特徴量の数が一致しない
```
[LightGBM] [Fatal] The number of features in data (11) is not the same as it was in training data (13).
```
**原因**: 
- 訓練時と予測時で異なる特徴量作成ロジック
- 騎手・調教師の勝率が予測時に作成されていない

**解決策**:
1. 特徴量作成の順序を統一（カテゴリカルエンコード前に数値特徴量を作成）
2. is_trainingフラグで処理を適切に分岐
3. デフォルト値の設定を確実に行う

#### 問題: データ型の不一致
```
You are trying to merge on int64 and object columns for key 'jockey_name'
```
**原因**: 
- LabelEncoderがjockey_nameを数値に変換した後でmergeしようとしている
- エンコードのタイミングが不適切

**解決策**:
1. 特徴量作成（merge）を先に実行
2. その後でカテゴリカル変数をエンコード

### 3. 環境関連

#### 問題: モジュールが見つからない
```
ModuleNotFoundError: No module named 'src'
```
**解決策**:
```bash
# プロジェクトルートから実行
cd /path/to/oi-keiba-ai
python scripts/script_name.py
```

### 4. データベース関連

#### 問題: データベースが空
**解決策**:
```bash
# サンプルデータで初期化
python scripts/create_sample_data.py
```

## 📝 デバッグ手順

### 1. 特徴量の確認
```python
# モデルの特徴量を確認
python -c "
from src.models.lightgbm_model import LightGBMModel
model = LightGBMModel()
model.load_model()
print('特徴量:', model.feature_names)
print('特徴量数:', len(model.feature_names))
"
```

### 2. データベースの状態確認
```python
# データベースの中身を確認
python scripts/debug_database.py
```

### 3. スクレイピングテスト
```python
# 単一レースのスクレイピングテスト
python scripts/test_single_scrape.py
```

## 🚨 既知の問題（2025年6月27日時点）

1. **netkeibaスクレイピング**: レース情報が取得できない
2. **特徴量エンジニアリング**: 訓練時と予測時の不一致
3. **コマンドライン引数**: 一部のスクリプトで機能しない

これらの問題は次回の作業で修正予定です。