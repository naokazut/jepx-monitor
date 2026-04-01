import os
import pandas as pd
import plotly.graph_objects as go
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
import pytz

# --- Project Zenith: Production Mail System (Ver.18.0) ---

def code_to_time(code):
    """30分刻みのタイムコード(1-48)を hh:mm 形式に変換"""
    m = (int(code) - 1) * 30
    return f"{m // 60:02d}:{m % 60:02d}"

def send_daily_reports():
    JST = pytz.timezone('Asia/Tokyo')
    target_date = (datetime.now(JST) + timedelta(days=1)).date()
    
    areas = ["東京", "東北", "関西", "中国", "九州"]
    # 送信先リストにGmailを追加
    target_emails = ["tsukada@inbox.co.jp", "naokazut@gmail.com"]
    
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

        avg_price = area_df['price'].mean()
        max_row = area_df.loc[area_df['price'].idxmax()]
        min_row = area_df.loc[area_df['price'].idxmin()]
        area_df['time_str'] = area_df['time_code'].apply(code_to_time)

        # --- グラフ生成 ---
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=area_df['time_str'], y=area_df['price'], mode='lines', line=dict(color='#1f77b4', width=2)))
        fig.add_hline(y=avg_price, line_dash="dash", line_color="orange", annotation_text=f"AVG: {avg_price:.2f}", annotation_position="bottom right")

        # 08:00(17)〜18:00(36)のピーク判定
        peak_df = area_df[(area_df['time_code'] >= 17) & (area_df['time_code'] <= 36) & (area_df['price'] > avg_price)]
        for _, row in peak_df.iterrows():
            t_str = row['time_str']
            fig.add_trace(go.Scatter(x=[t_str], y=[row['price']], mode='markers', marker=dict(color='red', size=8), showlegend=False))
            fig.add_vline(x=t_str, line_width=1, line_dash="dot", line_color="red", opacity=0.3)

        fig.add_trace(go.Scatter(x=[code_to_time(min_row['time_code'])], y=[min_row['price']], mode='markers', marker=dict(color='green', size=12), showlegend=False))

        fig.update_layout(
            title=f"JEPX Price Trend: {target_date} ({area_name})",
            xaxis_title="Time", yaxis_title="Price (JPY/kWh)",
            xaxis=dict(tickangle=-90, tickmode='linear', dtick=1),
            yaxis=dict(dtick=5), template="plotly_white", showlegend=False,
            margin=dict(l=50, r=50, t=80, b=100)
        )

        img_path = f"temp_{area_name}.png"
        fig.write_image(img_path, engine="kaleido", width=1200, height=600)

        # --- メール作成 ---
        msg = MIMEMultipart('related')
        msg['Subject'] = f"【{target_date} {area_name}エリアJEPX予報レポート】"
        msg['From'] = mail_user
        msg['To'] = ", ".join(target_emails) # 複数宛先に送信

        # 本文の文言修正
        html = f"""
        <html>
          <body style="font-family: sans-serif; color: #333; max-width: 800px;">
            <p>{target_date} の {area_name}エリアの市場価格推移です。</p>
            <p style="line-height: 1.6;">
              最高価格：{max_row['price']:.2f}円@{code_to_time(max_row['time_code'])}<br>
              最低価格：{min_row['price']:.2f}円@{code_to_time(min_row['time_code'])}<br>
              平均単価：{avg_price:.2f}円<br>
              <b style="color: red;">
                ※グラフ上の赤丸は、平日の午前8時から午後6時までの間で、その日の平均単価より価格が高い時間帯を示しています。<br>
                そのため該当時間帯に電気使用量を抑えられる場合は、極力抑えコスト抑制にご尽力ください！
              </b>
            </p>
            <div style="margin-top: 20px;">
              <img src="cid:chart_{area_name}" style="width: 100%; height: auto; display: block; border: 1px solid #ddd;">
            </div>
            <p style="color: #666; font-size: 0.8em; margin-top: 15px;">
              ※グラフ内 赤丸：対象時間の価格高騰 / 緑丸：最安値 / 橙線：平均価格
            </p>
          </body>
        </html>
        """
        msg.attach(MIMEText(html, 'html'))

        # 画像の埋め込み処理
        with open(img_path, 'rb') as f:
            img = MIMEImage(f.read())
            img.add_header('Content-ID', f'<chart_{area_name}>')
            img.add_header('Content-Disposition', 'inline', filename=img_path)
            msg.attach(img)

        # 送信実行
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
