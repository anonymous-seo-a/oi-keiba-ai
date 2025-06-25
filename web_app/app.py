"""
Streamlitを使用したWebアプリケーション
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.data_collection.database import OiKeibaDatabase
from src.models.lightgbm_model import LightGBMModel
from src.prediction.predictor import OiKeibaPredictor
from src.prediction.betting_strategy import BettingStrategy

# ページ設定
st.set_page_config(
    page_title="大井競馬予想AI",
    page_icon="🏇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# サイドバー
st.sidebar.title("🏇 大井競馬予想AI")
st.sidebar.markdown("---")

# メニュー選択
page = st.sidebar.selectbox(
    "ページを選択",
    ["ダッシュボード", "データ分析", "予想実行", "投票戦略", "成績管理", "モデル管理"]
)

# データベース接続
@st.cache_resource
def get_database():
    return OiKeibaDatabase()

@st.cache_resource
def get_predictor():
    return OiKeibaPredictor()

db = get_database()
predictor = get_predictor()

# メインコンテンツ
if page == "ダッシュボード":
    st.title("📊 ダッシュボード")
    
    # 基本統計
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_races = len(db.get_race_data())
        st.metric("総レース数", total_races)
    
    with col2:
        recent_data = db.get_race_data(limit=100)
        if not recent_data.empty:
            unique_horses = recent_data['horse_name'].nunique()
            st.metric("登録馬数", unique_horses)
        else:
            st.metric("登録馬数", 0)
    
    with col3:
        if not recent_data.empty:
            unique_jockeys = recent_data['jockey_name'].nunique()
            st.metric("騎手数", unique_jockeys)
        else:
            st.metric("騎手数", 0)
    
    with col4:
        # 最新データの日付
        if not recent_data.empty:
            latest_date = recent_data['race_date'].max()
            st.metric("最新データ", latest_date)
        else:
            st.metric("最新データ", "なし")
    
    st.markdown("---")
    
    # 最近のレース結果
    st.subheader("📈 最近のレース結果")
    if not recent_data.empty:
        display_data = recent_data[[
            'race_date', 'race_name', 'horse_name', 'finish_position', 
            'jockey_name', 'odds', 'popularity'
        ]].head(20)
        st.dataframe(display_data, use_container_width=True)
    else:
        st.info("データがありません。データ収集を実行してください。")

elif page == "データ分析":
    st.title("📊 データ分析")
    
    data = db.get_race_data()
    
    if data.empty:
        st.warning("分析するデータがありません。")
    else:
        # 期間選択
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("開始日", value=datetime.now() - timedelta(days=365))
        with col2:
            end_date = st.date_input("終了日", value=datetime.now())
        
        # フィルタリング
        filtered_data = data[
            (pd.to_datetime(data['race_date']) >= pd.to_datetime(start_date)) &
            (pd.to_datetime(data['race_date']) <= pd.to_datetime(end_date))
        ]
        
        st.markdown(f"**分析期間**: {start_date} ～ {end_date}")
        st.markdown(f"**対象レース数**: {filtered_data['race_id'].nunique()}件")
        
        # 着順分布
        st.subheader("着順分布")
        position_counts = filtered_data['finish_position'].value_counts().sort_index()
        fig = px.bar(x=position_counts.index, y=position_counts.values, 
                    labels={'x': '着順', 'y': '回数'})
        st.plotly_chart(fig, use_container_width=True)
        
        # 人気と着順の関係
        st.subheader("人気と着順の関係")
        popularity_analysis = filtered_data.groupby('popularity')['finish_position'].mean().reset_index()
        fig = px.line(popularity_analysis, x='popularity', y='finish_position',
                     labels={'popularity': '人気', 'finish_position': '平均着順'})
        st.plotly_chart(fig, use_container_width=True)
        
        # 騎手別成績
        st.subheader("騎手別成績 (上位10名)")
        jockey_stats = filtered_data.groupby('jockey_name').agg({
            'finish_position': ['count', 'mean'],
            'horse_name': lambda x: (filtered_data.loc[x.index, 'finish_position'] == 1).sum()
        }).round(2)
        
        jockey_stats.columns = ['出走数', '平均着順', '勝利数']
        jockey_stats['勝率'] = (jockey_stats['勝利数'] / jockey_stats['出走数'] * 100).round(1)
        jockey_stats = jockey_stats.sort_values('勝率', ascending=False).head(10)
        
        st.dataframe(jockey_stats, use_container_width=True)

elif page == "予想実行":
    st.title("🎯 予想実行")
    
    st.info("この機能は今後のレース予想に使用します。現在は過去データでの検証のみ対応しています。")
    
    # 予想精度の検証
    st.subheader("予想精度の検証")
    
    col1, col2 = st.columns(2)
    with col1:
        test_start = st.date_input("検証開始日", value=datetime.now() - timedelta(days=30))
    with col2:
        test_end = st.date_input("検証終了日", value=datetime.now())
    
    if st.button("精度検証を実行"):
        with st.spinner("検証中..."):
            accuracy_result = predictor.analyze_prediction_accuracy(
                test_start.strftime('%Y-%m-%d'),
                test_end.strftime('%Y-%m-%d')
            )
            
            if 'error' in accuracy_result:
                st.error(accuracy_result['error'])
            else:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("検証レース数", accuracy_result['total_races'])
                
                with col2:
                    win_accuracy = accuracy_result['win_accuracy'] * 100
                    st.metric("単勝的中率", f"{win_accuracy:.1f}%")
                
                with col3:
                    place_accuracy = accuracy_result['place_accuracy'] * 100
                    st.metric("複勝的中率", f"{place_accuracy:.1f}%")
                
                st.json(accuracy_result)

elif page == "投票戦略":
    st.title("💰 投票戦略")
    
    # 投票戦略の設定
    st.subheader("戦略設定")
    
    col1, col2 = st.columns(2)
    with col1:
        initial_budget = st.number_input("初期予算 (円)", min_value=1000, value=100000, step=1000)
    with col2:
        risk_level = st.selectbox("リスクレベル", ["保守的", "標準", "積極的"])
    
    # 投票戦略インスタンスを作成
    betting_strategy = BettingStrategy(initial_budget=initial_budget)
    
    st.subheader("戦略シミュレーション")
    st.info("実際の投票機能は開発中です。現在はシミュレーション結果を表示しています。")
    
    # サンプルデータでのシミュレーション
    sample_predictions = [
        {'horse_name': 'サンプル馬A', 'predicted_position': 1, 'confidence': 0.75},
        {'horse_name': 'サンプル馬B', 'predicted_position': 2, 'confidence': 0.65},
        {'horse_name': 'サンプル馬C', 'predicted_position': 3, 'confidence': 0.55},
    ]
    
    recommendations = betting_strategy.calculate_bet_amount(sample_predictions)
    
    if recommendations:
        st.subheader("投票推奨")
        rec_data = []
        for rec in recommendations:
            rec_data.append({
                '馬名': rec.horse_name,
                '投票タイプ': rec.bet_type,
                '投票額': f"{rec.bet_amount:,}円",
                '信頼度': f"{rec.confidence:.1%}",
                '期待収益': f"{rec.expected_return:,.0f}円",
                'リスクレベル': rec.risk_level
            })
        
        st.dataframe(pd.DataFrame(rec_data), use_container_width=True)
    
    # 成績サマリー（サンプル）
    st.subheader("成績サマリー（サンプル）")
    sample_summary = {
        'total_bets': 50,
        'hit_rate': 0.32,
        'recovery_rate': 0.85,
        'total_profit_loss': -15000
    }
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("投票回数", sample_summary['total_bets'])
    with col2:
        st.metric("的中率", f"{sample_summary['hit_rate']:.1%}")
    with col3:
        st.metric("回収率", f"{sample_summary['recovery_rate']:.1%}")
    with col4:
        st.metric("収支", f"{sample_summary['total_profit_loss']:+,}円")

elif page == "成績管理":
    st.title("📈 成績管理")
    
    st.info("投票履歴と成績の管理機能です。実際の投票実装後に利用可能になります。")
    
    # プレースホルダーのグラフ
    st.subheader("収支推移（サンプル）")
    
    # サンプルデータでグラフを作成
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='W')
    cumulative_profit = np.cumsum(np.random.normal(0, 5000, len(dates)))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=cumulative_profit, mode='lines', name='累積収支'))
    fig.update_layout(title='収支推移（サンプル）', xaxis_title='日付', yaxis_title='収支 (円)')
    st.plotly_chart(fig, use_container_width=True)
    
    # 月別成績
    st.subheader("月別成績（サンプル）")
    monthly_data = pd.DataFrame({
        '月': ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05'],
        '投票回数': [12, 15, 18, 20, 16],
        '的中回数': [4, 6, 7, 8, 5],
        '収支': [-5000, 12000, -8000, 15000, -3000]
    })
    
    monthly_data['的中率'] = (monthly_data['的中回数'] / monthly_data['投票回数'] * 100).round(1)
    st.dataframe(monthly_data, use_container_width=True)

elif page == "モデル管理":
    st.title("🤖 モデル管理")
    
    # モデル情報
    st.subheader("現在のモデル情報")
    
    model = LightGBMModel()
    if model.load_model():
        st.success("✅ モデルが正常に読み込まれています")
        
        # 特徴量重要度
        importance = model.get_feature_importance()
        if importance is not None:
            st.subheader("特徴量重要度")
            
            fig = px.bar(importance.head(10), 
                        x='importance', y='feature', 
                        orientation='h',
                        labels={'importance': '重要度', 'feature': '特徴量'})
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("全特徴量重要度"):
                st.dataframe(importance, use_container_width=True)
    else:
        st.warning("⚠️ モデルが読み込まれていません")
        
        if st.button("モデルを訓練"):
            with st.spinner("モデル訓練中..."):
                try:
                    accuracy = model.train()
                    if accuracy:
                        st.success(f"✅ モデル訓練完了 - 精度: {accuracy:.4f}")
                        st.rerun()
                    else:
                        st.error("❌ モデル訓練に失敗しました")
                except Exception as e:
                    st.error(f"❌ エラー: {e}")
    
    # データ収集
    st.subheader("データ収集")
    
    col1, col2 = st.columns(2)
    with col1:
        months_back = st.number_input("取得期間 (月)", min_value=1, max_value=60, value=12)
    
    with col2:
        if st.button("データ収集を実行"):
            st.info("データ収集を開始します。これには時間がかかる場合があります。")
            # 実際の実装では、バックグラウンドでスクレイピングを実行
            st.warning("この機能は実装中です。コマンドラインから実行してください。")

# フッター
st.sidebar.markdown("---")
st.sidebar.markdown("""
### 📖 使い方
1. **データ収集**: まずデータを収集
2. **モデル訓練**: AIモデルを訓練
3. **予想実行**: レース予想を実行
4. **投票戦略**: 戦略に基づいて投票
5. **成績管理**: 結果を分析・改善

### ⚠️ 注意事項
- 競馬投票は自己責任で行ってください
- このシステムは教育・研究目的です
- 投資には必ずリスクが伴います
""")
