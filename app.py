import streamlit as st
import pandas as pd
import plotly.express as px

# ページ設定
st.set_page_config(page_title="JEPX価格モニター", layout="wide")

# カスタムCSSでタイトルサイズ調整
st.markdown("""
    <style>
    .main-title {
        font-size: 24px !important;
        font-weight: bold;
        margin-bottom: 20px;
    }
    </style>
    <div class="main-title">⚡️ JEPXスポット価格 ダッシュボード</div>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv("data/spot_2025.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    # 時刻コードを「HH:MM」形式に変換
    def code_to_time(code):
        total_minutes = (code - 1) * 30
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"
    
    df['時刻'] = df['time_code'].apply(code_to_time)
    return df

try:
    df = load_data()
    
    # --- エリア選択機能の追加 ---
    # CSV内のエリア列（area）から重複を除いたリストを作成
    area_list = df['area'].unique().tolist()
    selected_area = st.selectbox("表示エリアを選択してください", area_list, index=area_list.index('東京') if '東京' in area_list else 0)
    
    # 選ばれたエリアでデータを絞り込み
    filtered_df = df[df['area'] == selected_area].copy()

    # --- セクション1: 特定の日付を選択して表示 ---
    st.subheader(f"📅 {selected_area}エリア：日別詳細")
    
    available_dates = filtered_df['date'].dt.date.unique()
    selected_date = st.date_input(
        "日付を選択",
        value=available_dates.max(),
        min_value=available_dates.min(),
        max_value=available_dates.max()
    )

    day_df = filtered_df[filtered_df['date'].dt.date == selected_date].copy()
    
    if not day_df.empty:
        fig_day = px.line(day_df, x='時刻', y='price',
                          labels={'price': '価格(円/kWh)', '時刻': '時刻'},
                          title=f"{selected_date.strftime('%Y/%m/%d')} の価格推移 ({selected_area})")
        fig_day.update_traces(line_color='#FF4B4B', line_width=3)
        fig_day.update_layout(xaxis_tickangle=-45, xaxis=dict(tickmode='linear', dtick=4))
        st.plotly_chart(fig_day, use_container_width=True)
    else:
        st.warning("選択された日のデータがありません。")

    st.markdown("---")

    # --- セクション2: 直近7日間の比較 ---
    st.subheader(f"📈 {selected_area}エリア：直近7日間の推移比較")
    
    plot_df = filtered_df.tail(48 * 7).copy()
    plot_df['日付'] = plot_df['date'].dt.strftime('%m/%d')

    fig_7d = px.line(plot_df, x='時刻', y='price', color='日付',
                     labels={'price': '価格(円/kWh)', '時刻': '時刻'})
    
    fig_7d.update_layout(
        xaxis_tickangle=-45,
        xaxis=dict(tickmode='linear', dtick=4),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig_7d, use_container_width=True)

except Exception as e:
    st.error(f"エラーが発生しました: {e}")
