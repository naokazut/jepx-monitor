import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import glob
import os
import pytz

# --- Project Zenith: JEPX統合分析 (Version 9.2 統合修正版) ---
# 【修正】先祖帰りを解消：統計メトリック、季節比較タブを完全復活。

# 日本タイムゾーンの設定
JST = pytz.timezone('Asia/Tokyo')

# 1. ページ設定
st.set_page_config(page_title="Project Zenith - JEPX分析", layout="wide")

# 2. データの読み込み
@st.cache_data(ttl=3600)
def load_data():
    file_list = glob.glob("data/spot_*.csv")
    if not file_list:
        return None, "dataフォルダ内にファイルが見つかりません。"
    latest_file = max(file_list, key=os.path.getmtime)
    try:
        df = pd.read_csv(latest_file)
        df['date'] = pd.to_datetime(df['date'])
        def code_to_time(code):
            total_minutes = (int(code) - 1) * 30
            return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
        if '時刻' not in df.columns:
            df['時刻'] = df['time_code'].apply(code_to_time)
        df['datetime'] = pd.to_datetime(df['date'].dt.strftime('%Y-%m-%d') + ' ' + df['時刻'])
        if 'area' in df.columns:
            df = df.rename(columns={'area': 'エリア'})
        return df, f"読み込み完了: {os.path.basename(latest_file)}"
    except Exception as e:
        return None, f"エラー: {e}"

# CSSデザイン (Version 7 のスタイルを継承)
st.markdown("""
    <style>
    .main-title { font-size: 24px !important; font-weight: bold; color: #1E1E1E; margin-bottom: 0px; }
    .today-date-banner { font-size: 16px; color: #555; margin-bottom: 20px; border-left: 5px solid #3498DB; padding-left: 10px; background: #f9f9f9; padding: 5px 10px; }
    .stMetric { background-color: #f8f9fb; padding: 10px; border-radius: 10px; border: 1px solid #eef2f6; }
    .section-header { margin-top: 25px; padding: 8px; background: #f0f2f6; border-radius: 5px; font-weight: bold; font-size: 15px; }
    </style>
    """, unsafe_allow_html=True)

