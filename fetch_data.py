import requests
import pandas as pd
import os
import io
import sys
from datetime import datetime
import pytz

# --- Project Zenith: JEPX Data Fetcher (Version 11) ---

def fetch_jepx_data():
    JST = pytz.timezone('Asia/Tokyo')
    now = datetime.now(JST)
    fy = now.year if now.month >= 4 else now.year - 1

    os.makedirs('data', exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

    url = f"https://www.jepx.jp/market/excel/spot_{fy}.csv"
    save_path = f"data/spot_{fy}.csv"

    print(f"年度 {fy} のデータを取得中: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = 'shift_jis'

        if '<html' in response.text.lower():
            print(f"エラー: 年度 {fy} はまだ公開されていないか、アクセス制限されています。")
            sys.exit(1)

        df = pd.read_csv(io.StringIO(response.text))

        date_col = '年月日'
        time_col = '時刻コード'
        area_keywords = ['システム値', '東京', '関西', '九州', '北海道', '東北', '中部', '北陸', '中国', '四国']

        found_columns = {}
        for kw in area_keywords:
            actual_col = next((c for c in df.columns if kw in c), None)
            if actual_col:
                found_columns[actual_col] = kw

        if not found_columns:
            print(f"エラー: CSV内にエリア列が見つかりません。")
            sys.exit(1)

        df_melted = pd.melt(
            df,
            id_vars=[date_col, time_col],
            value_vars=list(found_columns.keys()),
            var_name='raw_area',
            value_name='price'
        )

        df_melted['area'] = df_melted['raw_area'].map(found_columns)
        df_final = df_melted.rename(columns={date_col: 'date', time_col: 'time_code'})
        df_final = df_final[['date', 'time_code', 'area', 'price']]

        df_final.to_csv(save_path, index=False)
        print(f"成功: 年度 {fy} ({len(df_final)}件) を保存しました。")

    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fetch_jepx_data()
