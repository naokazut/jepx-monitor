import streamlit as st
import pandas as pd
import plotly.express as px

# 1. タイトルのフォントサイズ調整（HTML/CSSを使用）
st.set_page_config(page_title="JEPX価格モニター", layout="wide")

st.markdown("""
    <style>
    .main-title {
        font-size: 28px !important;
        font-weight: bold;
        margin-bottom: 20px;
    }
    </style>
    <div class="main-title">⚡️ JEPXスポット価格 ダッシュボード</div>
    """, unsafe_allow_index=True)

@st.cache_data
def load_data():
    df = pd.read_csv("data/spot_2025.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    # 2. 横軸を24時間表示に変換する処理
    # 時刻コード(1-48)を実際の時間(00:00-23:30)に変換
    def code_to_time(code):
        total_minutes = (code - 1) * 30
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"
    
    df['time_display'] = df['time_code'].apply(code_to_time)
    return df

try:
    df = load_data()
    
    latest_date = df['date'].max()
    st.info(f"最終更新データ: {latest_date.strftime('%Y/%m/%d')}")

    # グラフ作成
    # x軸を先ほど作った 'time_display' に変更
    fig = px.line(df.tail(48 * 7), x='time_display', y='price', color='date',
                  labels={'price': '価格(円/kWh)', 'time_display': '時刻'},
                  title="直近7日間の価格推移")
    
    # 横軸の目盛りをスッキリさせる設定
    fig.update_xaxes(tickangle=45, nbins=24)
    
    st.plotly_chart(fig, use_container_width=True)

    if st.checkbox("生データを確認"):
        st.write(df.tail(48))

except Exception as e:
    st.error(f"エラーが発生しました: {e}")
