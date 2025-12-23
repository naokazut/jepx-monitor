import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

# 1. ページ設定
st.set_page_config(page_title="Project Zenith - JEPX分析ダッシュボード", layout="wide")

# 2. データの読み込みと加工
@st.cache_data
def load_data():
    # データパスは環境に合わせて調整してください
    df = pd.read_csv("data/spot_2025.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    def code_to_time(code):
        total_minutes = (int(code) - 1) * 30
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
    
    if '時刻' not in df.columns:
        df['時刻'] = df['time_code'].apply(code_to_time)
    
    # areaカラムの統一
    if 'area' in df.columns:
        df = df.rename(columns={'area': 'エリア'})
    
    return df

# カスタムCSS
st.markdown("""
    <style>
    .main-title { font-size: 26px !important; font-weight: bold; color: #1E1E1E; border-bottom: 3px solid #2ECC71; padding-bottom: 10px; }
    .stMetric { background-color: #f8f9fb; padding: 15px; border-radius: 10px; border: 1px solid #eef2f6; }
    </style>
    <div class="main-title">🏔️ Project Zenith: JEPXスポット価格 統合分析 (Ver.2)</div>
    """, unsafe_allow_html=True)

try:
    df = load_data()
    
    # --- 3. サイドバー設定 ---
    st.sidebar.header("📊 表示設定")
    all_areas = sorted(df['エリア'].unique().tolist())
    selected_area = st.sidebar.selectbox("表示エリアを選択", ["全エリア"] + all_areas, index=0)
    
    available_dates = df['date'].dt.date.unique()
    max_date = available_dates.max()
    selected_date = st.sidebar.date_input("基準日を選択", value=max_date)

    # --- 4. 統計メトリクスの表示 (Ver.2 詳細ラベル) ---
    day_df = df[df['date'].dt.date == selected_date].copy()

    if not day_df.empty:
        display_name = "全国" if selected_area == "全エリア" else selected_area
        target_df = day_df if selected_area == "全エリア" else day_df[day_df['エリア'] == selected_area]

        st.subheader(f"📊 {selected_date} の統計（{display_name}）")
        avg_p = target_df['price'].mean()
        max_row = target_df.loc[target_df['price'].idxmax()]
        min_row = target_df.loc[target_df['price'].idxmin()]

        col1, col2, col3 = st.columns(3)
        col1.metric("平均価格", f"{avg_p:.2f} 円")
        col2.metric("最高価格", f"{max_row['price']:.2f} 円", delta=f"{max_row['エリア']} / {max_row['時刻']}", delta_color="inverse")
        col3.metric("最低価格", f"{min_row['price']:.2f} 円", delta=f"{min_row['エリア']} / {min_row['時刻']}", delta_color="normal")

        # ① 当日の詳細推移
        fig_today = px.line(target_df, x='時刻', y='price', color='エリア' if selected_area == "全エリア" else None, 
                            title=f"{selected_date} 詳細推移")
        fig_today.update_layout(hovermode="x unified", xaxis=dict(tickmode='linear', dtick=4))
        st.plotly_chart(fig_today, use_container_width=True)

        # --- 5. 期間比較グラフ群 (Ver.1全機能の復活) ---
        st.markdown("---")
        st.subheader("📅 期間トレンド分析")

        def plot_trend(area, days, title):
            end_date = pd.to_datetime(selected_date)
            start_date = end_date - timedelta(days=days)
            mask = (df['date'] >= start_date) & (df['date'] <= end_date)
            trend_df = df[mask].copy()
            
            if area != "全エリア":
                trend_df = trend_df[trend_df['エリア'] == area]
            
            # 日次平均に集約
            daily_avg = trend_df.groupby(trend_df['date'].dt.date)['price'].mean().reset_index()
            fig = px.line(daily_avg, x='date', y='price', title=title, markers=True)
            fig.add_hline(y=daily_avg['price'].mean(), line_dash="dash", line_color="red", annotation_text="期間平均")
            st.plotly_chart(fig, use_container_width=True)

        # 4つのタブで各期間を表示
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["直近7日間", "直近1ヶ月", "直近3ヶ月", "直近6ヶ月", "直近1年"])
        
        with tab1: plot_trend(selected_area, 7, "過去7日間の平均価格推移")
        with tab2: plot_trend(selected_area, 30, "過去1ヶ月の平均価格推移")
        with tab3: plot_trend(selected_area, 90, "過去3ヶ月の平均価格推移")
        with tab4: plot_trend(selected_area, 180, "過去6ヶ月の平均価格推移")
        with tab5: plot_trend(selected_area, 365, "過去1年の平均価格推移")

    else:
        st.warning(f"{selected_date} のデータが見つかりません。")

except Exception as e:
    st.error(f"⚠️ システムエラーが発生しました: {e}")
