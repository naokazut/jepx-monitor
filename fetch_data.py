import requests
import pandas as pd
import os
import io
import sys
from datetime import datetime
import pytz
import time

# --- Project Zenith: JEPX Data Fetcher (Version 10) ---
# 【修正】2020年度から現在まで全年度のデータを一括・逐次取得し、蓄積する仕様に変更。

def fetch_jepx_data():
    JST = pytz.timezone('Asia/Tokyo')
    now = datetime.now(JST)

    # 現在の会計年度を計算
    current_fiscal_year = now.year if now.month >= 4 else now.year - 1
    
    # 2020年度から現在までをターゲットにする
    target_years = range(2020, current_fiscal_year + 1)
    
    os.makedirs('data', exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    success_count = 0

    for fy in target_years:
        url = f"https://www.jepx.jp/market/excel/spot_{fy}.csv"
        save_path = f"data/spot_{fy}.csv"
        
        print(f"年度 {fy} のデータを取得中: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            response.encoding = 'shift_jis'
            
            if '<html' in response.text.lower():
                print(f"警告: 年度 {fy} はまだ公開されていないか、アクセス制限されています。スキップします。")
                continue
            
            # CSV読み込み
            df = pd.read_csv(io.StringIO(response.text))
            
            # 列名の定義
            date_col = '年月日'
            time_col = '時刻コード'
            area_keywords = ['システム値', '東京', '関西', '九州', '北海道', '東北', '中部', '北陸', '中国', '四国']
            
            found_columns = {}
            for kw in area_keywords:
                actual_col = next((c for c in df.columns if kw in c), None)
                if actual_col:
                    found_columns[actual_col] = kw

            if not found_columns:
                print(f"警告: 年度 {fy} のCSV内にエリア列が見つかりません。")
                continue

            # 形式変換
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
            
            # 保存
            df_final.to_csv(save_path, index=False)
            print(f"成功: 年度 {fy} ({len(df_final)}件) を保存しました。")
            success_count += 1
            
            # サーバー負荷軽減のための待機
            time.sleep(1)

        except Exception as e:
            print(f"年度 {fy} の処理中にエラーが発生しました: {e}")
            continue

    if success_count == 0:
        print("エラー: 1件もデータを取得できませんでした。")
        sys.exit(1)
    else:
        print(f"完了: 合計 {success_count} 年度分のデータを処理しました。")

if __name__ == "__main__":
    fetch_jepx_data()
