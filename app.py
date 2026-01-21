import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import glob
import os
import pytz

# --- Project Zenith: JEPX統合分析 (Version 9.2) ---
# 【仕様】「本日」＝基準日（最新データ日）。翌日分があれば翌日を初期表示。

# 日本タイムゾーンの設定
JST = pytz.timezone('Asia/Tokyo')

# 1. ページ設定
st.set_page_config(page_title="Project Zenith - JEPX分析 Ver.9.2", layout="wide")

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

# CSS
st.markdown("""
    <style>
    .main-title { font-size: 24px !important; font-weight: bold; color: #1E1E1E; }
    .today-date-banner { font-size: 14px; color: #555; margin-bottom: 10px; border-left: 5px solid #3498DB; padding-left: 10px; background: #f9f9f9; padding: 5px 10px; }
    .section-header { margin-top: 25px; padding: 8px; background: #f0f2f6; border-radius: 5px; font-weight: bold; font-size: 15px; }
    </style>
    """, unsafe_allow_html=True)

try:
    df, status_msg = load_data()
    today_jst = datetime.now(JST)
    
    st.markdown('<div class="main-title">⚡️ Project Zenith: JEPX統合分析 (Ver.9.2)</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="today-date-banner">実行時刻 (JST): {today_jst.strftime("%Y/%m/%d %H:%M")}</div>', unsafe_allow_html=True)

    if df is not None:
        # --- 基準日（本日）の自動判定ロジック ---
        latest_date_in_csv = df['date'].dt.date.max() # CSV内の最新日（翌日分があれば翌日）
        
        # サイドバー設定
        st.sidebar.header("📊 表示設定")
        all_areas = sorted(df['エリア'].unique().tolist())
        selected_area = st.sidebar.selectbox("表示エリアを選択", ["全エリア"] + all_areas)
        
        # デフォルトで最新データがある日（＝本日/基準日）を選択
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
                legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5)
            )
            return fig

        # 1. 基準日（selected_date）の24時間グラフ表示
        st.markdown(f'<div class="section-header">📈 基準日: {selected_date} の価格推移</div>', unsafe_allow_html=True)
        day_df = df[df['date'].dt.date == selected_date].copy()
        
        if not day_df.empty:
            target_day_df = day_df if selected_area == "全エリア" else day_df[day_df['エリア'] == selected_area]
            fig_today = px.line(target_day_df, x='時刻', y='price', color='エリア', markers=True)
            st.plotly_chart(update_chart_layout(fig_today, f"{selected_date} の30分単位推移"), use_container_width=True)
        else:
            st.warning(f"{selected_date} のデータは存在しません。")

        # 2. 多角トレンド分析
        st.markdown('<div class="section-header">📅 期間トレンド・時間帯分析</div>', unsafe_allow_html=True)
        tabs = st.tabs(["7日間", "1ヶ月", "3ヶ月", "6ヶ月", "1年", "🕒 時間帯分析"])
        
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
                    st.plotly_chart(update_chart_layout(fig, f"{selected_date} を基準とした直近{days}日の平均推移"), use_container_width=True)

        # 3. 時間帯分析（ラベルに期間を明示）
        with tabs[5]:
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
                    st.plotly_chart(update_chart_layout(fig_t, f"時間帯別平均価格 (期間: {s_d} ～ {e_d})"), use_container_width=True)

except Exception as e:
    st.error(f"システムエラー: {e}")
