import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta

# 1. ページ基本設定
st.set_page_config(page_title="Project Zenith - JEPX分析", layout="wide")

# 2. データの読み込みと確実な前処理
@st.cache_data
def load_data():
    # パスは実行環境に合わせてください
    df = pd.read_csv("data/spot_2025.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    # 時刻コードをhh:mm形式に変換
    def code_to_time(code):
        total_minutes = (int(code) - 1) * 30
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
    
    if '時刻' not in df.columns:
        df['時刻'] = df['time_code'].apply(code_to_time)
    
    # カラム名の統一
    if 'area' in df.columns:
        df = df.rename(columns={'area': 'エリア'})
    
    return df

# タイトルデザイン
st.markdown("""
    <style>
    .main-title { font-size: 26px !important; font-weight: bold; color: #1E1E1E; border-bottom: 3px solid #3498DB; padding-bottom: 10px; }
    .stMetric { background-color: #f8f9fb; padding: 15px; border-radius: 10px; border: 1px solid #eef2f6; }
    </style>
    <div class="main-title">🏔️ Project Zenith: JEPXスポット価格 統合分析 (Ver.2)</div>
    """, unsafe_allow_html=True)

try:
    df = load_data()
    
    # --- 3. サイドバー操作パネル ---
    st.sidebar.header("📊 表示設定")
    all_areas = sorted(df['エリア'].unique().tolist())
    selected_area = st.sidebar.selectbox("表示エリアを選択", ["全エリア"] + all_areas, index=0)
    
    max_date = df['date'].dt.date.max()
    selected_date = st.sidebar.date_input("基準日を選択", value=max_date)

    # --- 4. 統計メトリクス (最高・最低価格のラベル詳細化) ---
    day_df = df[df['date'].dt.date == selected_date].copy()

    if not day_df.empty:
        # 全国または個別エリアのフィルタリング
        target_df = day_df if selected_area == "全エリア" else day_df[day_df['エリア'] == selected_area]
        display_name = "全国" if selected_area == "全エリア" else selected_area

        st.subheader(f"📊 {selected_date} の統計（{display_name}）")
        
        avg_p = target_df['price'].mean()
        max_row = target_df.loc[target_df['price'].idxmax()]
        min_row = target_df.loc[target_df['price'].idxmin()]

        col1, col2, col3 = st.columns(3)
        col1.metric("平均価格", f"{avg_p:.2f} 円")
        
        # エリアと時刻を明記したラベル [cite: 2025-12-22]
        col2.metric("最高価格", f"{max_row['price']:.2f} 円", 
                    delta=f"{max_row['エリア']} / {max_row['時刻']}", delta_color="inverse")
        col3.metric("最低価格", f"{min_row['price']:.2f} 円", 
                    delta=f"{min_row['エリア']} / {min_row['時刻']}", delta_color="normal")

        # --- 5. 詳細推移グラフ (全エリア描画バグの完全修正) ---
        st.markdown(f"### {selected_date} 詳細推移")
        
        # 描画の安定性を高めるため、エリアと時刻で厳密にソート [cite: 2025-12-21]
        plot_df = target_df.sort_values(['エリア', '時刻'])
        
        # 全エリア時はcolor引数をエリアに、個別時は単色（None）に指定
        fig_today = px.line(
            plot_df, 
            x='時刻', 
            y='price', 
            color='エリア' if selected_area == "全エリア" else None,
            line_group='エリア' if selected_area == "全エリア" else None, # ラインの途切れを防止
            category_orders={"時刻": sorted(plot_df['時刻'].unique())},
            labels={'price': '価格 (円/kWh)', '時刻': '時刻'},
            template="plotly_white"
        )
        
        fig_today.update_layout(
            hovermode="x unified",
            xaxis=dict(tickmode='linear', dtick=4, gridcolor='#f0f0f0'),
            yaxis=dict(gridcolor='#f0f0f0'),
            legend_title_text='エリア'
        )
        st.plotly_chart(fig_today, use_container_width=True)

        # --- 6. 期間トレンド分析 (Ver.1全機能：直近7日間〜1年をタブで統合) ---
        st.markdown("---")
        st.subheader("📅 期間トレンド分析")

        def plot_period_trend(area_filter, num_days, tab_title):
            end_d = pd.to_datetime(selected_date)
            start_d = end_d - timedelta(days=num_days)
            mask = (df['date'] >= start_d) & (df['date'] <= end_d)
            t_df = df[mask].copy()
            
            if area_filter != "全エリア":
                t_df = t_df[t_df['エリア'] == area_filter]
            
            # 日ごとの平均価格を算出してトレンド化 [cite: 2025-12-21]
            daily_avg = t_df.groupby(t_df['date'].dt.date)['price'].mean().reset_index()
            
            fig = px.line(daily_avg, x='date', y='price', title=tab_title, markers=True, template="plotly_white")
            period_mean = daily_avg['price'].mean()
            fig.add_hline(y=period_mean, line_dash="dash", line_color="#E74C3C", 
                          annotation_text=f" 期間平均: {period_mean:.2f}円 ", annotation_position="top right")
            st.plotly_chart(fig, use_container_width=True)

        # 全ての期間比較機能をタブで実装 [cite: 2025-12-21, 2025-12-22]
        tabs = st.tabs(["直近7日間", "直近1ヶ月", "直近3ヶ月", "直近6ヶ月", "直近1年"])
        with tabs[0]: plot_period_trend(selected_area, 7, "過去7日間の平均価格推移")
        with tabs[1]: plot_period_trend(selected_area, 30, "過去1ヶ月の平均価格推移")
        with tabs[2]: plot_period_trend(selected_area, 90, "過去3ヶ月の平均価格推移")
        with tabs[3]: plot_period_trend(selected_area, 180, "過去6ヶ月の平均価格推移")
        with tabs[4]: plot_period_trend(selected_area, 365, "過去1年の平均価格推移")

    else:
        st.warning(f"{selected_date} のデータが見つかりません。")

except Exception as e:
    st.error(f"⚠️ エラーが発生しました。データ形式またはパスを確認してください: {e}")
