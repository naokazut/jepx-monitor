import os
import pandas as pd
import plotly.graph_objects as go
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
import pytz

# --- Project Zenith: Production Mail System (Ver.16.0) ---

def code_to_time(code):
    """30分刻みのタイムコード(1-48)を hh:mm 形式に変換"""
    m = (int(code) - 1) * 30
    return f"{m // 60:02d}:{m % 60:02d}"

def send_daily_reports():
    JST = pytz.timezone('Asia/Tokyo')
    target_date = (datetime.now(JST) + timedelta(days=1)).date()
    
    areas = ["東京", "東北", "関西", "中国", "九州"]
    target_email = "tsukada@inbox.co.jp"
    
    try:
        df = pd.read_csv("data/spot_2026.csv")
        df['date'] = pd.to_datetime(df['date']).dt.date
        target_df = df[df['date'] == target_date].copy()
        
        if target_df.empty:
            print(f"{target_date}のデータがありません。")
            return
    except Exception as e:
        print(f"データ読み込みエラー: {e}")
        return

    mail_user = os.environ.get('MAIL_ADDRESS')
    mail_pass = os.environ.get('MAIL_PASSWORD')
    smtp_server = os.environ.get('SMTP_SERVER')

    for area_name in areas:
        area_df = target_df[target_df['area'] == area_name].sort_values('time_code').copy()
        if area_df.empty: continue

        # 統計計算
        avg_price = area_df['price'].mean()
        max_row = area_df.loc[area_df['price'].idxmax()]
        min_row = area_df.loc[area_df['price'].idxmin()]

        # X軸ラベル (00:00, 00:30, ...)
        area_df['time_str'] = area_df['time_code'].apply(code_to_time)

        # --- グラフ生成 ---
        fig = go.Figure()

        # 基本ライン
        fig.add_trace(go.Scatter(
            x=area_df['time_str'], y=area_df['price'],
            mode='lines', line=dict(color='#1f77b4', width=2)
        ))

        # 平均単価線
        fig.add_hline(y=avg_price, line_dash="dash", line_color="orange", 
                      annotation_text=f"AVG: {avg_price:.2f}", 
                      annotation_position="bottom right")

        # 【追加ロジック】08:00〜18:00の間で平均単価を超える時間帯に赤丸と縦線
        # time_code 17(08:00) 〜 36(17:30) が対象
        peak_df = area_df[(area_df['time_code'] >= 17) & (area_df['time_code'] <= 36) & (area_df['price'] > avg_price)]
        
        for _, row in peak_df.iterrows():
            t_str = row['time_str']
            # 赤丸
            fig.add_trace(go.Scatter(
                x=[t_str], y=[row['price']],
                mode='markers', marker=dict(color='red', size=8),
                showlegend=False
            ))
            # 赤い縦線 (vlines)
            fig.add_vline(x=t_str, line_width=1, line_dash="dot", line_color="red", opacity=0.3)

        # 最低値（緑丸）
        fig.add_trace(go.Scatter(
            x=[code_to_time(min_row['time_code'])], y=[min_row['price']],
            mode='markers', marker=dict(color='green', size=12),
            showlegend=False
        ))

        # レイアウト設定
        fig.update_layout(
            title=f"JEPX Price Trend: {target_date} ({area_name})",
            xaxis_title="Time",
            yaxis_title="Price (JPY/kWh)",
            xaxis=dict(
                tickangle=-90,
                tickmode='linear',
                dtick=1 # 全ての時間ラベル(30分単位)を表示
            ),
            yaxis=dict(dtick=5),
            template="plotly_white",
            showlegend=False,
            margin=dict(l=50, r=50, t=80, b=100)
        )

        img_path = f"temp_{area_name}.png"
        fig.write_image(img_path, engine="kaleido", width=1200, height=600)

        # --- メール作成 ---
        msg = MIMEMultipart('related') # 'related'が本文埋め込みに重要
        msg['Subject'] = f"【{target_date} {area_name}エリアJEPX予報レポート】"
        msg['From'] = mail_user
        msg['To'] = target_email

        html = f"""
        <html>
          <body style="font-family: sans-serif; color: #333;">
            <p>{target_date} の {area_name}エリアの市場価格推移です。</p>
            <p style="line-height: 1.6;">
              最高価格：{max_row['price']:.2f}円@{code_to_time(max_row['time_code'])}<br>
              最低価格：{min_row['price']:.2f}円@{code_to_time(min_row['time_code'])}<br>
              平均単価：{avg_price:.2f}円<br>
              <b style="color: red;">※グラフ上の赤丸の時間帯は電気使用量を抑えられたら極力抑えてください！</b>
            </p>
            <div style="margin-top: 20px;">
              <img src="cid:chart_{area_name}" style="width: 100%; max-width: 800px; height: auto; border: 1px solid #eee;">
            </div>
            <p style="color: #666; font-size: 0.8em; margin-top: 15px;">
              ※グラフ内 赤丸：08-18時の平均超過時間 / 緑丸：最安値 / 橙線：平均価格
            </p>
          </body>
        </html>
        """
        msg.attach(MIMEText(html, 'html'))

        # 画像の埋め込み処理
        with open(img_path, 'rb') as f:
            img_data = f.read()
            img = MIMEImage(img_data)
            img.add_header('Content-ID', f'<chart_{area_name}>')
            # 添付ファイルとして出さないためのヘッダー設定
            img.add_header('Content-Disposition', 'inline', filename=os.path.basename(img_path))
            msg.attach(img)

        # 送信
        try:
            with smtplib.SMTP(smtp_server, 587) as server:
                server.starttls()
                server.login(mail_user, mail_pass)
                server.send_message(msg)
            print(f"成功: {area_name}")
        except Exception as e:
            print(f"失敗: {area_name} - {e}")
        
        if os.path.exists(img_path): os.remove(img_path)

if __name__ == "__main__":
    send_daily_reports()
