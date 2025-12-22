import streamlit as st
import pandas as pd
import plotly.express as px

# 1. ページ設定（必ず最初に記述）
st.set_page_config(page_title="JEPX価格モニター", layout="wide")

# 2. データの読み込みと加工
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
    
    # エリア列の正規化（日本語・英語どちらでも対応）
    if 'area' in df.columns:
        df = df.rename(columns={'area': 'エリア'})
    
    return df

# タイトル表示
st.markdown("""
    <style>
    .main-title { font-size: 24px !important; font-weight: bold; margin-bottom: 20px; }
    </style>
    <div class="main-title">⚡️ JEPXスポット価格 ダッシュボード</div>
    """, unsafe_allow_html=True)

try:
    df = load_data()
    
    # 3. 選択エリアの設定（全エリアを追加）
    all_areas = sorted(df['エリア'].unique().tolist())
    selection_options = ["全エリア"] + all_areas
    
    selected_area = st.selectbox("表示エリアを選択してください", selection_options, index=0)
    
    # 4. 日別詳細セクション
    st.subheader(f"📅 日別詳細")
    available_dates = df['date'].dt.date.unique()
    selected_date = st.date_input("日付を選択", value=available_dates.max())
    
    # 日付でフィルタリング
    day_df = df[df['date'].dt.date == selected_date].copy()
    
    if not day_df.empty:
        if selected_area == "全エリア":
            # 全エリアを重ねて表示
            fig_day = px.line(day_df, x='時刻', y='price', color='エリア',
                              title=f"{selected_date} の全エリア価格推移")
        else:
            # 特定エリアのみ表示
            filtered_day_df = day_df[day_df['エリア'] == selected_area]
            fig_day = px.line(filtered_day_df, x='時刻', y='price', 
                              title=f"{selected_date} の推移 ({selected_area})")
            fig_day.update_traces(line_color='#FF4B4B', line_width=3)

        fig_day.update_layout(xaxis_tickangle=-45, xaxis=dict(tickmode='linear', dtick=4))
        st.plotly_chart(fig_day, use_container_width=True)

    st.markdown("---")

    # 5. 7日間比較セクション（全エリア時は代表として東京を表示、または選択エリアを表示）
    if selected_area != "全エリア":
        st.subheader(f"📈 {selected_area}：直近7日間の比較")
        filtered_df = df[df['エリア'] == selected_area].copy()
        plot_df = filtered_df.tail(48 * 7).copy()
        plot_df['日付'] = plot_df['date'].dt.strftime('%m/%d')

        fig_7d = px.line(plot_df, x='時刻', y='price', color='日付')
        fig_7d.update_layout(xaxis_tickangle=-45, xaxis=dict(tickmode='linear', dtick=4),
                             legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_7d, use_container_width=True)
    else:
        st.info("※「全エリア」選択時は、上の日別詳細グラフでエリア間の比較が可能です。")

except Exception as e:
    st.error(f"データの読み込み中にエラーが発生しました。\nエラー詳細: {e}")