try:
    df, status_msg = load_data()
    today_jst = datetime.now(JST)
    
    st.markdown('<div class="main-title">⚡️ Project Zenith: JEPX統合分析 (Ver.9.2-Revised)</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="today-date-banner">現在時刻 (JST): {today_jst.strftime("%Y/%m/%d %H:%M")}</div>', unsafe_allow_html=True)

    if df is not None:
        # 基準日（本日）の判定
        latest_date_in_csv = df['date'].dt.date.max()
        
        # サイドバー設定
        st.sidebar.header("📊 表示設定")
        if st.sidebar.button("🔄 データを再読み込み"):
            st.cache_data.clear()
            st.rerun()

        all_areas = sorted(df['エリア'].unique().tolist())
        selected_area = st.sidebar.selectbox("表示エリアを選択", ["全エリア"] + all_areas, index=0)
        selected_date = st.sidebar.date_input("分析基準日を選択", value=latest_date_in_csv)

        st.sidebar.markdown("---")
        st.sidebar.subheader("📅 任意期間の指定")
        date_range = st.sidebar.date_input(
            "時間帯分析の対象期間",
            value=(selected_date - timedelta(days=7), selected_date),
            min_value=df['date'].min().date(),
            max_value=latest_date_in_csv
        )

        # グラフ共通レイアウト
        def update_chart_layout(fig, title_text):
            fig.update_layout(
                title=dict(text=title_text, font=dict(size=16)),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, font=dict(size=10)),
                margin=dict(l=10, r=10, t=50, b=80)
            )
            return fig

        # 4. 統計指標表示 (Version 7 の機能を完全復活)
        day_df = df[df['date'].dt.date == selected_date].copy()
        if not day_df.empty:
            target_df = day_df if selected_area == "全エリア" else day_df[day_df['エリア'] == selected_area]
            display_name = "全国" if selected_area == "全エリア" else selected_area
            
            st.subheader(f"📊 {selected_date} の統計（{display_name}）")
            col1, col2, col3 = st.columns(3)
            col1.metric("平均価格", f"{target_df['price'].mean():.2f} 円")
            
            max_row = target_df.loc[target_df['price'].idxmax()]
            min_row = target_df.loc[target_df['price'].idxmin()]
            
            col2.metric("最高価格", f"{max_row['price']:.1f} 円", f"{max_row['エリア']} {max_row['時刻']}", delta_color="inverse")
            col3.metric("最低価格", f"{min_row['price']:.1f} 円", f"{min_row['エリア']} {min_row['時刻']}")

            # 5. 当日の詳細推移グラフ (Version 9仕様)
            st.markdown(f'<div class="section-header">📈 {selected_date} の30分単位推移</div>', unsafe_allow_html=True)
            fig_today = px.line(target_df, x='時刻', y='price', color='エリア' if selected_area == "全エリア" else None, markers=True)
            st.plotly_chart(update_chart_layout(fig_today, ""), use_container_width=True)

            # 6. 定型トレンド分析 (タブ形式 - 季節比較と時間帯分析を統合)
            st.markdown('<div class="section-header">📅 期間トレンド・多角分析</div>', unsafe_allow_html=True)
            tabs = st.tabs(["7日間", "1ヶ月", "3ヶ月", "6ヶ月", "1年", "☀️ 季節比較", "🕒 時間帯分析"])
            
            periods = [7, 30, 90, 180, 365] 
            for i in range(5): 
                with tabs[i]:
                    days = periods[i]
                    s_date = pd.to_datetime(selected_date) - timedelta(days=days)
                    t_mask = (df['date'] >= s_date) & (df['date'] <= pd.to_datetime(selected_date))
                    if selected_area != "全エリア": t_mask &= (df['エリア'] == selected_area)
                    t_df = df[t_mask].copy()
                    if not t_df.empty:
                        d_avg = t_df.groupby(['date', 'エリア'])['price'].mean().reset_index()
                        fig = px.line(d_avg, x='date', y='price', color='エリア')
                        st.plotly_chart(update_chart_layout(fig, f"直近{days}日の日別平均"), use_container_width=True)

            # 7. 季節比較タブ (復活)
            with tabs[5]:
                st.subheader("☀️❄️ エリア別・季節平均価格比較")
                df['month'] = df['date'].dt.month
                summer = df[df['month'].isin([7, 8, 9])]
                winter = df[df['month'].isin([12, 1, 2])]
                if not summer.empty and not winter.empty:
                    s_avg = summer.groupby('エリア')['price'].mean().reset_index()
                    w_avg = winter.groupby('エリア')['price'].mean().reset_index()
                    fig_s = go.Figure(data=[
                        go.Bar(name='夏(7-9月)', x=s_avg['エリア'], y=s_avg['price'], marker_color='#FF4B4B'),
                        go.Bar(name='冬(12-2月)', x=w_avg['エリア'], y=w_avg['price'], marker_color='#0068C9')
                    ])
                    st.plotly_chart(update_chart_layout(fig_s, "季節平均のエリア別比較"), use_container_width=True)

            # 8. 時間帯分析タブ (修正点を維持)
            with tabs[6]:
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    s_d, e_d = date_range
                    mask = (df['date'].dt.date >= s_d) & (df['date'].dt.date <= e_d)
                    if selected_area != "全エリア": mask &= (df['エリア'] == selected_area)
                    c_df = df[mask].copy()
                    if not c_df.empty:
                        c_df['hour'] = c_df['datetime'].dt.hour
                        c_df['segment'] = c_df['hour'].apply(lambda h: '昼間(8-16)' if 8<=h<16 else ('夜間(16-24)' if 16<=h<24 else '夜中(0-8)'))
                        t_res = c_df.groupby(['segment', 'エリア'])['price'].mean().reset_index()
                        fig_t = px.bar(t_res, x='エリア', y='price', color='segment', barmode='group')
                        st.plotly_chart(update_chart_layout(fig_t, f"時間帯別平均 (期間: {s_d} ～ {e_d})"), use_container_width=True)
        else:
            st.warning(f"選択された日付 {selected_date} のデータが見つかりません。")

except Exception as e:
    st.error(f"システムエラー: {e}")
