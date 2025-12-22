import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta

# 1. ページ設定（必ず最初に記述）
st.set_page_config(page_title="JEPX価格分析ダッシュボード", layout="wide")

# 2. データの読み込みと加工（キャッシュ機能）
@st.cache_data
def load_data():
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

# カスタムデザイン
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
    
    # 3. 選択UI（サイドバー）
    all_areas = sorted(df['エリア'].unique().tolist())
    # ここで「全エリア」をリストの先頭に追加
    selection_options = ["全エリア"] + all_areas
    
    selected_area = st.sidebar.selectbox("表示エリアを選択", selection_options, index=0)
    
    available_dates = df['date'].dt.date.unique()
    selected_date = st.sidebar.date_input("基準日を選択", value=available_dates.max())

    # 4. データのフィルタリング（基準日）
    day_df = df[df['date'].dt.date == selected_date].copy()

    if not day_df.empty:
        # --- 統計値の計算 ---
        if selected_area == "全エリア":
            target_df = day_df
            display_name = "全国"
        else:
            target_df = day_df[day_df['エリア'] == selected_area]
            display_name = selected_area

        # 平均・最高・最低の算出
        avg_p = target_df['price'].mean()
        max_row = target_df.loc[target_df['price'].idxmax()]
        min_row = target_df.loc[target_df['price'].idxmin()]

        # --- 指標表示 ---
        st.subheader(f"📊 {selected_date} の統計（{display_name}）")
        col1, col2, col3 = st.columns(3)
        col1.metric("平均価格", f"{avg_p:.2f} 円")
        col2.metric("最高価格", f"{max_row['price']:.2f} 円", help=f"時刻: {max_row['時刻']} エリア: {max_row.get('エリア', '設定なし')}")
        col3.metric("最低価格", f"{min_row['price']:.2f} 円", help=f"時刻: {min_row['時刻']} エリア: {min_row.get('エリア', '設定なし')}")
        
        st.write(f"💡 **最高値:** {max_row['時刻']} ({max_row['price']:.2f}円) ／ **最低値:** {min_row['時刻']} ({min_row['price']:.2f}円)")

        # --- 今日のグラフ表示 ---
        if selected_area == "全エリア":
            fig_day = px.line(day_df, x='時刻', y='price', color='エリア', title=f"{selected_date} 全エリア価格推移")
        else:
            fig_day = px.line(target_df, x='時刻', y='price', title=f"{selected_date} {selected_area}価格推移")
            fig_day.update_traces(line_color='#FF4B4B', line_width=3)

        fig_day.update_layout(hovermode="x unified", xaxis_tickangle=-45, xaxis=dict(tickmode='linear', dtick=4))
        st.plotly_chart(fig_day, use_container_width=True)

        # --- 長期トレンド分析セクション ---
        st.markdown('<div class="section-header">📅 期間別トレンド分析</div>', unsafe_allow_html=True)

        def plot_trend(days, title, is_hourly=False):
            start_date = pd.to_datetime(selected_date) - timedelta(days=days)
            if selected_area == "全エリア":
                term_df = df[(df['date'] >= start_date) & (df['date'] <= pd.to_datetime(selected_date))]
            else:
                term_df = df[(df['date'] >= start_date) & (df['date'] <= pd.to_datetime(selected_date)) & (df['エリア'] == selected_area)]
            
            if not term_df.empty:
                if is_hourly:
                    # 7日間用：時刻別の重ね合わせ
                    term_df_plot = term_df.copy()
                    term_df_plot['日付'] = term_df_plot['date'].dt.strftime('%m/%d')
                    fig = px.line(term_df_plot, x='時刻', y='price', color='日付', title=title)
                else:
                    # 長期用：日次サマリー
                    daily_summary = term_df.groupby(['date'])['price'].agg(['mean', 'max', 'min']).reset_index()
                    fig = px.line(daily_summary, x='date', y=['mean', 'max', 'min'], title=title)
                
                fig.update_layout(hovermode="x unified", xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

        # 各スパンの表示
        if selected_area != "全エリア":
            st.write("### ① 直近7日間の比較（時刻別）")
            plot_trend(7, f"{selected_area}：過去7日間の時刻別推移", is_hourly=True)
        
        st.write("### ② 直近1ヶ月のトレンド")
        plot_trend(30, f"{display_name}：過去1ヶ月の価格変動（日次）")

        st.write("### ③ 直近3ヶ月のトレンド")
        plot_trend(90, f"{display_name}：過去3ヶ月の価格変動（日次）")

        st.write("### ④ 直近6ヶ月のトレンド")
        plot_trend(180, f"{display_name}：過去6ヶ月の価格変動（日次）")

        st.write("### ⑤ 直近1年のトレンド")
        plot_trend(365, f"{display_name}：過去1年の価格変動（日次）")

    else:
        st.warning(f"{selected_date} のデータが見つかりません。")

except Exception as e:
    st.error(f"アプリの実行中にエラーが発生しました: {e}")
