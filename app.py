import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta

# 1. ページ設定
st.set_page_config(page_title="JEPXスポット価格 統合分析ダッシュボード", layout="wide")

# 2. データの読み込みと加工（キャッシュ機能）
@st.cache_data
def load_data():
    df = pd.read_csv("data/spot_2025.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    # 時刻変換（time_code -> 00:00形式）
    def code_to_time(code):
        total_minutes = (int(code) - 1) * 30
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
    
    if '時刻' not in df.columns:
        df['時刻'] = df['time_code'].apply(code_to_time)
    
    # 【重要】連続時系列グラフ用の日時列を作成
    df['datetime'] = pd.to_datetime(df['date'].dt.strftime('%Y-%m-%d') + ' ' + df['時刻'])
    
    if 'area' in df.columns:
        df = df.rename(columns={'area': 'エリア'})
    
    return df

# カスタムデザイン
st.markdown("""
    <style>
    .main-title { font-size: 26px !important; font-weight: bold; color: #1E1E1E; border-bottom: 3px solid #FF4B4B; padding-bottom: 10px; }
    .stMetric { background-color: #f8f9fb; padding: 15px; border-radius: 10px; border: 1px solid #eef2f6; }
    .section-header { margin-top: 30px; padding: 8px; background: #f0f2f6; border-radius: 5px; font-weight: bold; }
    </style>
    <div class="main-title">⚡️ JEPXスポット価格 統合分析ダッシュボード</div>
    """, unsafe_allow_html=True)

try:
    df = load_data()
    
    # 3. UI設定
    all_areas = sorted(df['エリア'].unique().tolist())
    selection_options = ["全エリア"] + all_areas
    selected_area = st.sidebar.selectbox("表示エリアを選択", selection_options, index=0)
    available_dates = df['date'].dt.date.unique()
    selected_date = st.sidebar.date_input("基準日を選択", value=available_dates.max())

    day_df = df[df['date'].dt.date == selected_date].copy()

    if not day_df.empty:
        # 指標計算用のデータ抽出
        display_name = "全国" if selected_area == "全エリア" else selected_area
        target_df = day_df if selected_area == "全エリア" else day_df[day_df['エリア'] == selected_area]

        # 統計指標の表示
        avg_p = target_df['price'].mean()
        max_row = target_df.loc[target_df['price'].idxmax()]
        min_row = target_df.loc[target_df['price'].idxmin()]

        st.subheader(f"📊 {selected_date} の統計（{display_name}）")
        col1, col2, col3 = st.columns(3)
        col1.metric("平均価格", f"{avg_p:.2f} 円")
        col2.metric("最高価格", f"{max_row['price']:.2f} 円", help=f"発生時刻: {max_row['時刻']}")
        col3.metric("最低価格", f"{min_row['price']:.2f} 円", help=f"発生時刻: {min_row['時刻']}")

        # --- ① 基準日の詳細（尺度：時刻） ---
        if selected_area == "全エリア":
            fig_day = px.line(day_df, x='時刻', y='price', color='エリア', title=f"{selected_date} 全エリア詳細推移")
        else:
            fig_day = px.line(target_df, x='時刻', y='price', title=f"{selected_date} {selected_area}詳細推移")
            fig_day.update_traces(line_color='#FF4B4B', line_width=3)
        fig_day.update_layout(hovermode="x unified", xaxis=dict(tickmode='linear', dtick=4))
        st.plotly_chart(fig_day, use_container_width=True)

        st.markdown('<div class="section-header">📅 期間別トレンド分析</div>', unsafe_allow_html=True)

        # --- ② 直近7日間の推移（尺度：連続した日付・時間） ---
        st.write("### ① 直近7日間の推移（時系列連続）")
        start_date_7d = pd.to_datetime(selected_date) - timedelta(days=7)
        
        if selected_area == "全エリア":
            mask_7d = (df['date'] >= start_date_7d) & (df['date'] <= pd.to_datetime(selected_date))
            # 全エリアの場合は全国平均の連続時系列を作成
            trend_7d = df[mask_7d].groupby('datetime')['price'].mean().reset_index()
        else:
            mask_7d = (df['date'] >= start_date_7d) & (df['date'] <= pd.to_datetime(selected_date)) & (df['エリア'] == selected_area)
            trend_7d = df[mask_7d].copy()

        if not trend_7d.empty:
            # 横軸に datetime を使用することで、7日間が一本の線でつながります
            fig_7d = px.line(trend_7d, x='datetime', y='price', 
                             title=f"{display_name}：直近7日間の価格変動",
                             labels={'datetime': '日時', 'price': '価格 (円)'})
            fig_7d.update_traces(line_color='#00CC96')
            fig_7d.update_layout(hovermode="x unified")
            st.plotly_chart(fig_7d, use_container_width=True)

        # --- ③ 長期トレンド（尺度：日付単位の集計） ---
        def plot_long_term(days, title):
            start_date = pd.to_datetime(selected_date) - timedelta(days=days)
            if selected_area == "全エリア":
                term_df
