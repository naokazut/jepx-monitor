import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. ページ設定
st.set_page_config(page_title="Project Zenith - JEPX分析", layout="wide")

# 2. データの読み込み (キャッシュ有効期限1時間)
@st.cache_data(ttl=3600)
def load_data():
    # データ読み込み
    df = pd.read_csv("data/spot_2025.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    # 時刻コードをHH:mm形式に変換
    def code_to_time(code):
        total_minutes = (int(code) - 1) * 30
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
    
    if '時刻' not in df.columns:
        df['時刻'] = df['time_code'].apply(code_to_time)
    
    # 日時を結合したdatetime列を作成
    df['datetime'] = pd.to_datetime(df['date'].dt.strftime('%Y-%m-%d') + ' ' + df['時刻'])
    
    # エリア表記の統一
    if 'area' in df.columns:
        df = df.rename(columns={'area': 'エリア'})
    return df

# CSSデザイン (スマホ視認性向上)
st.markdown("""
    <style>
    .main-title { font-size: 24px !important; font-weight: bold; color: #1E1E1E; margin-bottom: 0px; }
    .today-date-banner { font-size: 16px; color: #555; margin-bottom: 20px; border-left: 5px solid #3498DB; padding-left: 10px; background: #f9f9f9; padding-top: 5px; padding-bottom: 5px; }
    .stMetric { background-color: #f8f9fb; padding: 10px; border-radius: 10px; border: 1px solid #eef2f6; }
    .section-header { margin-top: 25px; padding: 8px; background: #f0f2f6; border-radius: 5px; font-weight: bold; font-size: 15px; }
    /* タブのフォントサイズ調整 */
    .stTabs [data-baseweb="tab"] { font-size: 14px; padding-left: 10px; padding-right: 10px; }
    </style>
    """, unsafe_allow_html=True)

try:
    # データのロード
    df = load_data()
    
    # --- ヘッダー表示 ---
    today_str = datetime.now().strftime('%Y/%m/%d')
    st.markdown('<div class="main-title">⚡️ Project Zenith: JEPX統合分析 (Ver.7)</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="today-date-banner">本日の日付: {today_str}</div>', unsafe_allow_html=True)

    # --- 3. サイドバーUI ---
    st.sidebar.header("📊 表示設定")
    
    # キャッシュクリアボタン
    if st.sidebar.button("🔄 データを再読み込み"):
        st.cache_data.clear()
        st.rerun()
        
    all_areas = sorted(df['エリア'].unique().tolist())
    selected_area = st.sidebar.selectbox("表示エリアを選択", ["全エリア"] + all_areas, index=0)
    
    # 【デフォルト設定】CSV内の最新日付を自動選択
    latest_date_in_csv = df['date'].dt.date.max()
    selected_date = st.sidebar.date_input("分析基準日を選択", value=latest_date_in_csv)

    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 任意期間の指定")
    date_range = st.sidebar.date_input(
        "期間を選択",
        value=(latest_date_in_csv - timedelta(days=7), latest_date_in_csv),
        min_value=df['date'].min().date(),
        max_value=latest_date_in_csv
    )

    # グラフ共通レイアウト設定 (スマホ重なり・見切れ対策済み)
    def update_chart_layout(fig, title_text):
        fig.update_layout(
            title=dict(text=title_text, font=dict(size=16)),
            hovermode="x unified",
            dragmode=False,
            # 凡例をグラフ下部に2列配置
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.25,
                xanchor="center",
                x=0.5,
                font=dict(size=10),
                itemwidth=30
            ),
            margin=dict(l=10, r=10, t=50, b=80),
            hoverlabel=dict(
                bgcolor="rgba(255, 255, 255, 0.9)",
                font_size=11,
                namelength=-1
            )
        )
        # ホバー時のテキストを短縮
        fig.update_traces(hovertemplate="%{fullData.name}: %{y:.1f}円<extra></extra>")
        return fig

    # 4. 統計指標表示
    day_df = df[df['date'].dt.date == selected_date].copy()
    if not day_df.empty:
        target_df = day_df if selected_area == "全エリア" else day_df[day_df['エリア'] == selected_area]
        display_area_name = "全国" if selected_area == "全エリア" else selected_area
        
        st.subheader(f"📊 {selected_date} の統計（{display_area_name}）")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("平均価格", f"{target_df['price'].mean():.2f} 円")
        
        max_row = target_df.loc[target_df['price'].idxmax()]
        min_row = target_df.loc[target_df['price'].idxmin()]
        
        col2.metric("最高価格", f"{max_row['price']:.1f} 円", f"{max_row['エリア']} {max_row['時刻']}", delta_color="inverse")
        col3.metric("最低価格", f"{min_row['price']:.1f} 円", f"{min_row['エリア']} {min_row['時刻']}")

        # 5. 当日の詳細推移グラフ
        fig_today = px.line(target_df, x='時刻', y='price', color='エリア' if selected_area == "全エリア" else None)
        fig_today = update_chart_layout(fig_today, f"{selected_date} 詳細推移")
        st.plotly_chart(fig_today, use_container_width=True, config={'displayModeBar': False})

        # --- 6. 任意期間の分析 ---
        if isinstance(date_range, tuple) and len(date_range) == 2:
            s_d, e_d = date_range
            st.markdown(f'<div class="section-header">🔍 任意指定期間の分析: {s_d} ～ {e_d}</div>', unsafe_allow_html=True)
            
            mask = (df['date'].dt.date >= s_d) & (df['date'].dt.date <= e_d)
            if selected_area != "全エリア":
                mask &= (df['エリア'] == selected_area)
            
            c_df = df[mask].copy()
            if not c_df.empty:
                # 7日以内は時系列、それ以上は日次平均
                is_short = (e_d - s_d).days <= 7
                if is_short:
                    fig_custom = px.line(c_df, x='datetime', y='price', color='エリア', title="期間内連続推移")
                else:
                    custom_daily = c_df.groupby(['date', 'エリア'])['price'].mean().reset_index()
                    fig_custom = px.line(custom_daily, x='date', y='price', color='エリア', title="エリア別日次平均推移")
                
                fig_custom = update_chart_layout(fig_custom, "指定期間トレンド")
                st.plotly_chart(fig_custom, use_container_width=True, config={'displayModeBar': False})

        # --- 7. 定型トレンド分析 (タブ形式) ---
        st.markdown('<div class="section-header">📅 定型トレンド（エリア別比較）</div>', unsafe_allow_html=True)
        tabs = st.tabs(["7日間", "1ヶ月", "3ヶ月", "6ヶ月", "1年"])
        periods = [7, 30, 90, 180, 365]
        
        for tab, days in zip(tabs, periods):
            with tab:
                s_date = pd.to_datetime(selected_date) - timedelta(days=days)
                t_mask = (df['date'] >= s_date) & (df['date'] <= pd.to_datetime(selected_date))
                if selected_area != "全エリア":
                    t_mask &= (df['エリア'] == selected_area)
                
                t_df = df[t_mask].copy()
                if not t_df.empty:
                    if days == 7:
                        fig = px.line(t_df, x='datetime', y='price', color='エリア')
                    else:
                        d_avg = t_df.groupby(['date', 'エリア'])['price'].mean().reset_index()
                        fig = px.line(d_avg, x='date', y='price', color='エリア')
                    
                    fig = update_chart_layout(fig, f"直近{days}日間の推移")
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.warning(f"選択された日付 {selected_date} のデータがCSV内に見つかりません。再読み込みをお試しください。")

except Exception as e:
    st.error(f"システムエラーが発生しました: {e}")
