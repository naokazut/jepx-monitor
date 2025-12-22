import streamlit as st
import pandas as pd
import plotly.express as px

# データの読み込み
df = pd.read_csv('data/spot_2025.csv')

# 日付選択
dates = df['date'].unique()
selected_date = st.selectbox('日付を選択', dates)

# エリア選択肢の準備（全エリアを追加）
areas = ['東京', '関西', '中部', '九州', '北海道', '東北', '北陸', '中国', '四国']
selected_area = st.selectbox('エリアを選択', ['全エリア'] + areas)

# 選択された日付でフィルタリング
df_filtered = df[df['date'] == selected_date]

if selected_area == '全エリア':
    # 全エリアが選ばれた場合：全エリアを1つのグラフに表示
    fig = px.line(df_filtered, x='時刻', y=areas, 
                  title=f"{selected_date} の全エリア推移",
                  labels={'value': 'price', 'variable': 'エリア'})
else:
    # 特定のエリアが選ばれた場合：そのエリアのみ表示
    fig = px.line(df_filtered, x='時刻', y=selected_area, 
                  title=f"{selected_date} の推移 ({selected_area})")

st.plotly_chart(fig)

# ページ設定
st.set_page_config(page_title="JEPX価格モニター", layout="wide")

# タイトル
st.markdown("""
    <style>
    .main-title { font-size: 24px !important; font-weight: bold; margin-bottom: 20px; }
    </style>
    <div class="main-title">⚡️ JEPXスポット価格 ダッシュボード</div>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv("data/spot_2025.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    # 時刻変換
    def code_to_time(code):
        total_minutes = (int(code) - 1) * 30
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
    df['時刻'] = df['time_code'].apply(code_to_time)
    
    # 【エラー対策】area列がない場合の処理
    if 'area' not in df.columns:
        # もし列名が「エリア」など日本語になっている場合の予備対策
        if 'エリア' in df.columns:
            df = df.rename(columns={'エリア': 'area'})
        else:
            # それでもない場合は「システム（不明）」として埋める
            df['area'] = '不明'
            
    return df

try:
    df = load_data()
    
    # エリア選択（重複を排除してリスト化）
    area_list = sorted(df['area'].unique().tolist())
    
    # デフォルトで「東京」を選択（リストにあれば）
    default_index = area_list.index('東京') if '東京' in area_list else 0
    selected_area = st.selectbox("表示エリアを選択してください", area_list, index=default_index)
    
    # 選択エリアで絞り込み
    filtered_df = df[df['area'] == selected_area].copy()

    # --- 日別詳細 ---
    st.subheader(f"📅 {selected_area}：日別詳細")
    available_dates = filtered_df['date'].dt.date.unique()
    selected_date = st.date_input("日付を選択", value=available_dates.max())

    day_df = filtered_df[filtered_df['date'].dt.date == selected_date].copy()
    
    if not day_df.empty:
        fig_day = px.line(day_df, x='時刻', y='price', title=f"{selected_date} の推移 ({selected_area})")
        fig_day.update_traces(line_color='#FF4B4B', line_width=3)
        fig_day.update_layout(xaxis_tickangle=-45, xaxis=dict(tickmode='linear', dtick=4))
        st.plotly_chart(fig_day, use_container_width=True)

    st.markdown("---")

    # --- 7日間比較 ---
    st.subheader(f"📈 {selected_area}：直近7日間の比較")
    plot_df = filtered_df.tail(48 * 7).copy()
    plot_df['日付'] = plot_df['date'].dt.strftime('%m/%d')

    fig_7d = px.line(plot_df, x='時刻', y='price', color='日付')
    fig_7d.update_layout(xaxis_tickangle=-45, xaxis=dict(tickmode='linear', dtick=4),
                         legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_7d, use_container_width=True)

except Exception as e:
    st.error(f"表示できるデータがまだ整っていないようです。一度、GitHub Actionsを手動で実行して最新データを生成してみてください。\nエラー詳細: {e}")
