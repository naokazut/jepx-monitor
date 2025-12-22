import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta

# 1. ページ設定
st.set_page_config(page_title="JEPX高度分析ダッシュボード", layout="wide")

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
    
    if 'area' in df.columns:
        df = df.rename(columns={'area': 'エリア'})
    
    return df

# ヘッダーデザイン
st.markdown("""
    <style>
    .main-title { font-size: 28px !important; font-weight: bold; color: #1E1E1E; border-bottom: 3px solid #FF4B4B; padding-bottom: 10px; }
    .section-header { margin-top: 40px; padding: 10px; background: #f0f2f6; border-radius: 5px; font-weight: bold; }
    </style>
    <div class="main-title">⚡️ JEPXスポット価格 長期トレンド分析</div>
    """, unsafe_allow_html=True)

try:
    df = load_data()
    
    # サイドバーでエリア選択
    all_areas = sorted(df['エリア'].unique().tolist())
    selected_area = st.sidebar.selectbox("分析エリア", all_areas, index=0)
    
    available_dates = df['date'].dt.date.unique()
    selected_date = st.sidebar.date_input("基準日", value=available_dates.max())

    # データ抽出
    day_df = df[(df['date'].dt.date == selected_date) & (df['エリア'] == selected_area)].copy()

    if not day_df.empty:
        # --- 1. 本日の詳細情報 ---
        max_row = day_df.loc[day_df['price'].idxmax()]
        min_row = day_df.loc[day_df['price'].idxmin()]

        st.subheader(f"📊 {selected_area}：{selected_date} の詳細")
        col1, col2, col3 = st.columns(3)
        col1.metric("平均価格", f"{day_df['price'].mean():.2f} 円")
        col2.metric("最高価格", f"{max_row['price']:.2f} 円", help=f"時刻: {max_row['時刻']}")
        col3.metric("最低価格", f"{min_row['price']:.2f} 円", help=f"時刻: {min_row['時刻']}")
        
        fig_today = px.line(day_df, x='時刻', y='price', title="24時間の価格推移")
        st.plotly_chart(fig_today, use_container_width=True)

        # --- 共通の長期分析グラフ作成関数 ---
        def plot_long_term_trend(days, title):
            start_date = pd.to_datetime(selected_date) - timedelta(days=days)
            # 期間データを抽出
            mask = (df['date'] >= start_date) & (df['date'] <= pd.to_datetime(selected_date)) & (df['エリア'] == selected_area)
            term_df = df[mask].copy()
            
            if not term_df.empty:
                # 日単位に集計（平均・最高・最低を算出）
                daily_summary = term_df.groupby('date')['price'].agg(['mean', 'max', 'min']).reset_index()
                
                fig = px.line(daily_summary, x='date', y=['mean', 'max', 'min'], 
                             title=title,
                             labels={'value': '価格 (円)', 'date': '日付', 'variable': '指標'})
                fig.update_layout(hovermode="x unified", legend_title=None)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"{title}のデータが不足しています。")

        # --- 指定された各スパンの表示 ---
        st.markdown('<div class="section-header">📅 期間別トレンド比較</div>', unsafe_allow_html=True)

        # 1. 直近7日間（これは時刻ごとの重畳表示が見やすいため既存ロジックを維持）
        st.write("### ① 直近7日間の比較（時刻別）")
        trend_7d = df[(df['エリア'] == selected_area) & (df['date'] > pd.to_datetime(selected_date) - timedelta(days=7))].copy()
        trend_7d['日付'] = trend_7d['date'].dt.strftime('%m/%d')
        fig_7d = px.line(trend_7d, x='時刻', y='price', color='日付', title="過去7日間の時刻別推移")
        st.plotly_chart(fig_7d, use_container_width=True)

        # 2. 直近1ヶ月（30日）
        st.write("### ② 直近1ヶ月のトレンド")
        plot_long_term_trend(30, f"{selected_area}：過去1ヶ月の価格変動（日次）")

        # 3. 直近3ヶ月（90日）
        st.write("### ③ 直近3ヶ月のトレンド")
        plot_long_term_trend(90, f"{selected_area}：過去3ヶ月の価格変動（日次）")

        # 4. 直近6ヶ月（180日）
        st.write("### ④ 直近6ヶ月のトレンド")
        plot_long_term_trend(180, f"{selected_area}：過去6ヶ月の価格変動（日次）")

        # 5. 直近1年（365日）
        st.write("### ⑤ 直近1年のトレンド")
        plot_long_term_trend(365, f"{selected_area}：過去1年の価格変動（日次）")

    else:
        st.warning("選択された日付のデータがありません。")

except Exception as e:
    st.error(f"エラーが発生しました: {e}")
