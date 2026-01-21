import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz

# --- Project Zenith: JEPX統合分析 (Version 8) ---
# 【完了条件】Version番号を更新して提示すること。

st.set_page_config(
    page_title="Project Zenith JEPX Ver.8",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# タイムゾーン設定
JST = pytz.timezone('Asia/Tokyo')

@st.cache_data(ttl=3600)
def load_jepx_data():
    """JEPXからデータを取得し、Ver.8仕様に整形する"""
    # JEPXの最新年度データを取得（例として2025年度分を想定。運用に合わせてURL調整可）
    url = "https://www.jepx.org/market/excel/spot_2025.csv" # 実際のURL構造に合わせて更新
    try:
        # Shift-JISまたはCP932での読み込みが必要な場合が多い
        df = pd.read_csv(url, encoding='shift_jis')
        
        # 日付と時刻を結合してdatetimeオブジェクトを作成
        df['datetime'] = pd.to_datetime(df['年月日'] + ' ' + df['時刻'].str.split('-').str[0])
        df.set_index('datetime', inplace=True)
        
        # タイムゾーンの付与と変換
        if df.index.tz is None:
            df.index = df.index.tz_localize('Asia/Tokyo')
        else:
            df.index = df.index.tz_convert('Asia/Tokyo')
            
        # エリアリスト（価格変動要因の分析対象）
        # 列名はJEPXのCSVヘッダー（システムプライス, 北海道, 東北, 東京...）に依存
        return df
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return pd.DataFrame()

def main():
    st.title("⚡ JEPX 統合分析 (Ver.8)")
    st.caption(f"最終更新(JST): {datetime.now(JST).strftime('%Y-%m-%d %H:%M')}")

    df = load_jepx_data()

    if df.empty:
        st.warning("データが読み込めませんでした。URLまたはネットワークを確認してください。")
        return

    # エリア列の特定（不要な列を除外）
    exclude_cols = ['年月日', '時刻', 'month', 'hour', 'segment']
    areas = [col for col in df.columns if col not in exclude_cols and df[col].dtype in ['float64', 'int64']]

    tab1, tab2, tab3 = st.tabs(["基本価格・変動要因", "☀️❄️ 季節別比較", "🕒 時間帯別分析"])

    # --- Tab 1: 基本機能 (Ver.7 継承) ---
    with tab1:
        st.header("エリア別価格推移")
        selected_areas = st.multiselect("表示エリア選択", areas, default=["システムプライス", "東京"])
        
        fig_main = go.Figure()
        for area in selected_areas:
            fig_main.add_trace(go.Scatter(x=df.index, y=df[area], name=area, mode='lines'))
        
        fig_main.update_layout(title="スポット市場価格推移", yaxis_title="円/kWh", hovermode="x unified")
        st.plotly_chart(fig_main, use_container_width=True)

    # --- Tab 2: 季節別比較 (追加機能) ---
    with tab2:
        st.header("☀️❄️ 季節別平均価格 (夏:7-9月 vs 冬:12-2月)")
        df['month'] = df.index.month
        summer_df = df[df['month'].isin([7, 8, 9])]
        winter_df = df[df['month'].isin([12, 1, 2])]
        
        if not summer_df.empty or not winter_df.empty:
            summer_avg = summer_df[areas].mean()
            winter_avg = winter_df[areas].mean()

            fig_season = go.Figure(data=[
                go.Bar(name='夏場 (7-9月)', x=areas, y=summer_avg, marker_color='#FF4B4B'),
                go.Bar(name='冬場 (12-2月)', x=areas, y=winter_avg, marker_color='#0068C9')
            ])
            fig_season.update_layout(barmode='group', title="季節別エリア平均", yaxis_title="円/kWh")
            st.plotly_chart(fig_season, use_container_width=True)
        else:
            st.info("比較に必要な期間のデータが不足しています。")

    # --- Tab 3: 時間帯別分析 (追加機能) ---
    with tab3:
        st.header("🕒 時間帯別平均価格比較")
        
        col1, col2 = st.columns(2)
        with col1:
            s_date = st.date_input("開始日", df.index.min().date())
        with col2:
            e_date = st.date_input("終了日", df.index.max().date())

        mask = (df.index.date >= s_date) & (df.index.date <= e_date)
        f_df = df.loc[mask].copy()

        if not f_df.empty:
            def get_segment(hour):
                if 8 <= hour < 16: return '昼間 (8-16時)'
                elif 16 <= hour < 24: return '夜間 (16-24時)'
                else: return '夜中 (0-8時)'

            f_df['hour'] = f_df.index.hour
            f_df['segment'] = f_df['hour'].apply(get_segment)
            
            s_avg = f_df.groupby('segment')[areas].mean().reset_index()

            fig_time = go.Figure()
            colors = {'昼間 (8-16時)': '#FFA500', '夜間 (16-24時)': '#4B0082', '夜中 (0-8時)': '#2F4F4F'}
            for seg in ['昼間 (8-16時)', '夜間 (16-24時)', '夜中 (0-8時)']:
                seg_data = s_avg[s_avg['segment'] == seg]
                if not seg_data.empty:
                    fig_time.add_trace(go.Bar(
                        name=seg, x=areas, y=seg_data[areas].values[0],
                        marker_color=colors.get(seg)
                    ))

            fig_time.update_layout(barmode='group', title=f"{s_date} ～ {e_date} の時間帯平均", yaxis_title="円/kWh")
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.warning("選択期間のデータがありません。")

if __name__ == "__main__":
    main()
