import streamlit as st
import pandas as pd
import plotly.express as px

# 1. タイトルのフォントサイズ調整
st.set_page_config(page_title="JEPX価格モニター", layout="wide")

st.markdown("""
    <style>
    .main-title {
        font-size: 24px !important;
        font-weight: bold;
        margin-bottom: 20px;
    }
    </style>
    <div class="main-title">⚡️ JEPXスポット価格 ダッシュボード</div>
    """, unsafe_allow_html=True) # ここを修正しました

@st.cache_data
def load_data():
    df = pd.read_csv("data/spot_2025.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    # 2. 横軸を「時:分」形式に変換
    def code_to_time(code):
        total_minutes = (code - 1) * 30
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"
    
    df['時刻'] = df['time_code'].apply(code_to_time)
    return df

try:
    df = load_data()
    
    latest_date = df['date'].max()
    st.info(f"最終更新データ: {latest_date.strftime('%Y/%m/%d')}")

    # グラフ作成（直近7日間）
    plot_df = df.tail(48 * 7).copy()
    # 凡例の日付を綺麗にする
    plot_df['日付'] = plot_df['date'].dt.strftime('%m/%d')

    fig = px.line(plot_df, x='時刻', y='price', color='日付',
                  labels={'price': '価格(円/kWh)', '時刻': '時刻'},
                  title="直近7日間の価格推移")
    
    # スマホで見やすくするための軸設定
    fig.update_layout(
        xaxis_tickangle=-45,
        xaxis=dict(tickmode='linear', dtick=4), # 2時間おきに表示
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)

    if st.checkbox("生データを確認"):
        st.write(df.tail(48))

except Exception as e:
    st.error(f"エラーが発生しました: {e}")
