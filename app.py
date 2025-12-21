import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="JEPX価格モニター", layout="wide")

st.title("⚡️ JEPXスポット価格 ダッシュボード")

# データの読み込み
@st.cache_data
def load_data():
    df = pd.read_csv("data/spot_2025.csv")
    # 日付を扱いやすく変換
    df['date'] = pd.to_datetime(df['date'])
    return df

try:
    df = load_data()
    
    # 直近の日付を選択
    latest_date = df['date'].max()
    st.info(f"最終更新データ: {latest_date.strftime('%Y/%m/%d')}")

    # グラフの作成（Plotlyでスマホでも拡大・縮小可能に）
    fig = px.line(df.tail(48 * 7), x='time_code', y='price', color='date',
                  labels={'price': '価格(円/kWh)', 'time_code': '時刻(30分単位)'},
                  title="直近7日間の価格推移")
    
    st.plotly_chart(fig, use_container_width=True)

    # データの詳細表示
    if st.checkbox("生データを確認"):
        st.write(df.tail(48))

except Exception as e:
    st.error(f"データの読み込みに失敗しました。まだCSVが生成されていない可能性があります。")
