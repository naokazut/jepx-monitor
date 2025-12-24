import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta

# 1. ページ設定
st.set_page_config(page_title="Project Zenith - JEPX分析", layout="wide")

# 2. データの読み込み
@st.cache_data
def load_data():
    df = pd.read_csv("data/spot_2025.csv")
    df['date'] = pd.to_datetime(df['date'])
    def code_to_time(code):
        total_minutes = (int(code) - 1) * 30
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
    if '時刻' not in df.columns:
        df['時刻'] = df['time_code'].apply(code_to_time)
    df['datetime'] = pd.to_datetime(df['date'].dt.strftime('%Y-%m-%d') + ' ' + df['時刻'])
    if 'area' in df.columns:
        df = df.rename(columns={'area': 'エリア'})
    return df

# CSSデザイン (スマホ向けに余白をさらに最適化)
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; color: #1E1E1E; border-bottom: 3px solid #3498DB; padding-bottom: 5px; }
    .stMetric { background-color: #f8f9fb; padding: 8px; border-radius: 10px; border: 1px solid #eef2f6; }
    .section-header { margin-top: 20px; padding: 8px; background: #f0f2f6; border-radius: 5px; font-weight: bold; font-size: 14px; }
    </style>
    <div class="main-title">⚡️ Project Zenith: JEPX統合分析 (Ver.5)</div>
    """, unsafe_allow_html=True)

try:
    df = load_data()
    
    # --- 3. サイドバーUI ---
    st.sidebar.header("📊 表示設定")
    all_areas = sorted(df['エリア'].unique().tolist())
    selected_area = st.sidebar.selectbox("表示エリアを選択", ["全エリア"] + all_areas, index=0)
    max_date = df['date'].dt.date.max()
    selected_date = st.sidebar.date_input("基準日を選択", value=max_date)

    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 任意期間の指定")
    date_range = st.sidebar.date_input(
        "期間を選択",
        value=(max_date - timedelta(days=7), max_date),
        min_value=df['date'].min().date(),
        max_value=max_date
    )

    # 【修正】レイアウト更新関数（凡例の重なり防止）
    def update_chart_layout(fig, title_text):
        fig.update_layout(
            title=dict(text=title_text, font=dict(size=16)),
            hovermode="x unified",
            dragmode=False,
            # 凡例をグラフの下（y=-0.2以降）に配置し、重なりを回避
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.25, 
                xanchor="center",
                x=0.5,
                font=dict(size=10),
                traceorder="normal",
                itemwidth=30
            ),
            margin=dict(l=10, r=10, t=50, b=80), # 下側の余白を広げて凡例スペースを確保
            hoverlabel=dict(
                bgcolor="rgba(255, 255, 255, 0.9)",
                font_size=11,
                namelength=-1
            )
        )
        fig.update_traces(hovertemplate="%{fullData.name}: %{y:.1f}円<extra></extra>")
        return fig

    # 4. 統計指標
    day_df = df[df['date'].dt.date == selected_date].copy()
    if not day_df.empty:
        target_df = day_df if selected_area == "全エリア" else day_df[day_df['エリア'] == selected_area]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("平均", f"{target_df['price'].mean():.2f} 円")
        max_row = target_df.loc[target_df['price'].idxmax()]
        min_row = target_df.loc[target_df['price'].idxmin()]
        col2.metric("最高", f"{max_row['price']:.1f} 円", f"{max_row['エリア']} {max_row['時刻']}", delta_color="inverse")
        col3.metric("最低", f"{min_row['price']:.1f} 円", f"{min_row['エリア']} {min_row['時刻']}")

        # 5. 詳細推移グラフ
        fig_today = px.line(target_df, x='時刻', y='price', color='エリア' if selected_area == "全エリア" else None)
        fig_today = update_chart_layout(fig_today, f"{selected_date} 詳細推移")
        st.plotly_chart(fig_today, use_container_width=True, config={'displayModeBar': False})

        # 6. 任意期間の分析 (復旧済み)
        if isinstance(date_range, tuple) and len(date_range) == 2:
            s_d, e_d = date_range
            st.markdown(f'<div class="section-header">🔍 任意指定期間: {s_d} ～ {e_d}</div>', unsafe_allow_html=True)
            mask = (df['date'].dt.date >= s_d) & (df['date'].dt.date <= e_d)
            if selected_area != "全エリア": mask &= (df['エリア'] == selected_area)
            
            c_df = df[mask].copy()
            if not c_df.empty:
                is_short = (e_d - s_d).days <= 7
                plot_df = c_df if is_short else c_df.groupby(['date', 'エリア'])['price'].mean().reset_index()
                x_col = 'datetime' if is_short else 'date'
                
                fig_custom = px.line(plot_df, x=x_col, y='price', color='エリア')
                fig_custom = update_chart_layout(fig_custom, "指定期間トレンド")
                st.plotly_chart(fig_custom, use_container_width=True, config={'displayModeBar': False})

        # 7. 定型トレンド
        st.markdown('<div class="section-header">📅 定型トレンド</div>', unsafe_allow_html=True)
        tabs = st.tabs(["7日間", "1ヶ月", "3ヶ月", "6ヶ月", "1年"])
        periods = [7, 30, 90, 180, 365]
        
        for tab, days in zip(tabs, periods):
            with tab:
                s_date = pd.to_datetime(selected_date) - timedelta(days=days)
                mask = (df['date'] >= s_date) & (df['date'] <= pd.to_datetime(selected_date))
                if selected_area != "全エリア": mask &= (df['エリア'] == selected_area)
                
                t_df = df[mask].copy()
                if not t_df.empty:
                    if days == 7:
                        fig = px.line(t_df, x='datetime', y='price', color='エリア')
                    else:
                        d_avg = t_df.groupby(['date', 'エリア'])['price'].mean().reset_index()
                        fig = px.line(d_avg, x='date', y='price', color='エリア')
                    
                    fig = update_chart_layout(fig, f"過去{days}日間の推移")
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
except Exception as e:
    st.error(f"エラー: {e}")
