import os
import pandas as pd
import plotly.graph_objects as go
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
import pytz

# --- Project Zenith: Production Mail System (Ver.19.1) ---

def code_to_time(code):
    """30分刻みのタイムコード(1-48)を hh:mm 形式に変換"""
    m = (int(code) - 1) * 30
    return f"{m // 60:02d}:{m % 60:02d}"

def send_daily_reports():
    JST = pytz.timezone('Asia/Tokyo')
    target_date = (datetime.now(JST) + timedelta(days=1)).date()
    # ★修正2: 文字化け防止のため strftime で明示フォーマット
    date_str = target_date.strftime("%Y-%m-%d")

    areas = ["東京", "東北", "関西", "中国", "九州"]
    target_emails = ["tsukada@inbox.co.jp", "naokazut@gmail.com"]

    try:
        df = pd.read_csv("data/spot_2026.csv")
        df['date'] = pd.to_datetime(df['date']).dt.date
        target_df = df[df['date'] == target_date].copy()

        if target_df.empty:
            print(f"{date_str}のデータがありません。")
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

        # 08:00〜18:00のピーク判定
        peak_df = area_df[(area_df['time_code'] >= 17) & (area_df['time_code'] <= 36) & (area_df['price'] > avg_price)]
        for _, row in peak_df.iterrows():
            t_str = row['time_str']
            fig.add_trace(go.Scatter(x=[t_str], y=[row['price']], mode='markers', marker=dict(color='red', size=8), showlegend=False))
            fig.add_vline(x=t_str, line_width=1, line_dash="dot", line_color="red", opacity=0.3)

        fig.add_trace(go.Scatter(x=[code_to_time(min_row['time_code'])], y=[min_row['price']], mode='markers', marker=dict(color='green', size=12), showlegend=False))

        # ★修正2: date_str を使用（文字化けなし）
        fig.update_layout(
            title=f"JEPX Price Trend: {date_str} {area_name}",
            xaxis_title="Time", yaxis_title="Price (JPY/kWh)",
            xaxis=dict(tickangle=-90, tickmode='linear', dtick=1),
            yaxis=dict(dtick=5), template="plotly_white", showlegend=False,
            margin=dict(l=50, r=50, t=80, b=100)
        )

        img_path = f"temp_{area_name}.png"
        fig.write_image(img_path, engine="kaleido", width=1200, height=600)

        # ★修正1: Outlook対応 - multipart/alternative → multipart/related の入れ子構造
        msg = MIMEMultipart('mixed')
        msg['Subject'] = f"【{date_str} {area_name}エリアJEPX予報レポート】"
        msg['From'] = mail_user
        msg['To'] = ", ".join(target_emails)

        # HTMLとインライン画像をまとめる related パート
        msg_related = MIMEMultipart('related')

        # alternative パートで text/plain + text/html を包む
        msg_alternative = MIMEMultipart('alternative')

        plain_text = (
            f"{date_str} の {area_name}エリアの市場価格推移です。\n"
            f"最高価格：{max_row['price']:.2f}円@{code_to_time(max_row['time_code'])}\n"
            f"最低価格：{min_row['price']:.2f}円@{code_to_time(min_row['time_code'])}\n"
            f"平均単価：{avg_price:.2f}円\n"
        )
        msg_alternative.attach(MIMEText(plain_text, 'plain', 'utf-8'))

        html = f"""
        <html>
          <body style="font-family: sans-serif; color: #333; max-width: 800px;">
            <p>{date_str} の {area_name}エリアの市場価格推移です。</p>
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
              <img src="cid:chart_{area_name}" alt="Price Chart" style="width: 100%; max-width: 800px; height: auto;">
            </div>
          </body>
        </html>
        """
        msg_alternative.attach(MIMEText(html, 'html', 'utf-8'))

        # related に alternative を追加
        msg_related.attach(msg_alternative)

        # ★修正1: インライン画像を related に添付（mixed ではなく related へ）
        with open(img_path, 'rb') as f:
            img = MIMEImage(f.read(), _subtype='png')
            img.add_header('Content-ID', f'<chart_{area_name}>')
            img.add_header('Content-Disposition', 'inline', filename=f'chart_{area_name}.png')
            msg_related.attach(img)

        # mixed に related を追加
        msg.attach(msg_related)

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
