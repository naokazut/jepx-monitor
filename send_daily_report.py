import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
import pytz

# --- Project Zenith: Production Mail System (Ver.13.0) ---

def send_daily_reports():
    JST = pytz.timezone('Asia/Tokyo')
    # 翌日分の日付を取得
    target_date = (datetime.now(JST) + timedelta(days=1)).date()
    
    # 配信設定
    areas = ["東京", "東北", "関西", "中国", "九州"]
    target_email = "tsukada@inbox.co.jp"
    
    # 1. データ読み込み
    try:
        df = pd.read_csv("data/spot_2026.csv")
        df['date'] = pd.to_datetime(df['date']).dt.date
        target_df = df[df['date'] == target_date].copy()
        
        if target_df.empty:
            print(f"{target_date}のデータがまだありません。処理を中断します。")
            return
    except Exception as e:
        print(f"データ読み込みエラー: {e}")
        return

    # メールサーバー設定 (GitHub Secretsから取得)
    mail_user = os.environ.get('MAIL_ADDRESS')
    mail_pass = os.environ.get('MAIL_PASSWORD')
    smtp_server = os.environ.get('SMTP_SERVER')

    for area_name in areas:
        area_df = target_df[target_df['area'] == area_name].sort_values('time_code')
        if area_df.empty:
            continue

        # 統計計算
        avg_price = area_df['price'].mean()
        max_row = area_df.loc[area_df['price'].idxmax()]
        min_row = area_df.loc[area_df['price'].idxmin()]
        top3_rows = area_df.nlargest(3, 'price')

        # 2. グラフ生成
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=area_df['time_code'], y=area_df['price'], mode='lines', line=dict(color='#1f77b4', width=2)))
        fig.add_hline(y=avg_price, line_dash="dash", line_color="orange", 
                      annotation_text=f"AVG: {avg_price:.2f}", annotation_position="bottom right")
        fig.add_trace(go.Scatter(x=top3_rows['time_code'], y=top3_rows['price'], mode='markers', marker=dict(color='red', size=10)))
        fig.add_trace(go.Scatter(x=[min_row['time_code']], y=[min_row['price']], mode='markers', marker=dict(color='green', size=12)))

        fig.update_layout(
            title=f"JEPX Forecast: {target_date} ({area_name})",
            xaxis_title="Time Code (1-48)", yaxis_title="Price (JPY/kWh)",
            template="plotly_white", showlegend=False
        )

        img_path = f"temp_{area_name}.png"
        fig.write_image(img_path, engine="kaleido")

        # 3. メール作成
        msg = MIMEMultipart('related')
        msg['Subject'] = f"【{target_date} {area_name}エリアJEPX予報レポート】"
        msg['From'] = mail_user
        msg['To'] = target_email

        def code_to_time(code):
            m = (int(code) - 1) * 30
            return f"{m // 60:02d}:{m % 60:02d}"

        html = f"""
        <html>
          <body style="font-family: sans-serif;">
            <p>{target_date} の {area_name}エリアの市場価格推移です。</p>
            <p>
              <b>最高価格：</b>{code_to_time(max_row['time_code'])}　{max_row['price']:.2f}円<br>
              <b>最低価格：</b>{code_to_time(min_row['time_code'])}　{min_row['price']:.2f}円<br>
              <b>平均単価：</b>{avg_price:.2f}円
            </p>
            <img src="cid:chart_{area_name}">
            <p style="color: #666; font-size: 0.8em;">※赤丸：上位3位 / 緑丸：最安値 / 橙線：平均単価</p>
          </body>
        </html>
        """
        msg.attach(MIMEText(html, 'html'))

        with open(img_path, 'rb') as f:
            img = MIMEImage(f.read())
            img.add_header('Content-ID', f'<chart_{area_name}>')
            msg.attach(img)

        # 4. 送信
        try:
            with smtplib.SMTP(smtp_server, 587) as server:
                server.starttls()
                server.login(mail_user, mail_pass)
                server.send_message(msg)
            print(f"成功: {area_name} 配信完了")
        except Exception as e:
            print(f"失敗: {area_name} - {e}")
        
        if os.path.exists(img_path): os.remove(img_path)

if __name__ == "__main__":
    send_daily_reports()
