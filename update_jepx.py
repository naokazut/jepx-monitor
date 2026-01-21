import requests
import pandas as pd
import io
import os
from datetime import datetime

# --- 設定 ---
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def get_fiscal_year():
    """現在の年度を計算（4月基準）"""
    now = datetime.now()
    return now.year - 1 if now.month <= 3 else now.year

def fetch_historical_archive(current_fy):
    """過去の一括データを取得し、年度別に分割保存"""
    print(f"--- Archive Processing (Up to {current_fy - 1}) ---")
    # 2005-2024の一括アーカイブを使用
    url = "https://www.jepx.org/market/excel/spot_2005-2024.csv"
    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            # エンコーディングエラーを回避するための設定
            df = pd.read_csv(io.BytesIO(response.content), encoding='shift_jis', on_bad_lines='skip')
            df['年月日'] = pd.to_datetime(df['年月日'])
            
            # 2010年度から前年度までを切り出し
            for year in range(2010, current_fy):
                file_path = os.path.join(DATA_DIR, f"spot_{year}.csv")
                # 既にファイルがある場合はスキップして効率化
                if os.path.exists(file_path):
                    continue
                
                start_date = f"{year}-04-01"
                end_date = f"{year+1}-03-31"
                year_df = df[(df['年月日'] >= start_date) & (df['年月日'] <= end_date)]
                
                if not year_df.empty:
                    year_df.to_csv(file_path, index=False, encoding='shift_jis')
                    print(f"✅ Created Archive: {file_path}")
    except Exception as e:
        print(f"⚠️ Historical Archive Skip or Error: {e}")

def fetch_latest_year(year):
    """最新年度（今年度）のデータを取得"""
    print(f"--- Fetching Current Fiscal Year: {year} ---")
    url = f"https://www.jepx.org/market/excel/spot_{year}.csv"
    try:
        res = requests.get(url, timeout=30)
        if res.status_code == 200:
            file_path = os.path.join(DATA_DIR, f"spot_{year}.csv")
            with open(file_path, "wb") as f:
                f.write(res.content)
            print(f"✅ Updated Latest: {file_path}")
            return True
    except Exception as e:
        print(f"❌ Error fetching {year}: {e}")
    return False

def main():
    fy = get_fiscal_year()
    # 過去分(2010-2024)の構築
    fetch_historical_archive(fy)
    # 最新分(2025以降)の取得
    fetch_latest_year(fy)

if __name__ == "__main__":
    main()
