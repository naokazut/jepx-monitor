import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

# 1. ページ設定（Ver.1完全準拠）
st.set_page_config(page_title="JEPXスポット価格 統合分析ダッシュボード", layout="wide")

# 2. データの読み込みと加工（Ver.1完全準拠）
@st.cache_data
def load_data():
    # パスは実行環境に合わせてください
    df = pd.read_csv("data/spot_2025.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    # time_code (1-48) を時刻形式に変換
    def code_to_time(code):
        total_minutes = (int(code) - 1) * 30
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
    
    if '時刻' not in df.columns:
        df['時刻'] = df['time_code'].apply(code_to_time)
    
    # 連続時系列用の日時列 (datetime) を作成
    df['datetime'] = pd.to_datetime(df['date'].dt.strftime('%Y-%m-%d') + ' ' + df['時刻'])
    
    # カラム名 'area' を 'エリア' に統一
    if 'area' in df.columns:
        df = df.rename(columns={'area': 'エリア'})
    
    return df

# カスタムCSSデザイン（Ver.1ベースにタイトルのみ更新）
st.markdown("""
    <style>
    .main-title { font-size: 26px !important; font-weight: bold; color: #1E1E1E; border-bottom: 3px solid #FF4B4B; padding-bottom: 10px; }
    .stMetric { background-color: #f8f9fb; padding: 15px; border-radius: 10px; border: 1px solid #eef2f6; }
    .section-header { margin-top: 30px; padding: 8px; background: #f0f2f6; border-radius: 5px; font-weight: bold; }
    </style>
    <div class="main-title">🏔️ Project Zenith: JEPXスポット価格 統合分析ダッシュボード (Ver.2)</div>
    """, unsafe_allow_html=True)

try:
    df = load_data()
    
    # --- 3. サイドバーUI（Ver.1完全準拠） ---
    st.sidebar.header("📊 表示設定")
    all_areas = sorted(df['エリア'].unique().tolist())
    selected_area = st.sidebar.selectbox("表示エリアを選択", ["全エリア"] + all_areas, index=0)
    
    available_dates = df['date'].dt.date.unique()
    max_date = available_dates.max()
    selected_date = st.sidebar.date_input("基準日を選択", value=max_date)

    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 任意の期間を指定")
    date_range = st.sidebar.date_input(
        "期間を選択",
        value=(max_date - timedelta(days=7), max_date),
        min_value=df['date'].min().date(),
        max_value=max_date
    )

    # 4. データのフィルタリング
    day_df = df[df['date'].dt.date == selected_date].copy()

    if not day_df.empty:
        display_name = "全国" if selected_area == "全エリア" else selected_area
        target_df = day_df if selected_area == "全エリア" else day_df[day_df['エリア'] == selected_area]

        # 統計指標の表示（ここに追加ラベルをVer.1の書式に合わせて安全に実装）
        st.subheader(f"📊 {selected_date} の統計（{display_name}）")
        avg_p = target_df['price'].mean()
        max_row = target_df.loc[target_df['price'].idxmax()]
        min_row = target_df.loc[target_df['price'].idxmin()]

        col1, col2, col3 = st.columns(3)
        col1.metric("平均価格", f"{avg_p:.2f} 円")
        
        # 指示された追加ラベル（エリア/時刻）をVer.1のmetric書式で実装 [cite: 2025-12-22]
        col2.metric(
            "最高価格", 
            f"{max_row['price']:.2f} 円", 
            delta=f"{max_row['エリア']} / {max_row['時刻']}", 
            delta_color="inverse"
        )
        col3.metric(
            "最低価格", 
            f"{min_row['price']:.2f} 円", 
            delta=f"{min_row['エリア']} / {min_row['時刻']}", 
            delta_color="normal"
        )

        # ① 基準日の詳細推移（Ver.1のコードを1文字も変えず復元）
        fig_today = px.line(target_df, x='時刻', y='price', color='エリア' if selected_area == "全エリア" else None, 
                            title=f"{selected_date} 詳細推移")
        fig_today.update_layout(hovermode="x unified", xaxis=dict(tickmode='linear', dtick=4))
        st.plotly_chart(fig_today, use_container_width=True)

        # 【Ver.1】平均線をグラフに追加する関数（完全復元）
        def add_highlighted_mean(fig, data_df, label_prefix="期間平均"):
            if selected_area != "全エリア" and not data_df.empty:
                m_val = data_df['price'].mean()
                fig.add_hline(
                    y=m_val, 
                    line_dash="dash", 
                    line_color="#E74C3C", 
                    line_width=3,
                    annotation_text=f" <b>{label_prefix}: {m_val:.2f}円</b> ", 
                    annotation_position="top right",
                    annotation_font_size=14,
                    annotation_font_color="white",
                    annotation_bgcolor="#E74C3C"
                )
            return fig

        # --- ② 任意指定期間の分析（Ver.1完全復元） ---
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            st.markdown(f'<div class="section-header">🔍 指定期間の分析: {start_date} ～ {end_date}</div>', unsafe_allow_html=True)
            
            mask_custom = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
            if selected_area != "全エリア":
                mask_custom &= (df['エリア'] == selected_area)
            
            custom_df = df[mask_custom].copy()
            
            if not custom_df.empty:
                delta_days = (end_date - start_date).days
                if delta_days <= 7:
                    fig_custom = px.line(custom_df, x='datetime', y='price', color='エリア', title="指定期間の時系列推移")
                else:
                    custom_daily = custom_df.groupby(['date', 'エリア'])['price'].mean().reset_index()
                    fig_custom = px.line(custom_daily, x='date', y='price', color='エリア', title="指定期間のエリア別日次平均推移")
                
                fig_custom = add_highlighted_mean(fig_custom, custom_df)
                fig_custom.update_layout(hovermode="x unified")
                st.plotly_chart(fig_custom, use_container_width=True)

        # --- ③ 定型トレンド分析（Ver.1完全復元：7日〜1年） ---
        st.markdown('<div class="section-header">📅 定型トレンド分析（エリア別比較）</div>', unsafe_allow_html=True)

        def plot_all_periods(days, title, is_hourly=False):
            s_date = pd.to_datetime(selected_date) - timedelta(days=days)
            mask = (df['date'] >= s_date) & (df['date'] <= pd.to_datetime(selected_date))
            if selected_area != "全エリア":
                mask &= (df['エリア'] == selected_area)
            
            term_df = df[mask].copy()
            if not term_df.empty:
                if is_hourly:
                    fig = px.line(term_df, x='datetime', y='price', color='エリア', title=title)
                else:
                    daily_df = term_df.groupby(['date', 'エリア'])['price'].mean().reset_index()
                    fig = px.line(daily_df, x='date', y='price', color='エリア', title=title)
                
                fig = add_highlighted_mean(fig, term_df)
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)

        st.write("### ① 直近7日間の推移（時系列連続）")
        plot_all_periods(7, f"{display_name}：過去7日間の連続推移", is_hourly=True)

        st.write("### ② 直近1ヶ月のトレンド")
        plot_all_periods(30, f"{display_name}：過去1ヶ月のエリア別平均推移")

        st.write("### ③ 直近3ヶ月のトレンド")
        plot_all_periods(90, f"{display_name}：過去3ヶ月のエリア別平均推移")

        st.write("### ④ 直近6ヶ月のトレンド")
        plot_all_periods(180, f"{display_name}：過去6ヶ月のエリア別平均推移")

        st.write("### ⑤ 直近1年のトレンド")
        plot_all_periods(365, f"{display_name}：過去1年のエリア別平均推移")

    else:
        st.warning(f"{selected_date} のデータが見つかりません。")

except Exception as e:
    st.error(f"⚠️ エラーが発生しました: {e}")
