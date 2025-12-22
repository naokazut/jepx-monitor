import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta

# 1. ページ設定
st.set_page_config(page_title="JEPXスポット価格 統合分析ダッシュボード", layout="wide")

# 2. データの読み込みと加工
@st.cache_data
def load_data():
    df = pd.read_csv("data/spot_2025.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    def code_to_time(code):
        total_minutes = (int(code) - 1) * 30
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
    
    if '時刻' not in df.columns:
        df['時刻'] = df['time_code'].apply(code_to_time)
    
    # 連続時系列用の日時列
    df['datetime'] = pd.to_datetime(df['date'].dt.strftime('%Y-%m-%d') + ' ' + df['時刻'])
    
    if 'area' in df.columns:
        df = df.rename(columns={'area': 'エリア'})
    
    return df

# デザイン設定
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
        # 指標表示用の名称とデータ抽出
        display_name = "全国" if selected_area == "全エリア" else selected_area
        target_df = day_df if selected_area == "全エリア" else day_df[day_df['エリア'] == selected_area]

        # 統計指標
        avg_p = target_df['price'].mean()
        max_row = target_df.loc[target_df['price'].idxmax()]
        min_row = target_df.loc[target_df['price'].idxmin()]

        st.subheader(f"📊 {selected_date} の統計（{display_name}）")
        col1, col2, col3 = st.columns(3)
        col1.metric("平均価格", f"{avg_p:.2f} 円")
        col2.metric("最高価格", f"{max_row['price']:.2f} 円", help=f"エリア: {max_row.get('エリア', '不明')}")
        col3.metric("最低価格", f"{min_row['price']:.2f} 円", help=f"エリア: {min_row.get('エリア', '不明')}")

        # ① 本日の推移
        fig_today = px.line(target_df, x='時刻', y='price', color='エリア' if selected_area == "全エリア" else None, 
                            title=f"{selected_date} 詳細推移")
        if selected_area != "全エリア": fig_today.update_traces(line_color='#FF4B4B')
        fig_today.update_layout(hovermode="x unified", xaxis=dict(tickmode='linear', dtick=4))
        st.plotly_chart(fig_today, use_container_width=True)

        st.markdown('<div class="section-header">📅 期間別トレンド分析（エリア別比較）</div>', unsafe_allow_html=True)

        # --- 期間分析グラフ作成共通ロジック ---
        def plot_all_periods(days, title, is_hourly=False):
            start_date = pd.to_datetime(selected_date) - timedelta(days=days)
            mask = (df['date'] >= start_date) & (df['date'] <= pd.to_datetime(selected_date))
            
            if selected_area != "全エリア":
                mask &= (df['エリア'] == selected_area)
            
            term_df = df[mask].copy()
            
            if not term_df.empty:
                if is_hourly:
                    # 直近7日間：連続時系列（30分単位）
                    fig = px.line(term_df, x='datetime', y='price', color='エリア', title=title)
                else:
                    # 長期トレンド：日次平均に集約してエリア別に表示
                    # ※データ量爆発を防ぐため、1ヶ月以上は日次平均で描画
                    daily_df = term_df.groupby(['date', 'エリア'])['price'].mean().reset_index()
                    fig = px.line(daily_df, x='date', y='price', color='エリア', title=title)
                
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)

        # 4. 指定された各期間の表示
        st.write("### ① 直近7日間の推移（時系列連続）")
        plot_all_periods(7, f"{display_name}：過去7日間の連続推移", is_hourly=True)

        st.write("### ② 直近1ヶ月のトレンド")
        plot_all_periods(30, f"{display_name}：過去1ヶ月のエリア別平均推移")

        st.write("### ③ 直近3ヶ月のトレンド")
        plot_all_periods(90, f"{display_name}：過去3ヶ月のエリア別平均推移")

        st.write("### ④ 直近6ヶ月のトレンド")
        plot_all_periods(180, f"{display_name}：過去6ヶ月のエリア別平均推移")

        st.write("### ⑤ 直近1年のトレンド")
        plot_all_periods(365, f"{display_name}：過去1年のエリア別平均推移")

    else:
        st.warning("データが見つかりません。")

except Exception as e:
    st.error(f"エラーが発生しました: {e}")
