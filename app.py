import streamlit as st
import pandas as pd
import plotly.express as px

# 1. ページ設定（アプリの起動時に一度だけ実行される）
st.set_page_config(page_title="JEPX価格モニター", layout="wide")

# 2. データの読み込みと加工（キャッシュ機能で高速化）
@st.cache_data
def load_data():
    # データ読み込み
    df = pd.read_csv("data/spot_2025.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    # 時刻変換ロジック（time_code 1-48 を 00:00-23:30 に変換）
    def code_to_time(code):
        total_minutes = (int(code) - 1) * 30
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
    
    if '時刻' not in df.columns:
        df['時刻'] = df['time_code'].apply(code_to_time)
    
    # エリア列の名称を「エリア」に統一
    if 'area' in df.columns:
        df = df.rename(columns={'area': 'エリア'})
    
    return df

# カスタムスタイルの適用
st.markdown("""
    <style>
    .main-title { font-size: 26px !important; font-weight: bold; color: #1E1E1E; margin-bottom: 20px; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
    </style>
    <div class="main-title">⚡️ JEPXスポット価格 ダッシュボード</div>
    """, unsafe_allow_html=True)

try:
    # データのロード
    df = load_data()
    
    # 3. サイドバー/メインエリアでの選択設定
    all_areas = sorted(df['エリア'].unique().tolist())
    selection_options = ["全エリア"] + all_areas
    
    selected_area = st.selectbox("表示エリアを選択してください", selection_options, index=0)
    
    available_dates = df['date'].dt.date.unique()
    selected_date = st.date_input("表示日付を選択", value=available_dates.max())
    
    # 4. データのフィルタリング
    day_df = df[df['date'].dt.date == selected_date].copy()
    
    if not day_df.empty:
        # --- 統計値（メトリクス）の表示 ---
        st.subheader(f"📊 {selected_date} の統計指標")
        col1, col2, col3 = st.columns(3)
        
        if selected_area == "全エリア":
            # 全エリアの平均・最高
            avg_p = day_df['price'].mean()
            max_p = day_df['price'].max()
            min_p = day_df['price'].min()
            col1.metric("全国平均価格", f"{avg_p:.2f} 円")
            col2.metric("全国最高価格", f"{max_p:.2f} 円")
            col3.metric("全国最低価格", f"{min_p:.2f} 円")
            
            # グラフ描画
            fig_day = px.line(day_df, x='時刻', y='price', color='エリア',
                              title=f"{selected_date} 全エリア価格推移")
        else:
            # 特定エリアの平均・最高
            area_df = day_df[day_df['エリア'] == selected_area]
            avg_p = area_df['price'].mean()
            max_p = area_df['price'].max()
            min_p = area_df['price'].min()
            col1.metric(f"{selected_area} 平均", f"{avg_p:.2f} 円")
            col2.metric(f"{selected_area} 最高", f"{max_p:.2f} 円")
            col3.metric(f"{selected_area} 最低", f"{min_p:.2f} 円")
            
            # グラフ描画
            fig_day = px.line(area_df, x='時刻', y='price',
                              title=f"{selected_date} {selected_area}価格推移")
            fig_day.update_traces(line_color='#FF4B4B', line_width=3)

        # 共通のグラフレイアウト設定
        fig_day.update_layout(
            hovermode="x unified",
            xaxis_tickangle=-45,
            xaxis=dict(tickmode='linear', dtick=4),
            yaxis_title="価格 (円/kWh)"
        )
        st.plotly_chart(fig_day, use_container_width=True)

        # 5. 7日間トレンド比較（特定エリア選択時のみ表示）
        if selected_area != "全エリア":
            st.markdown("---")
            st.subheader(f"📈 {selected_area}：直近7日間の比較")
            full_area_df = df[df['エリア'] == selected_area].copy()
            trend_df = full_area_df.tail(48 * 7).copy()
            trend_df['日付表示'] = trend_df['date'].dt.strftime('%m/%d')

            fig_7d = px.line(trend_df, x='時刻', y='price', color='日付表示',
                             title=f"{selected_area} の直近1週間の動き")
            fig_7d.update_layout(xaxis_tickangle=-45, xaxis=dict(tickmode='linear', dtick=4))
            st.plotly_chart(fig_7d, use_container_width=True)
    else:
        st.warning(f"{selected_date} のデータはまだ存在しないようです。")

except Exception as e:
    st.error(f"エラーが発生しました。データ形式を確認してください。\n詳細: {e}")
