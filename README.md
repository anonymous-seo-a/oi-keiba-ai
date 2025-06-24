# 🏇 大井競馬予想AI（OI-Keiba-AI）

LightGBMを中心とした機械学習アルゴリズムで大井競馬場の予想を行い、収益を目指すAIシステムです。

## 🚀 プロジェクト概要

このプロジェクトは、以下の技術を組み合わせて大井競馬の予想精度を向上させ、持続的な収益を目指します：

- **LightGBM**: メインの予測モデル
- **スクレイピング**: レース情報の自動収集
- **JRA-VANデータ**: 転入馬の詳細情報
- **アンサンブル学習**: 複数モデルの組み合わせ
- **リスク管理**: 投資戦略の最適化

## 📊 主な機能

- 🔍 **自動データ収集**: 過去3年以上のレースデータを自動取得
- 🧠 **AI予想システム**: LightGBM + アンサンブルモデル
- 💰 **投資戦略**: リスクを考慮した投票戦略
- 📈 **収益管理**: 成績・収益の分析・可視化
- 🌐 **Webダッシュボード**: 予想結果の表示・管理

## 🛠️ 技術スタック

### フロントエンド
- **Streamlit**: Webアプリケーション
- **Plotly**: データ可視化

### バックエンド  
- **Python 3.9+**: メイン開発言語
- **LightGBM**: 機械学習モデル
- **pandas**: データ処理
- **SQLite**: データベース
- **BeautifulSoup**: Webスクレイピング

### インフラ
- **GitHub**: バージョン管理・プロジェクト管理
- **GitHub Actions**: CI/CD

## 📁 プロジェクト構成

```
oi-keiba-ai/
├── src/                     # ソースコード
│   ├── data_collection/     # データ収集
│   ├── feature_engineering/ # 特徴量エンジニアリング  
│   ├── models/              # 機械学習モデル
│   ├── prediction/          # 予想システム
│   └── utils/               # ユーティリティ
├── notebooks/               # Jupyter Notebooks
├── data/                    # データファイル
├── docs/                    # ドキュメント
├── tests/                   # テストコード
└── web_app/                 # Webアプリケーション
```

## 🚀 クイックスタート

### 1. リポジトリのクローン
```bash
git clone https://github.com/anonymous-seo-a/oi-keiba-ai.git
cd oi-keiba-ai
```

### 2. 仮想環境の作成
```bash
python -m venv oi_keiba_env
source oi_keiba_env/bin/activate  # Windows: oi_keiba_env\Scripts\activate
```

### 3. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 4. データ収集の実行
```bash
python scripts/run_data_collection.py
```

### 5. モデルの訓練
```bash
python scripts/train_model.py
```

### 6. Webアプリの起動
```bash
streamlit run web_app/app.py
```

## 📖 ドキュメント

- [📋 セットアップガイド](docs/setup.md)
- [🔧 API仕様](docs/api.md)
- [👤 ユーザーガイド](docs/user_guide.md)
- [🧪 開発者ガイド](docs/developer_guide.md)

## 🎯 開発ロードマップ

### Phase 1: 基盤構築 (進行中)
- [x] プロジェクト初期設定
- [ ] データ収集システム開発
- [ ] データベース構築
- [ ] 基本的な特徴量作成

### Phase 2: モデル開発 (予定)
- [ ] ベースラインモデル構築
- [ ] LightGBMモデル最適化
- [ ] アンサンブルモデル開発
- [ ] モデル評価システム

### Phase 3: 予想システム開発 (予定)
- [ ] 予想ロジック実装
- [ ] 投票戦略アルゴリズム
- [ ] リスク管理機能
- [ ] 自動実行システム

### Phase 4: Webアプリ開発 (予定)
- [ ] ダッシュボード作成
- [ ] 予想結果表示
- [ ] 成績管理機能
- [ ] 投票管理機能

## 📈 現在の成績

| 期間 | レース数 | 的中率 | 回収率 | 収益 |
|------|----------|--------|--------|------|
| 2024年1月 | - | - | - | - |
| 2024年2月 | - | - | - | - |
| **合計** | **-** | **-%** | **-%** | **¥-** |

*まだ運用開始前のため、データなし*

## 🤝 貢献方法

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'feat: Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## ⚠️ 注意事項

### 法的事項
- 競馬の投票は自己責任で行ってください
- このシステムは教育・研究目的で開発されています
- 投資にはリスクが伴います

### 技術的事項
- スクレイピングは各サイトの利用規約を遵守してください
- 商用利用時は有料データサービスの利用を検討してください
- APIレート制限を守ってアクセスしてください

## 📧 連絡先

- **開発者**: anonymous-seo-a
- **GitHub**: [@anonymous-seo-a](https://github.com/anonymous-seo-a)

## 📄 ライセンス

このプロジェクトは [MIT License](LICENSE) の下で公開されています。

## 🙏 謝辞

- [netkeiba.com](https://netkeiba.com/) - レースデータ提供
- [JRA-VAN](https://jra-van.jp/) - 競馬データサービス
- [LightGBM](https://lightgbm.readthedocs.io/) - 機械学習フレームワーク

---

⭐ このプロジェクトが役に立ったら、スターをつけてください！