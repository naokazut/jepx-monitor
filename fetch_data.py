import requests
import pandas as pd
import os
import io
import sys
from datetime import datetime
import pytz

def fetch_jepx_data():
    JST = pytz.timezone('Asia/Tokyo')
    now = datetime.now(JST)
    fy = now.year if now.month >= 4 else now.year - 1
    target_date = now.strftime('%Y/%m/%d')

    os.makedirs('data', exist_ok=True)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/91.0.4472.124 Safari/537.36"
    }

    url = f"https://www.jepx.jp/market/excel/spot_{fy}.csv"
    save_path = f"data/spot_{fy}.csv"

    print(f"[{now.strftime('%H:%M:%S')} JST] 取得開始")
    print(f"対象日: {target_date}")

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = 'shift_jis'

        # チェック1: HTMLが返ってきていないか
        if '<html' in response.text.lower():
            print("FAIL: HTMLレスポンス（アクセス制限）")
            sys.exit(1)

        df = pd.read_csv(io.StringIO(response.text))
        date_col = '年月日'
        time_col = '時刻コード'

        # チェック2: 必須列の存在確認
        if date_col not in df.columns or time_col not in df.columns:
            print(f"FAIL: 必須列なし。検出列: {list(df.columns)}")
            sys.exit(1)

        # チェック3: 当日データの存在確認
        latest_date = df[date_col].max()
        print(f"CSV最新日付: {latest_date} / 期待: {target_date}")

        if latest_date < target_date:
            print(f"FAIL: 当日データ未公開。retryします。")
            sys.exit(1)

        # チェック4: エリア列の存在確認
        area_keywords = [
            'システム値', '東京', '関西', '九州',
            '北海道', '東北', '中部', '北陸', '中国', '四国'
        ]
        found_columns = {}
        for kw in area_keywords:
            actual_col = next((c for c in df.columns if kw in c), None)
            if actual_col:
                found_columns[actual_col] = kw

        if not found_columns:
            print(f"FAIL: エリア列なし。検出列: {list(df.columns)}")
            sys.exit(1)

        # 変換・保存
        df_melted = pd.melt(
            df,
            id_vars=[date_col, time_col],
            value_vars=list(found_columns.keys()),
            var_name='raw_area',
            value_name='price'
        )
        df_melted['area'] = df_melted['raw_area'].map(found_columns)
        df_final = df_melted.rename(
            columns={date_col: 'date', time_col: 'time_code'}
        )
        df_final = df_final[['date', 'time_code', 'area', 'price']]

        # チェック5: 当日データの完全性確認
        expected_rows_per_day = len(found_columns) * 48
        today_rows = df_final[df_final['date'] == target_date]
        if len(today_rows) < expected_rows_per_day:
            print(f"FAIL: 当日データ不完全 "
                  f"({len(today_rows)}/{expected_rows_per_day}件)")
            sys.exit(1)

        df_final.to_csv(save_path, index=False)
        print(f"SUCCESS: {len(df_final)}件保存 / 当日{len(today_rows)}件確認")

    except SystemExit:
        raise
    except Exception as e:
        print(f"FAIL: 予期しないエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fetch_jepx_data()
