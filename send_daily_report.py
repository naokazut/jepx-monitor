import os
import pandas as pd
import plotly.graph_objects as go
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
import pytz

# --- Project Zenith: Production Mail System (Ver.15.0) ---

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
        area_df = target_df[target_df['area'] == area_name].sort_values('time_code')
        if area_df.empty: continue

        # 統計計算
        avg_price = area_df['price'].mean()
        max_row = area_df.loc[area_df['price'].idxmax()]
        min_row = area_df.loc[area_df['price'].idxmin()]

        # X軸ラベルの作成
        time_labels = [code_to_time(c) for c in area_df['time_code']]

        # --- グラフ生成 ---
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=time_labels, y=area_df['price'],
            mode='lines', line=dict(color='#1f77b4', width=2)
        ))

        # 平均価格線
        fig.add_hline(y=avg_price, line_dash="dash", line_color="orange", 
                      annotation_text=f"Average: {avg_price:.2f}", 
                      annotation_position="bottom right")

        # 最高値（赤丸）
        fig.add_trace(go.Scatter(
            x=[code_to_time(max_row['time_code'])], y=[max_row['price']],
            mode='markers', marker=dict(color='red', size=12)
        ))

        # 最低値（緑丸）
        fig.add_trace(go.Scatter(
            x=[code_to_time(min_row['time_code'])], y=[min_row['price']],
            mode='markers', marker=dict(color='green', size=12)
        ))

        # レイアウト設定（nbinsxを削除し、日本語ラベルを一旦英語にして文字化け回避）
        fig.update_layout(
            title=f"JEPX Price Trend: {target_date} ({area_name})",
            xaxis_title="Time",
            yaxis_title="Spot Price (JPY/kWh)",
            xaxis=dict(
                tickangle=-45,
                tickmode='linear',
                dtick=4 # 2時間おきに表示して重なりを防ぐ
            ),
            yaxis=dict(dtick=5),
            template="plotly_white",
            showlegend=False
        )

        img_path = f"temp_{area_name}.png"
        # kaleidoを使用して画像保存
        fig.write_image(img_path, engine="kaleido")

        # --- メール作成 ---
        msg = MIMEMultipart('related')
        msg['Subject'] = f"【{target_date} {area_name}エリアJEPX予報レポート】"
        msg['From'] = mail_user
        msg['To'] = target_email

        # 本文（HTML埋め込み）
        html = f"""
        <html>
          <body style="font-family: sans-serif;">
            <p>{target_date} の {area_name}エリアの市場価格推移です。</p>
            <p style="line-height: 1.6;">
              最高価格：{max_row['price']:.2f}円@{code_to_time(max_row['time_code'])}<br>
              最低価格：{min_row['price']:.2f}円@{code_to_time(min_row['time_code'])}<br>
              平均単価：{avg_price:.2f}円
            </p>
            <img src="cid:chart_{area_name}" style="max-width: 100%; height: auto;">
            <p style="color: #666; font-size: 0.8em;">※グラフ内 赤丸：最高値 / 緑丸：最安値 / 橙線：平均価格</p>
          </body>
        </html>
        """
        msg.attach(MIMEText(html, 'html'))

        # 画像をインラインとして添付
        with open(img_path, 'rb') as f:
            img = MIMEImage(f.read())
            img.add_header('Content-ID', f'<chart_{area_name}>')
            img.add_header('Content-Disposition', 'inline', filename=img_path)
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
