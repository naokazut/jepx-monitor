import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta

# 1. ページ設定
st.set_page_config(page_title="Project Zenith - JEPX分析", layout="wide")

# 2. データの読み込み
@st.cache_data
def load_data():
    # 実際のCSVパスに合わせて調整してください
    df = pd.read_csv("data/spot_2025.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    def code_to_time(code):
        total_minutes = (int(code) - 1) * 30
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
    
    if '時刻' not in df.columns:
        df['時刻'] = df['time_code'].apply(code_to_time)
    
    if 'area' in df.columns:
        df = df.rename(columns={'area': 'エリア'})
    
    return df

# ヘッダーデザイン
st.markdown("""
    <style>
    .main-title { font-size: 26px !important; font-weight: bold; color: #1E1E1E; border-bottom: 3px solid #3498DB; padding-bottom: 10px; }
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
    
    max_date = df['date'].dt.date.max()
    selected_date = st.sidebar.date_input("基準日を選択", value=max_date)

    # --- 4. 統計メトリクス (最高・最低価格ラベルの実装) ---
    day_df = df[df['date'].dt.date == selected_date].copy()

    if not day_df.empty:
        # メトリクス算出用のデータ
        target_df = day_df if selected_area == "全エリア" else day_df[day_df['エリア'] == selected_area]
        display_name = "全国" if selected_area == "全エリア" else selected_area

        st.subheader(f"📊 {selected_date} の統計（{display_name}）")
        
        avg_p = target_df['price'].mean()
        max_row = target_df.loc[target_df['price'].idxmax()]
        min_row = target_df.loc[target_df['price'].idxmin()]

        col1, col2, col3 = st.columns(3)
        col1.metric("平均価格", f"{avg_p:.2f} 円")
        # エリア/時刻ラベルの追加 [cite: 2025-12-22]
        col2.metric("最高価格", f"{max_row['price']:.2f} 円", delta=f"{max_row['エリア']} / {max_row['時刻']}", delta_color="inverse")
        col3.metric("最低価格", f"{min_row['price']:.2f} 円", delta=f"{min_row['エリア']} / {min_row['時刻']}", delta_color="normal")

        # --- 5. 詳細推移グラフ (全エリア描画の完全修正) ---
        # 描画前に必ずソートを行い、Plotlyのライン接続を保証する
        plot_df = target_df.sort_values(['エリア', '時刻'])
        
        fig_today = px.line(
            plot_df, 
            x='時刻', 
            y='price', 
            color='エリア' if selected_area == "全エリア" else None,
            title=f"{selected_date} 詳細推移 ({display_name})",
            markers=(selected_area != "全エリア") # 個別エリアの時のみマーカー表示
        )
        fig_today.update_layout(hovermode="x unified", xaxis=dict(tickmode='linear', dtick=4))
        st.plotly_chart(fig_today, use_container_width=True)

        # --- 6. 期間トレンド分析 (Ver.1全機能の維持・全エリア対応) ---
        st.markdown("---")
        st.subheader("📅 期間トレンド分析")

        def plot_period_trend(area_filter, num_days, tab_title):
            end_d = pd.to_datetime(selected_date)
            start_d = end_d - timedelta(days=num_days)
            mask = (df['date'] >= start_d) & (df['date'] <= end_d)
            t_df = df[mask].copy()
            
            if area_filter != "全エリア":
                t_df = t_df[t_df['エリア'] == area_filter]
            
            # 日次・エリアごとの平均を計算してから、全国平均を算出
            # これにより「全エリア」選択時も正しい1本のトレンドラインを描画
            daily_avg = t_df.groupby(t_df['date'].dt.date)['price'].mean().reset_index()
            
            fig = px.line(daily_avg, x='date', y='price', title=tab_title, markers=True)
            period_mean = daily_avg['price'].mean()
            fig.add_hline(y=period_mean, line_dash="dash", line_color="red", annotation_text=f"期間平均: {period_mean:.2f}円")
            st.plotly_chart(fig, use_container_width=True)

        # 全ての期間タブを確実に実装 [cite: 2025-12-21]
        tabs = st.tabs(["直近7日間", "直近1ヶ月", "直近3ヶ月", "直近6ヶ月", "直近1年"])
        with tabs[0]: plot_period_trend(selected_area, 7, "過去7日間の平均価格推移")
        with tabs[1]: plot_period_trend(selected_area, 30, "過去1ヶ月の平均価格推移")
        with tabs[2]: plot_period_trend(selected_area, 90, "過去3ヶ月の平均価格推移")
        with tabs[3]: plot_period_trend(selected_area, 180, "過去6ヶ月の平均価格推移")
        with tabs[4]: plot_period_trend(selected_area, 365, "過去1年の平均価格推移")

    else:
        st.warning(f"{selected_date} のデータが見つかりません。")

except Exception as e:
    st.error(f"⚠️ エラー: {e}")
