import requests
import pandas as pd
import io
import os

def fetch_and_save():
    url = "https://www.jepx.jp/_download.php"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.jepx.jp/electricpower/market-data/spot/",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {"dir": "spot_summary", "file": "spot_summary_2025.csv"}

    res = requests.post(url, headers=headers, data=payload, timeout=15)
    res.raise_for_status()
    
    # Colabで成功した読み込み設定
    df = pd.read_csv(io.BytesIO(res.content), encoding="cp932")
    df.columns = df.columns.str.strip()
    
    # 列名を扱いやすく変換
    mapping = {'受渡日': 'date', '時刻コード': 'time_code', 'システムプライス(円/kWh)': 'price'}
    df = df.rename(columns=mapping)
    
    # データを保存
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/spot_2025.csv", index=False, encoding="utf-8")
    print("Successfully saved data.")

if __name__ == "__main__":
    fetch_and_save()
