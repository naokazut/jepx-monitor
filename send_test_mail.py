import os
import pandas as pd
import plotly.express as px
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
import pytz

# --- Project Zenith: Mail Test Script (Ver.13.0) ---

def send_test_report():
    JST = pytz.timezone('Asia/Tokyo')
    target_date = (datetime.now(JST) + timedelta(days=1)).date()
    
    # 1. データ読み込み
    try:
        df = pd.read_csv("data/spot_2026.csv")
        df['date'] = pd.to_datetime(df['date']).dt.date
        target_df = df[df['date'] == target_date].copy()
        
        if target_df.empty:
            print(f"{target_date}のデータがまだありません。本日のデータでテストします。")
            target_date = datetime.now(JST).date()
            target_df = df[df['date'] == target_date].copy()
    except Exception as e:
        print(f"データ読み込みエラー: {e}")
        return

    # 2. グラフ生成 (東京エリアを例に)
    area = "東京"
    plot_df = target_df[target_df['area'] == area].sort_values('time_code')
    
    fig = px.line(plot_df, x='time_code', y='price', title=f"{target_date} {area}エリア価格予報", markers=True)
    fig.update_layout(template="plotly_dark")
    
    # 画像として一時保存
    img_path = "temp_chart.png"
    fig.write_image(img_path, engine="kaleido")

    # 3. メール作成
    mail_user = os.environ.get('MAIL_ADDRESS')
    mail_pass = os.environ.get('MAIL_PASSWORD')
    smtp_server = os.environ.get('SMTP_SERVER')
    to_email = "tsukada@inbox.co.jp"

    msg = MIMEMultipart('related')
    msg['Subject'] = f"【Zenithテスト】{target_date} JEPX予報レポート"
    msg['From'] = mail_user
    msg['To'] = to_email

    # 本文（HTML形式で画像を埋め込み）
    html = f"""
    <html>
      <body>
        <h3>Project Zenith: 自動配信テスト</h3>
        <p>{target_date} の {area}エリアの価格グラフです。</p>
        <img src="cid:chart_img">
        <p>※このメールはシステムによる自動テスト配信です。</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))

    # 画像を添付
    with open(img_path, 'rb') as f:
        img_data = f.read()
        image = MIMEImage(img_data)
        image.add_header('Content-ID', '<chart_img>')
        msg.attach(image)

    # 4. 送信実行
    try:
        with smtplib.SMTP(smtp_server, 587) as server:
            server.starttls()
            server.login(mail_user, mail_pass)
            server.send_message(msg)
        print("テストメール送信成功！")
    except Exception as e:
        print(f"送信失敗: {e}")

if __name__ == "__main__":
    send_test_report()
