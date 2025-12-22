import streamlit as st
import pandas as pd
import plotly.express as px

# 1. ページ設定
st.set_page_config(page_title="JEPX価格モニター", layout="wide")

# 2. データの読み込みと加工（キャッシュ機能）
@st.cache_data
def load_data():
    df = pd.read_csv("data/spot_2025.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    # 時刻変換ロジック
    def code_to_time(code):
        total_minutes = (int(code) - 1) * 30
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
    
    if '時刻' not in df.columns:
        df['時刻'] = df['time_code'].apply(code_to_time)
    
    if 'area' in df.columns:
        df = df.rename(columns={'area': 'エリア'})
    
    return df

# カスタムデザイン
st.markdown("""
    <style>
    .main-title { font-size: 26px !important; font-weight: bold; color: #1E1E1E; margin-bottom: 20px; }
    .stMetric { background-color: #f8f9fb; padding: 15px; border-radius: 10px; border: 1px solid #eef2f6; }
    </style>
    <div class="main-title">⚡️ JEPXスポット価格 ダッシュボード</div>
    """, unsafe_allow_html=True)

try:
    df = load_data()
    
    # 3. 選択UI
    all_areas = sorted(df['エリア'].unique().tolist())
    selection_options = ["全エリア"] + all_areas
    selected_area = st.selectbox("表示エリアを選択してください", selection_options, index=0)
    
    available_dates = df['date'].dt.date.unique()
    selected_date = st.date_input("表示日付を選択", value=available_dates.max())
    
    # 4. フィルタリング
    day_df = df[df['date'].dt.date == selected_date].copy()
    
    if not day_df.empty:
        # --- 統計値の計算 ---
        if selected_area == "全エリア":
            target_df = day_df
            display_name = "全国"
        else:
            target_df = day_df[day_df['エリア'] == selected_area]
            display_name = selected_area

        avg_p = target_df['price'].mean()
        
        # 最高値とその時刻
        max_row = target_df.loc[target_df['price'].idxmax()]
        max_p = max_row['price']
        max_t = max_row['時刻']
        
        # 最低値とその時刻
        min_row = target_df.loc[target_df['price'].idxmin()]
        min_p = min_row['price']
        min_t = min_row['時刻']

        # --- 統計指標の表示（メトリクス） ---
        st.subheader(f"📊 {selected_date} の統計指標")
        col1, col2, col3 = st.columns(3)
        
        col1.metric(f"{display_name} 平均価格", f"{avg_p:.2f} 円")
        col2.metric(f"{display_name} 最高価格", f"{max_p:.2f} 円", help=f"発生時刻: {max_t}")
        col3.metric(f"{display_name} 最低価格", f"{min_p:.2f} 円", help=f"発生時刻: {min_t}")
        
        # 時刻をテキストでも強調表示
        st.write(f"💡 **最高値発生:** {max_t} ({max_p:.2f}円) ／ **最低値発生:** {min_t} ({min_p:.2f}円)")

        # --- グラフ表示 ---
        if selected_area == "全エリア":
            fig_day = px.line(day_df, x='時刻', y='price', color='エリア',
                              title=f"{selected_date} 全エリア価格推移")
        else:
            fig_day = px.line(target_df, x='時刻', y='price',
                              title=f"{selected_date} {selected_area}価格推移")
            fig_day.update_traces(line_color='#FF4B4B', line_width=3)

        fig_day.update_layout(
            hovermode="x unified",
            xaxis_tickangle=-45,
            xaxis=dict(tickmode='linear', dtick=4),
            yaxis_title="価格 (円/kWh)"
        )
        st.plotly_chart(fig_day, use_container_width=True)

        # 5. 7日間比較（個別エリアのみ）
        if selected_area != "全エリア":
            st.markdown("---")
            st.subheader(f"📈 {selected_area}：直近7日間の比較")
            trend_df = df[df['エリア'] == selected_area].tail(48 * 7).copy()
            trend_df['日付表示'] = trend_df['date'].dt.strftime('%m/%d')
            fig_7d = px.line(trend_df, x='時刻', y='price', color='日付表示')
            fig_7d.update_layout(xaxis_tickangle=-45, xaxis=dict(tickmode='linear', dtick=4))
            st.plotly_chart(fig_7d, use_container_width=True)

    else:
        st.warning(f"{selected_date} のデータはまだ反映されていないようです。")

except Exception as e:
    st.error(f"エラーが発生しました。詳細: {e}")
