# トラブルシューティングガイド

## 環境構築関連

### Python 3.13でpandasインストールエラー
```
error: metadata-generation-failed
```

**解決方法**: requirements.txtを更新して、バージョン指定を柔軟にする
```txt
pandas>=2.2.0  # == ではなく >= を使用
numpy>=1.26.0
```

### LightGBMでlibompエラー（Mac）
```
OSError: dlopen(.../lib_lightgbm.dylib, 0x0006): Library not loaded: @rpath/libomp.dylib
```

**解決方法**: Homebrewでlibompをインストール
```bash
brew install libomp
```

## データ収集関連

### コマンドライン引数が機能しない
`--start-date`と`--end-date`オプションが無視される問題。

**原因**: `run_data_collection.py`がargparseを実装していない

**一時的な回避策**: 新しいスクリプトを作成
```python
# scripts/collect_recent_data.py
# 日付を直接指定してデータ収集
```

### レースが見つからない（0件）
`get_race_list`メソッドが空のリストを返す問題。

**考えられる原因**:
1. netkeibaのURL構造が変更された
2. 大井競馬場のコースコードが間違っている
3. HTML構造が変更された

**調査方法**:
```bash
python scripts/test_netkeiba_url.py
```

## よくある質問

### Q: Macでcontrol+Cが効かない
A: Macでは`control`キー（左下）を使います。`command`キーではありません。

### Q: ターミナルを閉じてしまった
A: 新しいターミナルを開いて、以下を実行：
```bash
cd ~/Desktop/oi-keiba-ai
source venv/bin/activate
```

### Q: データがまだ0件
A: サンプルデータで動作確認：
```bash
python scripts/create_sample_data.py
```
